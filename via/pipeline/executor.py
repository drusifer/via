"""Pipeline executor for running pipeline stages."""
from typing import Iterator, Optional, List
from via.pipeline.types import PipelineStage, StageType
from via.core.types import MatchResult, SymbolType, MatchOp
from via.core.match_record import RenderType, FormatType
from via.db.store import DatabaseStore
from via.renderers.factory import RendererFactory
import fnmatch
import re


class PipelineExecutor:
    """Execute pipeline stages sequentially.

    Stages are executed in order, passing Iterator[MatchResult] between stages
    for zero-copy streaming.
    """

    def __init__(self, db_store: DatabaseStore):
        """Initialize executor with database store.

        Args:
            db_store: DatabaseStore instance for querying symbols
        """
        self.db = db_store

    def execute(self, stages: List[PipelineStage]) -> Optional[Iterator[MatchResult]]:
        """Execute all stages, return final iterator or None if terminal stage.

        Args:
            stages: List of PipelineStage objects to execute

        Returns:
            Iterator of MatchResult if no terminal stage, None otherwise
        """
        result_iter = None

        for stage in stages:
            if stage.stage_type == StageType.MATCH:
                # First match stage queries DB
                if result_iter is None:
                    result_iter = self._execute_match_stage(stage)
                # Subsequent match stages filter previous results
                else:
                    result_iter = self._execute_filter_stage(stage, result_iter)

            elif stage.stage_type == StageType.RENDER:
                # Render consumes iterator and outputs formatted results
                self._execute_render_stage(stage, result_iter)
                return None  # Render is terminal stage

            elif stage.stage_type == StageType.STATS:
                self._execute_stats_stage(stage)
                return None  # Stats is terminal stage

        # No render stage - return iterator for caller to consume
        # (or default to list output if result_iter exists)
        return result_iter

    def _execute_match_stage(self, stage: PipelineStage) -> Iterator[MatchResult]:
        """Execute match stage against database.

        Args:
            stage: PipelineStage with MATCH type

        Returns:
            Iterator of MatchResult from database
        """
        args = stage.args

        # Extract arguments
        symbol_type = SymbolType(args.symbol_type)
        pattern = args.pattern
        case_sensitive = not args.case_insensitive
        limit = args.limit

        # Determine match operator (GLOB is default)
        # argparse sets pattern regardless of which flag was used
        match_op = MatchOp.GLOB  # Default

        # Query database
        results = self.db.match(symbol_type, match_op, pattern, case_sensitive, limit)

        # Return iterator
        return results

    def _execute_filter_stage(
        self,
        stage: PipelineStage,
        prev_results: Iterator[MatchResult]
    ) -> Iterator[MatchResult]:
        """Filter previous results (for chained matches).

        Args:
            stage: PipelineStage with MATCH type
            prev_results: Iterator from previous stage

        Returns:
            Filtered iterator
        """
        args = stage.args

        target_type = args.symbol_type
        pattern = args.pattern
        case_sensitive = not args.case_insensitive

        for record in prev_results:
            # Filter by type
            if record.symbol_type != target_type:
                continue

            # Apply pattern match (using glob by default)
            if self._pattern_matches(record.symbol_name, pattern, MatchOp.GLOB, case_sensitive):
                yield record

    def _pattern_matches(
        self,
        value: str,
        pattern: str,
        match_op: MatchOp,
        case_sensitive: bool
    ) -> bool:
        """Check if value matches pattern using given operator.

        Args:
            value: String to match
            pattern: Pattern to match against
            match_op: Match operator (GLOB, REGEXP, LIKE)
            case_sensitive: Whether to match case-sensitively

        Returns:
            True if value matches pattern
        """
        if not case_sensitive:
            value = value.lower()
            pattern = pattern.lower()

        if match_op == MatchOp.GLOB:
            return fnmatch.fnmatch(value, pattern)
        elif match_op == MatchOp.REGEXP:
            return bool(re.search(pattern, value))
        elif match_op == MatchOp.LIKE:
            # Convert SQL LIKE pattern to regex
            regex_pattern = pattern.replace('%', '.*').replace('_', '.')
            return bool(re.match(f'^{regex_pattern}$', value))

        return False

    def _execute_render_stage(self, stage: PipelineStage, records: Iterator[MatchResult]):
        """Render records to stdout.

        Args:
            stage: PipelineStage with RENDER type
            records: Iterator of MatchResult to render
        """
        args = stage.args

        # Convert string render_type to RenderType enum (default: LIST)
        render_type_str = getattr(args, 'render_type', None) or 'list'
        render_type = RenderType(render_type_str)

        # Convert string format to FormatType enum (default: ASCII)
        format_str = getattr(args, 'format', None)
        format_type = FormatType(format_str) if format_str else None

        # Create renderer and render output
        renderer = RendererFactory.create(render_type, format_type)
        output = renderer.render(records)

        if output:
            print(output)

    def _execute_stats_stage(self, stage: PipelineStage):
        """Execute stats stage (placeholder for Phase 8).

        Args:
            stage: PipelineStage with STATS type
        """
        # Placeholder - will be implemented in Phase 8
        print("Stats command not yet implemented")
