"""
SQLite-backed data access layer for the VIA index.

TLDR:
    Provides the DatabaseStore class, which wraps a SQLite connection and
    exposes CRUD operations for files, symbols, and relationships. Symbols are
    stored in a denormalized table (file_path inline) to allow zero-JOIN
    lookups via match(). Relationship resolution uses a two-pass strategy:
    insert_pending_relationship() during indexing, then
    resolve_pending_relationships() after all symbols exist. The @require_connection
    decorator enforces connection state; explicit begin/commit/rollback methods
    allow batching writes for performance.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import sqlite3
import time
from functools import wraps
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar

from ..core.match_record import MatchRecord, MatchRecordFactory
from ..core.types import MatchOp, SymbolType
from .schema import (
    ALL_TABLES,
    CREATE_INDEXES,
    CREATE_LINE_OFFSETS_TABLE,
    SCHEMA_VERSION,
)

F = TypeVar('F', bound=Callable[..., Any])


def require_connection(func: F) -> F:
    """Decorator that ensures database connection exists.

    Raises:
        RuntimeError: If database is not connected
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.conn:
            raise RuntimeError("Database not connected")
        return func(self, *args, **kwargs)
    return wrapper  # type: ignore


class DatabaseStore:
    """Manages SQLite database for code index."""

    def __init__(self, db_path: str, index_root: str):
        """
        Initialize database store.

        Args:
            db_path: Path to SQLite database file
            index_root: Absolute path to the root directory being indexed
        """
        self.db_path = db_path
        self.index_root = os.path.abspath(index_root)
        self.conn: Optional[sqlite3.Connection] = None
        self._in_transaction = False
        self._record_factory = MatchRecordFactory()

    def connect(self) -> None:
        """Connect to database and enable foreign keys and WAL mode."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        # SQLite has autocommit off by default when using execute()
        self.conn.isolation_level = None  # Enable autocommit mode

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    @require_connection
    def initialize_schema(self) -> None:
        """Create all tables and indexes if they don't exist, applying migrations as needed."""
        cursor = self.conn.cursor()

        # Create core tables (metadata must exist first to read current version)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at REAL NOT NULL,
                description TEXT
            );
        """)
        self._commit_if_needed()

        # Read current schema version (0 if fresh database)
        cursor.execute("SELECT value FROM metadata WHERE key = 'schema_version'")
        row = cursor.fetchone()
        current_version = int(row[0]) if row else 0

        # Create all tables (IF NOT EXISTS — safe for existing DBs)
        for table_sql in ALL_TABLES:
            cursor.execute(table_sql)

        # Create all indexes
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)

        # Apply incremental migrations for existing databases
        if current_version < 4:
            cursor.execute(CREATE_LINE_OFFSETS_TABLE)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_line_offsets_file ON line_offsets(file_id)"
            )
            cursor.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)"
                " VALUES (?, ?, ?)",
                (4, time.time(), "Add line_offsets table for -mL line slice queries")
            )

        if current_version < 5:
            # Only ALTER if symbols.mtime column doesn't already exist.
            # Fresh DBs have it from CREATE_SYMBOLS_TABLE; old DBs need ALTER.
            existing_cols = {
                row[1] for row in cursor.execute("PRAGMA table_info(symbols)")
            }
            if 'mtime' not in existing_cols:
                cursor.execute("ALTER TABLE symbols ADD COLUMN mtime REAL")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbols_mtime ON symbols(mtime)"
            )
            cursor.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)"
                " VALUES (?, ?, ?)",
                (5, time.time(), "Add symbols.mtime for temporal query operators")
            )

        if current_version < 6:
            existing_cols = {
                row[1] for row in cursor.execute("PRAGMA table_info(symbols)")
            }
            if 'language' not in existing_cols:
                cursor.execute("ALTER TABLE symbols ADD COLUMN language TEXT")
                # Backfill language from files table for existing rows
                cursor.execute(
                    "UPDATE symbols SET language = ("
                    "  SELECT f.language FROM files f WHERE f.path = symbols.file_path"
                    ") WHERE language IS NULL"
                )
            if 'symbol_subtype' not in existing_cols:
                cursor.execute("ALTER TABLE symbols ADD COLUMN symbol_subtype TEXT")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbols_language ON symbols(language)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbols_subtype ON symbols(symbol_subtype)"
            )
            cursor.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)"
                " VALUES (?, ?, ?)",
                (6, time.time(), "Add symbols.language and symbols.symbol_subtype columns")
            )

        # Store metadata
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("index_root", self.index_root)
        )
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION))
        )

        # Record initial schema migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
            VALUES (?, ?, ?)
            """,
            (SCHEMA_VERSION, time.time(), "Initial schema")
        )

        self._commit_if_needed()

    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Metadata value or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def _to_relative_path(self, abs_path: str) -> str:
        """
        Convert absolute path to relative path from index root.

        Args:
            abs_path: Absolute file path

        Returns:
            Relative path from index root
        """
        return os.path.relpath(abs_path, self.index_root)

    def _to_absolute_path(self, rel_path: str) -> str:
        """
        Convert relative path to absolute path.

        Args:
            rel_path: Relative path from index root

        Returns:
            Absolute file path
        """
        return os.path.join(self.index_root, rel_path)

    # File CRUD operations

    def insert_file(
        self,
        path: str,
        language: Optional[str] = None,
        size_bytes: Optional[int] = None,
        mtime: Optional[float] = None,
        parsed: bool = False,
        oversized: bool = False,
    ) -> int:
        """
        Insert a file record.

        Args:
            path: Absolute file path
            language: Programming language ('python', 'markdown', etc.)
            size_bytes: File size in bytes
            mtime: File modification time (timestamp)
            parsed: Whether file has been parsed
            oversized: Whether file exceeded size limit

        Returns:
            File ID
        """
        rel_path = self._to_relative_path(path)
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO files (path, language, size_bytes, mtime, indexed_at, parsed, oversized)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (rel_path, language, size_bytes, mtime, time.time(), parsed, oversized)
        )
        self._commit_if_needed()
        return cursor.lastrowid

    def update_file(
        self,
        file_id: int,
        language: Optional[str] = None,
        size_bytes: Optional[int] = None,
        mtime: Optional[float] = None,
        parsed: Optional[bool] = None,
    ) -> None:
        """
        Update file record.

        Args:
            file_id: File ID
            language: Programming language
            size_bytes: File size in bytes
            mtime: File modification time
            parsed: Whether file has been parsed
        """
        updates = []
        params = []

        if language is not None:
            updates.append("language = ?")
            params.append(language)
        if size_bytes is not None:
            updates.append("size_bytes = ?")
            params.append(size_bytes)
        if mtime is not None:
            updates.append("mtime = ?")
            params.append(mtime)
        if parsed is not None:
            updates.append("parsed = ?")
            params.append(parsed)

        if not updates:
            return

        updates.append("indexed_at = ?")
        params.append(time.time())
        params.append(file_id)

        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE files SET {', '.join(updates)} WHERE id = ?",
            params
        )
        self._commit_if_needed()

    def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get file record by path.

        Args:
            path: Absolute file path

        Returns:
            File record as dict or None if not found
        """
        rel_path = self._to_relative_path(path)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE path = ?", (rel_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get file record by ID.

        Args:
            file_id: File ID

        Returns:
            File record as dict or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_files(self, parsed_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all file records.

        Args:
            parsed_only: If True, only return parsed files

        Returns:
            List of file records as dicts
        """
        cursor = self.conn.cursor()
        if parsed_only:
            cursor.execute("SELECT * FROM files WHERE parsed = 1")
        else:
            cursor.execute("SELECT * FROM files")
        return [dict(row) for row in cursor.fetchall()]

    def delete_file(self, file_id: int) -> None:
        """
        Delete file record (cascades to all entities).

        Args:
            file_id: File ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        self._commit_if_needed()

    def delete_file_by_path(self, path: str) -> None:
        """
        Delete file record by path.

        Args:
            path: Absolute file path
        """
        rel_path = self._to_relative_path(path)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE path = ?", (rel_path,))
        self._commit_if_needed()

    def delete_file_completely(self, path: str) -> None:
        """Delete a file and all its symbols and relationships atomically.

        FK CASCADE on symbol_references handles relationship cleanup when symbols
        are deleted. Replaces the three-step delete pattern in WatchService._remove_file().

        Args:
            path: Absolute file path
        """
        rel_path = self._to_relative_path(path)
        # Symbols table stores absolute paths; files table stores relative paths.
        cursor = self.conn.cursor()
        cursor.execute("BEGIN")
        try:
            # Delete symbols — FK CASCADE removes dependent symbol_references rows
            cursor.execute("DELETE FROM symbols WHERE file_path = ?", (path,))
            # Delete file record (stored with relative path)
            cursor.execute("DELETE FROM files WHERE path = ?", (rel_path,))
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise

    # Line offset methods (Sprint 8)

    def upsert_line_offsets(
        self,
        file_id: int,
        offsets: List[tuple],
    ) -> None:
        """Insert or replace line byte offsets for a file (atomic).

        Deletes existing rows for file_id then bulk-inserts new ones.
        Safe to call within an outer transaction.

        Args:
            file_id: File ID (FK to files.id)
            offsets: List of (file_id, line_number, byte_offset, byte_length) tuples
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM line_offsets WHERE file_id = ?", (file_id,))
        cursor.executemany(
            "INSERT INTO line_offsets (file_id, line_number, byte_offset, byte_length)"
            " VALUES (?, ?, ?, ?)",
            offsets,
        )
        self._commit_if_needed()

    def get_line_byte_range(
        self,
        file_path: str,
        abs_start: int,
        abs_end: int,
    ) -> tuple:
        """Return (byte_offset, byte_length) covering lines abs_start..abs_end inclusive.

        Line numbers are 1-based absolute file line numbers.
        Returns (0, 0) if the file or lines are not found in the index.

        Args:
            file_path: Absolute file path
            abs_start: First line number (1-based, inclusive)
            abs_end: Last line number (1-based, inclusive)

        Returns:
            (byte_offset, byte_length) tuple
        """
        rel_path = self._to_relative_path(file_path)
        row = self.conn.execute(
            """
            SELECT
                MIN(lo.byte_offset)                                         AS start_off,
                MAX(lo.byte_offset) + MAX(lo.byte_length) - MIN(lo.byte_offset) AS length
            FROM line_offsets lo
            JOIN files f ON lo.file_id = f.id
            WHERE f.path = ?
              AND lo.line_number BETWEEN ? AND ?
            """,
            (rel_path, abs_start, abs_end),
        ).fetchone()
        if not row or row[0] is None:
            return (0, 0)
        return (row[0], row[1])

    def get_line_count(self, file_path: str) -> int:
        """Return total indexed line count for a file.

        Used for resolving negative slice indices (last N lines).

        Args:
            file_path: Absolute file path

        Returns:
            Total line count, or 0 if file not indexed
        """
        rel_path = self._to_relative_path(file_path)
        row = self.conn.execute(
            """
            SELECT MAX(lo.line_number)
            FROM line_offsets lo
            JOIN files f ON lo.file_id = f.id
            WHERE f.path = ?
            """,
            (rel_path,),
        ).fetchone()
        return row[0] if row and row[0] else 0

    # Symbol CRUD operations

    def insert_symbol(
        self,
        symbol_name: str,
        symbol_type: str,
        file_path: str,
        line_number: int,
        qualified_name: str,
        byte_offset: Optional[int] = None,
        byte_length: Optional[int] = None,
        parent_name: Optional[str] = None,
        mtime: Optional[float] = None,
        language: Optional[str] = None,
        symbol_subtype: Optional[str] = None,
    ) -> int:
        """
        Insert a symbol record into the denormalized symbols table.

        Args:
            symbol_name: Simple symbol name (e.g., 'save', 'User')
            symbol_type: Symbol type (method, class, function, filepath, filename, import, global)
            file_path: Relative file path
            line_number: Starting line number
            qualified_name: Fully qualified name (e.g., 'models.user.User.save')
            byte_offset: Byte offset in file (None for files)
            byte_length: Symbol byte length (None for files)
            parent_name: Parent class name for methods (None otherwise)
            mtime: File modification time (Unix timestamp) when symbol was indexed
            language: Source language ('python', 'javascript', 'typescript', 'markdown')
            symbol_subtype: Optional subtype ('interface', 'enum', 'arrow_function', etc.)

        Returns:
            Symbol ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO symbols (
                symbol_name, symbol_type, file_path, line_number,
                byte_offset, byte_length, qualified_name, parent_name, mtime,
                language, symbol_subtype
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol_name, symbol_type, file_path, line_number,
             byte_offset, byte_length, qualified_name, parent_name, mtime,
             language, symbol_subtype)
        )
        self._commit_if_needed()
        return cursor.lastrowid

    def delete_symbols_by_file(self, file_path: str) -> None:
        """
        Delete all symbol records for a file.

        Args:
            file_path: Relative file path
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM symbols WHERE file_path = ?",
            (file_path,)
        )
        self._commit_if_needed()

    # Batch operations for performance

    @require_connection
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._in_transaction = True
        self.conn.execute("BEGIN TRANSACTION")

    @require_connection
    def commit_transaction(self) -> None:
        """Commit current transaction."""
        self.conn.commit()
        self._in_transaction = False

    @require_connection
    def rollback_transaction(self) -> None:
        """Rollback current transaction."""
        self.conn.rollback()
        self._in_transaction = False

    def _commit_if_needed(self) -> None:
        """Commit if not in a transaction."""
        if not self._in_transaction and self.conn:
            self.conn.commit()

    @require_connection
    def match(
        self,
        symbol_type: Optional[SymbolType],
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool = True,
        limit: Optional[int] = None,
        match_qualified: bool = False,
        newerthan_seconds: Optional[float] = None,
        olderthan_seconds: Optional[float] = None,
        negated: bool = False,
    ) -> Iterator[MatchRecord]:
        """
        Match symbols using denormalized symbols table.

        Args:
            symbol_type: SymbolType enum value, or None to match all types
            match_op: MatchOp enum value
            pattern: Pattern to match (user provides wildcards/regex)
            case_sensitive: Whether matching is case-sensitive
            limit: Optional result limit (0 = unlimited, None = default 10)
            match_qualified: If True, match against qualified_name instead of symbol_name

        Yields:
            MatchRecord objects with complete position data and metadata

        Example:
            for result in db.match(SymbolType.METHOD, MatchOp.GLOB, '*save()'):
                print(f"{result.qualified_name} at byte {result.byte_offset}")
        """
        # Handle REGEXP specially - use Python-side filtering
        # SQLite doesn't have native REGEXP support
        if match_op == MatchOp.REGEXP:
            yield from self._match_with_regex(
                symbol_type, pattern, case_sensitive, limit, match_qualified,
                newerthan_seconds=newerthan_seconds,
                olderthan_seconds=olderthan_seconds,
                negated=negated,
            )
            return

        # Build WHERE clause for SQL-based matching (GLOB, LIKE, EXACT)
        where_parts: List[str] = []
        params: List[Any] = []

        # Add symbol type filter only if specified
        if symbol_type is not None:
            where_parts.append("symbol_type = ?")
            params.append(symbol_type.value)

        # Add name match clause
        base_column = "qualified_name" if match_qualified else "symbol_name"
        column = base_column
        if not case_sensitive:
            column = f"LOWER({base_column})"
            pattern = pattern.lower()

        # Escape pattern if needed
        if match_op.needs_escaping:
            pattern = pattern.replace("'", "''")

        not_prefix = "NOT " if negated else ""
        where_parts.append(f"{not_prefix}{column} {match_op.sql_op} ?")
        params.append(pattern)

        # Temporal filters (per-stage --newerthan / --olderthan)
        now = time.time()
        if newerthan_seconds is not None:
            where_parts.append("mtime > ?")
            params.append(now - newerthan_seconds)
        if olderthan_seconds is not None:
            where_parts.append("mtime < ?")
            params.append(now - olderthan_seconds)

        where_clause = ' AND '.join(where_parts)

        # COUNT(*) OVER () is a window function: gives total matching rows before LIMIT.
        # This replaces the old pre-query aggregation in _get_match_metadata().
        # LEFT JOIN with aggregated inherits-from relationships populates base_classes
        # for ClassMatchRecord diagram rendering.
        query = f"""
            SELECT
                s.symbol_name,
                s.symbol_type,
                s.file_path,
                s.line_number,
                s.byte_offset,
                s.byte_length,
                s.qualified_name,
                s.parent_name,
                COUNT(*) OVER () as total_count,
                b.base_names,
                s.symbol_subtype
            FROM symbols s
            LEFT JOIN (
                SELECT sr.from_symbol_id,
                       GROUP_CONCAT(s2.symbol_name, ',') as base_names
                FROM symbol_references sr
                JOIN symbols s2 ON sr.to_symbol_id = s2.id
                WHERE sr.reference_type = 'inherits-from'
                GROUP BY sr.from_symbol_id
            ) b ON b.from_symbol_id = s.id
            WHERE {where_clause}
            ORDER BY s.file_path, s.line_number
        """

        # Add limit if specified (0 means unlimited)
        if limit is not None and limit > 0:
            query += f"\nLIMIT {limit}"

        # Execute and yield results; total_count from window function drives limit warning
        cursor = self.conn.execute(query, params)
        for row in cursor:
            row_dict = {
                'symbol_name': row[0],
                'symbol_type': row[1],
                'file_path': row[2],
                'line_number': row[3],
                'byte_offset': row[4],
                'byte_length': row[5],
                'qualified_name': row[6],
                'parent_name': row[7],
                'base_names': row[9],
                'symbol_subtype': row[10],
            }
            yield self._record_factory.create_from_row(row_dict, {'total_matches': row[8]})

    def _match_with_regex(
        self,
        symbol_type: Optional[SymbolType],
        pattern: str,
        case_sensitive: bool,
        limit: Optional[int],
        match_qualified: bool,
        newerthan_seconds: Optional[float] = None,
        olderthan_seconds: Optional[float] = None,
        negated: bool = False,
    ) -> Iterator[MatchRecord]:
        """Match using Python regex instead of SQL REGEXP.

        SQLite doesn't have native REGEXP support, so we:
        1. Query all symbols of the type (fast, uses index)
        2. Apply regex filtering in Python during iteration
        3. Stream results for O(1) memory

        Args:
            symbol_type: SymbolType to filter by, or None for all
            pattern: Regex pattern to match
            case_sensitive: Whether matching is case-sensitive
            limit: Optional result limit
            match_qualified: If True, match against qualified_name

        Yields:
            MatchRecord objects matching the regex
        """
        import re

        # Compile regex pattern (will raise re.error if invalid)
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        # Build query for type filter only (no pattern in SQL)
        where_parts: List[str] = []
        params: List[Any] = []

        if symbol_type is not None:
            where_parts.append("symbol_type = ?")
            params.append(symbol_type.value)

        # Temporal filters
        now = time.time()
        if newerthan_seconds is not None:
            where_parts.append("mtime > ?")
            params.append(now - newerthan_seconds)
        if olderthan_seconds is not None:
            where_parts.append("mtime < ?")
            params.append(now - olderthan_seconds)

        where_clause = ' AND '.join(where_parts) if where_parts else "1=1"

        # Query all symbols of type, with base class names for diagram support
        query = f"""
            SELECT
                s.symbol_name,
                s.symbol_type,
                s.file_path,
                s.line_number,
                s.byte_offset,
                s.byte_length,
                s.qualified_name,
                s.parent_name,
                b.base_names,
                s.symbol_subtype
            FROM symbols s
            LEFT JOIN (
                SELECT sr.from_symbol_id,
                       GROUP_CONCAT(s2.symbol_name, ',') as base_names
                FROM symbol_references sr
                JOIN symbols s2 ON sr.to_symbol_id = s2.id
                WHERE sr.reference_type = 'inherits-from'
                GROUP BY sr.from_symbol_id
            ) b ON b.from_symbol_id = s.id
            WHERE {where_clause}
            ORDER BY s.file_path, s.line_number
        """

        cursor = self.conn.execute(query, params)
        count = 0

        for row in cursor:
            # Get the value to match against
            match_value = row[6] if match_qualified else row[0]  # qualified_name or symbol_name

            # Apply regex filter (negated=True inverts the match)
            if (regex.search(match_value) is not None) != negated:
                row_dict = {
                    'symbol_name': row[0],
                    'symbol_type': row[1],
                    'file_path': row[2],
                    'line_number': row[3],
                    'byte_offset': row[4],
                    'byte_length': row[5],
                    'qualified_name': row[6],
                    'parent_name': row[7],
                    'base_names': row[8],
                    'symbol_subtype': row[9],
                }
                yield self._record_factory.create_from_row(row_dict)
                count += 1

                # Check limit
                if limit is not None and 0 < limit <= count:
                    break

    @require_connection
    def get_symbol_id(
        self,
        name: str,
        symbol_type: str,
        file_path: str,
        parent_name: Optional[str] = None,
    ) -> Optional[int]:
        """Return the id of a symbol by its identity fields, or None if not found.

        Args:
            name: Symbol name
            symbol_type: Symbol type string (e.g. 'function', 'method')
            file_path: Absolute file path
            parent_name: Parent class/function name for methods and nested symbols

        Returns:
            Symbol id, or None if not found
        """
        cursor = self.conn.execute(
            """SELECT id FROM symbols
               WHERE symbol_name = ? AND symbol_type = ? AND file_path = ?
               AND (parent_name = ? OR (parent_name IS NULL AND ? IS NULL))
               LIMIT 1""",
            (name, symbol_type, file_path, parent_name, parent_name),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def count_symbols(self) -> int:
        """Count total symbols in database.

        Returns:
            Total number of symbols
        """
        cursor = self.conn.execute("SELECT COUNT(*) FROM symbols")
        row = cursor.fetchone()
        return row[0] if row else 0

    def count_files(self) -> int:
        """Count unique files in database.

        Returns:
            Number of unique files
        """
        cursor = self.conn.execute("SELECT COUNT(DISTINCT file_path) FROM symbols")
        row = cursor.fetchone()
        return row[0] if row else 0

    def count_by_type(self) -> Dict[str, int]:
        """Count symbols by type, including markdown headers."""
        cursor = self.conn.execute(
            "SELECT symbol_type, COUNT(*) FROM symbols GROUP BY symbol_type ORDER BY COUNT(*) DESC"
        )
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        # Normalize: always include 'header' (markdown)
        if 'header' not in counts:
            counts['header'] = 0
        return counts

    def top_files_by_symbols(self, limit: int = 10) -> List[tuple]:
        """Get files with most symbols.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of (file_path, count) tuples
        """
        cursor = self.conn.execute(
            "SELECT file_path, COUNT(*) as cnt FROM symbols "
            "GROUP BY file_path ORDER BY cnt DESC LIMIT ?",
            (limit,)
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]

    # =========================================================================
    # Relationship Methods (Sprint 5)
    # =========================================================================

    @require_connection
    def insert_relationship(
        self,
        source_id: int,
        target_id: int,
        rel_type: str
    ) -> int:
        """Insert a relationship between two symbols.

        Args:
            source_id: ID of the source symbol
            target_id: ID of the target symbol
            rel_type: Type of relationship (e.g., 'inherits-from', 'calls')

        Returns:
            ID of the inserted relationship
        """
        cursor = self.conn.execute(
            """INSERT INTO symbol_references (from_symbol_id, to_symbol_id, reference_type)
               VALUES (?, ?, ?)""",
            (source_id, target_id, rel_type)
        )
        return cursor.lastrowid

    @require_connection
    def insert_pending_relationship(
        self,
        source_id: int,
        target_name: str,
        rel_type: str
    ) -> int:
        """Insert a pending relationship (target not yet resolved).

        Used in two-pass indexing when the target symbol may not exist yet.

        Args:
            source_id: ID of the source symbol
            target_name: Name of the target symbol (to be resolved later)
            rel_type: Type of relationship

        Returns:
            ID of the inserted pending relationship
        """
        cursor = self.conn.execute(
            """INSERT INTO pending_relationships (source_id, target_name, rel_type)
               VALUES (?, ?, ?)""",
            (source_id, target_name, rel_type)
        )
        return cursor.lastrowid

    @require_connection
    def resolve_pending_relationships(self) -> int:
        """Resolve pending relationships after all symbols have been indexed.

        For each pending relationship, tries to find the target symbol by name
        and creates a resolved relationship if found. For imports, creates
        module symbols for external modules. Cleans up pending entries.

        Returns:
            Number of relationships resolved
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, source_id, target_name, rel_type FROM pending_relationships"
        )
        pending = cursor.fetchall()

        resolved_count = 0
        for row in pending:
            pending_id, source_id, target_name, rel_type = row

            # Try to find target symbol by name, preferring definitions
            # (class/function/method/global) over import symbols to ensure
            # relationships point to the actual definition.
            target_cursor = self.conn.execute(
                """SELECT id FROM symbols WHERE symbol_name = ?
                   ORDER BY CASE symbol_type
                       WHEN 'class' THEN 0
                       WHEN 'function' THEN 1
                       WHEN 'method' THEN 2
                       WHEN 'global' THEN 3
                       WHEN 'module' THEN 4
                       ELSE 5
                   END
                   LIMIT 1""",
                (target_name,)
            )
            target_row = target_cursor.fetchone()

            if target_row:
                # Create resolved relationship
                self.insert_relationship(source_id, target_row[0], rel_type)
                resolved_count += 1
            elif rel_type == 'imports':
                # For imports, create a module symbol for external modules
                module_id = self._get_or_create_module_symbol(target_name)
                if module_id:
                    self.insert_relationship(source_id, module_id, rel_type)
                    resolved_count += 1

            # Delete pending entry (resolved or not)
            self.conn.execute(
                "DELETE FROM pending_relationships WHERE id = ?",
                (pending_id,)
            )

        return resolved_count

    def _get_or_create_module_symbol(self, module_name: str) -> int:
        """Get or create a module symbol for external modules.

        Args:
            module_name: Name of the module (e.g., 'os', 'typing')

        Returns:
            Symbol ID of the module
        """
        # Check if module symbol already exists
        cursor = self.conn.execute(
            "SELECT id FROM symbols WHERE symbol_name = ? AND symbol_type = 'module' LIMIT 1",
            (module_name,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        # Create new module symbol for external module
        cursor = self.conn.execute(
            """INSERT INTO symbols
               (symbol_name, symbol_type, file_path, line_number, qualified_name)
               VALUES (?, 'module', '<external>', 0, ?)""",
            (module_name, module_name)
        )
        return cursor.lastrowid

    @require_connection
    def query_relationships(
        self,
        relationship_type: str,
        subject_pattern: Optional[str] = None,
        object_pattern: Optional[str] = None,
        subject_type: Optional[str] = None,
        object_type: Optional[str] = None,
        subject_parent_pattern: Optional[str] = None,
        invert: bool = False,
        match_op: MatchOp = MatchOp.GLOB,
        case_sensitive: bool = True,
        limit: int = 100,
        result_newerthan_seconds: Optional[float] = None,
        result_olderthan_seconds: Optional[float] = None,
    ) -> Iterator[MatchRecord]:
        """Query symbols by relationship.

        When invert=False (default):
            Returns subjects that have the relationship TO objects matching pattern.
            Example: Find classes that inherit from 'BaseClass'

        When invert=True:
            Returns targets that have the relationship FROM subjects matching pattern.
            Example: Find what 'ChildClass' inherits from

        Args:
            relationship_type: Type of relationship (e.g., 'inherits-from')
            subject_pattern: Pattern to filter subject symbols
            object_pattern: Pattern to filter object (target) symbols
            subject_type: Symbol type filter for subjects
            object_type: Symbol type filter for objects
            subject_parent_pattern: Pattern to filter subject's parent_name (e.g. class name for methods)
            invert: If True, swap subject/object in query
            match_op: Match operator for pattern matching
            case_sensitive: Whether pattern matching is case-sensitive
            limit: Maximum results to return

        Yields:
            MatchRecord objects for matching symbols
        """
        # Build the query
        if not invert:
            # Normal: find subjects that relate TO objects
            # Return the subjects (sources)
            select_from = "s"  # source symbol
            join_source = "from_symbol_id"
            join_target = "to_symbol_id"
        else:
            # Inverted: find targets that relate FROM subjects
            # Return the targets
            select_from = "t"  # target symbol
            join_source = "from_symbol_id"
            join_target = "to_symbol_id"

        # Build WHERE clauses
        where_parts = ["r.reference_type = ?"]
        params: List[Any] = [relationship_type]

        # Pattern filtering: subject_pattern always filters source (s),
        # object_pattern always filters target (t). The caller (executor)
        # handles any swapping needed for inverted queries.
        if subject_pattern and subject_pattern != '*':
            column = "s.symbol_name"
            pat = subject_pattern
            if not case_sensitive:
                column = "LOWER(s.symbol_name)"
                pat = pat.lower()
            where_parts.append(f"{column} {match_op.sql_op} ?")
            params.append(pat)

        if object_pattern and object_pattern != '*':
            column = "t.symbol_name"
            pat = object_pattern
            if not case_sensitive:
                column = "LOWER(t.symbol_name)"
                pat = pat.lower()
            where_parts.append(f"{column} {match_op.sql_op} ?")
            params.append(pat)

        # Type filtering: subject_type filters source, object_type filters target
        if subject_type:
            where_parts.append("s.symbol_type = ?")
            params.append(subject_type)

        if subject_parent_pattern and subject_parent_pattern != '*':
            column = "s.parent_name"
            pat = subject_parent_pattern
            if not case_sensitive:
                column = "LOWER(s.parent_name)"
                pat = pat.lower()
            where_parts.append(f"{column} {match_op.sql_op} ?")
            params.append(pat)

        if object_type:
            where_parts.append("t.symbol_type = ?")
            params.append(object_type)

        # Temporal filter on the returned symbol (select_from)
        now = time.time()
        if result_newerthan_seconds is not None:
            where_parts.append(f"{select_from}.mtime > ?")
            params.append(now - result_newerthan_seconds)
        if result_olderthan_seconds is not None:
            where_parts.append(f"{select_from}.mtime < ?")
            params.append(now - result_olderthan_seconds)

        # Anchor is the other symbol in the join (used for --stale)
        anchor_alias = "t" if select_from == "s" else "s"

        # Build query
        where_clause = " AND ".join(where_parts)
        query = f"""
            SELECT
                {select_from}.symbol_name,
                {select_from}.symbol_type,
                {select_from}.file_path,
                {select_from}.line_number,
                {select_from}.byte_offset,
                {select_from}.byte_length,
                {select_from}.qualified_name,
                {select_from}.parent_name,
                {select_from}.mtime,
                {anchor_alias}.mtime AS anchor_mtime,
                b.base_names
            FROM symbol_references r
            JOIN symbols s ON r.{join_source} = s.id
            JOIN symbols t ON r.{join_target} = t.id
            LEFT JOIN (
                SELECT sr2.from_symbol_id,
                       GROUP_CONCAT(s2.symbol_name, ',') as base_names
                FROM symbol_references sr2
                JOIN symbols s2 ON sr2.to_symbol_id = s2.id
                WHERE sr2.reference_type = 'inherits-from'
                GROUP BY sr2.from_symbol_id
            ) b ON b.from_symbol_id = {select_from}.id
            WHERE {where_clause}
            ORDER BY {select_from}.file_path, {select_from}.line_number
            LIMIT ?
        """
        params.append(limit)

        # Execute and yield results
        cursor = self.conn.execute(query, params)
        for row in cursor:
            row_dict = {
                'symbol_name': row[0],
                'symbol_type': row[1],
                'file_path': row[2],
                'line_number': row[3],
                'byte_offset': row[4],
                'byte_length': row[5],
                'qualified_name': row[6],
                'parent_name': row[7],
                'mtime': row[8],
                'base_names': row[10],
            }
            record = self._record_factory.create_from_row(row_dict)
            record.anchor_mtime = row[9]
            yield record

    @require_connection
    def query_negative_relationships(
        self,
        relationship_type: str,
        subject_pattern: Optional[str] = None,
        object_pattern: Optional[str] = None,
        subject_type: Optional[str] = None,
        object_type: Optional[str] = None,
        match_op: MatchOp = MatchOp.GLOB,
        case_sensitive: bool = True,
        limit: int = 100,
        result_newerthan_seconds: Optional[float] = None,
        result_olderthan_seconds: Optional[float] = None,
        invert_join: bool = False,
    ) -> Iterator[MatchRecord]:
        """Query symbols that do NOT have the specified relationship (--sans semantics).

        Returns subjects that have NO relationship of relationship_type to any
        symbol matching object_pattern.

        Args:
            relationship_type: Type of relationship (e.g., 'inherits-from')
            subject_pattern: Pattern to filter subject symbols
            object_pattern: Pattern to filter object symbols in the NOT EXISTS check
            subject_type: Symbol type filter for subjects
            object_type: Symbol type filter for objects in the NOT EXISTS check
            match_op: Match operator for pattern matching
            case_sensitive: Whether pattern matching is case-sensitive
            limit: Maximum results to return
            result_newerthan_seconds: Filter subjects to symbols newer than N seconds ago
            result_olderthan_seconds: Filter subjects to symbols older than N seconds ago

        Yields:
            MatchRecord objects for matching symbols
        """
        # Outer query: select subjects matching the subject filter
        outer_where: List[Any] = []
        outer_params: List[Any] = []

        if subject_type:
            outer_where.append("s.symbol_type = ?")
            outer_params.append(subject_type)

        if subject_pattern and subject_pattern != '*':
            col = "s.symbol_name"
            pat = subject_pattern
            if not case_sensitive:
                col = "LOWER(s.symbol_name)"
                pat = pat.lower()
            outer_where.append(f"{col} {match_op.sql_op} ?")
            outer_params.append(pat)

        # Temporal filters on the returned subject
        now = time.time()
        if result_newerthan_seconds is not None:
            outer_where.append("s.mtime > ?")
            outer_params.append(now - result_newerthan_seconds)
        if result_olderthan_seconds is not None:
            outer_where.append("s.mtime < ?")
            outer_params.append(now - result_olderthan_seconds)

        # NOT EXISTS subquery: no relationship of this type to any matching object.
        # invert_join=True flips the join direction for relationships where the subject
        # is the TO side (e.g. 'declares': container is to_symbol_id, member is from_symbol_id).
        if invert_join:
            sub_anchor = "r.to_symbol_id = s.id"
            sub_join = "JOIN symbols t ON r.from_symbol_id = t.id"
        else:
            sub_anchor = "r.from_symbol_id = s.id"
            sub_join = "JOIN symbols t ON r.to_symbol_id = t.id"

        sub_where = [sub_anchor, "r.reference_type = ?"]
        sub_params: List[Any] = [relationship_type]

        if object_type:
            sub_where.append("t.symbol_type = ?")
            sub_params.append(object_type)

        if object_pattern and object_pattern != '*':
            col = "t.symbol_name"
            pat = object_pattern
            if not case_sensitive:
                col = "LOWER(t.symbol_name)"
                pat = pat.lower()
            sub_where.append(f"{col} {match_op.sql_op} ?")
            sub_params.append(pat)

        not_exists_clause = (
            "NOT EXISTS ("
            "SELECT 1 FROM symbol_references r "
            f"{sub_join} "
            f"WHERE {' AND '.join(sub_where)}"
            ")"
        )
        outer_where.append(not_exists_clause)

        where_clause = " AND ".join(outer_where) if outer_where else "1=1"
        all_params = outer_params + sub_params + [limit]

        query = f"""
            SELECT
                s.symbol_name,
                s.symbol_type,
                s.file_path,
                s.line_number,
                s.byte_offset,
                s.byte_length,
                s.qualified_name,
                s.parent_name,
                s.mtime,
                NULL as anchor_mtime,
                b.base_names
            FROM symbols s
            LEFT JOIN (
                SELECT sr2.from_symbol_id,
                       GROUP_CONCAT(s2.symbol_name, ',') as base_names
                FROM symbol_references sr2
                JOIN symbols s2 ON sr2.to_symbol_id = s2.id
                WHERE sr2.reference_type = 'inherits-from'
                GROUP BY sr2.from_symbol_id
            ) b ON b.from_symbol_id = s.id
            WHERE {where_clause}
            ORDER BY s.file_path, s.line_number
            LIMIT ?
        """

        cursor = self.conn.execute(query, all_params)
        for row in cursor:
            row_dict = {
                'symbol_name': row[0],
                'symbol_type': row[1],
                'file_path': row[2],
                'line_number': row[3],
                'byte_offset': row[4],
                'byte_length': row[5],
                'qualified_name': row[6],
                'parent_name': row[7],
                'mtime': row[8],
                'base_names': row[10],
            }
            record = self._record_factory.create_from_row(row_dict)
            record.anchor_mtime = row[9]
            yield record

    @require_connection
    def get_counts(self) -> dict:
        """Return file and symbol counts for the index.

        Returns:
            dict with keys 'files' (int) and 'symbols' (int).
        """
        file_count = self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbol_count = self.conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        return {"files": file_count, "symbols": symbol_count}

    @require_connection
    def get_last_indexed_iso(self) -> Optional[str]:
        """Return the most recent indexed_at timestamp as an ISO8601 UTC string.

        Returns:
            ISO8601 string (e.g. '2026-03-22T20:00:00+00:00') or None if no
            files are indexed.
        """
        import datetime as _dt
        row = self.conn.execute("SELECT MAX(indexed_at) FROM files").fetchone()
        if row is None or row[0] is None:
            return None
        ts = float(row[0])
        return _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc).isoformat()

