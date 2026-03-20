"""
Tests for reference relationship indexing and querying (Sprint 5).

TLDR:
    Tests that the indexing pipeline correctly extracts and resolves "references"
    relationships between functions/methods and the global constants they use.
    Key test classes: TestReferenceExtractionFromAST (AST-based extraction,
    exclusion of local variables, parameters, and Python builtins),
    TestReferenceRelationshipResolution (relationship storage and resolution
    across files), TestReferenceRelationshipQueries (forward and inverted
    queries, glob-pattern matching against referenced names).
    Role: protects via.parsers.python_parser reference extraction and
    via.db.store relationship query paths; depends on IndexingService,
    DatabaseStore, PythonParser, and ParserRegistry.

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


class TestReferenceExtractionFromAST:
    """Test extraction of symbol references from AST."""

    def test_function_references_global_constant(self, db_store, indexing_service, tmp_path):
        """Test that a function referencing a global constant is extracted."""
        test_file = tmp_path / "const_ref.py"
        test_file.write_text("""
MY_CONSTANT = 42

def use_constant():
    return MY_CONSTANT + 1
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Check pending relationships for references
        cursor = db_store.conn.execute(
            "SELECT target_name, rel_type FROM pending_relationships WHERE rel_type = 'references'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # use_constant() references MY_CONSTANT
        assert 'MY_CONSTANT' in target_names

    def test_multiple_references_in_function(self, db_store, indexing_service, tmp_path):
        """Test that multiple references in a function are extracted."""
        test_file = tmp_path / "multi_ref.py"
        test_file.write_text("""
CONFIG_A = "value_a"
CONFIG_B = "value_b"
CONFIG_C = "value_c"

def process_config():
    a = CONFIG_A
    b = CONFIG_B
    c = CONFIG_C
    return a + b + c
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'references'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        assert 'CONFIG_A' in target_names
        assert 'CONFIG_B' in target_names
        assert 'CONFIG_C' in target_names

    def test_method_references_constant(self, db_store, indexing_service, tmp_path):
        """Test that method references to constants are extracted."""
        test_file = tmp_path / "method_ref.py"
        test_file.write_text("""
MAX_SIZE = 100

class MyClass:
    def check_size(self, value):
        return value < MAX_SIZE
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'references'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # check_size() references MAX_SIZE
        assert 'MAX_SIZE' in target_names

    def test_local_variables_not_indexed_as_references(self, db_store, indexing_service, tmp_path):
        """Test that local variables are not indexed as references."""
        test_file = tmp_path / "local_vars.py"
        test_file.write_text("""
def process():
    local_var = 10
    result = local_var + 5
    return result
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'references'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # local_var should not be indexed (it's a local variable)
        assert 'local_var' not in target_names

    def test_function_parameters_not_indexed(self, db_store, indexing_service, tmp_path):
        """Test that function parameters are not indexed as references."""
        test_file = tmp_path / "params.py"
        test_file.write_text("""
def process(param1, param2):
    return param1 + param2
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT COUNT(*) FROM pending_relationships WHERE rel_type = 'references'"
        )
        count = cursor.fetchone()[0]
        # No references should be created for parameters
        assert count == 0

    def test_builtins_not_indexed_as_references(self, db_store, indexing_service, tmp_path):
        """Test that Python builtins are not indexed as references."""
        test_file = tmp_path / "builtins.py"
        test_file.write_text("""
def process():
    return True, False, None
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.execute(
            "SELECT target_name FROM pending_relationships WHERE rel_type = 'references'"
        )
        pending = cursor.fetchall()
        target_names = [r[0] for r in pending]

        # Python builtins should not be indexed
        assert 'True' not in target_names
        assert 'False' not in target_names
        assert 'None' not in target_names


class TestReferenceRelationshipResolution:
    """Test resolution of reference relationships."""

    def test_reference_resolves_to_global_in_same_file(self, db_store, indexing_service, tmp_path):
        """Test that references resolve to globals in the same file."""
        test_file = tmp_path / "same_file_ref.py"
        test_file.write_text("""
MY_SETTING = "production"

def get_setting():
    return MY_SETTING
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that reference 'MY_SETTING'
        results = list(db_store.query_relationships(
            relationship_type='references',
            object_pattern='MY_SETTING',
            invert=False
        ))

        # Should find 'get_setting' as a referencer of 'MY_SETTING'
        names = [r.symbol_name for r in results]
        assert 'get_setting' in names


class TestReferenceRelationshipQueries:
    """Test querying reference relationships."""

    def test_query_referencers_of_constant(self, db_store, indexing_service, tmp_path):
        """Test finding all symbols that reference a constant."""
        test_file = tmp_path / "referencers.py"
        test_file.write_text("""
API_KEY = "secret"

def connect():
    return API_KEY

def validate():
    key = API_KEY
    return key is not None

def unrelated():
    return 42
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that reference 'API_KEY'
        results = list(db_store.query_relationships(
            relationship_type='references',
            object_pattern='API_KEY',
            invert=False
        ))

        names = [r.symbol_name for r in results]
        assert 'connect' in names
        assert 'validate' in names
        assert 'unrelated' not in names

    def test_query_what_function_references_inverted(self, db_store, indexing_service, tmp_path):
        """Test finding what a function references (inverted query)."""
        test_file = tmp_path / "references_list.py"
        test_file.write_text("""
CONST_A = 1
CONST_B = 2

def compute():
    return CONST_A + CONST_B
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find what 'compute' references (inverted)
        results = list(db_store.query_relationships(
            relationship_type='references',
            subject_pattern='compute',
            invert=True
        ))

        names = [r.symbol_name for r in results]
        assert 'CONST_A' in names
        assert 'CONST_B' in names

    def test_query_references_with_glob_pattern(self, db_store, indexing_service, tmp_path):
        """Test reference query with glob pattern."""
        test_file = tmp_path / "pattern_refs.py"
        test_file.write_text("""
CONFIG_HOST = "localhost"
CONFIG_PORT = 8080
DATA_FILE = "data.csv"

def connect():
    return CONFIG_HOST, CONFIG_PORT
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find functions that reference 'CONFIG_*' constants
        results = list(db_store.query_relationships(
            relationship_type='references',
            object_pattern='CONFIG_*',
            invert=False
        ))

        names = [r.symbol_name for r in results]
        # 'connect' references both CONFIG_HOST and CONFIG_PORT
        assert 'connect' in names
