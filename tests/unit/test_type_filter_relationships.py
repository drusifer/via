"""Unit tests for type-filter correctness in relationship queries.

Result-first semantics: result stage types filter what gets returned,
filter stage types narrow the relationship anchor.
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

    constant_id = store.insert_symbol(
        symbol_name='MY_CONSTANT', symbol_type='global',
        file_path='/test/constants.py', line_number=1,
        byte_offset=0, byte_length=20,
        qualified_name='constants.MY_CONSTANT', parent_name=None)

    method_id = store.insert_symbol(
        symbol_name='shared_logic', symbol_type='method',
        file_path='/test/base.py', line_number=10,
        byte_offset=100, byte_length=50,
        qualified_name='base.BaseClass.shared_logic', parent_name='BaseClass')

    func_ref_id = store.insert_symbol(
        symbol_name='use_constant', symbol_type='function',
        file_path='/test/utils.py', line_number=5,
        byte_offset=50, byte_length=30,
        qualified_name='utils.use_constant', parent_name=None)

    helper_id = store.insert_symbol(
        symbol_name='helper_func', symbol_type='function',
        file_path='/test/helpers.py', line_number=1,
        byte_offset=0, byte_length=40,
        qualified_name='helpers.helper_func', parent_name=None)

    main_id = store.insert_symbol(
        symbol_name='main_func', symbol_type='function',
        file_path='/test/main.py', line_number=1,
        byte_offset=0, byte_length=100,
        qualified_name='main.main_func', parent_name=None)

    other_caller_id = store.insert_symbol(
        symbol_name='other_caller', symbol_type='function',
        file_path='/test/other.py', line_number=1,
        byte_offset=0, byte_length=100,
        qualified_name='other.other_caller', parent_name=None)

    # shared_logic (method) references MY_CONSTANT (global)
    store.insert_relationship(method_id, constant_id, 'references')
    # use_constant (function) references MY_CONSTANT (global)
    store.insert_relationship(func_ref_id, constant_id, 'references')
    # main_func calls helper_func
    store.insert_relationship(main_id, helper_id, 'calls')
    # main_func also references MY_CONSTANT; other_caller only calls helper_func
    store.insert_relationship(main_id, constant_id, 'references')
    store.insert_relationship(other_caller_id, helper_id, 'calls')

    yield store
    store.close()


class TestTypeFilterInRelationshipQueries:
    """Test that type filters work correctly with result-first semantics."""

    def test_via_references_returns_referencers(self, db_with_cross_type_relationships):
        """via -mg '*' --via references -mg 'MY_CONSTANT' -tg → shared_logic, use_constant."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='*',  # RESULT: all symbols
            match_syntax='glob', symbol_type=None, symbol_types=[],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                filter_pattern='MY_CONSTANT',  # FILTER: things that reference MY_CONSTANT
                filter_match_syntax='glob', filter_types=['global'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'shared_logic' in names
        assert 'use_constant' in names
        assert 'MY_CONSTANT' not in names

    def test_result_type_filter_narrows_returned_symbols(self, db_with_cross_type_relationships):
        """via -mg '*' -tm --via references -mg 'MY_CONSTANT' -tg → only methods."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='*',
            match_syntax='glob', symbol_type='method', symbol_types=['method'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                filter_pattern='MY_CONSTANT',
                filter_match_syntax='glob', filter_types=['global'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'shared_logic' in names
        assert 'use_constant' not in names

    def test_filter_type_narrows_anchor(self, db_with_cross_type_relationships):
        """Filter type must match the anchor symbol type."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        # MY_CONSTANT is a global, but we specify -tc (class) on filter → no match
        args = Namespace(
            pattern='*',
            match_syntax='glob', symbol_type=None, symbol_types=[],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.REFERENCES,
                filter_pattern='MY_CONSTANT',
                filter_match_syntax='glob', filter_types=['class'],  # Wrong type
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        assert len(results) == 0

    def test_calls_without_type_filter(self, db_with_cross_type_relationships):
        """via -mg '*' --via calls -mg 'helper_func' → main_func."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='*',
            match_syntax='glob', symbol_type=None, symbol_types=[],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                filter_pattern='helper_func',
                filter_match_syntax='glob', filter_types=[],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'main_func' in names

    def test_multiple_positive_relationship_filters_are_applied_sequentially(
        self, db_with_cross_type_relationships
    ):
        """calls helper_func + references MY_CONSTANT returns only main_func."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='*',
            match_syntax='glob', symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=None,
            relationships=[
                RelationshipFilter(
                    relationship_type=RelationshipType.CALLS,
                    filter_pattern='helper_func',
                    filter_match_syntax='glob', filter_types=['function'],
                    is_negative=False, inverted=False,
                ),
                RelationshipFilter(
                    relationship_type=RelationshipType.REFERENCES,
                    filter_pattern='MY_CONSTANT',
                    filter_match_syntax='glob', filter_types=['global'],
                    is_negative=False, inverted=False,
                ),
            ])
        args.relationship = args.relationships[0]
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        assert [r.symbol_name for r in results] == ['main_func']

    def test_later_negative_relationship_filter_excludes_existing_results(
        self, db_with_cross_type_relationships
    ):
        """calls helper_func + sans references MY_CONSTANT excludes main_func."""
        executor = PipelineExecutor(db_with_cross_type_relationships)

        args = Namespace(
            pattern='*',
            match_syntax='glob', symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=None,
            relationships=[
                RelationshipFilter(
                    relationship_type=RelationshipType.CALLS,
                    filter_pattern='helper_func',
                    filter_match_syntax='glob', filter_types=['function'],
                    is_negative=False, inverted=False,
                ),
                RelationshipFilter(
                    relationship_type=RelationshipType.REFERENCES,
                    filter_pattern='MY_CONSTANT',
                    filter_match_syntax='glob', filter_types=['global'],
                    is_negative=True, inverted=False,
                ),
            ])
        args.relationship = args.relationships[0]
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        assert [r.symbol_name for r in results] == ['other_caller']
