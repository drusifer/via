"""
Parses raw CLI argv into an ordered list of PipelineStage objects.

TLDR: Parses command-line arguments into a chain of PipelineStage objects, handling syntax, type filters, relationship queries (--via/--sans), and pattern negation (--not).

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import argparse
import re
from typing import List, Optional, Tuple

from via.core.flag_groups import (
    FORMAT_FLAGS,
    MATCH_FLAGS,
    OUTPUT_FLAGS,
    TYPE_FLAGS,
    get_match_short_flags,
    get_type_short_flags,
)
from via.core.relationship_types import ReferenceType
from via.pipeline.stage_builder import (
    build_match_stage,
    build_relationship_filter,
    finalize_match_namespace,
)
from via.pipeline.errors import PipelineParseError
from via.pipeline.types import PipelineStage, StageType


class _StoreSyntax(argparse.Action):
    """Custom action to store both pattern and match_syntax."""

    def __init__(self, option_strings, dest, syntax='glob', **kwargs):
        self.syntax = syntax
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, _option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, 'match_syntax', self.syntax)


class _AppendType(argparse.Action):
    """Custom action to append type to a list (for OR-ing multiple types)."""

    def __init__(self, option_strings, dest, type_value=None, **kwargs):
        self.type_value = type_value
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, _option_string=None):
        current = getattr(namespace, self.dest, None) or []
        current.append(self.type_value)
        setattr(namespace, self.dest, current)


class PipelineParser:
    """Parse command line into pipeline stages using argparse.

    A single via invocation includes:
    - Match syntax: -mg (glob), -mr (regex), -ms (sql)
    - Symbol types: -tc, -tf, -tm, etc. (multiple allowed, OR'd together)
    - Output: -oL, -oT, -oD, etc.
    - Format: -fa, -fm, -fh, -fp

    The --via separator chains additional match+type filters to narrow results.
    """

    def __init__(self):
        """Initialize parser."""
        self.match_parser = self._create_match_parser()
        self.stats_parser = self._create_stats_parser()

    def parse(self, argv: List[str]) -> List[PipelineStage]:
        """Parse argv into pipeline stages.

        Args:
            argv: Command line arguments (without program name)

        Returns:
            List of PipelineStage objects

        Raises:
            PipelineParseError: If parsing fails
        """
        segments = self._split_on_via(argv)
        stages = []

        for segment in segments:
            stage = self._parse_stage(segment)
            stages.append(stage)

        return stages

    def _split_on_via(self, argv: List[str]) -> List[List[str]]:
        """Split argv into segments at each plain --via separator.

        --via followed by a valid relationship type (forward or inverse) is a
        relationship flag (kept in the current segment). --via alone is a
        pipeline separator. -V is always a relationship short form (never a
        separator).

        Args:
            argv: Command line arguments

        Returns:
            List of argument segments (empty segments filtered out)
        """
        full_map = ReferenceType.get_full_value_map()
        segments = [[]]
        i = 0
        while i < len(argv):
            arg = argv[i]
            if arg == '--via':
                # Check if next arg is a relationship type → relationship flag
                if i + 1 < len(argv) and argv[i + 1] in full_map:
                    segments[-1].append(arg)
                    segments[-1].append(argv[i + 1])
                    i += 2
                    continue
                # Plain --via separator → start new segment
                segments.append([])
                i += 1
                continue
            segments[-1].append(arg)
            i += 1

        return [s for s in segments if s]

    def _find_relationship_splits(
        self, args: List[str]
    ) -> Optional[Tuple[List[str], List[Tuple['ReferenceType', List[str], bool, bool]]]]:
        """Find relationship clauses and split into result/filter parts.

        Args:
            args: Command line arguments for a stage

        Returns:
            Tuple of (result_args, relationship clauses) or None. Each clause is
            (relationship_type, filter_args, is_negative, inverted).

        Raises:
            PipelineParseError: If relationship type value is invalid
        """
        full_map = ReferenceType.get_full_value_map()
        valid_rels = ', '.join(sorted(full_map.keys()))

        rel_flags = {'--via', '-V', '--sans', '-S'}
        first_rel_index = next(
            (i for i, arg in enumerate(args) if arg in rel_flags),
            None,
        )
        if first_rel_index is None:
            return None

        result_args = args[:first_rel_index]
        clauses: List[Tuple['ReferenceType', List[str], bool, bool]] = []
        i = first_rel_index
        while i < len(args):
            arg = args[i]
            if arg not in rel_flags:
                raise PipelineParseError(
                    f"Unexpected argument between relationship filters: {arg}",
                    code="invalid_relationship_chain",
                    hint="Each relationship filter must start with --via, -V, --sans, or -S.",
                )
            is_negative = arg in ('--sans', '-S')
            if i + 1 >= len(args):
                flag_name = '--sans' if is_negative else '--via'
                raise PipelineParseError(
                    f"{flag_name} requires a relationship type argument.\n"
                    f"Valid: {valid_rels}",
                    code="missing_relationship_type",
                    hint=f"Use {flag_name} <relationship>. Valid values: {valid_rels}.",
                )

            rel_str = args[i + 1]
            if rel_str not in full_map:
                flag_name = '--sans' if is_negative else '--via'
                raise PipelineParseError(
                    f"Unknown relationship type '{rel_str}'.\n"
                    f"Valid: {valid_rels}",
                    code="invalid_relationship",
                    hint=f"Valid relationship types: {valid_rels}.",
                )

            rel_type, inverted = full_map[rel_str]
            filter_start = i + 2
            next_rel_index = next(
                (j for j in range(filter_start, len(args)) if args[j] in rel_flags),
                len(args),
            )
            clauses.append((rel_type, args[filter_start:next_rel_index], is_negative, inverted))
            i = next_rel_index

        return (result_args, clauses)

    def _find_relationship_split(
        self, args: List[str]
    ) -> Optional[Tuple[List[str], 'ReferenceType', List[str], bool, bool]]:
        """Find the first relationship split.

        Kept as a compatibility helper for tests and callers that exercise the
        parser internals directly. Multi-filter parsing uses
        _find_relationship_splits().
        """
        rel_splits = self._find_relationship_splits(args)
        if rel_splits is None:
            return None
        result_args, clauses = rel_splits
        rel_type, filter_args, is_negative, inverted = clauses[0]
        return (result_args, rel_type, filter_args, is_negative, inverted)

        return None

    def _extract_not_flag(self, args: List[str]) -> Tuple[List[str], bool]:
        """Extract --not flag from args and validate it precedes a match flag.

        Args:
            args: Command line arguments

        Returns:
            Tuple of (filtered_args_without_not, negated)

        Raises:
            PipelineParseError: If --not is not followed by a match flag
        """
        match_flags = {'-mg', '--match-glob', '-mr', '--match-regex', '-ms', '--match-sql'}
        filtered = []
        negated = False
        for i, arg in enumerate(args):
            if arg == '--not':
                # Verify next arg is a match flag
                remaining = args[i + 1:]
                if not any(a in match_flags for a in remaining):
                    raise PipelineParseError(
                        "--not must precede a match flag "
                        "(--match-glob, --match-regex, --match-sql)",
                        code="invalid_not_usage",
                        hint="Place --not immediately before -mg, -mr, or -ms.",
                    )
                negated = True
            else:
                filtered.append(arg)
        return filtered, negated

    def _validate_single_matcher(self, args: List[str], stage_label: str) -> None:
        """Reject repeated or mixed match flags in one user-visible stage."""
        match_flags = {
            '-mg': '--match-glob',
            '--match-glob': '--match-glob',
            '-mr': '--match-regex',
            '--match-regex': '--match-regex',
            '-ms': '--match-sql',
            '--match-sql': '--match-sql',
        }
        seen = []
        for arg in args:
            flag = arg.split('=', 1)[0]
            if flag in match_flags:
                seen.append(match_flags[flag])

        if len(seen) > 1:
            raise PipelineParseError(
                f"{stage_label} has multiple match flags: {', '.join(seen)}.",
                code="multiple_matchers",
                hint=(
                    "Use one match flag per stage. Compose with relationship "
                    "stages or rerun a narrower query."
                ),
            )

    def _validate_regex_pattern(self, parsed_args: argparse.Namespace, stage_label: str) -> None:
        """Validate regex match patterns during parsing."""
        if getattr(parsed_args, 'match_syntax', None) != 'r':
            return
        pattern = getattr(parsed_args, 'pattern', None)
        if pattern is None:
            return
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PipelineParseError(
                f"Invalid regex in {stage_label}: {exc}",
                code="invalid_regex",
                hint="Fix the -mr/--match-regex pattern or use -mg for glob matching.",
            ) from exc

    def _parse_stage(self, args: List[str]) -> PipelineStage:
        """Parse single stage using appropriate argparse parser.

        Args:
            args: Arguments for this stage

        Returns:
            PipelineStage object

        Raises:
            PipelineParseError: If stage cannot be parsed
        """
        if not args:
            raise PipelineParseError(
                "Empty pipeline stage",
                code="empty_stage",
                hint="Add a match flag such as -mg '*' and a type flag such as -tf.",
            )

        # Detect stage type from command/flags
        if args[0] == 'match' or self._is_match_stage(args):
            return self._parse_match_stage(args)
        if args[0] == 'stats':
            return self._parse_stats_stage(args)
        raise PipelineParseError(
            f"Unknown stage type: {args}",
            code="unknown_stage",
            hint="Use match flags such as -mg/-mr/-ms with type flags such as -tf/-tc.",
        )

    def _is_match_stage(self, args: List[str]) -> bool:
        """Check if args indicate a match stage."""
        match_flags = get_match_short_flags()  # {'-mg', '-mr', '-ms'}
        type_flags = get_type_short_flags()    # {'-tc', '-tf', '-tm', ...}
        # Also check for output flags (which are now part of match)
        output_flags = {f.short for f in OUTPUT_FLAGS}
        all_match_flags = match_flags | type_flags | output_flags
        return any(arg in all_match_flags for arg in args)

    def _parse_match_stage(self, args: List[str]) -> PipelineStage:
        """Parse match stage using argparse.

        Args:
            args: Arguments for match stage

        Returns:
            PipelineStage with StageType.MATCH

        Raises:
            PipelineParseError: If parsing fails
        """
        try:
            # Remove 'match' if present (for long form)
            if args and args[0] == 'match':
                args = args[1:]

            # Check for relationship query (--via/-V or --sans/-S)
            rel_splits = self._find_relationship_splits(args)
            if rel_splits:
                result_args, rel_specs = rel_splits
                # Extract --not from result args
                result_args, negated = self._extract_not_flag(result_args)

                # Parse result args (what gets returned)
                self._validate_single_matcher(result_args, "result stage")
                parsed_args = self.match_parser.parse_args(result_args)
                finalize_match_namespace(parsed_args)
                self._validate_regex_pattern(parsed_args, "result stage")

                relationships = []
                for idx, (rel_type, filter_args, is_negative, inverted) in enumerate(rel_specs, start=1):
                    if not filter_args:
                        flag = '--sans' if is_negative else '--via'
                        raise PipelineParseError(
                            f"{flag} requires a filter pattern after the relationship type",
                            code="missing_relationship_filter",
                            hint=(
                                "Add a filter stage after the relationship, "
                                f"e.g. {flag} calls -mg '*' -tf."
                            ),
                        )

                    # Parse filter args (the relationship anchor)
                    stage_label = "filter stage" if len(rel_specs) == 1 else f"filter stage {idx}"
                    self._validate_single_matcher(filter_args, stage_label)
                    filter_parsed = self.match_parser.parse_args(filter_args)
                    finalize_match_namespace(filter_parsed)
                    self._validate_regex_pattern(filter_parsed, stage_label)

                    # Merge output/format flags from filter args to result. Last one wins.
                    if filter_parsed.render_type:
                        parsed_args.render_type = filter_parsed.render_type
                    if filter_parsed.format:
                        parsed_args.format = filter_parsed.format

                    try:
                        relationships.append(build_relationship_filter(
                            rel_type, filter_parsed, is_negative, inverted=inverted,
                        ))
                    except ValueError as exc:
                        raise PipelineParseError(
                            str(exc),
                            code="invalid_relationship_filter",
                            hint=(
                                "Adjust the relationship filter stage to use supported "
                                "types and options."
                            ),
                        ) from exc

                return build_match_stage(
                    parsed_args,
                    relationship=relationships[0],
                    relationships=relationships,
                    negate_pattern=negated,
                )
            else:
                # Regular match stage — extract --not if present
                args, negated = self._extract_not_flag(args)
                self._validate_single_matcher(args, "result stage")
                parsed_args = self.match_parser.parse_args(args)
                finalize_match_namespace(parsed_args)
                self._validate_regex_pattern(parsed_args, "result stage")
                return build_match_stage(parsed_args, negate_pattern=negated)
        except (SystemExit, argparse.ArgumentError) as exc:
            raise PipelineParseError(
                f"Invalid match stage arguments: {args}",
                code="invalid_argument",
                hint=(
                    "Use one match flag (-mg, -mr, or -ms), type flags like "
                    "-tf/-tc, and supported output flags."
                ),
            ) from exc

    def _parse_stats_stage(self, args: List[str]) -> PipelineStage:
        """Parse stats stage using argparse.

        Args:
            args: Arguments for stats stage

        Returns:
            PipelineStage with StageType.STATS

        Raises:
            PipelineParseError: If parsing fails
        """
        try:
            # Remove 'stats' if present
            if args[0] == 'stats':
                args = args[1:]

            parsed_args = self.stats_parser.parse_args(args)
            return PipelineStage(StageType.STATS, parsed_args)
        except (SystemExit, argparse.ArgumentError) as exc:
            raise PipelineParseError(
                f"Invalid stats stage arguments: {args}",
                code="invalid_argument",
                hint="Use stats options such as --json or -v.",
            ) from exc

    def _create_match_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for match stage.

        A single match stage includes:
        - Match syntax: -mg, -mr, -ms (mutually exclusive)
        - Symbol types: -tc, -tf, -tm, etc. (multiple allowed, OR'd)
        - Output: -oL, -oT, -oD, etc. (mutually exclusive)
        - Format: -fa, -fm, -fh, -fp (mutually exclusive)
        - Options: -n, -I, -Q, -A, -B, -C, --theme, --nodelims

        Returns:
            ArgumentParser configured for match stage
        """
        parser = argparse.ArgumentParser(
            add_help=False,
            exit_on_error=False
        )

        # Match syntax (mutually exclusive)
        syntax_group = parser.add_mutually_exclusive_group()
        for flag in MATCH_FLAGS:
            syntax_group.add_argument(
                flag.short, flag.long,
                dest='pattern',
                metavar='PATTERN',
                action=_StoreSyntax,
                syntax=flag.suffix,
                help=flag.help
            )

        # Symbol types - allow multiple (OR'd together)
        for flag in TYPE_FLAGS:
            parser.add_argument(
                flag.short, flag.long,
                dest='symbol_types',
                action=_AppendType,
                type_value=flag.const,
                help=flag.help
            )

        # Output type (mutually exclusive)
        output_group = parser.add_mutually_exclusive_group()
        for flag in OUTPUT_FLAGS:
            output_group.add_argument(
                flag.short, flag.long,
                dest='render_type',
                action='store_const',
                const=flag.const,
                help=flag.help
            )

        # Format (mutually exclusive)
        format_group = parser.add_mutually_exclusive_group()
        for flag in FORMAT_FLAGS:
            format_group.add_argument(
                flag.short, flag.long,
                dest='format',
                action='store_const',
                const=flag.const,
                help=flag.help
            )

        # Match options
        parser.add_argument('-I', '--case-insensitive', dest='case_insensitive', action='store_true', default=False,
                          help='Case-insensitive matching (patterns are case-sensitive by default)')
        parser.add_argument('-n', '--limit', type=int, default=None,
                          help='Limit results to N matches (default: 10). Use -n 0 for all results.')
        parser.add_argument('--slice', dest='result_slice', default=None, metavar='SLICE',
                          help='Result window: 0:20 (first 20), 20:40 (results 20-39), 20: (from 20 to end). '
                               'Mutually exclusive with -n.')
        parser.add_argument('-Q', '--qualified', dest='match_qualified', action='store_true', default=False,
                          help='Match against qualified_name instead of symbol_name')

        # Context lines (for raw/formatted output)
        parser.add_argument('-A', '--after-context', dest='after_context', type=int, default=0)
        parser.add_argument('-B', '--before-context', dest='before_context', type=int, default=0)
        parser.add_argument('-C', '--context', type=int)

        # Theme
        parser.add_argument('--theme', type=str)

        # Delimiters
        parser.add_argument('--nodelims', dest='nodelims', action='store_true', default=False,
                          help='Disable delimiter headers between matches')

        # Line slice modifier (optional, combinable with any match flag)
        parser.add_argument('-mL', '--match-lines', dest='line_slice', default=None, metavar='SLICE',
                          help='Line slice: 5:10, 1:, :5, 7 (relative to matched symbol start)')

        # Temporal filters: per-stage modifiers for symbol mtime
        parser.add_argument('--newerthan', dest='newerthan', default=None, metavar='DURATION',
                          help='Filter: symbols whose file was modified within DURATION ago (e.g. 1h, 2d)')
        parser.add_argument('--olderthan', dest='olderthan', default=None, metavar='DURATION',
                          help='Filter: symbols whose file was NOT modified within DURATION (e.g. 1h, 2d)')
        parser.add_argument('--stale', dest='stale', action='store_true', default=False,
                          help='Filter --via results older than their anchor (e.g. stale tests). '
                               "Example: via --match-glob '*' --type-class "
                               "--via inherits-from --match-glob 'test_*' --type-function --stale")

        # Language and subtype filters
        parser.add_argument('--lang', dest='language_filter', default=None, metavar='LANG',
                          help='Filter by language: py/python, js/javascript, ts/typescript, md/markdown')
        parser.add_argument('--subtype', dest='symbol_subtype_filter', default=None, metavar='TYPE',
                          help='Filter by symbol subtype (e.g. interface, enum, arrow_function). '
                               'Case-sensitive; unknown values return no results.')
        parser.add_argument('--contains', dest='contains_pattern', default=None, metavar='PATTERN',
                          help='Filter matched symbols by whether their source body contains PATTERN. '
                               'Returns symbols, not grep-style line snippets.')

        return parser

    def _create_stats_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for stats stage.

        Returns:
            ArgumentParser configured for stats stage
        """
        parser = argparse.ArgumentParser(
            add_help=False,
            exit_on_error=False
        )

        parser.add_argument('-v', '--verbose', action='count', default=0)
        parser.add_argument('--json', action='store_true', default=False)

        return parser
