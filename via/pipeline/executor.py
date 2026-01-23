"""Pipeline executor for running pipeline stages."""
import sys
from typing import Iterator, Optional, List, Dict, Set
from via.pipeline.types import PipelineStage, StageType
from via.core.types import SymbolType, MatchOp
from via.core.match_record import MatchRecord, RenderType, FormatType
from via.db.store import DatabaseStore
from via.renderers.factory import RendererFactory
import fnmatch
import re


def _safe_print(text: str, file=None) -> None:
    """Print text safely, handling Unicode encoding errors.

    Some terminals use latin-1 or ASCII encoding which can't handle
    Unicode characters like emojis. This handles such cases gracefully.
    """
    if file is None:
        file = sys.stdout
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        print(safe_text, file=file)


# Mapping of symbol types to their supported render types (for error messages)
SYMBOL_RENDER_SUPPORT: Dict[str, Set[RenderType]] = {
    'class': {RenderType.LIST, RenderType.TABLE, RenderType.DIAGRAM,
              RenderType.USAGE, RenderType.RAW, RenderType.FORMATTED},
    'method': {RenderType.LIST, RenderType.TABLE, RenderType.USAGE,
               RenderType.RAW, RenderType.FORMATTED},
    'function': {RenderType.LIST, RenderType.TABLE, RenderType.USAGE,
                 RenderType.RAW, RenderType.FORMATTED},
    'filepath': {RenderType.LIST, RenderType.TABLE, RenderType.RAW},
    'filename': {RenderType.LIST, RenderType.TABLE, RenderType.RAW},
    'import': {RenderType.LIST, RenderType.TABLE, RenderType.USAGE, RenderType.RAW},
    'global': {RenderType.LIST, RenderType.TABLE, RenderType.RAW, RenderType.FORMATTED},
}

# User-friendly render type names for CLI flags
RENDER_TYPE_FLAGS: Dict[RenderType, str] = {
    RenderType.LIST: '-oL (list)',
    RenderType.TABLE: '-oT (table)',
    RenderType.DIAGRAM: '-oD (diagram)',
    RenderType.USAGE: '-oU (usage)',
    RenderType.RAW: '-oR (raw)',
    RenderType.FORMATTED: '-oF (formatted)',
}


class PipelineExecutor:
    """Execute pipeline stages sequentially.

    Stages are executed in order, passing Iterator[MatchRecord] between stages
    for zero-copy streaming.
    """

    def __init__(self, db_store: DatabaseStore):
        """Initialize executor with database store.

        Args:
            db_store: DatabaseStore instance for querying symbols
        """
        self.db = db_store

    def execute(self, stages: List[PipelineStage]) -> Optional[Iterator[MatchRecord]]:
        """Execute all stages, return final iterator or None if terminal stage.

        Args:
            stages: List of PipelineStage objects to execute

        Returns:
            Iterator of MatchRecord if no terminal stage, None otherwise
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

    def _execute_match_stage(self, stage: PipelineStage) -> Iterator[MatchRecord]:
        """Execute match stage against database.

        Args:
            stage: PipelineStage with MATCH type

        Returns:
            Iterator of MatchRecord from database
        """
        args = stage.args

        # Extract arguments - symbol_type can be None to match all types
        symbol_type = SymbolType(args.symbol_type) if args.symbol_type else None
        pattern = args.pattern
        case_sensitive = not args.case_insensitive
        limit = args.limit
        match_qualified = getattr(args, 'match_qualified', False)

        # Determine match operator (GLOB is default)
        # argparse sets pattern regardless of which flag was used
        match_op = MatchOp.GLOB  # Default

        # Query database
        results = self.db.match(symbol_type, match_op, pattern, case_sensitive, limit, match_qualified)

        # Return iterator
        return results

    def _execute_filter_stage(
        self,
        stage: PipelineStage,
        prev_results: Iterator[MatchRecord]
    ) -> Iterator[MatchRecord]:
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

    def _execute_render_stage(self, stage: PipelineStage, records: Iterator[MatchRecord]):
        """Render records to stdout.

        Args:
            stage: PipelineStage with RENDER type
            records: Iterator of MatchRecord to render
        """
        args = stage.args

        # Convert string render_type to RenderType enum (default: LIST)
        render_type_str = getattr(args, 'render_type', None) or 'list'
        render_type = RenderType(render_type_str)

        # Convert string format to FormatType enum (default: ASCII)
        format_str = getattr(args, 'format', None)
        format_type = FormatType(format_str) if format_str else None

        # Build render options
        render_options = {
            'after_context': getattr(args, 'after_context', 0),
            'before_context': getattr(args, 'before_context', 0),
            'context': getattr(args, 'context', None),
            'theme': getattr(args, 'theme', None),
            'nodelims': getattr(args, 'nodelims', False),
        }

        # Filter records and track unsupported types
        skipped_types: Dict[str, int] = {}

        def filter_supported(records_iter: Iterator[MatchRecord]) -> Iterator[MatchRecord]:
            for record in records_iter:
                if record.supports_render_type(render_type):
                    yield record
                else:
                    skipped_types[record.symbol_type] = skipped_types.get(record.symbol_type, 0) + 1

        # Create renderer and render output
        renderer = RendererFactory.create(render_type, format_type)
        output = renderer.render(filter_supported(records), **render_options)

        if output:
            _safe_print(output)

        # Show helpful message for skipped types
        if skipped_types:
            self._print_unsupported_warning(render_type, skipped_types)

    def _print_unsupported_warning(
        self,
        render_type: RenderType,
        skipped_types: Dict[str, int]
    ) -> None:
        """Print warning about symbol types that don't support the render type.

        Args:
            render_type: The requested render type
            skipped_types: Dict mapping symbol_type -> count of skipped records
        """
        render_flag = RENDER_TYPE_FLAGS.get(render_type, render_type.value)
        print(f"\nWarning: {sum(skipped_types.values())} record(s) skipped "
              f"(don't support {render_flag}):", file=sys.stderr)

        for symbol_type, count in skipped_types.items():
            supported = SYMBOL_RENDER_SUPPORT.get(symbol_type, set())
            supported_flags = [RENDER_TYPE_FLAGS[rt] for rt in supported if rt in RENDER_TYPE_FLAGS]
            print(f"  {symbol_type}: {count} skipped. Supported: {', '.join(supported_flags)}",
                  file=sys.stderr)

    def _execute_stats_stage(self, stage: PipelineStage):
        """Execute stats stage (placeholder for Phase 8).

        Args:
            stage: PipelineStage with STATS type
        """
        # Placeholder - will be implemented in Phase 8
        print("Stats command not yet implemented")
