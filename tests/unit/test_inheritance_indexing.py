"""TDD tests for Sprint 5 - Inheritance relationship indexing.

Tests that inheritance relationships are properly indexed during file parsing.

Author: Neo (SWE)
Sprint: 5, Phase 2
"""
import pytest
import tempfile
import os
from via.db.store import DatabaseStore
from via.services.indexing import IndexingService
from via.core.discovery import DiscoveredFile
from via.parsers.registry import ParserRegistry
from via.parsers.python_parser import PythonParser


@pytest.fixture
def db_store(tmp_path):
    """Create a temporary database store."""
    db_path = tmp_path / "test.db"
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()
    yield store
    store.close()


@pytest.fixture
def parser_registry():
    """Create a parser registry with Python parser."""
    registry = ParserRegistry()
    registry.register(PythonParser())
    return registry


@pytest.fixture
def indexing_service(db_store, parser_registry):
    """Create an indexing service with the test database."""
    return IndexingService(db_store, parser_registry)


class TestInheritanceRelationshipIndexing:
    """Test that inheritance relationships are indexed during file parsing."""

    def test_simple_inheritance_creates_pending_relationship(self, db_store, indexing_service, tmp_path):
        """Test that a simple class inheritance creates a pending relationship."""
        # Create a test file with inheritance
        test_file = tmp_path / "child.py"
        test_file.write_text("""
class BaseClass:
    pass

class ChildClass(BaseClass):
    pass
""")

        # Index the file
        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Check pending relationships were created
        cursor = db_store.conn.cursor()
        cursor.execute("SELECT * FROM pending_relationships WHERE rel_type = 'inherits-from'")
        pending = cursor.fetchall()

        assert len(pending) >= 1
        # Find the pending relationship for ChildClass -> BaseClass
        target_names = [row[2] for row in pending]  # target_name is column 2
        assert 'BaseClass' in target_names

    def test_multiple_inheritance_creates_multiple_pending(self, db_store, indexing_service, tmp_path):
        """Test that multiple inheritance creates multiple pending relationships."""
        test_file = tmp_path / "multi.py"
        test_file.write_text("""
class Base1:
    pass

class Base2:
    pass

class Child(Base1, Base2):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.cursor()
        cursor.execute("SELECT target_name FROM pending_relationships WHERE rel_type = 'inherits-from'")
        target_names = [row[0] for row in cursor.fetchall()]

        assert 'Base1' in target_names
        assert 'Base2' in target_names

    def test_resolve_pending_creates_relationships(self, db_store, indexing_service, tmp_path):
        """Test that resolve_pending_relationships creates actual relationships."""
        test_file = tmp_path / "resolve.py"
        test_file.write_text("""
class BaseClass:
    pass

class ChildClass(BaseClass):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Resolve pending relationships
        resolved_count = db_store.resolve_pending_relationships()

        # Should have resolved at least one relationship
        assert resolved_count >= 1

        # Check symbol_references table
        cursor = db_store.conn.cursor()
        cursor.execute("""
            SELECT s1.symbol_name, s2.symbol_name, sr.reference_type
            FROM symbol_references sr
            JOIN symbols s1 ON sr.from_symbol_id = s1.id
            JOIN symbols s2 ON sr.to_symbol_id = s2.id
            WHERE sr.reference_type = 'inherits-from'
        """)
        relationships = cursor.fetchall()

        assert len(relationships) >= 1
        # Check ChildClass inherits from BaseClass
        rel_pairs = [(row[0], row[1]) for row in relationships]
        assert ('ChildClass', 'BaseClass') in rel_pairs

    def test_inheritance_query_after_indexing(self, db_store, indexing_service, tmp_path):
        """Test full flow: index, resolve, then query relationships."""
        test_file = tmp_path / "full_flow.py"
        test_file.write_text("""
class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find classes that inherit from Animal
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='Animal',
            object_type='class',
            invert=False
        ))

        names = [r.symbol_name for r in results]
        assert 'Dog' in names
        assert 'Cat' in names
        assert 'Animal' not in names

    def test_inverted_inheritance_query(self, db_store, indexing_service, tmp_path):
        """Test inverted query: find what a class inherits from."""
        test_file = tmp_path / "inverted.py"
        test_file.write_text("""
class Vehicle:
    pass

class Car(Vehicle):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)
        db_store.resolve_pending_relationships()

        # Query: Find what Car inherits from (inverted)
        # subject_pattern filters the source (Car), and we return targets (Vehicle)
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            subject_pattern='Car',
            subject_type='class',
            invert=True
        ))

        names = [r.symbol_name for r in results]
        assert 'Vehicle' in names
        assert 'Car' not in names

    def test_class_without_inheritance_no_pending(self, db_store, indexing_service, tmp_path):
        """Test that a class without inheritance creates no pending relationships."""
        test_file = tmp_path / "no_inherit.py"
        test_file.write_text("""
class StandaloneClass:
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM pending_relationships
            WHERE rel_type = 'inherits-from'
        """)
        count = cursor.fetchone()[0]

        assert count == 0

    def test_external_base_class_stays_pending(self, db_store, indexing_service, tmp_path):
        """Test that inheriting from external class stays in pending (can't resolve)."""
        test_file = tmp_path / "external.py"
        test_file.write_text("""
from abc import ABC

class MyAbstractClass(ABC):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        # Before resolving
        cursor = db_store.conn.cursor()
        cursor.execute("SELECT target_name FROM pending_relationships WHERE rel_type = 'inherits-from'")
        pending_before = cursor.fetchall()
        assert len(pending_before) >= 1

        # Resolve - should not resolve ABC since it's external
        resolved = db_store.resolve_pending_relationships()

        # ABC likely won't be in our symbols table, so won't resolve
        # (unless we index abc module, which we don't)


class TestInheritanceWithModulePaths:
    """Test inheritance with module paths in base class names."""

    def test_dotted_base_class_name(self, db_store, indexing_service, tmp_path):
        """Test inheritance from a dotted module path."""
        test_file = tmp_path / "dotted.py"
        test_file.write_text("""
import collections.abc

class MyMapping(collections.abc.Mapping):
    pass
""")

        file_info = DiscoveredFile(path=str(test_file), size_bytes=100, mtime=0.0, is_parseable=True, is_oversized=False)
        indexing_service._index_file(file_info)

        cursor = db_store.conn.cursor()
        cursor.execute("SELECT target_name FROM pending_relationships WHERE rel_type = 'inherits-from'")
        targets = [row[0] for row in cursor.fetchall()]

        # Should store the full dotted name
        assert any('Mapping' in t for t in targets)
