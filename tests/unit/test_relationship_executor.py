"""Unit tests for PipelineExecutor relationship query execution (Sprint 5).

TLDR:
    Tests that PipelineExecutor correctly dispatches relationship-filtered queries
    against a real DatabaseStore. Key fixtures: db_with_relationships (in-memory DB
    seeded with inherits-from and calls relationships). Key test classes:
    TestExecutorRelationshipQueries (forward/inverted inherits-from and calls,
    glob object patterns, subject-side filtering), TestExecutorRelationshipLimit
    (limit enforcement on relationship results), TestExecutorNoRelationship (plain
    match queries still work without a relationship stage).
    Role: protects the executor's relationship dispatch path; depends on
    PipelineExecutor, RelationshipFilter, DatabaseStore, PipelineStage, StageType.

"""
import os
import tempfile
from argparse import Namespace

import pytest
from via.core.relationship_types import RelationshipType
from via.db.store import DatabaseStore
from via.pipeline.executor import PipelineExecutor
from via.pipeline.relationship_filter import RelationshipFilter
from via.pipeline.types import PipelineStage, StageType


@pytest.fixture
def db_with_relationships(tmp_path):
    """Create a database with symbols and relationships for testing."""
    db_path = tmp_path / 'test.db'
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()

    # Create test symbols:
    # - BaseClass (class)
    # - ChildA (class, inherits from BaseClass)
    # - ChildB (class, inherits from BaseClass)
    # - helper_func (function)
    # - main_func (function, calls helper_func)

    # Insert class symbols
    base_id = store.insert_symbol(
        symbol_name='BaseClass',
        symbol_type='class',
        file_path='/test/base.py',
        line_number=1,
        byte_offset=0,
        byte_length=100,
        qualified_name='base.BaseClass',
        parent_name=None
    )

    child_a_id = store.insert_symbol(
        symbol_name='ChildA',
        symbol_type='class',
        file_path='/test/child_a.py',
        line_number=1,
        byte_offset=0,
        byte_length=100,
        qualified_name='child_a.ChildA',
        parent_name=None
    )

    child_b_id = store.insert_symbol(
        symbol_name='ChildB',
        symbol_type='class',
        file_path='/test/child_b.py',
        line_number=1,
        byte_offset=0,
        byte_length=100,
        qualified_name='child_b.ChildB',
        parent_name=None
    )

    # Insert function symbols
    helper_id = store.insert_symbol(
        symbol_name='helper_func',
        symbol_type='function',
        file_path='/test/utils.py',
        line_number=10,
        byte_offset=0,
        byte_length=50,
        qualified_name='utils.helper_func',
        parent_name=None
    )

    main_id = store.insert_symbol(
        symbol_name='main_func',
        symbol_type='function',
        file_path='/test/main.py',
        line_number=1,
        byte_offset=0,
        byte_length=200,
        qualified_name='main.main_func',
        parent_name=None
    )

    # Insert relationships
    # ChildA inherits from BaseClass
    store.insert_relationship(child_a_id, base_id, 'inherits-from')
    # ChildB inherits from BaseClass
    store.insert_relationship(child_b_id, base_id, 'inherits-from')
    # main_func calls helper_func
    store.insert_relationship(main_id, helper_id, 'calls')

    yield store
    store.close()


class TestExecutorRelationshipQueries:
    """Test executor handling of relationship queries."""

    def test_execute_inherits_from_query(self, db_with_relationships):
        """Test finding classes that inherit from a base class."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find classes that inherit from BaseClass
        # Pattern BEFORE --via = what you relate TO (BaseClass)
        # Pattern AFTER --via = filter results (all children)
        args = Namespace(
            pattern='BaseClass',  # Relate TO BaseClass
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='*',  # Return ALL children
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find ChildA and ChildB (they inherit from BaseClass)
        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names
        assert 'BaseClass' not in names

    def test_execute_inherits_from_inverted(self, db_with_relationships):
        """Test --sans inherits-from: find classes with no parent (NOT EXISTS)."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find classes with NO inherits-from relationship (--sans semantics)
        # BaseClass has no parent → should appear
        # ChildA, ChildB have parents → should NOT appear
        args = Namespace(
            pattern='*',  # All classes
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=True  # NOT EXISTS: no inherits-from relationship
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # BaseClass has no parent → returned
        # ChildA, ChildB have parents → not returned
        names = [r.symbol_name for r in results]
        assert 'BaseClass' in names
        assert 'ChildA' not in names
        assert 'ChildB' not in names

    def test_execute_calls_query(self, db_with_relationships):
        """Test finding functions that call another function."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find functions that call helper_func
        # Pattern BEFORE --via = what you relate TO (helper_func - the called function)
        args = Namespace(
            pattern='helper_func',  # Relate TO helper_func
            match_syntax='glob',
            symbol_type='function',
            symbol_types=['function'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                object_pattern='*',  # Return ALL callers
                object_match_syntax='glob',
                object_types=['function'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find main_func (it calls helper_func)
        names = [r.symbol_name for r in results]
        assert 'main_func' in names
        assert 'helper_func' not in names

    def test_execute_calls_inverted(self, db_with_relationships):
        """Test --sans calls: find functions that call nothing (NOT EXISTS)."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find functions with NO calls relationship (--sans semantics)
        # helper_func calls nothing → should appear
        # main_func calls helper_func → should NOT appear
        args = Namespace(
            pattern='*',  # All functions
            match_syntax='glob',
            symbol_type='function',
            symbol_types=['function'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=['function'],
                is_negative=True  # NOT EXISTS: no calls relationship
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # helper_func has no calls → returned
        # main_func calls helper_func → not returned
        names = [r.symbol_name for r in results]
        assert 'helper_func' in names
        assert 'main_func' not in names

    def test_execute_relationship_with_glob_pattern(self, db_with_relationships):
        """Test relationship query with glob pattern on what we relate TO."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find classes that inherit from *Base*
        # Pattern BEFORE --via = relate TO classes matching *Base*
        args = Namespace(
            pattern='*Base*',  # Relate TO parents matching *Base*
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='*',  # Return ALL children
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find ChildA and ChildB
        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names

    def test_execute_relationship_with_subject_filter(self, db_with_relationships):
        """Test relationship query with filter on results."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find Child* classes that inherit from BaseClass
        # Pattern BEFORE --via = relate TO (BaseClass)
        # Pattern AFTER --via = filter results (Child*)
        args = Namespace(
            pattern='BaseClass',  # Relate TO BaseClass
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='Child*',  # Filter results to Child*
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find ChildA and ChildB
        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names
        assert len(names) == 2

    def test_execute_relationship_no_matches(self, db_with_relationships):
        """Test relationship query with no matching results."""
        executor = PipelineExecutor(db_with_relationships)

        # Query: Find classes that inherit from NonExistent
        args = Namespace(
            pattern='NonExistent',  # Relate TO NonExistent (doesn't exist)
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find no results
        assert len(results) == 0


class TestExecutorRelationshipLimit:
    """Test limit handling in relationship queries."""

    def test_relationship_query_respects_limit(self, db_with_relationships):
        """Test that relationship queries respect the limit parameter."""
        executor = PipelineExecutor(db_with_relationships)

        # Query with limit of 1
        args = Namespace(
            pattern='BaseClass',  # Relate TO BaseClass
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=1,  # Only return 1 result
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                object_pattern='*',  # Return all children
                object_match_syntax='glob',
                object_types=['class'],
                is_negative=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should only return 1 result even though 2 children exist
        assert len(results) == 1


class TestExecutorNoRelationship:
    """Test executor with non-relationship queries still works."""

    def test_execute_simple_match_still_works(self, db_with_relationships):
        """Test that simple match queries without relationships still work."""
        executor = PipelineExecutor(db_with_relationships)

        # Simple match query without relationship
        args = Namespace(
            pattern='*',
            match_syntax='glob',
            symbol_type='class',
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=None  # No relationship filter
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find all classes
        names = [r.symbol_name for r in results]
        assert 'BaseClass' in names
        assert 'ChildA' in names
        assert 'ChildB' in names
