"""Unit tests for PipelineExecutor relationship query execution.

Tests result-first query semantics where the first stage determines returned
results and --via/--sans stages act as filters. Includes forward and inverse
relationship types.
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

    base_id = store.insert_symbol(
        symbol_name='BaseClass', symbol_type='class',
        file_path='/test/base.py', line_number=1,
        byte_offset=0, byte_length=100,
        qualified_name='base.BaseClass', parent_name=None)

    child_a_id = store.insert_symbol(
        symbol_name='ChildA', symbol_type='class',
        file_path='/test/child_a.py', line_number=1,
        byte_offset=0, byte_length=100,
        qualified_name='child_a.ChildA', parent_name=None)

    child_b_id = store.insert_symbol(
        symbol_name='ChildB', symbol_type='class',
        file_path='/test/child_b.py', line_number=1,
        byte_offset=0, byte_length=100,
        qualified_name='child_b.ChildB', parent_name=None)

    helper_id = store.insert_symbol(
        symbol_name='helper_func', symbol_type='function',
        file_path='/test/utils.py', line_number=10,
        byte_offset=0, byte_length=50,
        qualified_name='utils.helper_func', parent_name=None)

    main_id = store.insert_symbol(
        symbol_name='main_func', symbol_type='function',
        file_path='/test/main.py', line_number=1,
        byte_offset=0, byte_length=200,
        qualified_name='main.main_func', parent_name=None)

    # ChildA inherits from BaseClass
    store.insert_relationship(child_a_id, base_id, 'inherits-from')
    # ChildB inherits from BaseClass
    store.insert_relationship(child_b_id, base_id, 'inherits-from')
    # main_func calls helper_func
    store.insert_relationship(main_id, helper_id, 'calls')

    yield store
    store.close()


class TestExecutorRelationshipQueries:
    """Test executor with result-first relationship queries."""

    def test_via_inherits_from_returns_children(self, db_with_relationships):
        """via -mg '*' -tc --via inherits-from -mg 'BaseClass' -tc → ChildA, ChildB."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*',  # RESULT: return all classes
            match_syntax='glob', symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='BaseClass',  # FILTER: that inherit from BaseClass
                filter_match_syntax='glob', filter_types=['class'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names
        assert 'BaseClass' not in names

    def test_via_inherited_by_returns_parents(self, db_with_relationships):
        """via -mg '*' -tc --via inherited-by -mg 'ChildA' -tc → BaseClass."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*',  # RESULT: return all classes
            match_syntax='glob', symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='ChildA',  # FILTER: what ChildA inherits from
                filter_match_syntax='glob', filter_types=['class'],
                is_negative=False, inverted=True,  # Inverse: return target (parent) side
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'BaseClass' in names
        assert 'ChildA' not in names

    def test_sans_inherits_from_returns_root_classes(self, db_with_relationships):
        """via -mg '*' -tc --sans inherits-from -mg '*' -tc → BaseClass (no parent)."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='*', filter_match_syntax='glob',
                filter_types=['class'],
                is_negative=True, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'BaseClass' in names
        assert 'ChildA' not in names
        assert 'ChildB' not in names

    def test_via_calls_returns_callers(self, db_with_relationships):
        """via -mg '*' -tf --via calls -mg 'helper_func' -tf → main_func."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*',  # RESULT: all functions
            match_syntax='glob', symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                filter_pattern='helper_func',  # FILTER: that call helper_func
                filter_match_syntax='glob', filter_types=['function'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'main_func' in names
        assert 'helper_func' not in names

    def test_via_called_by_returns_callees(self, db_with_relationships):
        """via -mg '*' -tf --via called-by -mg 'main_func' -tf → helper_func."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*',  # RESULT: all functions
            match_syntax='glob', symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                filter_pattern='main_func',  # FILTER: called by main_func
                filter_match_syntax='glob', filter_types=['function'],
                is_negative=False, inverted=True,  # Inverse: return callee (to) side
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'helper_func' in names
        assert 'main_func' not in names

    def test_sans_calls_returns_functions_that_call_nothing(self, db_with_relationships):
        """via -mg '*' -tf --sans calls -mg '*' -tf → helper_func (calls nothing)."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                filter_pattern='*', filter_match_syntax='glob',
                filter_types=['function'],
                is_negative=True, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'helper_func' in names
        assert 'main_func' not in names

    def test_sans_called_by_returns_unused_functions(self, db_with_relationships):
        """via -mg '*' -tf --sans called-by -mg '*' -tf → functions nobody calls."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='function', symbol_types=['function'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.CALLS,
                filter_pattern='*', filter_match_syntax='glob',
                filter_types=['function'],
                is_negative=True, inverted=True,  # Inverse --sans: nobody calls me
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        # main_func is never called by anything → should appear
        assert 'main_func' in names
        # helper_func IS called by main_func → should NOT appear
        assert 'helper_func' not in names

    def test_via_inherits_from_with_glob_filter(self, db_with_relationships):
        """Glob pattern on filter side narrows the anchor."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='*Base*',  # FILTER: parents matching *Base*
                filter_match_syntax='glob', filter_types=['class'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names

    def test_via_inherits_from_with_result_pattern_filter(self, db_with_relationships):
        """Result pattern narrows what gets returned."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='Child*',  # RESULT: only Child* classes
            match_syntax='glob', symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='BaseClass', filter_match_syntax='glob',
                filter_types=['class'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'ChildA' in names
        assert 'ChildB' in names
        assert len(names) == 2

    def test_no_matches_returns_empty(self, db_with_relationships):
        """Filter for non-existent anchor returns empty."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='NonExistent', filter_match_syntax='glob',
                filter_types=['class'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        assert len(results) == 0


class TestExecutorRelationshipLimit:
    """Test limit handling in relationship queries."""

    def test_relationship_query_respects_limit(self, db_with_relationships):
        """Limit applies to result set."""
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=1, match_qualified=False,
            render_type=None, format=None,
            relationship=RelationshipFilter(
                relationship_type=RelationshipType.INHERITS_FROM,
                filter_pattern='BaseClass', filter_match_syntax='glob',
                filter_types=['class'],
                is_negative=False, inverted=False,
            ))
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        assert len(results) == 1


class TestExecutorNoRelationship:
    """Test executor with non-relationship queries still works."""

    def test_execute_simple_match_still_works(self, db_with_relationships):
        executor = PipelineExecutor(db_with_relationships)

        args = Namespace(
            pattern='*', match_syntax='glob',
            symbol_type='class', symbol_types=['class'],
            case_insensitive=False, limit=10, match_qualified=False,
            render_type=None, format=None,
            relationship=None)
        stage = PipelineStage(StageType.MATCH, args)
        results = list(executor.execute([stage]))

        names = [r.symbol_name for r in results]
        assert 'BaseClass' in names
        assert 'ChildA' in names
        assert 'ChildB' in names
