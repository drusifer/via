"""Pipeline executor for running pipeline stages."""
import fnmatch
import re
import sys
from typing import Iterator, Optional, List, Dict

from via.pipeline.types import PipelineStage, StageType
from via.pipeline.relationship_filter import RelationshipFilter
from via.core.types import SymbolType, MatchOp
from via.core.match_record import MatchRecord, RenderType, FormatType
from via.core.utils import safe_print, get_match_op
from via.db.store import DatabaseStore
from via.renderers.factory import RendererFactory


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

        In the new design, output flags (-oL, -oT, etc.) are part of MATCH stages.
        The last MATCH stage's render_type determines how output is rendered.

        Args:
            stages: List of PipelineStage objects to execute

        Returns:
            Iterator of MatchRecord if no terminal stage, None otherwise
        """
        result_iter = None
        last_match_stage = None

        for stage in stages:
            if stage.stage_type == StageType.MATCH:
                # First match stage queries DB
                if result_iter is None:
                    result_iter = self._execute_match_stage(stage)
                # Subsequent match stages filter previous results
                else:
                    result_iter = self._execute_filter_stage(stage, result_iter)
                last_match_stage = stage

            elif stage.stage_type == StageType.RENDER:
                # Legacy: Render consumes iterator and outputs formatted results
                self._execute_render_stage(stage, result_iter)
                return None  # Render is terminal stage

            elif stage.stage_type == StageType.STATS:
                self._execute_stats_stage(stage)
                return None  # Stats is terminal stage

        # Check if last match stage has render_type (new design)
        if last_match_stage and hasattr(last_match_stage.args, 'render_type'):
            render_type = getattr(last_match_stage.args, 'render_type', None)
            if render_type:
                # Render using the match stage's args
                self._execute_render_stage(last_match_stage, result_iter)
                return None

        # No render type specified - return iterator for caller to consume
        return result_iter

    def _execute_match_stage(self, stage: PipelineStage) -> Iterator[MatchRecord]:
        """Execute match stage against database.

        Args:
            stage: PipelineStage with MATCH type

        Returns:
            Iterator of MatchRecord from database
        """
        args = stage.args

        # Check if this is a relationship query
        relationship = getattr(args, 'relationship', None)
        if relationship:
            return self._execute_relationship_query(stage)

        # Extract arguments - check for symbol_types list (OR'd) or symbol_type (single)
        symbol_types = getattr(args, 'symbol_types', None) or []
        symbol_type = args.symbol_type if hasattr(args, 'symbol_type') else None

        pattern = args.pattern
        case_sensitive = not args.case_insensitive
        limit = args.limit
        match_qualified = getattr(args, 'match_qualified', False)

        # Determine match operator from match_syntax attribute
        # match_syntax is the suffix from flag groups: 'g' (glob), 'r' (regex), 's' (sql)
        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        # Handle multiple symbol types (OR'd together)
        if len(symbol_types) > 1:
            return self._match_multiple_types(
                symbol_types, pattern, match_op, case_sensitive, limit, match_qualified
            )

        # Single type or all types
        st = SymbolType(symbol_type) if symbol_type else None
        results = self.db.match(st, match_op, pattern, case_sensitive, limit, match_qualified)
        return results

    def _execute_relationship_query(self, stage: PipelineStage) -> Iterator[MatchRecord]:
        """Execute relationship query against database.

        Args:
            stage: PipelineStage with relationship filter

        Returns:
            Iterator of MatchRecord from database
        """
        args = stage.args
        rel: RelationshipFilter = args.relationship

        # Extract query params from CLI
        # - Pattern BEFORE --via: what user is relating TO (the "known" thing)
        # - Pattern AFTER --via: filter on results (defaults to '*' = all)
        cli_relate_to_pattern = args.pattern
        cli_results_pattern = rel.object_pattern

        cli_relate_to_types = getattr(args, 'symbol_types', None) or []
        cli_relate_to_type = args.symbol_type if hasattr(args, 'symbol_type') else None
        if cli_relate_to_types:
            cli_relate_to_type = cli_relate_to_types[0]

        cli_results_type = rel.object_types[0] if rel.object_types else None

        case_sensitive = not args.case_insensitive
        limit = args.limit

        # Map CLI patterns to DB query based on invert flag
        # Without invert: relate TO = targets (parents), results = sources (children)
        # With invert: relate TO = sources (children), results = targets (parents)
        if not rel.invert:
            # "Find children that inherit FROM parents matching pattern"
            subject_pattern = cli_results_pattern   # filter results (sources/children)
            object_pattern = cli_relate_to_pattern  # filter what we relate TO (targets/parents)
            subject_type = cli_results_type
            object_type = cli_relate_to_type
        else:
            # "Find parents that are inherited BY children matching pattern"
            subject_pattern = cli_relate_to_pattern  # filter what we query about (sources/children)
            object_pattern = cli_results_pattern     # filter results (targets/parents)
            subject_type = cli_relate_to_type
            object_type = cli_results_type

        # Query relationships from database
        return self.db.query_relationships(
            relationship_type=rel.relationship_type.value,
            subject_pattern=subject_pattern,
            object_pattern=object_pattern,
            subject_type=subject_type,
            object_type=object_type,
            invert=rel.invert,
            limit=limit,
            case_sensitive=case_sensitive
        )

    def _match_multiple_types(
        self,
        symbol_types: List[str],
        pattern: str,
        match_op: MatchOp,
        case_sensitive: bool,
        limit: int,
        match_qualified: bool
    ) -> Iterator[MatchRecord]:
        """Query database for multiple symbol types (OR'd together).

        Args:
            symbol_types: List of symbol type strings to match
            pattern: Pattern to match
            match_op: Match operator
            case_sensitive: Whether to match case-sensitively
            limit: Max results per type
            match_qualified: Whether to match qualified names

        Yields:
            MatchRecord objects from database
        """
        count = 0
        for type_str in symbol_types:
            st = SymbolType(type_str)
            for record in self.db.match(
                st, match_op, pattern, case_sensitive, limit, match_qualified
            ):
                yield record
                count += 1
                if count >= limit:
                    return

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

        # Handle multiple symbol types (OR'd) or single type
        symbol_types = getattr(args, 'symbol_types', None) or []
        target_type = args.symbol_type if hasattr(args, 'symbol_type') else None

        # Build set of allowed types
        if len(symbol_types) > 1:
            allowed_types = set(symbol_types)
        elif target_type:
            allowed_types = {target_type}
        else:
            allowed_types = None  # Allow all types

        pattern = args.pattern
        case_sensitive = not args.case_insensitive

        # Determine match operator from match_syntax attribute
        # match_syntax is the suffix from flag groups: 'g' (glob), 'r' (regex), 's' (sql)
        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        for record in prev_results:
            # Filter by type if specified
            if allowed_types and record.symbol_type not in allowed_types:
                continue

            # Apply pattern match
            if self._pattern_matches(record.symbol_name, pattern, match_op, case_sensitive):
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
        if match_op == MatchOp.REGEXP:
            return bool(re.search(pattern, value))
        if match_op == MatchOp.LIKE:
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
            safe_print(output)

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
        total = sum(skipped_types.values())
        types_str = ', '.join(f"{t}({c})" for t, c in skipped_types.items())
        print(f"Warning: {total} record(s) skipped (don't support {render_flag}): {types_str}",
              file=sys.stderr)

    def _execute_stats_stage(self, stage: PipelineStage):  # noqa: ARG002  pylint: disable=unused-argument
        """Execute stats stage (placeholder for Phase 8).

        Args:
            stage: PipelineStage with STATS type
        """
        # Placeholder - will be implemented in Phase 8
        print("Stats command not yet implemented")
