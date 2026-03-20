"""Unit tests for pipeline executor (Task 1.2).

TLDR:
    Tests the PipelineExecutor class that runs ordered pipeline stages against the
    symbol database. Covers single-stage match queries, chained match stages used as
    filters, render stage output, type-based filtering, and zero-copy iterator passing
    between stages.
    Role: protects the core pipeline execution engine that drives all via query commands.

"""
from argparse import Namespace
from unittest.mock import MagicMock, Mock

import pytest
from via.core.match_record import ClassMatchRecord, FunctionMatchRecord, MethodMatchRecord
from via.core.types import MatchOp, SymbolType
from via.pipeline.executor import PipelineExecutor
from via.pipeline.types import PipelineStage, StageType


class TestExecuteSingleMatchStage:
    """Test executing a single match stage."""

    def test_executes_match_against_database(self):
        """Single match stage queries database."""
        # Setup
        db = Mock()
        db.match = Mock(return_value=iter([
            ClassMatchRecord('class', 'User', 'models.User', 'models.py', 10, 100, 50, None)
        ]))

        executor = PipelineExecutor(db)

        # Create match stage
        stage = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='User*',
                case_insensitive=False,
                limit=10
            )
        )

        # Execute
        result = list(executor.execute([stage]))

        # Verify
        assert len(result) == 1
        assert result[0].symbol_name == 'User'
        db.match.assert_called_once()

    def test_extract_match_op_from_glob_flag(self):
        """Executor determines MatchOp.GLOB from parsed args."""
        db = Mock()
        db.match = Mock(return_value=iter([]))

        executor = PipelineExecutor(db)

        # When -g flag is used, pattern is set by argparse
        stage = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='function',
                pattern='calc*',
                case_insensitive=False,
                limit=10
            )
        )

        list(executor.execute([stage]))

        # Should call with GLOB match op
        call_args = db.match.call_args
        assert call_args[0][0] == SymbolType.FUNCTION
        assert call_args[0][1] == MatchOp.GLOB
        assert call_args[0][2] == 'calc*'


class TestExecuteChainedMatchStages:
    """Test executing chained match stages (filter)."""

    def test_second_match_filters_first_results(self):
        """Second match stage filters previous results."""
        db = Mock()

        # First stage returns classes
        first_results = [
            ClassMatchRecord('class', 'UserModel', 'models.UserModel', 'models.py', 10, 100, 50, None),
            ClassMatchRecord('class', 'User', 'core.User', 'core.py', 20, 200, 60, None),
        ]
        db.match = Mock(return_value=iter(first_results))

        executor = PipelineExecutor(db)

        # Stage 1: Match classes
        stage1 = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='User*',
                case_insensitive=False,
                limit=10
            )
        )

        # Stage 2: Filter for 'UserModel' only
        stage2 = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='*Model',
                case_insensitive=False,
                limit=10
            )
        )

        # Execute pipeline
        result = list(executor.execute([stage1, stage2]))

        # Should only return UserModel (filtered by second stage)
        assert len(result) == 1
        assert result[0].symbol_name == 'UserModel'


class TestExecuteRenderStage:
    """Test executing render stage."""

    def test_render_stage_consumes_iterator(self, capsys):
        """Render stage consumes iterator and outputs."""
        db = Mock()
        matches = [
            ClassMatchRecord(
                symbol_type='class',
                symbol_name='User',
                qualified_name='models.User',
                file_path='models.py',
                line_number=10,
                byte_offset=100,
                byte_length=50,
                total_matches=1,
            )
        ]
        db.match = Mock(return_value=iter(matches))

        executor = PipelineExecutor(db)

        # Match stage
        match_stage = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='User',
                case_insensitive=False,
                limit=10
            )
        )

        # Render stage (list renderer - just prints __str__)
        render_stage = PipelineStage(
            StageType.RENDER,
            Namespace(
                render_type='list',
                format=None,
                after_context=0,
                before_context=0,
                context=None,
                theme=None
            )
        )

        # Execute
        executor.execute([match_stage, render_stage])

        # Check output
        captured = capsys.readouterr()
        assert 'class:models.py:10:models.User:@100+50' in captured.out


class TestExecuteDefaultOutput:
    """Test default output when no render stage."""

    def test_no_render_stage_returns_iterator(self):
        """Pipeline without render stage returns iterator for caller to handle."""
        db = Mock()
        matches = [
            FunctionMatchRecord('function', 'calc', 'utils.calc', 'utils.py', 15, 150, 30, None)
        ]
        db.match = Mock(return_value=iter(matches))

        executor = PipelineExecutor(db)

        stage = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='function',
                pattern='calc',
                case_insensitive=False,
                limit=10
            )
        )

        # Execute without render stage
        result = list(executor.execute([stage]))

        # Should return results
        assert len(result) == 1
        assert result[0].symbol_name == 'calc'


class TestFilterByTypeAndPattern:
    """Test filtering logic."""

    def test_filters_by_symbol_type(self):
        """Filter stage only passes matching types."""
        db = Mock()

        # Mix of classes and methods
        first_results = [
            ClassMatchRecord('class', 'User', 'models.User', 'models.py', 10, 100, 50, None),
            MethodMatchRecord('method', 'save', 'models.User.save', 'models.py', 20, 200, 30, 'models.User'),
            ClassMatchRecord('class', 'UserModel', 'models.UserModel', 'models.py', 40, 400, 60, None),
        ]
        db.match = Mock(return_value=iter(first_results))

        executor = PipelineExecutor(db)

        # Stage 1: Match all
        stage1 = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='*',
                case_insensitive=False,
                limit=10
            )
        )

        # Stage 2: Filter for methods only
        stage2 = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='method',
                pattern='*',
                case_insensitive=False,
                limit=10
            )
        )

        result = list(executor.execute([stage1, stage2]))

        # Should only return the method
        assert len(result) == 1
        assert result[0].symbol_type == 'method'
        assert result[0].symbol_name == 'save'


class TestIteratorPassing:
    """Test that iterators are passed correctly between stages."""

    def test_zero_copy_iterator_passing(self):
        """Iterators passed between stages without materializing."""
        db = Mock()

        # Use a generator that tracks if it was converted to list
        materialized = {'count': 0}

        def tracking_generator():
            yield ClassMatchRecord('class', 'User', 'User', 'models.py', 10, 100, 50, None)
            materialized['count'] += 1

        db.match = Mock(return_value=tracking_generator())

        executor = PipelineExecutor(db)

        stage = PipelineStage(
            StageType.MATCH,
            Namespace(
                symbol_type='class',
                pattern='User',
                case_insensitive=False,
                limit=10
            )
        )

        # Execute and consume exactly once
        result = list(executor.execute([stage]))

        assert len(result) == 1
        # Generator should only be consumed once
        assert materialized['count'] == 1
