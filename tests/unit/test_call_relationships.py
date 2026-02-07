"""
TDD tests for Sprint 5 - Call Relationship Indexing.

Tests the indexing and querying of call relationships:
- Function calls function
- Method calls method
- Query callers of a function
- Query what a function calls (inverted)

Author: Neo (SWE)
Sprint: 5, Phase 4
"""

import pytest
from pathlib import Path

from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser
from via.core.discovery import DiscoveredFile


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


class TestCallExtractionFromAST:
    """Test extraction of function calls from AST."""

    def test_simple_function_call_extracted(self, db_store, indexing_service, tmp_path):
        """Test that a simple function call is extracted."""
        test_file = tmp_path / "simple_call.py"
        test_file.write_text("""
def helper():
    pass

def main():
    helper()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Check pending relationships for calls
        cursor = db_store.conn.execute(
            "SELECT target_name, rel_type FROM pending_relationships WHERE rel_type = 'calls'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # main() calls helper()
        assert 'helper' in target_names

    def test_multiple_calls_in_function(self, db_store, indexing_service, tmp_path):
        """Test that multiple calls in a function are extracted."""
        test_file = tmp_path / "multi_call.py"
        test_file.write_text("""
def func_a():
    pass

def func_b():
    pass

def func_c():
    pass

def main():
    func_a()
    func_b()
    func_c()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'calls'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        assert 'func_a' in target_names
        assert 'func_b' in target_names
        assert 'func_c' in target_names

    def test_method_call_extracted(self, db_store, indexing_service, tmp_path):
        """Test that method calls are extracted."""
        test_file = tmp_path / "method_call.py"
        test_file.write_text("""
class MyClass:
    def helper(self):
        pass

    def process(self):
        self.helper()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'calls'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # process() calls self.helper() -> should capture 'helper'
        assert 'helper' in target_names

    def test_builtin_calls_not_indexed(self, db_store, indexing_service, tmp_path):
        """Test that calls to builtins like print() are not indexed."""
        test_file = tmp_path / "builtin_call.py"
        test_file.write_text("""
def main():
    print("hello")
    len([1, 2, 3])
    str(42)
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'calls'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # Should not include builtins
        assert 'print' not in target_names
        assert 'len' not in target_names
        assert 'str' not in target_names

    def test_function_with_no_calls(self, db_store, indexing_service, tmp_path):
        """Test that a function without calls creates no call relationships."""
        test_file = tmp_path / "no_calls.py"
        test_file.write_text("""
def simple():
    x = 1 + 2
    return x
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT COUNT(*) FROM pending_relationships WHERE rel_type = 'calls'"
        )
        count = cursor.fetchone()[0]
        assert count == 0


class TestCallRelationshipResolution:
    """Test resolution of call relationships."""

    def test_call_resolves_to_function_in_same_file(self, db_store, indexing_service, tmp_path):
        """Test that calls resolve to functions in the same file."""
        test_file = tmp_path / "same_file.py"
        test_file.write_text("""
def helper():
    return 42

def main():
    result = helper()
    return result
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that call 'helper'
        results = list(db_store.query_relationships(
            relationship_type='calls',
            object_pattern='helper',
            invert=False
        ))

        # Should find 'main' as a caller of 'helper'
        names = [r.symbol_name for r in results]
        assert 'main' in names


class TestCallRelationshipQueries:
    """Test querying call relationships."""

    def test_query_callers_of_function(self, db_store, indexing_service, tmp_path):
        """Test finding all callers of a function."""
        test_file = tmp_path / "callers.py"
        test_file.write_text("""
def utility():
    pass

def caller1():
    utility()

def caller2():
    utility()

def no_call():
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that call 'utility'
        results = list(db_store.query_relationships(
            relationship_type='calls',
            object_pattern='utility',
            invert=False
        ))

        names = [r.symbol_name for r in results]
        assert 'caller1' in names
        assert 'caller2' in names
        assert 'no_call' not in names

    def test_query_what_function_calls_inverted(self, db_store, indexing_service, tmp_path):
        """Test finding what a function calls (inverted query)."""
        test_file = tmp_path / "callees.py"
        test_file.write_text("""
def helper1():
    pass

def helper2():
    pass

def main():
    helper1()
    helper2()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find what 'main' calls (inverted)
        results = list(db_store.query_relationships(
            relationship_type='calls',
            subject_pattern='main',
            invert=True
        ))

        names = [r.symbol_name for r in results]
        assert 'helper1' in names
        assert 'helper2' in names

    def test_query_calls_with_glob_pattern(self, db_store, indexing_service, tmp_path):
        """Test call query with glob pattern."""
        test_file = tmp_path / "pattern_calls.py"
        test_file.write_text("""
def get_data():
    pass

def get_config():
    pass

def set_value():
    pass

def process():
    get_data()
    get_config()
    set_value()
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that call 'get_*' functions
        results = list(db_store.query_relationships(
            relationship_type='calls',
            object_pattern='get_*',
            invert=False
        ))

        names = [r.symbol_name for r in results]
        # 'process' calls both get_data and get_config
        assert 'process' in names
