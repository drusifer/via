"""Unit tests for indexing service.

TLDR:
    Exercises IndexingService end-to-end: full directory scans, symbol extraction
    (functions, classes, imports, globals), incremental re-indexing, force-reindex,
    progress callbacks, oversized-file handling, parse-error resilience, and stats
    accuracy. Also confirms that re-indexing a modified file replaces stale symbols
    and that nested directories and empty directories are handled correctly.
    Role: protects the core indexing pipeline that populates the via symbol database.

"""

import os
import tempfile
from pathlib import Path

import pytest
from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService, IndexingStats


@pytest.fixture
def temp_project():
    """Create a temporary project with Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Python files
        Path(os.path.join(tmpdir, "module.py")).write_text("""
def hello():
    \"\"\"Say hello.\"\"\"
    print("Hello")

class MyClass:
    def method(self):
        pass
""")

        Path(os.path.join(tmpdir, "utils.py")).write_text("""
import os
from pathlib import Path

DEBUG = True

def utility():
    pass
""")

        # Create subdirectory
        os.makedirs(os.path.join(tmpdir, "subdir"))
        Path(os.path.join(tmpdir, "subdir", "nested.py")).write_text("""
class Nested:
    pass
""")

        yield tmpdir


@pytest.fixture
def indexing_service(temp_project):
    """Create indexing service with temp database."""
    db_path = os.path.join(temp_project, ".via", "index.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db_store = DatabaseStore(db_path, temp_project)
    db_store.connect()
    db_store.initialize_schema()

    registry = ParserRegistry()
    registry.register(PythonParser())

    service = IndexingService(db_store, registry)

    yield service

    db_store.close()


class TestIndexingService:
    """Test IndexingService class."""

    def test_index_directory(self, indexing_service, temp_project):
        """Test indexing a directory."""
        stats = indexing_service.index(temp_project)

        assert stats.total_files >= 3  # At least our 3 Python files
        assert stats.indexed_files >= 3
        assert stats.failed_files == 0

    def test_index_extracts_functions(self, indexing_service, temp_project):
        """Test that functions are extracted."""
        indexing_service.index(temp_project)

        # Query symbols table for functions
        cursor = indexing_service.db_store.conn.execute(
            "SELECT symbol_name FROM symbols WHERE symbol_type = ?",
            ('function',)
        )
        functions = cursor.fetchall()

        # Should have at least: hello, utility (method is a METHOD, not a function)
        assert len(functions) >= 2

        # Verify specific function names
        function_names = [row[0] for row in functions]
        assert 'hello' in function_names
        assert 'utility' in function_names

    def test_index_extracts_classes(self, indexing_service, temp_project):
        """Test that classes are extracted."""
        indexing_service.index(temp_project)

        # Query symbols table for classes
        cursor = indexing_service.db_store.conn.execute(
            "SELECT symbol_name FROM symbols WHERE symbol_type = ?",
            ('class',)
        )
        classes = cursor.fetchall()

        # Should have at least: MyClass, Nested
        assert len(classes) >= 2

        # Verify specific class names
        class_names = [row[0] for row in classes]
        assert 'MyClass' in class_names
        assert 'Nested' in class_names

    def test_index_extracts_imports(self, indexing_service, temp_project):
        """Test that imports are extracted."""
        indexing_service.index(temp_project)

        # Query symbols table for imports
        cursor = indexing_service.db_store.conn.execute(
            "SELECT symbol_name FROM symbols WHERE symbol_type = ?",
            ('import',)
        )
        imports = cursor.fetchall()

        # Should have at least: os, Path (from pathlib)
        assert len(imports) >= 2

        # Verify specific imports
        import_names = [row[0] for row in imports]
        assert 'os' in import_names
        assert 'Path' in import_names

    def test_index_extracts_globals(self, indexing_service, temp_project):
        """Test that globals are extracted."""
        indexing_service.index(temp_project)

        # Query symbols table for globals
        cursor = indexing_service.db_store.conn.execute(
            "SELECT symbol_name FROM symbols WHERE symbol_type = ?",
            ('global',)
        )
        globals_list = cursor.fetchall()

        # Should have at least: DEBUG
        assert len(globals_list) >= 1

        # Verify DEBUG global
        global_names = [row[0] for row in globals_list]
        assert 'DEBUG' in global_names

    def test_incremental_indexing_skips_unchanged(self, indexing_service, temp_project):
        """Test that incremental indexing skips unchanged files."""
        # First index
        stats1 = indexing_service.index(temp_project)
        indexed_count = stats1.indexed_files

        # Second index without changes
        stats2 = indexing_service.index(temp_project, force=False)

        # Should skip all files
        assert stats2.indexed_files == 0
        assert stats2.skipped_files >= indexed_count

    def test_incremental_indexing_reindexes_modified(self, indexing_service, temp_project):
        """Test that modified files are re-indexed."""
        # First index
        indexing_service.index(temp_project)

        # Modify a file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        module_path = os.path.join(temp_project, "module.py")
        with open(module_path, 'a') as f:
            f.write("\ndef new_function():\n    pass\n")

        # Second index
        stats = indexing_service.index(temp_project, force=False)

        # Should re-index the modified file
        assert stats.indexed_files >= 1

    def test_force_flag_reindexes_all(self, indexing_service, temp_project):
        """Test that force flag re-indexes all files."""
        # First index
        stats1 = indexing_service.index(temp_project)
        indexed_count = stats1.indexed_files

        # Second index with force
        stats2 = indexing_service.index(temp_project, force=True)

        # Should re-index all files
        assert stats2.indexed_files >= indexed_count

    def test_progress_callback(self, indexing_service, temp_project):
        """Test progress callback is called."""
        calls = []

        def callback(message, current, total):
            calls.append((message, current, total))

        indexing_service.index(temp_project, progress_callback=callback)

        assert len(calls) > 0
        assert any("Discovering" in msg for msg, _, _ in calls)

    def test_oversized_files_marked(self, indexing_service, temp_project):
        """Test that oversized files are marked."""
        # Create large file
        large_path = os.path.join(temp_project, "large.py")
        with open(large_path, 'w') as f:
            f.write("x" * (11 * 1024 * 1024))  # 11MB

        # Index with small size limit
        indexing_service.size_limit = 10 * 1024 * 1024  # 10MB
        stats = indexing_service.index(temp_project)

        assert stats.oversized_files >= 1

    def test_parse_error_handling(self, indexing_service, temp_project):
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        error_path = os.path.join(temp_project, "broken.py")
        Path(error_path).write_text("def broken(\n")  # Missing closing paren

        stats = indexing_service.index(temp_project)

        # Should not fail the entire index
        assert stats.total_files >= 4
        # File should be stored as unparsed
        file_record = indexing_service.db_store.get_file_by_path(error_path)
        assert file_record is not None

    def test_stats_accuracy(self, indexing_service, temp_project):
        """Test that stats accurately reflect indexing results."""
        stats = indexing_service.index(temp_project)

        # Verify stats fields
        assert stats.total_files > 0
        assert stats.indexed_files > 0
        assert stats.duration_seconds > 0
        assert stats.functions >= 3
        assert stats.classes >= 2

    def test_reindex_updates_entities(self, indexing_service, temp_project):
        """Test that re-indexing updates entities correctly."""
        # First index
        indexing_service.index(temp_project)

        # Modify file - replace content with a single new function
        import time
        time.sleep(0.1)
        module_path = os.path.join(temp_project, "module.py")
        with open(module_path, 'w') as f:
            f.write("""
def new_function():
    pass
""")

        # Re-index
        indexing_service.index(temp_project, force=True)

        # Check that old entities are gone and new ones exist
        # Query symbols for this specific file
        cursor = indexing_service.db_store.conn.execute(
            "SELECT symbol_name, symbol_type FROM symbols WHERE file_path = ? AND symbol_type = ?",
            (module_path, 'function')
        )
        functions = cursor.fetchall()

        # Should only have new_function now (old hello and method should be gone)
        assert len(functions) == 1
        assert functions[0][0] == 'new_function'

    def test_nested_directory_indexing(self, indexing_service, temp_project):
        """Test indexing of nested directories."""
        stats = indexing_service.index(temp_project)

        # Should find nested.py
        nested_path = os.path.join(temp_project, "subdir", "nested.py")
        file_record = indexing_service.db_store.get_file_by_path(nested_path)

        assert file_record is not None
        assert file_record['parsed'] == 1

    def test_error_handling_is_resilient(self, indexing_service, temp_project):
        """Test that errors in individual files don't fail entire index."""
        # Manually break file parsing for one file
        original_parse = PythonParser.parse

        def failing_parse(self, file_path, content):
            if 'utils.py' in file_path:
                raise RuntimeError("Simulated parse error")
            return original_parse(self, file_path, content)

        PythonParser.parse = failing_parse

        try:
            # Index should complete despite error in one file
            stats = indexing_service.index(temp_project)

            # Should have at least one failed file
            assert stats.failed_files >= 1

            # Other files should still be indexed
            assert stats.indexed_files >= 1

        finally:
            # Restore original method
            PythonParser.parse = original_parse

    def test_empty_directory(self, indexing_service):
        """Test indexing an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = indexing_service.index(tmpdir)

            assert stats.total_files == 0
            assert stats.indexed_files == 0
