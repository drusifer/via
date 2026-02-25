"""
TDD tests for type filter behavior in relationship queries.

These tests verify that type filters are correctly applied when querying
relationships, especially in cross-type scenarios (e.g., method references global).

Issue: Type filters may incorrectly filter out valid relationship results when
the result type differs from the filter type.

Author: Neo (SWE)
Sprint: 5, Phase 6 (Type Filter Fix)
"""

from argparse import Namespace

import pytest
from via.core.relationship_types import RelationshipType
from via.db.store import DatabaseStore
from via.pipeline.executor import PipelineExecutor
from via.pipeline.relationship_filter import RelationshipFilter
from via.pipeline.types import PipelineStage, StageType


@pytest.fixture
def db_with_cross_type_relationships(tmp_path):
    """Create a database with cross-type relationships for testing.

    Setup:
    - MY_CONSTANT (global)
    - shared_logic (method in BaseClass) - references MY_CONSTANT
    - use_constant (function) - references MY_CONSTANT
    - helper_func (function) - called by main_func
    - main_func (function) - calls helper_func
    """
    db_path = tmp_path / 'test.db'
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()

    # Insert global constant
    constant_id = store.insert_symbol(
        symbol_name='MY_CONSTANT',
        symbol_type='global',
        file_path='/test/constants.py',
        line_number=1,
        byte_offset=0,
        byte_length=20,
        qualified_name='constants.MY_CONSTANT',
        parent_name=None
    )

    # Insert method that references the constant
    method_id = store.insert_symbol(
        symbol_name='shared_logic',
        symbol_type='method',
        file_path='/test/base.py',
        line_number=10,
        byte_offset=100,
        byte_length=50,
        qualified_name='base.BaseClass.shared_logic',
        parent_name='BaseClass'
    )

    # Insert function that references the constant
    func_ref_id = store.insert_symbol(
        symbol_name='use_constant',
        symbol_type='function',
        file_path='/test/utils.py',
        line_number=5,
        byte_offset=50,
        byte_length=30,
        qualified_name='utils.use_constant',
        parent_name=None
    )

    # Insert helper function (for calls relationship)
    helper_id = store.insert_symbol(
        symbol_name='helper_func',
        symbol_type='function',
        file_path='/test/helpers.py',
        line_number=1,
        byte_offset=0,
        byte_length=40,
        qualified_name='helpers.helper_func',
        parent_name=None
    )

    # Insert main function that calls helper
    main_id = store.insert_symbol(
        symbol_name='main_func',
        symbol_type='function',
        file_path='/test/main.py',
        line_number=1,
        byte_offset=0,
        byte_length=100,
        qualified_name='main.main_func',
        parent_name=None
    )

    # Create relationships:
    # shared_logic (method) references MY_CONSTANT (global)
    store.insert_relationship(method_id, constant_id, 'references')
    # use_constant (function) references MY_CONSTANT (global)
    store.insert_relationship(func_ref_id, constant_id, 'references')
    # main_func calls helper_func
    store.insert_relationship(main_id, helper_id, 'calls')

    yield store
    store.close()


class TestTypeFilterInRelationshipQueries:
    """Test that type filters work correctly with relationship queries."""

    def test_reference_query_returns_method_not_global(self, db_with_cross_type_relationships):
        """
        When querying 'what references MY_CONSTANT', should return the method,
        not filter it out because we specified -tg (global type).

        The type filter should apply to the OBJECT (MY_CONSTANT is a global),
        not filter the RESULTS (which are methods/functions).
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        # Query: Find symbols that reference MY_CONSTANT
        # This is similar to: via -mg MY_CONSTANT -tg -Vr -mg *
        args = Namespace(
            pattern='MY_CONSTANT',
            match_syntax='glob',
            symbol_type='global',  # The thing we're relating TO is a global
            symbol_types=['global'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                object_pattern='*',  # Return ALL referencers
                object_match_syntax='glob',
                object_types=None,  # Don't filter result types
                invert=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find shared_logic (method) and use_constant (function)
        names = [r.symbol_name for r in results]
        assert 'shared_logic' in names, f"Expected shared_logic in results, got: {names}"
        assert 'use_constant' in names, f"Expected use_constant in results, got: {names}"
        # Should NOT return MY_CONSTANT itself
        assert 'MY_CONSTANT' not in names

    def test_reference_query_with_result_type_filter(self, db_with_cross_type_relationships):
        """
        When we explicitly filter results by type, it should work.
        Query: Find only METHODS that reference MY_CONSTANT
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        # Query: Find methods that reference MY_CONSTANT
        args = Namespace(
            pattern='MY_CONSTANT',
            match_syntax='glob',
            symbol_type='global',
            symbol_types=['global'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=['method'],  # Only return methods
                invert=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        # Should find shared_logic (method)
        assert 'shared_logic' in names, f"Expected shared_logic in results, got: {names}"
        # Should NOT find use_constant (function) because we filtered to methods
        assert 'use_constant' not in names

    def test_inverted_reference_query_returns_global(self, db_with_cross_type_relationships):
        """
        Inverted query: What does shared_logic reference?
        Should return MY_CONSTANT (a global), even if we filter subject by method.
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        # Query: Find what shared_logic references
        # Similar to: via -mg shared_logic -tm -Vr -mg * --invert
        args = Namespace(
            pattern='shared_logic',
            match_syntax='glob',
            symbol_type='method',  # The subject is a method
            symbol_types=['method'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=None,  # Don't filter result types
                invert=True  # Inverted: what does shared_logic reference?
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        # Should find MY_CONSTANT (the global that shared_logic references)
        assert 'MY_CONSTANT' in names, f"Expected MY_CONSTANT in results, got: {names}"

    def test_calls_query_without_type_filter_on_results(self, db_with_cross_type_relationships):
        """
        Query: Find functions that call helper_func
        Should return main_func without type filtering issues.
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='helper_func',
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
                object_types=None,  # Don't filter - return all callers
                invert=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'main_func' in names, f"Expected main_func in results, got: {names}"


class TestTypeFilterOrdering:
    """Test that type filters are applied at the correct pipeline stage."""

    def test_subject_type_filter_applies_to_relate_to_target(self, db_with_cross_type_relationships):
        """
        The type filter BEFORE --via should filter the 'relate to' target.
        Query: -mg MY_CONSTANT -tg -Vr -mg *
        The -tg should ensure MY_CONSTANT is a global (it is).
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='MY_CONSTANT',
            match_syntax='glob',
            symbol_type='global',
            symbol_types=['global'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=None,
                invert=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find referencers because MY_CONSTANT IS a global
        assert len(results) > 0, "Should find referencers of MY_CONSTANT"

    def test_wrong_subject_type_filter_returns_empty(self, db_with_cross_type_relationships):
        """
        If the subject type filter doesn't match, query should return empty.
        Query: -mg MY_CONSTANT -tc (class) -Vr -mg *
        MY_CONSTANT is a global, not a class, so no matches.
        """
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='MY_CONSTANT',
            match_syntax='glob',
            symbol_type='class',  # Wrong type - MY_CONSTANT is a global
            symbol_types=['class'],
            case_insensitive=False,
            limit=10,
            match_qualified=False,
            render_type=None,
            format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                object_pattern='*',
                object_match_syntax='glob',
                object_types=None,
                invert=False
            )
        )
        stage = PipelineStage(StageType.MATCH, args)

        results = list(executor.execute([stage]))

        # Should find NO results because MY_CONSTANT is not a class
        assert len(results) == 0, f"Should find no results, got: {[r.symbol_name for r in results]}"
