"""
Unit tests for Python import relationship indexing and querying.

TLDR:
    Verifies that the indexing pipeline correctly records Python import statements
    as pending relationships and resolves them into queryable symbol references.
    Covers simple imports, from-imports, nested module paths, multiple imports, and
    files with no imports. Also tests forward and inverted relationship queries and
    glob-pattern matching against import targets.
    Key class: TestImportRelationshipIndexing — exercises IndexingService._index_file()
    and DatabaseStore relationship queries via pytest fixtures.
    Role: protects import-relationship indexing and querying in IndexingService and
    DatabaseStore.

"""

from pathlib import Path

import pytest
from via.core.discovery import DiscoveredFile
from via.db.store import DatabaseStore
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


@pytest.fixture
def db_store(tmp_path):
    """Create a test database."""
    db_path = tmp_path / "test.db"
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def parser_registry():
    """Create parser registry with Python parser."""
    registry = ParserRegistry()
    registry.register(PythonParser())
    return registry


@pytest.fixture
def indexing_service(db_store, parser_registry, tmp_path):
    """Create indexing service for tests."""
    return IndexingService(db_store, parser_registry, str(tmp_path))


class TestImportRelationshipIndexing:
    """Test import relationship indexing during file parsing."""

    def test_simple_import_creates_pending_relationship(self, db_store, indexing_service, tmp_path):
        """Test that 'import os' creates a pending import relationship."""
        test_file = tmp_path / "simple_import.py"
        test_file.write_text("""
import os

def main():
    os.getcwd()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Check pending relationships were created for the import
        cursor = db_store.conn.execute(
            "SELECT target_name, rel_type FROM pending_relationships WHERE rel_type = 'imports'"
        )
        pending = cursor.fetchall()

        # Should have pending relationship for 'os' module
        target_names = [r[0] for r in pending]
        assert 'os' in target_names

    def test_from_import_creates_pending_relationship(self, db_store, indexing_service, tmp_path):
        """Test that 'from typing import List' creates pending relationship."""
        test_file = tmp_path / "from_import.py"
        test_file.write_text("""
from typing import List, Dict

def get_items() -> List[str]:
    return []
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name, rel_type FROM pending_relationships WHERE rel_type = 'imports'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # Should have pending relationships for 'typing.List' and 'typing.Dict'
        assert 'typing.List' in target_names or 'typing' in target_names

    def test_nested_module_import(self, db_store, indexing_service, tmp_path):
        """Test importing from nested modules like os.path."""
        test_file = tmp_path / "nested_import.py"
        test_file.write_text("""
import os.path

def check_file(path):
    return os.path.exists(path)
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'imports'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        assert 'os.path' in target_names

    def test_multiple_imports_all_tracked(self, db_store, indexing_service, tmp_path):
        """Test that multiple imports all create relationships."""
        test_file = tmp_path / "multi_import.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Optional

def main():
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'imports'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # Should track all imports
        assert len(target_names) >= 4

    def test_file_with_no_imports_no_pending(self, db_store, indexing_service, tmp_path):
        """Test that a file without imports creates no import relationships."""
        test_file = tmp_path / "no_imports.py"
        test_file.write_text("""
def add(a, b):
    return a + b
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT COUNT(*) FROM pending_relationships WHERE rel_type = 'imports'"
        )
        count = cursor.fetchone()[0]
        assert count == 0


class TestImportRelationshipQueries:
    """Test querying import relationships."""

    def test_query_files_importing_module(self, db_store, indexing_service, tmp_path):
        """Test finding files that import a specific module."""
        # Create two files - one imports typing, one doesn't
        file1 = tmp_path / "uses_typing.py"
        file1.write_text("""
from typing import List

def get_list() -> List[str]:
    return []
""")

        file2 = tmp_path / "no_typing.py"
        file2.write_text("""
def simple():
    return "hello"
""")

        # Index both files
        for f in [file1, file2]:
            file_info = DiscoveredFile(path=str(f), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
            indexing_service._index_file(file_info)

        db_store.resolve_pending_relationships()

        # Query: Find files that import 'typing'
        results = list(db_store.query_relationships(
            relationship_type='imports',
            object_pattern='typing*',
            invert=False
        ))

        # Should find file1 (uses_typing.py)
        file_paths = [r.file_path for r in results]
        assert any('uses_typing.py' in fp for fp in file_paths)
        assert not any('no_typing.py' in fp for fp in file_paths)

    def test_query_what_file_imports_inverted(self, db_store, indexing_service, tmp_path):
        """Test finding what modules an import symbol relates to (inverted query).

        Note: For import relationships, the source is the import SYMBOL (e.g., 'os'),
        not the file itself. To query "what does file X import", use the relationship
        with a pattern matching the import symbol name.
        """
        test_file = tmp_path / "imports_many.py"
        test_file.write_text("""
import os
import sys
from typing import List
from pathlib import Path
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find what module the 'os' import relates to (inverted)
        # This finds the target module for imports matching 'os'
        results = list(db_store.query_relationships(
            relationship_type='imports',
            subject_pattern='os',
            invert=True
        ))

        # Should find the 'os' module
        names = [r.symbol_name for r in results]
        assert 'os' in names

    def test_query_import_with_glob_pattern(self, db_store, indexing_service, tmp_path):
        """Test import query with glob pattern matching."""
        test_file = tmp_path / "pattern_test.py"
        test_file.write_text("""
from typing import List, Dict, Optional
from collections import defaultdict
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find files importing anything from 'typ*'
        results = list(db_store.query_relationships(
            relationship_type='imports',
            object_pattern='typ*',
            invert=False
        ))

        # Should match typing imports
        assert len(results) >= 1

    def test_query_filepath_imports_module(self, db_store, indexing_service, tmp_path):
        """Test finding filepath symbols that import a module."""
        test_file = tmp_path / "uses_sqlite.py"
        test_file.write_text("import sqlite3\n")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find filepath symbols that import 'sqlite3'
        results = list(db_store.query_relationships(
            relationship_type='imports',
            subject_type='filepath',
            object_pattern='sqlite3',
            object_type='import',
            invert=False
        ))

        assert len(results) == 1
        assert results[0].symbol_type == 'filepath'
        assert results[0].symbol_name == "uses_sqlite.py"

    def test_query_filepath_imports_filepath(self, db_store, indexing_service, tmp_path):
        """Test finding filepath symbols that import another file's exported module/symbol."""
        file_a = tmp_path / "module_a.py"
        file_a.write_text("class MyClass:\n    pass\n")

        file_b = tmp_path / "module_b.py"
        file_b.write_text("from module_a import MyClass\n")

        # Index both
        for f in (file_a, file_b):
            file_info = DiscoveredFile(path=str(f), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
            indexing_service._index_file(file_info)

        db_store.resolve_pending_relationships()

        # Query: Find filepath symbols that import from module_a
        results = list(db_store.query_relationships(
            relationship_type='imports',
            subject_type='filepath',
            object_pattern='*module_a*',
            object_type='filepath',
            invert=False
        ))

        assert len(results) == 1
        assert results[0].symbol_type == 'filepath'
        assert results[0].symbol_name == "module_b.py"

    def test_query_filepath_sans_imports_module(self, db_store, indexing_service, tmp_path):
        """Test finding files that do NOT import a module (negative query)."""
        file_a = tmp_path / "uses_sqlite.py"
        file_a.write_text("import sqlite3\n")

        file_b = tmp_path / "no_sqlite.py"
        file_b.write_text("import os\n")

        for f in (file_a, file_b):
            file_info = DiscoveredFile(path=str(f), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
            indexing_service._index_file(file_info)

        db_store.resolve_pending_relationships()

        # Query: Find filepaths that do NOT import 'sqlite3'
        results = list(db_store.query_negative_relationships(
            relationship_type='imports',
            subject_type='filepath',
            object_pattern='sqlite3',
            object_type='import',
            invert_join=False
        ))

        # Should find file_b (no_sqlite.py) but not file_a (uses_sqlite.py)
        names = [r.symbol_name for r in results]
        assert "no_sqlite.py" in names
        assert "uses_sqlite.py" not in names

