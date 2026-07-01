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
import contextlib
import weakref
from functools import wraps
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar, Tuple

from ..core.match_record import MatchRecord, MatchRecordFactory
from ..core.types import MatchOp, SymbolType
from .schema import (
    ALL_TABLES,
    CREATE_INDEXES,
    CREATE_LINE_OFFSETS_TABLE,
    CREATE_METADATA_TABLE,
    CREATE_SCHEMA_MIGRATIONS_TABLE,
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
        self._conn_finalizer: Optional[weakref.finalize] = None
        self._in_transaction = False
        self._record_factory = MatchRecordFactory()

    def connect(self) -> None:
        """Connect to database and enable foreign keys and WAL mode."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._clear_conn_finalizer()
        self._conn_finalizer = weakref.finalize(
            self,
            self._close_connection_safely,
            self.conn,
        )
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
        self._clear_conn_finalizer()

    def __del__(self):
        """Best-effort cleanup for stores not explicitly closed by callers."""
        with contextlib.suppress(Exception):
            self.close()

    @staticmethod
    def _close_connection_safely(conn: sqlite3.Connection) -> None:
        """Best-effort close for leaked connections during object finalization."""
        with contextlib.suppress(Exception):
            conn.close()

    def _clear_conn_finalizer(self) -> None:
        """Detach any existing connection finalizer after explicit cleanup."""
        if self._conn_finalizer is not None and self._conn_finalizer.alive:
            self._conn_finalizer.detach()
        self._conn_finalizer = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Context manager exit."""
        self.close()

    @require_connection
    def initialize_schema(self) -> None:
        """Create all tables and indexes if they don't exist, applying migrations as needed."""
        cursor = self.conn.cursor()

        # Create core tables (metadata must exist first to read current version)
        cursor.execute(CREATE_METADATA_TABLE)
        cursor.execute(CREATE_SCHEMA_MIGRATIONS_TABLE)
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

    @staticmethod
    def _build_match_where(
        symbol_type: Optional[SymbolType],
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool,
        negated: bool,
        match_qualified: bool,
        newerthan_seconds: Optional[float],
        olderthan_seconds: Optional[float],
        language: Optional[str],
        subtype: Optional[str],
    ) -> tuple:
        """Build WHERE clause and params for SQL-based match query."""
        where_parts: List[str] = []
        params: List[Any] = []

        if symbol_type is not None:
            where_parts.append("symbol_type = ?")
            params.append(symbol_type.value)

        base_column = "qualified_name" if match_qualified else "symbol_name"
        column = base_column
        if not case_sensitive:
            column = f"LOWER({base_column})"
            pattern = pattern.lower()
        if match_op.needs_escaping:
            pattern = pattern.replace("'", "''")
        not_prefix = "NOT " if negated else ""
        where_parts.append(f"{not_prefix}{column} {match_op.sql_op} ?")
        params.append(pattern)

        now = time.time()
        if newerthan_seconds is not None:
            where_parts.append("mtime > ?")
            params.append(now - newerthan_seconds)
        if olderthan_seconds is not None:
            where_parts.append("mtime < ?")
            params.append(now - olderthan_seconds)

        if language is not None:
            where_parts.append("s.language = ?")
            params.append(language)
        if subtype is not None:
            where_parts.append("s.symbol_subtype = ?")
            params.append(subtype)

        return ' AND '.join(where_parts), params

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
        language: Optional[str] = None,
        subtype: Optional[str] = None,
        offset: Optional[int] = None,
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
                language=language,
                subtype=subtype,
                offset=offset,
            )
            return

        where_clause, params = self._build_match_where(
            symbol_type, match_op, pattern, case_sensitive, negated,
            match_qualified, newerthan_seconds, olderthan_seconds, language, subtype,
        )

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

        # Apply OFFSET + LIMIT for --slice, or just LIMIT for -n
        if offset is not None:
            # --slice mode: OFFSET is the start index; limit 0 = unlimited (-1 in SQLite)
            sql_limit = limit if limit and limit > 0 else -1
            query += f"\nLIMIT {sql_limit} OFFSET {offset}"
        elif limit is not None and limit > 0:
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
        language: Optional[str] = None,
        subtype: Optional[str] = None,
        offset: Optional[int] = None,
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

        # Language and subtype filters
        if language is not None:
            where_parts.append("s.language = ?")
            params.append(language)
        if subtype is not None:
            where_parts.append("s.symbol_subtype = ?")
            params.append(subtype)

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
        skipped = 0
        skip_count = offset or 0

        for row in cursor:
            # Get the value to match against
            match_value = row[6] if match_qualified else row[0]  # qualified_name or symbol_name

            # Apply regex filter (negated=True inverts the match)
            if (regex.search(match_value) is not None) != negated:
                # Apply offset (skip first N matching results)
                if skipped < skip_count:
                    skipped += 1
                    continue
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
                # Check if the target name corresponds to a project file.
                # E.g. target_name 'module_a' -> 'module_a.py' or 'module_a/__init__.py'
                rel_path_base = target_name.replace('.', '/')
                potentials = (f"{rel_path_base}.py", f"{rel_path_base}/__init__.py")
                
                file_cursor = self.conn.execute(
                    """SELECT id, file_path FROM symbols 
                       WHERE symbol_type = 'filepath' AND qualified_name IN (?, ?) 
                       LIMIT 1""",
                    potentials
                )
                project_file_row = file_cursor.fetchone()
                
                if project_file_row:
                    filepath_symbol_id, absolute_file_path = project_file_row
                    
                    # Get or create module symbol with correct project file_path
                    cursor = self.conn.execute(
                        "SELECT id FROM symbols WHERE symbol_name = ? AND symbol_type = 'module' LIMIT 1",
                        (target_name,)
                    )
                    row = cursor.fetchone()
                    if row:
                        module_id = row[0]
                        # If existing module was external, update it
                        self.conn.execute(
                            "UPDATE symbols SET file_path = ? WHERE id = ? AND file_path = '<external>'",
                            (absolute_file_path, module_id)
                        )
                    else:
                        cursor = self.conn.execute(
                            """INSERT INTO symbols
                               (symbol_name, symbol_type, file_path, line_number, qualified_name)
                               VALUES (?, 'module', ?, 0, ?)""",
                            (target_name, absolute_file_path, target_name)
                        )
                        module_id = cursor.lastrowid
                    
                    # Create declares relationships to filename and filepath symbols
                    filename_cursor = self.conn.execute(
                        "SELECT id FROM symbols WHERE symbol_type = 'filename' AND file_path = ? LIMIT 1",
                        (absolute_file_path,)
                    )
                    filename_row = filename_cursor.fetchone()
                    
                    self.insert_relationship(module_id, filepath_symbol_id, 'declares')
                    if filename_row:
                        self.insert_relationship(module_id, filename_row[0], 'declares')
                    
                    self.insert_relationship(source_id, module_id, rel_type)
                    resolved_count += 1
                else:
                    # For external imports, create/get default module symbol
                    module_id = self._get_or_create_module_symbol(target_name)
                    if module_id:
                        self.insert_relationship(source_id, module_id, rel_type)
                        resolved_count += 1
            elif rel_type == 'inherits-from':
                # External base classes/interfaces are still useful relationship anchors.
                class_id = self._get_or_create_external_class_symbol(target_name)
                if class_id:
                    self.insert_relationship(source_id, class_id, rel_type)
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

    def _get_or_create_external_class_symbol(self, class_name: str) -> int:
        """Get or create an external class-like symbol for unresolved inheritance targets."""
        cursor = self.conn.execute(
            "SELECT id FROM symbols WHERE symbol_name = ? AND symbol_type IN ('class', 'external_class') LIMIT 1",
            (class_name,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor = self.conn.execute(
            """INSERT INTO symbols
               (symbol_name, symbol_type, file_path, line_number, qualified_name, symbol_subtype)
               VALUES (?, 'external_class', '<external>', 0, ?, 'external')""",
            (class_name, class_name)
        )
        return cursor.lastrowid

    @staticmethod
    def _add_pattern_clause(
        where_parts: List[str],
        params: List[Any],
        column: str,
        raw_pattern: Optional[str],
        match_op: MatchOp,
        case_sensitive: bool,
        negated: bool = False,
    ) -> None:
        """Append a pattern-matching WHERE clause if *raw_pattern* is non-trivial."""
        if not raw_pattern or raw_pattern == '*':
            return
        col = column
        pat = raw_pattern
        if not case_sensitive:
            col = f"LOWER({column})"
            pat = pat.lower()
        not_prefix = "NOT " if negated else ""
        where_parts.append(f"{not_prefix}{col} {match_op.sql_op} ?")
        params.append(pat)

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
        subject_negated: bool = False,
        object_negated: bool = False,
        subject_qualified: bool = False,
        object_qualified: bool = False,
        result_names: Optional[List[str]] = None,
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
            result_newerthan_seconds: Filter returned symbols to symbols newer than N seconds ago
            result_olderthan_seconds: Filter returned symbols to symbols older than N seconds ago
            subject_negated: If True, negate subject match pattern
            object_negated: If True, negate object match pattern
            subject_qualified: If True, match subject against qualified_name
            object_qualified: If True, match object against qualified_name
            result_names: Optional list of names to filter returned symbols

        Yields:
            MatchRecord objects for matching symbols
        """
        # For declares relationship, s is always member and t is always container in the DB.
        # Check if the caller passed container on the subject side or object side.
        if relationship_type == 'declares':
            _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename'}
            subject_is_container = subject_type in _DECLARES_CONTAINER_TYPES
            object_is_container = object_type in _DECLARES_CONTAINER_TYPES

            # If subject is container and object is not, swap subject and object parameters
            if subject_is_container and not object_is_container:
                subject_pattern, object_pattern = object_pattern, subject_pattern
                subject_type, object_type = object_type, subject_type
                subject_qualified, object_qualified = object_qualified, subject_qualified
                subject_negated, object_negated = object_negated, subject_negated
                invert = not invert

        # Build the query
        if not invert:
            select_from = "s"  # source symbol
        else:
            select_from = "t"  # target symbol
        join_source = "from_symbol_id"
        join_target = "to_symbol_id"

        # Build WHERE clauses
        where_parts = ["r.reference_type = ?"]
        params: List[Any] = [relationship_type]

        # Determine joins and aliases
        joins = [
            f"JOIN symbols s ON r.{join_source} = s.id",
            f"JOIN symbols t ON r.{join_target} = t.id"
        ]

        is_subject_file = relationship_type == 'imports' and subject_type in ('filepath', 'filename')
        is_object_file = relationship_type == 'imports' and object_type in ('filepath', 'filename')

        if is_subject_file:
            joins.append("JOIN symbol_references rs ON rs.from_symbol_id = s.id AND rs.reference_type = 'declares'")
            joins.append("JOIN symbols fs ON rs.to_symbol_id = fs.id")
            subject_alias = "fs"
            if select_from == "s":
                select_from = "fs"
        else:
            subject_alias = "s"

        if is_object_file:
            joins.append("JOIN symbol_references rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'")
            joins.append("JOIN symbols ft ON rt.to_symbol_id = ft.id")
            object_alias = "ft"
            if select_from == "t":
                select_from = "ft"
        else:
            object_alias = "t"

        subject_col = f"{subject_alias}.qualified_name" if subject_qualified else f"{subject_alias}.symbol_name"
        object_col = f"{object_alias}.qualified_name" if object_qualified else f"{object_alias}.symbol_name"
        self._add_pattern_clause(where_parts, params, subject_col, subject_pattern, match_op, case_sensitive, subject_negated)
        self._add_pattern_clause(where_parts, params, object_col, object_pattern, match_op, case_sensitive, object_negated)

        if result_names is not None:
            result_qualified = object_qualified if invert else subject_qualified
            result_col = f"{select_from}.qualified_name" if result_qualified else f"{select_from}.symbol_name"
            if result_names:
                placeholders = ", ".join("?" for _ in result_names)
                where_parts.append(f"{result_col} IN ({placeholders})")
                params.extend(result_names)
            else:
                where_parts.append("1=0")

        if subject_type:
            if is_subject_file:
                where_parts.append("fs.symbol_type = ?")
                params.append(subject_type)
            else:
                where_parts.append("s.symbol_type = ?")
                params.append(subject_type)

        self._add_pattern_clause(where_parts, params, "s.parent_name", subject_parent_pattern, match_op, case_sensitive)

        if object_type == 'class':
            where_parts.append("(t.symbol_type = ? OR t.symbol_type = 'external_class')")
            params.append(object_type)
        elif relationship_type == 'imports' and object_type == 'import':
            where_parts.append("(t.symbol_type = 'import' OR t.symbol_type = 'module')")
        elif object_type:
            if is_object_file:
                where_parts.append("ft.symbol_type = ?")
                params.append(object_type)
            else:
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
        if select_from in ("fs", "s"):
            anchor_alias = object_alias
        else:
            anchor_alias = subject_alias

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
            {" ".join(joins)}
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
        subject_negated: bool = False,
        object_negated: bool = False,
        subject_qualified: bool = False,
        object_qualified: bool = False,
        result_names: Optional[List[str]] = None,
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
            invert_join: If True, invert the NOT EXISTS subquery join anchor
            subject_negated: If True, negate subject match pattern
            object_negated: If True, negate object match pattern
            subject_qualified: If True, match subject against qualified_name
            object_qualified: If True, match object against qualified_name
            result_names: Optional list of names to filter returned symbols

        Yields:
            MatchRecord objects for matching symbols
        """
        # Outer query: select subjects matching the subject filter
        outer_where: List[Any] = []
        outer_params: List[Any] = []

        if subject_type:
            outer_where.append("s.symbol_type = ?")
            outer_params.append(subject_type)

        subject_col = "s.qualified_name" if subject_qualified else "s.symbol_name"
        self._add_pattern_clause(outer_where, outer_params, subject_col, subject_pattern, match_op, case_sensitive, subject_negated)

        if result_names is not None:
            result_col = "s.qualified_name" if subject_qualified else "s.symbol_name"
            if result_names:
                placeholders = ", ".join("?" for _ in result_names)
                outer_where.append(f"{result_col} IN ({placeholders})")
                outer_params.extend(result_names)
            else:
                outer_where.append("1=0")

        # Temporal filters on the returned subject
        now = time.time()
        if result_newerthan_seconds is not None:
            outer_where.append("s.mtime > ?")
            outer_params.append(now - result_newerthan_seconds)
        if result_olderthan_seconds is not None:
            outer_where.append("s.mtime < ?")
            outer_params.append(now - result_olderthan_seconds)


        is_subject_file = relationship_type == 'imports' and subject_type in ('filepath', 'filename')
        is_object_file = relationship_type == 'imports' and object_type in ('filepath', 'filename')

        # NOT EXISTS subquery: no relationship of this type to any matching object.
        # invert_join=True flips the join direction for relationships where the subject
        # is the TO side (e.g. 'declares': container is to_symbol_id, member is from_symbol_id).
        sub_joins = []
        if is_subject_file:
            # outer 's' is file, so sub_anchor connects 'rs' to 's'
            sub_anchor = "rs.to_symbol_id = s.id AND rs.reference_type = 'declares'"
            sub_joins.append("JOIN symbols s_imp ON rs.from_symbol_id = s_imp.id AND s_imp.symbol_type = 'import'")
            sub_joins.append("JOIN symbol_references r ON r.from_symbol_id = s_imp.id AND r.reference_type = ?")
            sub_joins.append("JOIN symbols t ON r.to_symbol_id = t.id")
            sub_where = [sub_anchor]
            sub_params: List[Any] = [relationship_type]
        else:
            if invert_join:
                sub_anchor = "r.to_symbol_id = s.id"
                sub_joins.append("JOIN symbols t ON r.from_symbol_id = t.id")
            else:
                sub_anchor = "r.from_symbol_id = s.id"
                sub_joins.append("JOIN symbols t ON r.to_symbol_id = t.id")
            sub_where = [sub_anchor, "r.reference_type = ?"]
            sub_params: List[Any] = [relationship_type]

        if is_object_file:
            sub_joins.append("JOIN symbol_references rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'")
            sub_joins.append("JOIN symbols ft ON rt.to_symbol_id = ft.id")
            object_alias = "ft"
            sub_where.append("ft.symbol_type = ?")
            sub_params.append(object_type)
        else:
            object_alias = "t"
            if object_type == 'class':
                sub_where.append("(t.symbol_type = ? OR t.symbol_type = 'external_class')")
                sub_params.append(object_type)
            elif relationship_type == 'imports' and object_type == 'import':
                sub_where.append("(t.symbol_type = 'import' OR t.symbol_type = 'module')")
            elif object_type:
                sub_where.append("t.symbol_type = ?")
                sub_params.append(object_type)

        object_col = f"{object_alias}.qualified_name" if object_qualified else f"{object_alias}.symbol_name"
        self._add_pattern_clause(sub_where, sub_params, object_col, object_pattern, match_op, case_sensitive, object_negated)

        if is_subject_file:
            not_exists_clause = (
                "NOT EXISTS ("
                "SELECT 1 FROM symbol_references rs "
                f"{' '.join(sub_joins)} "
                f"WHERE {' AND '.join(sub_where)}"
                ")"
            )
        else:
            not_exists_clause = (
                "NOT EXISTS ("
                "SELECT 1 FROM symbol_references r "
                f"{' '.join(sub_joins)} "
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

    def _build_relationship_cte_sql(
        self,
        index: int,
        relationship_type: str,
        subject_pattern: Optional[str] = None,
        object_pattern: Optional[str] = None,
        subject_type: Optional[str] = None,
        object_type: Optional[str] = None,
        subject_parent_pattern: Optional[str] = None,
        invert: bool = False,
        match_op: MatchOp = MatchOp.GLOB,
        case_sensitive: bool = True,
        result_newerthan_seconds: Optional[float] = None,
        result_olderthan_seconds: Optional[float] = None,
        subject_negated: bool = False,
        object_negated: bool = False,
        subject_qualified: bool = False,
        object_qualified: bool = False,
        is_first: bool = False,
    ) -> Tuple[str, List[Any]]:
        # For declares relationship, s is always member and t is always container in the DB.
        if relationship_type == 'declares':
            _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename'}
            subject_is_container = subject_type in _DECLARES_CONTAINER_TYPES
            object_is_container = object_type in _DECLARES_CONTAINER_TYPES

            if subject_is_container and not object_is_container:
                subject_pattern, object_pattern = object_pattern, subject_pattern
                subject_type, object_type = object_type, subject_type
                subject_qualified, object_qualified = object_qualified, subject_qualified
                subject_negated, object_negated = object_negated, subject_negated
                invert = not invert

        if not invert:
            select_from = "s"
        else:
            select_from = "t"
        join_source = "from_symbol_id"
        join_target = "to_symbol_id"

        where_parts = ["r.reference_type = ?"]
        params: List[Any] = [relationship_type]

        joins = [
            f"JOIN symbols s ON r.{join_source} = s.id",
            f"JOIN symbols t ON r.{join_target} = t.id"
        ]

        is_subject_file = relationship_type == 'imports' and subject_type in ('filepath', 'filename')
        is_object_file = relationship_type == 'imports' and object_type in ('filepath', 'filename')

        if is_subject_file:
            joins.append("JOIN symbol_references rs ON rs.from_symbol_id = s.id AND rs.reference_type = 'declares'")
            joins.append("JOIN symbols fs ON rs.to_symbol_id = fs.id")
            subject_alias = "fs"
            if select_from == "s":
                select_from = "fs"
        else:
            subject_alias = "s"

        if is_object_file:
            joins.append("JOIN symbol_references rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'")
            joins.append("JOIN symbols ft ON rt.to_symbol_id = ft.id")
            object_alias = "ft"
            if select_from == "t":
                select_from = "ft"
        else:
            object_alias = "t"

        subject_col = f"{subject_alias}.qualified_name" if subject_qualified else f"{subject_alias}.symbol_name"
        object_col = f"{object_alias}.qualified_name" if object_qualified else f"{object_alias}.symbol_name"
        self._add_pattern_clause(where_parts, params, subject_col, subject_pattern, match_op, case_sensitive, subject_negated)
        self._add_pattern_clause(where_parts, params, object_col, object_pattern, match_op, case_sensitive, object_negated)

        if subject_type:
            if is_subject_file:
                where_parts.append("fs.symbol_type = ?")
                params.append(subject_type)
            else:
                where_parts.append("s.symbol_type = ?")
                params.append(subject_type)

        self._add_pattern_clause(where_parts, params, "s.parent_name", subject_parent_pattern, match_op, case_sensitive)

        if object_type == 'class':
            where_parts.append("(t.symbol_type = ? OR t.symbol_type = 'external_class')")
            params.append(object_type)
        elif relationship_type == 'imports' and object_type == 'import':
            where_parts.append("(t.symbol_type = 'import' OR t.symbol_type = 'module')")
        elif object_type:
            if is_object_file:
                where_parts.append("ft.symbol_type = ?")
                params.append(object_type)
            else:
                where_parts.append("t.symbol_type = ?")
                params.append(object_type)

        now = time.time()
        if result_newerthan_seconds is not None:
            where_parts.append(f"{select_from}.mtime > ?")
            params.append(now - result_newerthan_seconds)
        if result_olderthan_seconds is not None:
            where_parts.append(f"{select_from}.mtime < ?")
            params.append(now - result_olderthan_seconds)

        if select_from in ("fs", "s"):
            anchor_alias = object_alias
        else:
            anchor_alias = subject_alias

        where_clause = " AND ".join(where_parts)

        if is_first:
            sql = f"""
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
                    b.base_names,
                    {select_from}.id AS symbol_id
                FROM symbol_references r
                {" ".join(joins)}
                LEFT JOIN (
                    SELECT sr2.from_symbol_id,
                           GROUP_CONCAT(s2.symbol_name, ',') as base_names
                    FROM symbol_references sr2
                    JOIN symbols s2 ON sr2.to_symbol_id = s2.id
                    WHERE sr2.reference_type = 'inherits-from'
                    GROUP BY sr2.from_symbol_id
                ) b ON b.from_symbol_id = {select_from}.id
                WHERE {where_clause}
            """
        else:
            sql = f"""
                SELECT {select_from}.id AS symbol_id
                FROM symbol_references r
                {" ".join(joins)}
                WHERE {where_clause}
            """
        return sql, params

    def _build_negative_relationship_cte_sql(
        self,
        index: int,
        relationship_type: str,
        subject_pattern: Optional[str] = None,
        object_pattern: Optional[str] = None,
        subject_type: Optional[str] = None,
        object_type: Optional[str] = None,
        match_op: MatchOp = MatchOp.GLOB,
        case_sensitive: bool = True,
        result_newerthan_seconds: Optional[float] = None,
        result_olderthan_seconds: Optional[float] = None,
        invert_join: bool = False,
        subject_negated: bool = False,
        object_negated: bool = False,
        subject_qualified: bool = False,
        object_qualified: bool = False,
        is_first: bool = False,
    ) -> Tuple[str, List[Any]]:
        outer_where: List[Any] = []
        outer_params: List[Any] = []

        if subject_type:
            outer_where.append("s.symbol_type = ?")
            outer_params.append(subject_type)

        subject_col = "s.qualified_name" if subject_qualified else "s.symbol_name"
        self._add_pattern_clause(outer_where, outer_params, subject_col, subject_pattern, match_op, case_sensitive, subject_negated)

        now = time.time()
        if result_newerthan_seconds is not None:
            outer_where.append("s.mtime > ?")
            outer_params.append(now - result_newerthan_seconds)
        if result_olderthan_seconds is not None:
            outer_where.append("s.mtime < ?")
            outer_params.append(now - result_olderthan_seconds)

        is_subject_file = relationship_type == 'imports' and subject_type in ('filepath', 'filename')
        is_object_file = relationship_type == 'imports' and object_type in ('filepath', 'filename')

        sub_joins = []
        if is_subject_file:
            sub_anchor = "rs.to_symbol_id = s.id AND rs.reference_type = 'declares'"
            sub_joins.append("JOIN symbols s_imp ON rs.from_symbol_id = s_imp.id AND s_imp.symbol_type = 'import'")
            sub_joins.append("JOIN symbol_references r ON r.from_symbol_id = s_imp.id AND r.reference_type = ?")
            sub_joins.append("JOIN symbols t ON r.to_symbol_id = t.id")
            sub_where = [sub_anchor]
            sub_params = [relationship_type]
        else:
            if invert_join:
                sub_anchor = "r.to_symbol_id = s.id"
                sub_joins.append("JOIN symbols t ON r.from_symbol_id = t.id")
            else:
                sub_anchor = "r.from_symbol_id = s.id"
                sub_joins.append("JOIN symbols t ON r.to_symbol_id = t.id")
            sub_where = [sub_anchor, "r.reference_type = ?"]
            sub_params = [relationship_type]

        if is_object_file:
            sub_joins.append("JOIN symbol_references rt ON rt.from_symbol_id = t.id AND rt.reference_type = 'declares'")
            sub_joins.append("JOIN symbols ft ON rt.to_symbol_id = ft.id")
            object_alias = "ft"
            sub_where.append("ft.symbol_type = ?")
            sub_params.append(object_type)
        else:
            object_alias = "t"
            if object_type == 'class':
                sub_where.append("(t.symbol_type = ? OR t.symbol_type = 'external_class')")
                sub_params.append(object_type)
            elif relationship_type == 'imports' and object_type == 'import':
                sub_where.append("(t.symbol_type = 'import' OR t.symbol_type = 'module')")
            elif object_type:
                sub_where.append("t.symbol_type = ?")
                sub_params.append(object_type)

        object_col = f"{object_alias}.qualified_name" if object_qualified else f"{object_alias}.symbol_name"
        self._add_pattern_clause(sub_where, sub_params, object_col, object_pattern, match_op, case_sensitive, object_negated)

        if is_subject_file:
            not_exists_clause = (
                "NOT EXISTS ("
                "SELECT 1 FROM symbol_references rs "
                f"{' '.join(sub_joins)} "
                f"WHERE {' AND '.join(sub_where)}"
                ")"
            )
        else:
            not_exists_clause = (
                "NOT EXISTS ("
                "SELECT 1 FROM symbol_references r "
                f"{' '.join(sub_joins)} "
                f"WHERE {' AND '.join(sub_where)}"
                ")"
            )
        outer_where.append(not_exists_clause)

        where_clause = " AND ".join(outer_where) if outer_where else "1=1"
        params = outer_params + sub_params

        if is_first:
            sql = f"""
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
                    NULL AS anchor_mtime,
                    b.base_names,
                    s.id AS symbol_id
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
            """
        else:
            sql = f"""
                SELECT s.id AS symbol_id
                FROM symbols s
                WHERE {where_clause}
            """
        return sql, params

    @require_connection
    def query_relationships_chained(
        self,
        stages: List[Dict[str, Any]],
        limit: int = 100,
        case_sensitive: bool = True,
    ) -> Iterator[MatchRecord]:
        """Query symbols by a chain of positive/negative relationships using nested CTEs."""
        ctes = []
        all_params = []
        for i, args in enumerate(stages):
            is_first = (i == 0)
            is_negative = args.get('is_negative', False)
            if not is_negative:
                sql, params = self._build_relationship_cte_sql(
                    index=i,
                    relationship_type=args['relationship_type'],
                    subject_pattern=args.get('subject_pattern'),
                    object_pattern=args.get('object_pattern'),
                    subject_type=args.get('subject_type'),
                    object_type=args.get('object_type'),
                    subject_parent_pattern=args.get('subject_parent_pattern'),
                    invert=args.get('invert', False),
                    match_op=args.get('match_op', MatchOp.GLOB),
                    case_sensitive=case_sensitive,
                    result_newerthan_seconds=args.get('result_newerthan_seconds'),
                    result_olderthan_seconds=args.get('result_olderthan_seconds'),
                    subject_negated=args.get('subject_negated', False),
                    object_negated=args.get('object_negated', False),
                    subject_qualified=args.get('subject_qualified', False),
                    object_qualified=args.get('object_qualified', False),
                    is_first=is_first,
                )
            else:
                sql, params = self._build_negative_relationship_cte_sql(
                    index=i,
                    relationship_type=args['relationship_type'],
                    subject_pattern=args.get('subject_pattern'),
                    object_pattern=args.get('object_pattern'),
                    subject_type=args.get('subject_type'),
                    object_type=args.get('object_type'),
                    match_op=args.get('match_op', MatchOp.GLOB),
                    case_sensitive=case_sensitive,
                    result_newerthan_seconds=args.get('result_newerthan_seconds'),
                    result_olderthan_seconds=args.get('result_olderthan_seconds'),
                    invert_join=args.get('invert_join', False),
                    subject_negated=args.get('subject_negated', False),
                    object_negated=args.get('object_negated', False),
                    subject_qualified=args.get('subject_qualified', False),
                    object_qualified=args.get('object_qualified', False),
                    is_first=is_first,
                )
            ctes.append(f"rel_{i} AS (\n{sql}\n)")
            all_params.extend(params)

        # Build main query selecting from rel_0
        filters = []
        for i in range(1, len(stages)):
            filters.append(f"symbol_id IN (SELECT symbol_id FROM rel_{i})")

        filter_clause = " AND ".join(filters)
        where_clause = f" WHERE {filter_clause}" if filters else ""

        query = f"""
            WITH {', '.join(ctes)}
            SELECT
                symbol_name,
                symbol_type,
                file_path,
                line_number,
                byte_offset,
                byte_length,
                qualified_name,
                parent_name,
                mtime,
                anchor_mtime,
                base_names
            FROM rel_0
            {where_clause}
            ORDER BY file_path, line_number
            LIMIT ?
        """
        all_params.append(limit)

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
