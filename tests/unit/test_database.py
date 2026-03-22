"""Unit tests for database layer.

TLDR:
    Verifies the full lifecycle of DatabaseStore operations: connection management,
    context-manager usage, schema initialisation, and CRUD operations on file records.
    Also covers transaction commit/rollback semantics and automatic absolute-to-relative
    path conversion when storing and retrieving file entries.
    Key test class: TestDatabaseStore — exercises connect/close, context manager,
    schema init, file insert/update/delete/get-all, and relative-path conversion.
    Role: protects the SQLite persistence layer that underpins the via index store.

"""

import os
import tempfile
import time
from pathlib import Path

import pytest
from via.db.schema import SCHEMA_VERSION
from via.db.store import DatabaseStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        index_root = tmpdir
        yield db_path, index_root


@pytest.fixture
def db_store(temp_db):
    """Create a DatabaseStore instance."""
    db_path, index_root = temp_db
    store = DatabaseStore(db_path, index_root)
    with store:
        store.initialize_schema()
        yield store


class TestDatabaseStore:
    """Test DatabaseStore class."""

    def test_connect_and_close(self, temp_db):
        """Test database connection and closing."""
        db_path, index_root = temp_db
        store = DatabaseStore(db_path, index_root)

        assert store.conn is None
        store.connect()
        assert store.conn is not None
        store.close()
        assert store.conn is None

    def test_context_manager(self, temp_db):
        """Test context manager usage."""
        db_path, index_root = temp_db
        store = DatabaseStore(db_path, index_root)

        with store:
            assert store.conn is not None
        assert store.conn is None

    def test_initialize_schema(self, temp_db):
        """Test schema initialization."""
        db_path, index_root = temp_db
        store = DatabaseStore(db_path, index_root)

        with store:
            store.initialize_schema()

            # Check metadata
            assert store.get_metadata("index_root") == index_root
            assert store.get_metadata("schema_version") == str(SCHEMA_VERSION)

            # Check tables exist
            cursor = store.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "files",
                "metadata",
                "pending_relationships",
                "schema_migrations",
                "symbol_references",
                "symbols",
            ]
            # sqlite_sequence is auto-created for AUTOINCREMENT columns
            assert all(t in tables for t in expected_tables)

    def test_schema_migration_from_v4_does_not_crash(self, temp_db):
        """S9-001: initialize_schema() on a v4 DB (symbols lacks mtime) must not crash.

        Simulates upgrading from Sprint 8 to Sprint 9: the symbols table exists
        but has no mtime column, and metadata has schema_version = 4.
        CREATE_INDEXES includes idx_symbols_mtime; if it runs before the ALTER TABLE
        the index creation fails with 'no such column: mtime'.
        """
        import sqlite3 as _sqlite3
        db_path, index_root = temp_db

        # Bootstrap a v4 DB manually (symbols without mtime, metadata at version 4)
        conn = _sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)
        """)
        conn.execute("""
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY, applied_at REAL NOT NULL, description TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL, language TEXT, size_bytes INTEGER,
                mtime REAL, indexed_at REAL, parsed BOOLEAN DEFAULT 0,
                oversized BOOLEAN DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_name TEXT NOT NULL, symbol_type TEXT NOT NULL,
                file_path TEXT NOT NULL, line_number INTEGER NOT NULL,
                byte_offset INTEGER, byte_length INTEGER,
                qualified_name TEXT NOT NULL, parent_name TEXT
                -- NOTE: no mtime column — this is the v4 schema
            )
        """)
        conn.execute("""
            CREATE TABLE symbol_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_symbol_id INTEGER NOT NULL, to_symbol_id INTEGER NOT NULL,
                reference_type TEXT NOT NULL, line_number INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE pending_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL, target_name TEXT NOT NULL, rel_type TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO metadata VALUES ('schema_version', '4')")
        conn.execute("INSERT INTO metadata VALUES ('index_root', ?)", (index_root,))
        conn.commit()
        conn.close()

        # This must not raise — the migration should add mtime before the index is created
        store = DatabaseStore(db_path, index_root)
        with store:
            store.initialize_schema()  # Must not crash with 'no such column: mtime'
            # Verify mtime column was added
            cols = {
                row[1]
                for row in store.conn.execute("PRAGMA table_info(symbols)")
            }
            assert 'mtime' in cols, "symbols.mtime column missing after migration"
            # Verify version updated
            assert store.get_metadata("schema_version") == str(SCHEMA_VERSION)

    def test_insert_and_get_file(self, db_store):
        """Test file insertion and retrieval."""
        test_path = os.path.join(db_store.index_root, "test.py")

        # Insert file
        file_id = db_store.insert_file(
            path=test_path,
            language="python",
            size_bytes=1024,
            mtime=time.time(),
            parsed=True,
        )

        assert file_id > 0

        # Get by path
        file_record = db_store.get_file_by_path(test_path)
        assert file_record is not None
        assert file_record["id"] == file_id
        assert file_record["path"] == "test.py"  # Relative path
        assert file_record["language"] == "python"
        assert file_record["size_bytes"] == 1024
        assert file_record["parsed"] == 1

        # Get by ID
        file_record2 = db_store.get_file_by_id(file_id)
        assert file_record2 is not None
        assert file_record2["id"] == file_id

    def test_update_file(self, db_store):
        """Test file update."""
        test_path = os.path.join(db_store.index_root, "test.py")

        file_id = db_store.insert_file(path=test_path, parsed=False)

        # Update
        db_store.update_file(file_id, language="python", parsed=True)

        file_record = db_store.get_file_by_id(file_id)
        assert file_record["language"] == "python"
        assert file_record["parsed"] == 1

    def test_delete_file(self, db_store):
        """Test file deletion."""
        test_path = os.path.join(db_store.index_root, "test.py")

        file_id = db_store.insert_file(path=test_path)
        assert db_store.get_file_by_id(file_id) is not None

        db_store.delete_file(file_id)
        assert db_store.get_file_by_id(file_id) is None

    def test_delete_file_by_path(self, db_store):
        """Test file deletion by path."""
        test_path = os.path.join(db_store.index_root, "test.py")

        db_store.insert_file(path=test_path)
        assert db_store.get_file_by_path(test_path) is not None

        db_store.delete_file_by_path(test_path)
        assert db_store.get_file_by_path(test_path) is None

    def test_get_all_files(self, db_store):
        """Test getting all files."""
        path1 = os.path.join(db_store.index_root, "test1.py")
        path2 = os.path.join(db_store.index_root, "test2.py")

        db_store.insert_file(path=path1, parsed=True)
        db_store.insert_file(path=path2, parsed=False)

        all_files = db_store.get_all_files()
        assert len(all_files) == 2

        parsed_files = db_store.get_all_files(parsed_only=True)
        assert len(parsed_files) == 1
        assert parsed_files[0]["path"] == "test1.py"

    def test_transaction_commit(self, db_store):
        """Test transaction commit."""
        test_path = os.path.join(db_store.index_root, "test.py")

        db_store.begin_transaction()
        file_id = db_store.insert_file(path=test_path)
        db_store.commit_transaction()

        assert db_store.get_file_by_id(file_id) is not None

    def test_transaction_rollback(self, db_store):
        """Test transaction rollback."""
        test_path = os.path.join(db_store.index_root, "test.py")

        db_store.begin_transaction()
        file_id = db_store.insert_file(path=test_path)
        db_store.rollback_transaction()

        assert db_store.get_file_by_id(file_id) is None

    def test_relative_path_conversion(self, db_store):
        """Test relative path conversion."""
        # Test with nested path
        nested_path = os.path.join(db_store.index_root, "subdir", "test.py")

        file_id = db_store.insert_file(path=nested_path)
        file_record = db_store.get_file_by_id(file_id)

        assert file_record["path"] == os.path.join("subdir", "test.py")

        # Verify we can retrieve by absolute path
        file_record2 = db_store.get_file_by_path(nested_path)
        assert file_record2["id"] == file_id


class TestQueryRelationshipsStale:
    """S10-2: query_relationships returns mtime + anchor_mtime on each record."""

    def _insert_sym(self, store, name, sym_type, file_path, mtime):
        return store.insert_symbol(
            symbol_name=name,
            symbol_type=sym_type,
            file_path=file_path,
            line_number=1,
            qualified_name=name,
            mtime=mtime,
        )

    def test_result_has_mtime_and_anchor_mtime(self, db_store):
        """Results from query_relationships carry mtime and anchor_mtime."""
        anchor_path = os.path.join(db_store.index_root, "base.py")
        result_path = os.path.join(db_store.index_root, "child.py")
        anchor_mtime = 1000.0
        result_mtime = 900.0  # result is older than anchor (stale)

        anchor_id = self._insert_sym(db_store, 'Base', 'class', anchor_path, anchor_mtime)
        result_id = self._insert_sym(db_store, 'Child', 'class', result_path, result_mtime)
        db_store.conn.execute(
            "INSERT INTO symbol_references (from_symbol_id, to_symbol_id, reference_type) VALUES (?, ?, ?)",
            (result_id, anchor_id, 'inherits-from')
        )
        db_store.conn.commit()

        results = list(db_store.query_relationships('inherits-from'))
        assert len(results) == 1
        r = results[0]
        assert r.mtime == result_mtime
        assert r.anchor_mtime == anchor_mtime

    def test_stale_result_identified_by_mtime(self, db_store):
        """result.mtime < anchor.mtime identifies a stale result."""
        anchor_path = os.path.join(db_store.index_root, "base.py")
        result_path = os.path.join(db_store.index_root, "child.py")

        anchor_id = self._insert_sym(db_store, 'Base', 'class', anchor_path, 2000.0)
        result_id = self._insert_sym(db_store, 'Child', 'class', result_path, 1000.0)
        db_store.conn.execute(
            "INSERT INTO symbol_references (from_symbol_id, to_symbol_id, reference_type) VALUES (?, ?, ?)",
            (result_id, anchor_id, 'inherits-from')
        )
        db_store.conn.commit()

        results = list(db_store.query_relationships('inherits-from'))
        assert len(results) == 1
        r = results[0]
        assert r.mtime < r.anchor_mtime  # stale

    def test_fresh_result_identified_by_mtime(self, db_store):
        """result.mtime >= anchor.mtime identifies a fresh result."""
        anchor_path = os.path.join(db_store.index_root, "base.py")
        result_path = os.path.join(db_store.index_root, "child.py")

        anchor_id = self._insert_sym(db_store, 'Base', 'class', anchor_path, 1000.0)
        result_id = self._insert_sym(db_store, 'Child', 'class', result_path, 2000.0)
        db_store.conn.execute(
            "INSERT INTO symbol_references (from_symbol_id, to_symbol_id, reference_type) VALUES (?, ?, ?)",
            (result_id, anchor_id, 'inherits-from')
        )
        db_store.conn.commit()

        results = list(db_store.query_relationships('inherits-from'))
        assert len(results) == 1
        r = results[0]
        assert r.mtime >= r.anchor_mtime  # fresh

    def test_none_mtime_when_not_indexed(self, db_store):
        """anchor_mtime and mtime are None when symbols have no mtime."""
        anchor_path = os.path.join(db_store.index_root, "base.py")
        result_path = os.path.join(db_store.index_root, "child.py")

        anchor_id = self._insert_sym(db_store, 'Base', 'class', anchor_path, None)
        result_id = self._insert_sym(db_store, 'Child', 'class', result_path, None)
        db_store.conn.execute(
            "INSERT INTO symbol_references (from_symbol_id, to_symbol_id, reference_type) VALUES (?, ?, ?)",
            (result_id, anchor_id, 'inherits-from')
        )
        db_store.conn.commit()

        results = list(db_store.query_relationships('inherits-from'))
        assert len(results) == 1
        r = results[0]
        assert r.mtime is None
        assert r.anchor_mtime is None
