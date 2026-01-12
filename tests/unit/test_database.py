"""Unit tests for database layer."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from via.db.store import DatabaseStore
from via.db.schema import SCHEMA_VERSION


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
                "classes",
                "files",
                "functions",
                "globals",
                "imports",
                "log_statements",
                "markdown_headings",
                "metadata",
                "schema_migrations",
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

    def test_insert_and_get_function(self, db_store):
        """Test function insertion and retrieval."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        func_id = db_store.insert_function(
            file_id=file_id,
            name="test_func",
            line_start=1,
            line_end=10,
            byte_offset=0,
            byte_length=100,
            args="arg1, arg2",
            decorators="@decorator",
            docstring="Test function",
        )

        assert func_id > 0

        funcs = db_store.get_functions_by_file(file_id)
        assert len(funcs) == 1
        assert funcs[0]["name"] == "test_func"
        assert funcs[0]["args"] == "arg1, arg2"

        funcs_by_name = db_store.get_functions_by_name("test_func")
        assert len(funcs_by_name) == 1

    def test_insert_method_with_class_id(self, db_store):
        """Test inserting a method with class_id."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        # Insert class first
        class_id = db_store.insert_class(
            file_id=file_id,
            name="TestClass",
            line_start=1,
            line_end=20,
            byte_offset=0,
            byte_length=200,
        )

        # Insert method
        method_id = db_store.insert_function(
            file_id=file_id,
            class_id=class_id,
            name="test_method",
            line_start=5,
            line_end=10,
            byte_offset=50,
            byte_length=100,
        )

        funcs = db_store.get_functions_by_file(file_id)
        assert len(funcs) == 1
        assert funcs[0]["class_id"] == class_id

    def test_delete_functions_by_file(self, db_store):
        """Test deleting all functions for a file."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        db_store.insert_function(
            file_id=file_id,
            name="func1",
            line_start=1,
            line_end=5,
            byte_offset=0,
            byte_length=50,
        )
        db_store.insert_function(
            file_id=file_id,
            name="func2",
            line_start=6,
            line_end=10,
            byte_offset=50,
            byte_length=50,
        )

        assert len(db_store.get_functions_by_file(file_id)) == 2

        db_store.delete_functions_by_file(file_id)
        assert len(db_store.get_functions_by_file(file_id)) == 0

    def test_insert_and_get_class(self, db_store):
        """Test class insertion and retrieval."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        class_id = db_store.insert_class(
            file_id=file_id,
            name="TestClass",
            line_start=1,
            line_end=20,
            byte_offset=0,
            byte_length=200,
            bases="BaseClass",
            decorators="@dataclass",
            docstring="Test class",
        )

        assert class_id > 0

        classes = db_store.get_classes_by_file(file_id)
        assert len(classes) == 1
        assert classes[0]["name"] == "TestClass"
        assert classes[0]["bases"] == "BaseClass"

        classes_by_name = db_store.get_classes_by_name("TestClass")
        assert len(classes_by_name) == 1

    def test_delete_classes_by_file(self, db_store):
        """Test deleting all classes for a file."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        db_store.insert_class(
            file_id=file_id,
            name="Class1",
            line_start=1,
            line_end=10,
            byte_offset=0,
            byte_length=100,
        )

        assert len(db_store.get_classes_by_file(file_id)) == 1

        db_store.delete_classes_by_file(file_id)
        assert len(db_store.get_classes_by_file(file_id)) == 0

    def test_insert_and_get_import(self, db_store):
        """Test import insertion and retrieval."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        import_id = db_store.insert_import(
            file_id=file_id,
            module="os.path",
            name="join",
            alias="path_join",
            line_number=1,
            byte_offset=0,
            byte_length=30,
        )

        assert import_id > 0

        imports = db_store.get_imports_by_file(file_id)
        assert len(imports) == 1
        assert imports[0]["module"] == "os.path"
        assert imports[0]["name"] == "join"
        assert imports[0]["alias"] == "path_join"

    def test_delete_imports_by_file(self, db_store):
        """Test deleting all imports for a file."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        db_store.insert_import(
            file_id=file_id,
            module="os",
            line_number=1,
            byte_offset=0,
            byte_length=10,
        )

        assert len(db_store.get_imports_by_file(file_id)) == 1

        db_store.delete_imports_by_file(file_id)
        assert len(db_store.get_imports_by_file(file_id)) == 0

    def test_insert_and_get_global(self, db_store):
        """Test global variable insertion and retrieval."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        global_id = db_store.insert_global(
            file_id=file_id,
            name="CONSTANT",
            value="42",
            type_hint="int",
            line_number=1,
            byte_offset=0,
            byte_length=15,
        )

        assert global_id > 0

        globals_list = db_store.get_globals_by_file(file_id)
        assert len(globals_list) == 1
        assert globals_list[0]["name"] == "CONSTANT"
        assert globals_list[0]["value"] == "42"
        assert globals_list[0]["type_hint"] == "int"

    def test_delete_globals_by_file(self, db_store):
        """Test deleting all globals for a file."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        db_store.insert_global(
            file_id=file_id,
            name="VAR",
            line_number=1,
            byte_offset=0,
            byte_length=10,
        )

        assert len(db_store.get_globals_by_file(file_id)) == 1

        db_store.delete_globals_by_file(file_id)
        assert len(db_store.get_globals_by_file(file_id)) == 0

    def test_cascade_delete(self, db_store):
        """Test that deleting a file cascades to all entities."""
        test_path = os.path.join(db_store.index_root, "test.py")
        file_id = db_store.insert_file(path=test_path, language="python")

        # Add entities
        class_id = db_store.insert_class(
            file_id=file_id,
            name="TestClass",
            line_start=1,
            line_end=10,
            byte_offset=0,
            byte_length=100,
        )
        db_store.insert_function(
            file_id=file_id,
            name="test_func",
            line_start=1,
            line_end=5,
            byte_offset=0,
            byte_length=50,
        )
        db_store.insert_import(
            file_id=file_id,
            module="os",
            line_number=1,
            byte_offset=0,
            byte_length=10,
        )
        db_store.insert_global(
            file_id=file_id,
            name="VAR",
            line_number=1,
            byte_offset=0,
            byte_length=10,
        )

        # Verify entities exist
        assert len(db_store.get_classes_by_file(file_id)) == 1
        assert len(db_store.get_functions_by_file(file_id)) == 1
        assert len(db_store.get_imports_by_file(file_id)) == 1
        assert len(db_store.get_globals_by_file(file_id)) == 1

        # Delete file
        db_store.delete_file(file_id)

        # Verify all entities are deleted
        assert len(db_store.get_classes_by_file(file_id)) == 0
        assert len(db_store.get_functions_by_file(file_id)) == 0
        assert len(db_store.get_imports_by_file(file_id)) == 0
        assert len(db_store.get_globals_by_file(file_id)) == 0

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

    def test_foreign_key_constraints(self, db_store):
        """Test that foreign key constraints are enforced."""
        # Try to insert function with non-existent file_id
        with pytest.raises(Exception):  # sqlite3.IntegrityError
            db_store.insert_function(
                file_id=99999,
                name="test",
                line_start=1,
                line_end=5,
                byte_offset=0,
                byte_length=50,
            )
