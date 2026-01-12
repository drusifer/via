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
from pathlib import Path
from typing import Optional, List, Dict, Any

from .schema import (
    ALL_TABLES,
    CREATE_INDEXES,
    SCHEMA_VERSION,
)
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

    def initialize_schema(self) -> None:
        """Create all tables and indexes if they don't exist."""
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        self._commit_if_needed()

    def delete_file_by_path(self, path: str) -> None:
        """
        Delete file record by path.

        Args:
            path: Absolute file path
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM functions WHERE name = ?", (name,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_functions_by_file(self, file_id: int) -> None:
        """
        Delete all functions for a file.

        Args:
            file_id: File ID
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE name = ?", (name,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_classes_by_file(self, file_id: int) -> None:
        """
        Delete all classes for a file.

        Args:
            file_id: File ID
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM imports WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_imports_by_file(self, file_id: int) -> None:
        """
        Delete all imports for a file.

        Args:
            file_id: File ID
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

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
        if not self.conn:
            raise RuntimeError("Database not connected")

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

    def get_globals_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all globals in a file.

        Args:
            file_id: File ID

        Returns:
            List of global records as dicts
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM globals WHERE file_id = ?", (file_id,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_globals_by_file(self, file_id: int) -> None:
        """
        Delete all globals for a file.

        Args:
            file_id: File ID
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM globals WHERE file_id = ?", (file_id,))
        self._commit_if_needed()

    # Batch operations for performance

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        self._in_transaction = True
        self.conn.execute("BEGIN TRANSACTION")

    def commit_transaction(self) -> None:
        """Commit current transaction."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        self.conn.commit()
        self._in_transaction = False

    def rollback_transaction(self) -> None:
        """Rollback current transaction."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        self.conn.rollback()
        self._in_transaction = False

    def _commit_if_needed(self) -> None:
        """Commit if not in a transaction."""
        if not self._in_transaction and self.conn:
            self.conn.commit()
