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
