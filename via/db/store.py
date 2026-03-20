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
        """Create all tables and indexes if they don't exist."""
        cursor = self.conn.cursor()

        # Create all tables
        for table_sql in ALL_TABLES:
            cursor.execute(table_sql)

        # Create all indexes
        for index_sql in CREATE_INDEXES:
            cursor.execute(index_sql)

        # Store metadata
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("index_root", self.index_root)
        )
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION))
        )

        # Record schema migration
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

        Replaces the three-step delete pattern in WatchService._remove_file().

        Args:
            path: Absolute file path
        """
        rel_path = self._to_relative_path(path)
        # Symbols table stores absolute paths; files table stores relative paths.
        cursor = self.conn.cursor()
        cursor.execute("BEGIN")
        try:
            # Delete relationships (symbol_references) for all symbols in this file
            cursor.execute(
                """DELETE FROM symbol_references
                   WHERE from_symbol_id IN (SELECT id FROM symbols WHERE file_path = ?)
                      OR to_symbol_id   IN (SELECT id FROM symbols WHERE file_path = ?)""",
                (path, path),
            )
            # Delete symbols (stored with absolute path)
            cursor.execute("DELETE FROM symbols WHERE file_path = ?", (path,))
            # Delete file record (stored with relative path)
            cursor.execute("DELETE FROM files WHERE path = ?", (rel_path,))
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise

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

        Returns:
            Symbol ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO symbols (
                symbol_name, symbol_type, file_path, line_number,
                byte_offset, byte_length, qualified_name, parent_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol_name, symbol_type, file_path, line_number,
             byte_offset, byte_length, qualified_name, parent_name)
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

    def _get_match_metadata(
        self,
        where_clause: str,
        params: List[Any]
    ) -> Dict[str, Any]:
        """
        Compute metadata for match results before streaming.

        Runs a single aggregation query to get total count and max column widths.
        This metadata is attached to every record for streaming renderers.

        Args:
            where_clause: SQL WHERE clause (without WHERE keyword)
            params: Query parameters

        Returns:
            Dict with 'total_matches' and 'column_widths'
        """
        query = f"""
            SELECT
                COUNT(*) as total,
                MAX(LENGTH(symbol_name)) as max_symbol_name,
                MAX(LENGTH(qualified_name)) as max_qualified_name,
                MAX(LENGTH(file_path)) as max_file_path,
                MAX(LENGTH(symbol_type)) as max_symbol_type,
                MAX(LENGTH(COALESCE(parent_name, ''))) as max_parent_name
            FROM symbols
            WHERE {where_clause}
        """

        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()

        return {
            'total_matches': row[0],
            'column_widths': {
                'symbol_name': row[1] or 0,
                'qualified_name': row[2] or 0,
                'file_path': row[3] or 0,
                'symbol_type': row[4] or 0,
                'parent_name': row[5] or 0,
            }
        }

    @require_connection
    def match(
        self,
        symbol_type: Optional[SymbolType],
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool = True,
        limit: Optional[int] = None,
        match_qualified: bool = False
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
                symbol_type, pattern, case_sensitive, limit, match_qualified
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

        where_parts.append(f"{column} {match_op.sql_op} ?")
        params.append(pattern)

        where_clause = ' AND '.join(where_parts)

        # Get metadata BEFORE streaming results (for column widths, total count)
        metadata = self._get_match_metadata(where_clause, params)

        # Build results query
        query = f"""
            SELECT
                symbol_name,
                symbol_type,
                file_path,
                line_number,
                byte_offset,
                byte_length,
                qualified_name,
                parent_name
            FROM symbols
            WHERE {where_clause}
            ORDER BY file_path, line_number
        """

        # Add limit if specified (0 means unlimited)
        if limit is not None and limit > 0:
            query += f"\nLIMIT {limit}"

        # Execute and yield results using factory with metadata
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
            }
            yield self._record_factory.create_from_row(row_dict, metadata)

    def _match_with_regex(
        self,
        symbol_type: Optional[SymbolType],
        pattern: str,
        case_sensitive: bool,
        limit: Optional[int],
        match_qualified: bool
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

        where_clause = ' AND '.join(where_parts) if where_parts else "1=1"

        # Get metadata for column widths
        metadata = self._get_match_metadata(where_clause, params)

        # Query all symbols of type
        query = f"""
            SELECT
                symbol_name,
                symbol_type,
                file_path,
                line_number,
                byte_offset,
                byte_length,
                qualified_name,
                parent_name
            FROM symbols
            WHERE {where_clause}
            ORDER BY file_path, line_number
        """

        cursor = self.conn.execute(query, params)
        count = 0

        for row in cursor:
            # Get the value to match against
            match_value = row[6] if match_qualified else row[0]  # qualified_name or symbol_name

            # Apply regex filter
            if regex.search(match_value):
                row_dict = {
                    'symbol_name': row[0],
                    'symbol_type': row[1],
                    'file_path': row[2],
                    'line_number': row[3],
                    'byte_offset': row[4],
                    'byte_length': row[5],
                    'qualified_name': row[6],
                    'parent_name': row[7],
                }
                yield self._record_factory.create_from_row(row_dict, metadata)
                count += 1

                # Check limit
                if limit is not None and 0 < limit <= count:
                    break

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
        invert: bool = False,
        match_op: MatchOp = MatchOp.GLOB,
        case_sensitive: bool = True,
        limit: int = 100
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

        if object_type:
            where_parts.append("t.symbol_type = ?")
            params.append(object_type)

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
                {select_from}.parent_name
            FROM symbol_references r
            JOIN symbols s ON r.{join_source} = s.id
            JOIN symbols t ON r.{join_target} = t.id
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
            }
            yield self._record_factory.create_from_row(row_dict)

    @require_connection
    def delete_relationships_for_file(self, file_path: str) -> int:
        """Delete all relationships involving symbols from a file.

        Used when re-indexing a file to clean up stale relationships.

        Args:
            file_path: Path to the file

        Returns:
            Number of relationships deleted
        """
        # Get symbol IDs for this file
        cursor = self.conn.execute(
            "SELECT id FROM symbols WHERE file_path = ?",
            (file_path,)
        )
        symbol_ids = [row[0] for row in cursor.fetchall()]

        if not symbol_ids:
            return 0

        # Delete relationships where these symbols are source or target
        placeholders = ",".join("?" * len(symbol_ids))
        deleted = 0

        cursor = self.conn.execute(
            f"DELETE FROM symbol_references WHERE from_symbol_id IN ({placeholders})",
            symbol_ids
        )
        deleted += cursor.rowcount

        cursor = self.conn.execute(
            f"DELETE FROM symbol_references WHERE to_symbol_id IN ({placeholders})",
            symbol_ids
        )
        deleted += cursor.rowcount

        return deleted
