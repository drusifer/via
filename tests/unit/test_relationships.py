"""Unit tests for symbol relationship indexing and querying (Sprint 5).

TLDR:
    Tests that DatabaseStore correctly stores and queries symbol relationships.
    Key test classes: TestRelationshipTypeEnum (validates RelationshipType enum
    values: inherits-from, calls, imports, references), TestDatabaseStoreRelationships
    (store/query inherits-from, calls, imports, references via add_relationship and
    get_relationships; covers forward, inverted, type-filtered, and multi-symbol
    queries), TestPendingRelationships (deferred relationship resolution when
    referenced symbols are not yet indexed).
    Role: foundational test coverage for DatabaseStore relationship storage; depends
    on DatabaseStore and RelationshipType.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
import tempfile

import pytest
from via.core.relationship_types import RelationshipType
from via.db.store import DatabaseStore


class TestRelationshipTypeEnum:
    """Tests for RelationshipType enum."""

    def test_inherits_from_value(self):
        """Test INHERITS_FROM enum value."""
        assert RelationshipType.INHERITS_FROM.value == 'inherits-from'

    def test_calls_value(self):
        """Test CALLS enum value."""
        assert RelationshipType.CALLS.value == 'calls'

    def test_imports_value(self):
        """Test IMPORTS enum value."""
        assert RelationshipType.IMPORTS.value == 'imports'

    def test_references_value(self):
        """Test REFERENCES enum value."""
        assert RelationshipType.REFERENCES.value == 'references'

    def test_relationship_count(self):
        """Test that we have exactly 5 relationship types (including DECLARES)."""
        assert len(RelationshipType) == 5


class TestDatabaseStoreRelationships:
    """Tests for DatabaseStore relationship methods."""

    @pytest.fixture
    def db_store(self, tmp_path):
        """Create a temporary database store."""
        db_path = tmp_path / "test.db"
        store = DatabaseStore(str(db_path), str(tmp_path))
        store.connect()
        store.initialize_schema()
        yield store
        store.close()

    @pytest.fixture
    def populated_db(self, db_store):
        """Create a database with some symbols for relationship testing."""
        # Insert some test symbols
        cursor = db_store.conn.cursor()

        # Base class
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('BaseClass', 'class', 'base.py', 1, 'base.BaseClass')
        """)
        base_id = cursor.lastrowid

        # Child class
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('ChildClass', 'class', 'child.py', 1, 'child.ChildClass')
        """)
        child_id = cursor.lastrowid

        # Function
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('helper', 'function', 'utils.py', 10, 'utils.helper')
        """)
        helper_id = cursor.lastrowid

        # Another function that calls helper
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('main', 'function', 'main.py', 1, 'main.main')
        """)
        main_id = cursor.lastrowid

        return db_store, {
            'base_id': base_id,
            'child_id': child_id,
            'helper_id': helper_id,
            'main_id': main_id,
        }

    def test_insert_relationship(self, populated_db):
        """Test inserting a relationship."""
        db_store, ids = populated_db

        # Insert inheritance relationship: ChildClass inherits from BaseClass
        rel_id = db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        assert rel_id is not None
        assert rel_id > 0

    def test_insert_relationship_stores_correctly(self, populated_db):
        """Test that inserted relationship is stored correctly."""
        db_store, ids = populated_db

        db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        # Verify it was stored
        cursor = db_store.conn.cursor()
        cursor.execute("""
            SELECT from_symbol_id, to_symbol_id, reference_type
            FROM symbol_references
            WHERE from_symbol_id = ? AND to_symbol_id = ?
        """, (ids['child_id'], ids['base_id']))
        row = cursor.fetchone()

        assert row is not None
        assert row['from_symbol_id'] == ids['child_id']
        assert row['to_symbol_id'] == ids['base_id']
        assert row['reference_type'] == 'inherits-from'

    def test_query_relationships_finds_inheritance(self, populated_db):
        """Test querying inheritance relationships."""
        db_store, ids = populated_db

        # Insert inheritance relationship
        db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        # Query: Find classes that inherit from BaseClass
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='BaseClass'
        ))

        assert len(results) == 1
        assert results[0].symbol_name == 'ChildClass'

    def test_query_relationships_inverted(self, populated_db):
        """Test inverted relationship query (find parents)."""
        db_store, ids = populated_db

        # Insert inheritance relationship
        db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        # Query inverted: Find what ChildClass inherits from
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            subject_pattern='ChildClass',
            invert=True
        ))

        assert len(results) == 1
        assert results[0].symbol_name == 'BaseClass'

    def test_query_relationships_with_glob_pattern(self, populated_db):
        """Test relationship query with glob pattern."""
        db_store, ids = populated_db

        db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        # Query with glob pattern
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='*Class'
        ))

        assert len(results) == 1

    def test_query_relationships_call(self, populated_db):
        """Test querying call relationships."""
        db_store, ids = populated_db

        # main calls helper
        db_store.insert_relationship(
            source_id=ids['main_id'],
            target_id=ids['helper_id'],
            rel_type='calls'
        )

        # Find what calls helper
        results = list(db_store.query_relationships(
            relationship_type='calls',
            object_pattern='helper'
        ))

        assert len(results) == 1
        assert results[0].symbol_name == 'main'

    def test_query_relationships_returns_match_records(self, populated_db):
        """Test that query_relationships returns MatchRecord objects."""
        db_store, ids = populated_db

        db_store.insert_relationship(
            source_id=ids['child_id'],
            target_id=ids['base_id'],
            rel_type='inherits-from'
        )

        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='BaseClass'
        ))

        assert len(results) == 1
        result = results[0]

        # Should be a MatchRecord with proper attributes
        assert hasattr(result, 'symbol_name')
        assert hasattr(result, 'symbol_type')
        assert hasattr(result, 'file_path')
        assert hasattr(result, 'line_number')

    def test_query_relationships_no_results(self, db_store):
        """Test query with no matching relationships."""
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='NonExistent'
        ))

        assert len(results) == 0

    def test_query_relationships_with_limit(self, populated_db):
        """Test relationship query respects limit."""
        db_store, ids = populated_db

        # Add multiple inheritance relationships
        cursor = db_store.conn.cursor()
        for i in range(5):
            cursor.execute("""
                INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
                VALUES (?, 'class', 'test.py', ?, ?)
            """, (f'Child{i}', i+1, f'test.Child{i}'))
            child_id = cursor.lastrowid
            db_store.insert_relationship(child_id, ids['base_id'], 'inherits-from')

        # Query with limit
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='BaseClass',
            limit=3
        ))

        assert len(results) == 3


class TestPendingRelationships:
    """Tests for pending relationship resolution (two-pass indexing)."""

    @pytest.fixture
    def db_store(self, tmp_path):
        """Create a temporary database store."""
        db_path = tmp_path / "test.db"
        store = DatabaseStore(str(db_path), str(tmp_path))
        store.connect()
        store.initialize_schema()
        yield store
        store.close()

    def test_insert_pending_relationship(self, db_store):
        """Test inserting a pending (unresolved) relationship."""
        # First insert a source symbol
        cursor = db_store.conn.cursor()
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('ChildClass', 'class', 'child.py', 1, 'child.ChildClass')
        """)
        source_id = cursor.lastrowid

        # Insert pending relationship (target not yet indexed)
        pending_id = db_store.insert_pending_relationship(
            source_id=source_id,
            target_name='BaseClass',
            rel_type='inherits-from'
        )

        assert pending_id is not None

    def test_resolve_pending_relationships(self, db_store):
        """Test resolving pending relationships after all symbols indexed."""
        cursor = db_store.conn.cursor()

        # Insert child class first
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('ChildClass', 'class', 'child.py', 1, 'child.ChildClass')
        """)
        child_id = cursor.lastrowid

        # Insert pending relationship before base class exists
        db_store.insert_pending_relationship(child_id, 'BaseClass', 'inherits-from')

        # Now insert base class
        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('BaseClass', 'class', 'base.py', 1, 'base.BaseClass')
        """)

        # Resolve pending relationships
        db_store.resolve_pending_relationships()

        # Should now be able to query the relationship
        results = list(db_store.query_relationships(
            relationship_type='inherits-from',
            object_pattern='BaseClass'
        ))

        assert len(results) == 1
        assert results[0].symbol_name == 'ChildClass'

    def test_unresolvable_pending_cleaned_up(self, db_store):
        """Test that unresolvable pending relationships are cleaned up."""
        cursor = db_store.conn.cursor()

        cursor.execute("""
            INSERT INTO symbols (symbol_name, symbol_type, file_path, line_number, qualified_name)
            VALUES ('OrphanClass', 'class', 'orphan.py', 1, 'orphan.OrphanClass')
        """)
        orphan_id = cursor.lastrowid

        # Insert pending relationship to non-existent class
        db_store.insert_pending_relationship(orphan_id, 'DoesNotExist', 'inherits-from')

        # Resolve - should not crash, should clean up
        db_store.resolve_pending_relationships()

        # Check pending table is empty
        cursor.execute("SELECT COUNT(*) FROM pending_relationships")
        count = cursor.fetchone()[0]
        assert count == 0
