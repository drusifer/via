"""
Database store for managing VIA index.

TLDR:
    Provides DatabaseStore class for SQLite operations with full CRUD for all
    entity types (files, functions, classes, imports, globals). Handles relative
    paths, transaction support, and automatic timestamp tracking. Row factory
    returns dicts for easy access.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import sqlite3
import time
from functools import wraps
from typing import Optional, List, Dict, Any, Iterator, Callable, TypeVar

from .schema import (
    ALL_TABLES,
    CREATE_INDEXES,
    SCHEMA_VERSION,
)
from ..core.types import SymbolType, MatchOp
from ..core.match_record import MatchRecord, MatchRecordFactory

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
        """Connect to database and enable foreign keys."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
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

    # Function CRUD operations

    def insert_function(
        self,
        file_id: int,
        name: str,
        line_start: int,
        line_end: int,
        byte_offset: int,
        byte_length: int,
        class_id: Optional[int] = None,
        args: Optional[str] = None,
        decorators: Optional[str] = None,
        docstring: Optional[str] = None,
    ) -> int:
        """
        Insert a function record.

        Args:
            file_id: File ID
            name: Function name
            line_start: Starting line number
            line_end: Ending line number
            byte_offset: Byte offset in file
            byte_length: Length in bytes
            class_id: Class ID if this is a method
            args: Function arguments (serialized)
            decorators: Decorators (serialized)
            docstring: Function docstring

        Returns:
            Function ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO functions (
                file_id, class_id, name, line_start, line_end,
                byte_offset, byte_length, args, decorators, docstring
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, class_id, name, line_start, line_end, byte_offset, byte_length,
             args, decorators, docstring)
        )
        self._commit_if_needed()
        return cursor.lastrowid

    def get_functions_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all functions in a file.

        Args:
            file_id: File ID

        Returns:
            List of function records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM functions WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_functions_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Get all functions by name.

        Args:
            name: Function name

        Returns:
            List of function records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM functions WHERE name = ?", (name,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_functions_by_file(self, file_id: int) -> None:
        """
        Delete all functions for a file.

        Args:
            file_id: File ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM functions WHERE file_id = ?", (file_id,))
        self._commit_if_needed()

    # Class CRUD operations

    def insert_class(
        self,
        file_id: int,
        name: str,
        line_start: int,
        line_end: int,
        byte_offset: int,
        byte_length: int,
        bases: Optional[str] = None,
        decorators: Optional[str] = None,
        docstring: Optional[str] = None,
    ) -> int:
        """
        Insert a class record.

        Args:
            file_id: File ID
            name: Class name
            line_start: Starting line number
            line_end: Ending line number
            byte_offset: Byte offset in file
            byte_length: Length in bytes
            bases: Base classes (serialized)
            decorators: Decorators (serialized)
            docstring: Class docstring

        Returns:
            Class ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO classes (
                file_id, name, line_start, line_end,
                byte_offset, byte_length, bases, decorators, docstring
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, name, line_start, line_end, byte_offset, byte_length,
             bases, decorators, docstring)
        )
        self._commit_if_needed()
        return cursor.lastrowid

    def get_classes_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all classes in a file.

        Args:
            file_id: File ID

        Returns:
            List of class records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_classes_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Get all classes by name.

        Args:
            name: Class name

        Returns:
            List of class records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE name = ?", (name,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_classes_by_file(self, file_id: int) -> None:
        """
        Delete all classes for a file.

        Args:
            file_id: File ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM classes WHERE file_id = ?", (file_id,))
        self._commit_if_needed()

    # Import CRUD operations

    def insert_import(
        self,
        file_id: int,
        module: str,
        line_number: int,
        byte_offset: int,
        byte_length: int,
        name: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> int:
        """
        Insert an import record.

        Args:
            file_id: File ID
            module: Module name
            line_number: Line number
            byte_offset: Byte offset in file
            byte_length: Length in bytes
            name: Imported name (for 'from X import Y')
            alias: Import alias ('as Z')

        Returns:
            Import ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO imports (file_id, module, name, alias, line_number, byte_offset, byte_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, module, name, alias, line_number, byte_offset, byte_length)
        )
        self._commit_if_needed()
        return cursor.lastrowid

    def get_imports_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all imports in a file.

        Args:
            file_id: File ID

        Returns:
            List of import records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM imports WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_imports_by_file(self, file_id: int) -> None:
        """
        Delete all imports for a file.

        Args:
            file_id: File ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM imports WHERE file_id = ?", (file_id,))
        self._commit_if_needed()

    # Global CRUD operations

    def insert_global(
        self,
        file_id: int,
        name: str,
        line_number: int,
        byte_offset: int,
        byte_length: int,
        value: Optional[str] = None,
        type_hint: Optional[str] = None,
    ) -> int:
        """
        Insert a global variable record.

        Args:
            file_id: File ID
            name: Variable name
            line_number: Line number
            byte_offset: Byte offset in file
            byte_length: Length in bytes
            value: Variable value (if literal)
            type_hint: Type hint

        Returns:
            Global ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO globals (file_id, name, value, type_hint, line_number, byte_offset, byte_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, name, value, type_hint, line_number, byte_offset, byte_length)
        )
        self._commit_if_needed()
        return cursor.lastrowid

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

    def get_globals_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all globals in a file.

        Args:
            file_id: File ID

        Returns:
            List of global records as dicts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM globals WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_globals_by_file(self, file_id: int) -> None:
        """
        Delete all globals for a file.

        Args:
            file_id: File ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM globals WHERE file_id = ?", (file_id,))
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
                if limit is not None and limit > 0 and count >= limit:
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
            "SELECT file_path, COUNT(*) as cnt FROM symbols GROUP BY file_path ORDER BY cnt DESC LIMIT ?",
            (limit,)
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]
