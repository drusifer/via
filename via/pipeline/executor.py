"""
Executes a parsed pipeline by driving database queries and rendering output.

TLDR: Sequentially executes PipelineStage objects, handling database queries, in-memory filtering, and relationship processing (--via/--sans) with streaming MatchRecord iterators.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import dataclasses
import fnmatch
import copy
import re
import sys
from typing import Any, Dict, Iterator, List, Optional

from via.core.duration import parse_duration
from via.core.match_record import FormatType, MatchRecord, RenderType
from via.core.relationship_types import execute_relation, is_category
from via.core.types import MatchOp, SymbolType
from via.core.utils import get_match_op, parse_result_slice, safe_print
from via.db.store import DatabaseStore
from via.pipeline.relationship_filter import RelationshipFilter
from via.pipeline.types import PipelineStage, StageType
from via.pipeline.handlers import STAGE_REGISTRY
from via.renderers.factory import RendererFactory
from via.renderers.utils import extract_source

# Language alias normalization for --lang
_LANG_ALIASES: Dict[str, str] = {
    'py': 'python', 'python': 'python',
    'js': 'javascript', 'javascript': 'javascript',
    'ts': 'typescript', 'typescript': 'typescript',
    'md': 'markdown', 'markdown': 'markdown',
    'dart': 'dart',
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
            handler = STAGE_REGISTRY.get(stage.stage_type)
            if handler:
                result_iter = handler.handle(stage, self, result_iter)
                if result_iter is None:
                    return None
                if stage.stage_type == StageType.MATCH:
                    last_match_stage = stage

        # Apply line slice if -mL was specified on the last match stage
        if last_match_stage and getattr(last_match_stage.args, 'line_slice', None):
            result_iter = self._apply_line_slice(result_iter, last_match_stage.args)

        # Check if last match stage has render_type (new design)
        if last_match_stage and hasattr(last_match_stage.args, 'render_type'):
            render_type = getattr(last_match_stage.args, 'render_type', None)
            if render_type:
                # Render using the match stage's args
                self._execute_render_stage(last_match_stage, result_iter)
                return None

        # No render type specified - return iterator for caller to consume
        return result_iter

    @staticmethod
    def _resolve_limit_and_offset(args) -> tuple:
        """Return (limit, offset) from --slice or -n args, or defaults."""
        raw_slice = getattr(args, 'result_slice', None)
        raw_limit = getattr(args, 'limit', None)
        if raw_slice is not None:
            if raw_limit is not None:
                from via.pipeline.parser import PipelineParseError
                raise PipelineParseError(
                    "--slice and --limit are mutually exclusive. "
                    "Use --slice start:end for windowed results."
                )
            start, end = parse_result_slice(raw_slice)
            offset: Optional[int] = start if start is not None else 0
            limit = (end - offset) if end is not None else 0  # 0 = unlimited
            return limit, offset
        return raw_limit if raw_limit is not None else 10, None  # default 10

    @staticmethod
    def _resolve_language_filter(raw_lang: Optional[str]) -> Optional[str]:
        """Normalize language alias; raise PipelineParseError if unknown."""
        if not raw_lang:
            return None
        language_filter = _LANG_ALIASES.get(raw_lang.lower())
        if language_filter is None:
            from via.pipeline.parser import PipelineParseError
            raise PipelineParseError(
                f"Unknown --lang '{raw_lang}'. "
                f"Valid: py/python, js/javascript, ts/typescript, dart, md/markdown."
            )
        return language_filter

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
            relationships = getattr(args, 'relationships', None) or [relationship]
            if len(relationships) > 1:
                for rel in relationships:
                    if is_category(rel.relationship_type):
                        raise ValueError(
                            "Relationship categories (e.g. 'upstream-ref') are not yet "
                            "supported when chaining multiple --via/--sans filters in one "
                            "query. Use a category as the only relationship filter, or use "
                            "concrete relationship types when chaining."
                        )
                compiled_stages = [
                    self._compile_relationship_params(stage, rel, is_first=(i == 0))
                    for i, rel in enumerate(relationships)
                ]
                limit = getattr(args, 'limit', None) or 10
                case_sensitive = not args.case_insensitive
                results = list(self.db.query_relationships_chained(
                    compiled_stages,
                    limit=limit,
                    case_sensitive=case_sensitive,
                ))
                
                # Post-filter for --stale for any relationship filter that requested it
                for rel in relationships:
                    if rel.result_stale:
                        if results and all(r.mtime is None for r in results):
                            raise ValueError(
                                '--stale requires symbols.mtime — rebuild index with `via index --force`.'
                            )
                        results = [
                            r for r in results
                            if r.anchor_mtime is not None and r.mtime is not None
                            and r.mtime < r.anchor_mtime
                        ]
                
                # Contains filter
                contains_pattern = getattr(args, 'contains_pattern', None)
                if contains_pattern:
                    return self._filter_records_by_body(iter(results), contains_pattern, case_sensitive)
                return iter(results)

            primary_stage = self._stage_with_relationship(stage, relationships[0])
            if relationships[0].is_negative:
                results = self._execute_negative_relationship_query(primary_stage)
            else:
                results = self._execute_relationship_query(primary_stage)
            contains_pattern = getattr(args, 'contains_pattern', None)
            if contains_pattern:
                return self._filter_records_by_body(results, contains_pattern, not args.case_insensitive)
            return results

        # Extract arguments - check for symbol_types list (OR'd) or symbol_type (single)
        symbol_types = getattr(args, 'symbol_types', None) or []
        symbol_type = args.symbol_type if hasattr(args, 'symbol_type') else None

        pattern = args.pattern
        case_sensitive = not args.case_insensitive
        match_qualified = getattr(args, 'match_qualified', False)
        negated = getattr(args, 'negate_pattern', False)

        limit, offset = self._resolve_limit_and_offset(args)

        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        newerthan_seconds = parse_duration(args.newerthan) if getattr(args, 'newerthan', None) else None
        olderthan_seconds = parse_duration(args.olderthan) if getattr(args, 'olderthan', None) else None

        language_filter = self._resolve_language_filter(getattr(args, 'language_filter', None))
        subtype_filter = getattr(args, 'symbol_subtype_filter', None) or None

        # Handle multiple symbol types (OR'd together)
        if len(symbol_types) > 1:
            results = self._match_multiple_types(
                symbol_types, pattern, match_op, case_sensitive, limit,
                match_qualified, negated,
                language=language_filter, subtype=subtype_filter,
                offset=offset,
            )
            contains_pattern = getattr(args, 'contains_pattern', None)
            if contains_pattern:
                return self._filter_records_by_body(results, contains_pattern, case_sensitive)
            return results

        # Single type or all types
        st = SymbolType(symbol_type) if symbol_type else None
        results = self.db.match(
            st, match_op, pattern, case_sensitive, limit, match_qualified,
            newerthan_seconds=newerthan_seconds,
            olderthan_seconds=olderthan_seconds,
            negated=negated,
            language=language_filter,
            subtype=subtype_filter,
            offset=offset,
        )
        contains_pattern = getattr(args, 'contains_pattern', None)
        if contains_pattern:
            return self._filter_records_by_body(results, contains_pattern, case_sensitive)
        return results

    def _compile_relationship_params(self, stage: PipelineStage, rel: RelationshipFilter, is_first: bool) -> Dict[str, Any]:
        args = stage.args
        negated = getattr(args, 'negate_pattern', False) if is_first else False
        subject_pattern = args.pattern if is_first else "*"

        # Result stage types
        result_types = getattr(args, 'symbol_types', None) or []
        result_type = args.symbol_type if hasattr(args, 'symbol_type') else None
        if result_types:
            result_type = result_types[0]

        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        if not rel.is_negative:
            # Positive relationship
            object_pattern = rel.filter_pattern
            filter_type = rel.filter_types[0] if rel.filter_types else None
            actual_inverted = self._get_actual_inverted(rel, result_type, filter_type)

            if not actual_inverted:
                db_subject_pattern = subject_pattern
                db_object_pattern = object_pattern
                db_subject_type = result_type
                db_object_type = filter_type
            else:
                db_subject_pattern = object_pattern
                db_object_pattern = subject_pattern
                db_subject_type = filter_type
                db_object_type = result_type

            subject_parent_pattern = None
            if rel.relationship_type.value == 'calls' and db_subject_type == 'class':
                subject_parent_pattern = db_subject_pattern
                db_subject_pattern = '*'
                db_subject_type = 'method'

            if not actual_inverted:
                subject_qualified = getattr(args, 'match_qualified', False) if is_first else False
                object_qualified = rel.filter_qualified
            else:
                subject_qualified = rel.filter_qualified
                object_qualified = getattr(args, 'match_qualified', False) if is_first else False

            # Check container validation
            _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename', None}
            if rel.relationship_type.value == 'declares':
                container_type = db_subject_type if actual_inverted else db_object_type
                if container_type not in _DECLARES_CONTAINER_TYPES:
                    raise ValueError(
                        f"'{container_type}' is not a valid container type for "
                        f"{'declares' if actual_inverted else 'declared-in'}. "
                        f"Valid container types: class, file/filepath."
                    )

            return {
                'is_negative': False,
                'relationship_type': rel.relationship_type.value,
                'subject_pattern': db_subject_pattern,
                'object_pattern': db_object_pattern,
                'subject_type': db_subject_type,
                'object_type': db_object_type,
                'subject_parent_pattern': subject_parent_pattern,
                'invert': actual_inverted,
                'match_op': match_op,
                'result_newerthan_seconds': rel.result_newerthan_seconds,
                'result_olderthan_seconds': rel.result_olderthan_seconds,
                'subject_negated': negated if not actual_inverted else False,
                'object_negated': negated if actual_inverted else False,
                'subject_qualified': subject_qualified,
                'object_qualified': object_qualified,
            }
        else:
            # Negative relationship
            object_pattern = rel.filter_pattern
            object_type = rel.filter_types[0] if rel.filter_types else None
            actual_inverted = self._get_actual_inverted(rel, result_type, object_type)
            invert_join = actual_inverted

            # Check container validation
            _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename', None}
            if rel.relationship_type.value == 'declares':
                container_type = result_type if actual_inverted else object_type
                if container_type not in _DECLARES_CONTAINER_TYPES:
                    raise ValueError(
                        f"'{container_type}' is not a valid container type for "
                        f"{'declares' if actual_inverted else 'declared-in'}. "
                        f"Valid container types: class, file/filepath."
                    )

            subject_qualified = getattr(args, 'match_qualified', False) if is_first else False
            object_qualified = rel.filter_qualified

            return {
                'is_negative': True,
                'relationship_type': rel.relationship_type.value,
                'subject_pattern': subject_pattern,
                'object_pattern': object_pattern,
                'subject_type': result_type,
                'object_type': object_type,
                'match_op': match_op,
                'result_newerthan_seconds': rel.result_newerthan_seconds,
                'result_olderthan_seconds': rel.result_olderthan_seconds,
                'invert_join': invert_join,
                'subject_negated': negated,
                'object_negated': False,
                'subject_qualified': subject_qualified,
                'object_qualified': object_qualified,
            }

    @staticmethod
    def _get_actual_inverted(rel: RelationshipFilter, result_type: Optional[str], filter_type: Optional[str]) -> bool:
        """Determine actual inversion status, correcting for declares user query directions."""
        return rel.inverted

    def _execute_relationship_query(self, stage: PipelineStage, result_names: Optional[List[str]] = None) -> Iterator[MatchRecord]:
        """Execute positive relationship query (--via) against database.

        One uniform call regardless of whether the resolved relationship is a
        concrete leaf (e.g. Calls) or a category (e.g. UpstreamRef, from
        --via upstream-ref) — `execute_relation` asks the relationship type
        itself to run `run_leaf` once per concrete leaf beneath it and merge,
        via real polymorphism (`leaves()` walking `__subclasses__()`), not a
        branch here. A leaf's `leaves()` is just itself, so this runs the
        query exactly once for the plain single-relationship case.

        Error-handling policy differs by *why* a leaf is being run, not by
        mechanism: a category (e.g. upstream-ref) pulls in leaves like
        Declares that may not apply to every type combination (e.g. a
        function can't be a 'declares' container) — that leaf should just
        contribute nothing. A direct `--via declares` query with the same
        invalid combination should still raise its normal, clear error.
        """
        args = stage.args
        rel: RelationshipFilter = args.relationship
        limit = getattr(args, 'limit', None) or 10
        fan_out = is_category(rel.relationship_type)

        def run_leaf(leaf_cls):
            # inverted is a separate RelationshipFilter field from
            # relationship_type.inverted (the class attribute) — both must
            # be replaced together or a category's leaves silently keep the
            # category's own (meaningless) top-level inverted flag. Plain
            # ReferenceType members (older call sites, e.g. tests/web API)
            # have no .inverted at all — rel.inverted is already correct
            # for those, so fall back to it unchanged.
            leaf_inverted = getattr(leaf_cls, 'inverted', rel.inverted)
            leaf_rel = dataclasses.replace(rel, relationship_type=leaf_cls, inverted=leaf_inverted)
            if not fan_out:
                return self._execute_single_relationship_query(stage, leaf_rel, result_names)
            try:
                return self._execute_single_relationship_query(stage, leaf_rel, result_names)
            except ValueError:
                return []

        return iter(execute_relation(rel.relationship_type, run_leaf)[:limit])

    def _execute_single_relationship_query(
        self,
        stage: PipelineStage,
        rel: RelationshipFilter,
        result_names: Optional[List[str]] = None,
    ) -> Iterator[MatchRecord]:
        """Execute positive relationship query (--via) against database for one concrete leaf.

        Result-first direction convention:
          Pattern BEFORE --via = result stage (what gets returned)
          Pattern AFTER --via  = filter stage (the relationship anchor)
          For forward relationships: returns source (from) side symbols.
          For inverse relationships (e.g. called-by): returns target (to) side symbols.

        Args:
          stage: PipelineStage with relationship filter (is_negative=False)
          rel: The (concrete leaf) relationship filter to execute
          result_names: Optional list of names to filter returned symbols

        Returns:
          Iterator of MatchRecord from database
        """
        args = stage.args
        negated = getattr(args, 'negate_pattern', False)

        # Result-first: pattern BEFORE --via is what gets returned
        subject_pattern = args.pattern
        # Filter: pattern AFTER --via is the relationship anchor
        object_pattern = rel.filter_pattern

        # Result stage types
        result_types = getattr(args, 'symbol_types', None) or []
        result_type = args.symbol_type if hasattr(args, 'symbol_type') else None
        if result_types:
            result_type = result_types[0]

        # Filter stage types
        filter_type = rel.filter_types[0] if rel.filter_types else None

        actual_inverted = self._get_actual_inverted(rel, result_type, filter_type)

        # declares requires a container (file or class) as the container type
        _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename', None}
        if rel.relationship_type.value == 'declares':
            container_type = result_type if actual_inverted else filter_type
            if container_type not in _DECLARES_CONTAINER_TYPES:
                raise ValueError(
                    f"'{container_type}' is not a valid container type for "
                    f"{'declares' if actual_inverted else 'declared-in'}. "
                    f"Valid container types: class, file/filepath."
                )

        case_sensitive = not args.case_insensitive
        limit = getattr(args, 'limit', None) or 10

        # Map result-first CLI args to DB subject/object convention.
        # For forward (inverted=False): result=subject (from side), filter=object (to side)
        # For inverse (inverted=True): result=object (to side), filter=subject (from side)
        if not actual_inverted:
            db_subject_pattern = subject_pattern
            db_object_pattern = object_pattern
            db_subject_type = result_type
            db_object_type = filter_type
        else:
            db_subject_pattern = object_pattern
            db_object_pattern = subject_pattern
            db_subject_type = filter_type
            db_object_type = result_type

        # calls stored from method symbols, not class symbols.
        # When subject side is a class for calls, expand to include methods.
        subject_parent_pattern = None
        if rel.relationship_type.value == 'calls' and db_subject_type == 'class':
            subject_parent_pattern = db_subject_pattern
            db_subject_pattern = '*'
            db_subject_type = 'method'

        if not actual_inverted:
            subject_qualified = getattr(args, 'match_qualified', False)
            object_qualified = rel.filter_qualified
        else:
            subject_qualified = rel.filter_qualified
            object_qualified = getattr(args, 'match_qualified', False)

        # Query relationships from database
        results = list(self.db.query_relationships(
            relationship_type=rel.relationship_type.value,
            subject_pattern=db_subject_pattern,
            object_pattern=db_object_pattern,
            subject_type=db_subject_type,
            object_type=db_object_type,
            subject_parent_pattern=subject_parent_pattern,
            invert=actual_inverted,
            limit=limit,
            case_sensitive=case_sensitive,
            result_newerthan_seconds=rel.result_newerthan_seconds,
            result_olderthan_seconds=rel.result_olderthan_seconds,
            subject_negated=negated if not actual_inverted else False,
            object_negated=negated if actual_inverted else False,
            subject_qualified=subject_qualified,
            object_qualified=object_qualified,
            result_names=result_names,
        ))

        # --stale post-filter: keep results whose mtime < anchor's mtime
        if rel.result_stale:
            if results and all(r.mtime is None for r in results):
                raise ValueError(
                    '--stale requires symbols.mtime — rebuild index with `via index --force`.'
                )
            results = [
                r for r in results
                if r.anchor_mtime is not None and r.mtime is not None
                and r.mtime < r.anchor_mtime
            ]

        return iter(results)

    @staticmethod
    def _stage_with_relationship(stage: PipelineStage, rel: RelationshipFilter) -> PipelineStage:
        """Return a shallow stage copy with one active relationship filter."""
        args = copy.copy(stage.args)
        args.relationship = rel
        args.relationships = [rel]
        return PipelineStage(stage.stage_type, args)

    @staticmethod
    def _record_key(record: MatchRecord) -> tuple:
        """Return a stable identity key for comparing relationship query results."""
        return (
            record.symbol_type,
            record.qualified_name,
            record.file_path,
            record.line_number,
        )

    def _filter_results_by_relationship(
        self,
        stage: PipelineStage,
        prev_results: Iterator[MatchRecord],
        rel: RelationshipFilter,
    ) -> Iterator[MatchRecord]:
        """Apply an additional relationship filter to existing result records."""
        prev_list = list(prev_results)
        if not prev_list:
            return iter([])

        result_qualified = getattr(stage.args, 'match_qualified', False)
        candidate_names = [
            r.qualified_name if result_qualified else r.symbol_name 
            for r in prev_list
        ]

        allowed = set()
        for chunk in [candidate_names[i:i + 500] for i in range(0, len(candidate_names), 500)]:
            rel_stage = self._stage_with_relationship(stage, rel)
            rel_stage.args.limit = 1_000_000
            if rel.is_negative:
                matching = self._execute_negative_relationship_query(rel_stage, result_names=chunk)
            else:
                matching = self._execute_relationship_query(rel_stage, result_names=chunk)
            for record in matching:
                allowed.add(self._record_key(record))

        for record in prev_list:
            if self._record_key(record) in allowed:
                yield record

    def _execute_negative_relationship_query(self, stage: PipelineStage, result_names: Optional[List[str]] = None) -> Iterator[MatchRecord]:
        """Execute NOT EXISTS relationship query (--sans) against database.

        Result-first: the result stage (BEFORE --sans) specifies symbols to return.
        The filter stage (AFTER --sans) specifies what relationship must NOT exist.
        For inverse relationship types (e.g. called-by), invert_join flips which
        side of the join the NOT EXISTS check anchors on.

        Args:
            stage: PipelineStage with relationship filter (is_negative=True)
            result_names: Optional list of names to filter returned symbols

        Returns:
            Iterator of MatchRecord from database
        """
        args = stage.args
        rel: RelationshipFilter = args.relationship
        negated = getattr(args, 'negate_pattern', False)

        # Result-first: result stage pattern = what gets returned
        subject_pattern = args.pattern
        object_pattern = rel.filter_pattern

        subject_types = getattr(args, 'symbol_types', None) or []
        subject_type = args.symbol_type if hasattr(args, 'symbol_type') else None
        if subject_types:
            subject_type = subject_types[0]

        object_type = rel.filter_types[0] if rel.filter_types else None

        case_sensitive = not args.case_insensitive
        limit = getattr(args, 'limit', None) or 10

        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        # invert_join flips which side of the relationship the NOT EXISTS anchors on.
        # For inverse relationship types (e.g. called-by, declared-in), the result
        # is on the target (to) side, so the NOT EXISTS must anchor there.
        actual_inverted = self._get_actual_inverted(rel, subject_type, object_type)
        invert_join = actual_inverted

        # declares requires a container (file or class) as the container type
        _DECLARES_CONTAINER_TYPES = {'file', 'class', 'filepath', 'filename', None}
        if rel.relationship_type.value == 'declares':
            container_type = subject_type if actual_inverted else object_type
            if container_type not in _DECLARES_CONTAINER_TYPES:
                raise ValueError(
                    f"'{container_type}' is not a valid container type for "
                    f"{'declares' if actual_inverted else 'declared-in'}. "
                    f"Valid container types: class, file/filepath."
                )

        subject_qualified = getattr(args, 'match_qualified', False)
        object_qualified = rel.filter_qualified

        return self.db.query_negative_relationships(
            relationship_type=rel.relationship_type.value,
            subject_pattern=subject_pattern,
            object_pattern=object_pattern,
            subject_type=subject_type,
            object_type=object_type,
            match_op=match_op,
            case_sensitive=case_sensitive,
            limit=limit,
            result_newerthan_seconds=rel.result_newerthan_seconds,
            result_olderthan_seconds=rel.result_olderthan_seconds,
            invert_join=invert_join,
            subject_negated=negated,
            object_negated=False,
            subject_qualified=subject_qualified,
            object_qualified=object_qualified,
            result_names=result_names,
        )

    def _match_multiple_types(
        self,
        symbol_types: List[str],
        pattern: str,
        match_op: MatchOp,
        case_sensitive: bool,
        limit: Optional[int],
        match_qualified: bool,
        negated: bool = False,
        language: Optional[str] = None,
        subtype: Optional[str] = None,
        offset: Optional[int] = None,
    ) -> Iterator[MatchRecord]:
        """Query database for multiple symbol types (OR'd together).

        Args:
            symbol_types: List of symbol type strings to match
            pattern: Pattern to match
            match_op: Match operator
            case_sensitive: Whether to match case-sensitively
            limit: Max combined results (0 or None means unlimited)
            match_qualified: Whether to match qualified names
            negated: If True, invert the pattern match (--not semantics)
            language: Optional language filter (canonical form)
            subtype: Optional symbol_subtype filter
            offset: Optional start index into the combined ordered result set

        Yields:
            MatchRecord objects from database
        """
        combined_results: List[MatchRecord] = []
        for type_str in symbol_types:
            st = SymbolType(type_str)
            combined_results.extend(self.db.match(
                st, match_op, pattern, case_sensitive, 0, match_qualified,
                negated=negated, language=language, subtype=subtype,
            ))

        combined_results.sort(
            key=lambda record: (
                record.file_path,
                record.line_number,
                record.symbol_name,
                record.symbol_type,
            )
        )

        total_matches = len(combined_results)
        start = offset or 0
        end = None if limit in (None, 0) else start + limit

        for record in combined_results[start:end]:
            record.total_matches = total_matches
            yield record

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
        negated = getattr(args, 'negate_pattern', False)
        contains_pattern = getattr(args, 'contains_pattern', None)

        # Determine match operator from match_syntax attribute
        # match_syntax is the suffix from flag groups: 'g' (glob), 'r' (regex), 's' (sql)
        match_syntax = getattr(args, 'match_syntax', 'g')
        match_op = get_match_op(match_syntax)

        for record in prev_results:
            # Filter by type if specified
            if allowed_types and record.symbol_type not in allowed_types:
                continue

            # Apply pattern match (optionally negated)
            matches = self._pattern_matches(record.symbol_name, pattern, match_op, case_sensitive)
            if negated:
                matches = not matches
            if matches and contains_pattern:
                if record.byte_offset is None or record.byte_length is None or record.byte_length <= 0:
                    continue
                body = extract_source(
                    record.file_path,
                    record.byte_offset,
                    record.byte_length,
                    read_full_file=False,
                )
                if not body or not self._contains_matches(body, contains_pattern, case_sensitive):
                    continue
            if matches:
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

    def _contains_matches(self, body: str, pattern: str, case_sensitive: bool) -> bool:
        """Apply --contains semantics to a symbol body.

        If the pattern includes glob wildcards, use fnmatch against the full body.
        Otherwise treat the value as a plain substring search.
        """
        haystack = body if case_sensitive else body.lower()
        needle = pattern if case_sensitive else pattern.lower()
        if '*' in needle or '?' in needle:
            return fnmatch.fnmatch(haystack, f"*{needle}*")
        return needle in haystack

    def _filter_records_by_body(
        self,
        records: Iterator[MatchRecord],
        pattern: str,
        case_sensitive: bool,
    ) -> Iterator[MatchRecord]:
        """Filter records by source body text using stored byte spans."""
        skipped = 0
        yielded = 0
        for record in records:
            if record.byte_offset is None or record.byte_length is None or record.byte_length <= 0:
                skipped += 1
                continue
            body = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                read_full_file=False,
            )
            if not body:
                skipped += 1
                continue
            if self._contains_matches(body, pattern, case_sensitive):
                yielded += 1
                yield record

        if skipped:
            safe_print(
                f"Warning: --contains skipped {skipped} record(s) without readable source spans",
                file=sys.stderr,
            )

    def _apply_line_slice(
        self, records: Iterator[MatchRecord], args
    ) -> Iterator[MatchRecord]:
        """Update each record's byte_offset/byte_length to cover the requested line slice.

        The slice is relative to the matched symbol/file start (line 1 = first
        line of the matched thing). Absolute file line numbers are resolved by
        adding (record.line_number - 1) to the relative start/end.

        Records where the slice resolves to a zero-length range are skipped.

        Args:
            records: Upstream match records
            args: Parsed argparse Namespace with 'line_slice' attribute

        Yields:
            Updated MatchRecord objects
        """
        from via.core.utils import parse_line_slice

        rel_start, rel_end = parse_line_slice(args.line_slice)

        for record in records:
            # filepath/filename symbols use line_number=0 as "whole file" sentinel;
            # treat as line 1 so relative slices resolve correctly.
            sym_line = record.line_number if record.line_number > 0 else 1

            # Resolve relative slice to absolute file line numbers
            abs_start = sym_line + (rel_start - 1) if rel_start is not None else sym_line
            abs_end = sym_line + (rel_end - 1) if rel_end is not None else sym_line + 9999

            new_offset, new_length = self.db.get_line_byte_range(
                record.file_path, abs_start, abs_end
            )
            if new_length > 0:
                record.byte_offset = new_offset
                record.byte_length = new_length
                record.line_number = abs_start
                yield record

    def _execute_render_stage(self, stage: PipelineStage, records: Iterator[MatchRecord]):
        """Render records to stdout.

        Args:
            stage: PipelineStage with RENDER type
            records: Iterator of MatchRecord to render
        """
        args = stage.args
        raw_limit = getattr(args, 'limit', None)
        limit = raw_limit if raw_limit is not None else 10

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

        # Filter records, track unsupported types, and capture total_matches
        skipped_types: Dict[str, int] = {}
        rendered_count = [0]
        total_matches_ref = [None]

        def filter_supported(records_iter: Iterator[MatchRecord]) -> Iterator[MatchRecord]:
            for record in records_iter:
                if total_matches_ref[0] is None:
                    total_matches_ref[0] = record.total_matches
                if record.supports_render_type(render_type):
                    rendered_count[0] += 1
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

        # Warn when results are capped by the limit
        total = total_matches_ref[0]
        if limit > 0 and total is not None and total > limit:
            print(
                f"results 1-{rendered_count[0]} of {total} matches returned "
                f"(--limit={limit}) use --slice 0:{total} or -n 0 for all results",
                file=sys.stderr,
            )

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
