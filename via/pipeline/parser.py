"""
Parses raw CLI argv into an ordered list of PipelineStage objects.

TLDR:
    PipelineParser is the single entry point for turning a via command line
    into an executable pipeline. It splits argv on plain --via separators to
    produce per-stage argument segments, then uses argparse internally (via
    _StoreSyntax and _AppendType custom actions) to decode match-syntax flags
    (-mg/-mr/-ms), OR'd symbol-type flags (-tc/-tf/...), output flags, and
    format flags for each segment. Relationship queries (--via/-V or --sans/-S)
    are detected within a segment and assembled into a RelationshipFilter
    attached to the resulting PipelineStage. --not negates the match pattern.
    Raises PipelineParseError on any invalid input.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import argparse
from typing import List, Optional, Tuple

from via.core.flag_groups import (
    FORMAT_FLAGS,
    MATCH_FLAGS,
    OUTPUT_FLAGS,
    TYPE_FLAGS,
    get_match_short_flags,
    get_type_short_flags,
)
from via.core.duration import parse_duration
from via.core.relationship_types import ReferenceType
from via.pipeline.relationship_filter import RelationshipFilter
from via.pipeline.types import PipelineStage, StageType


class PipelineParseError(Exception):
    """Raised when pipeline parsing fails."""




class _StoreSyntax(argparse.Action):
    """Custom action to store both pattern and match_syntax."""

    def __init__(self, option_strings, dest, syntax='glob', **kwargs):
        self.syntax = syntax
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, 'match_syntax', self.syntax)


class _AppendType(argparse.Action):
    """Custom action to append type to a list (for OR-ing multiple types)."""

    def __init__(self, option_strings, dest, type_value=None, **kwargs):
        self.type_value = type_value
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
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

        --via followed by a valid relationship type is a relationship flag
        (kept in the current segment). --via alone is a pipeline separator.
        -V is always a relationship short form (never a separator).

        Args:
            argv: Command line arguments

        Returns:
            List of argument segments (empty segments filtered out)
        """
        value_map = ReferenceType.get_value_map()
        segments = [[]]
        i = 0
        while i < len(argv):
            arg = argv[i]
            if arg == '--via':
                # Check if next arg is a relationship type → relationship flag
                if i + 1 < len(argv) and argv[i + 1] in value_map:
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

    def _find_relationship_split(
        self, args: List[str]
    ) -> Optional[Tuple[List[str], 'ReferenceType', List[str], bool]]:
        """Find --via/-V or --sans/-S in args and split into subject/object parts.

        Args:
            args: Command line arguments for a stage

        Returns:
            Tuple of (subject_args, relationship_type, object_args, is_negative) or None

        Raises:
            PipelineParseError: If relationship type value is invalid
        """
        value_map = ReferenceType.get_value_map()
        valid_rels = ', '.join(sorted(value_map.keys()))

        for i, arg in enumerate(args):
            if arg in ('--via', '-V', '--sans', '-S'):
                is_negative = arg in ('--sans', '-S')
                if i + 1 >= len(args):
                    flag_name = '--sans' if is_negative else '--via'
                    raise PipelineParseError(
                        f"{flag_name} requires a relationship type argument.\n"
                        f"Valid: {valid_rels}"
                    )
                rel_str = args[i + 1]
                if rel_str not in value_map:
                    flag_name = '--sans' if is_negative else '--via'
                    raise PipelineParseError(
                        f"Unknown relationship type '{rel_str}'.\n"
                        f"Valid: {valid_rels}"
                    )
                rel_type = value_map[rel_str]
                subject_args = args[:i]
                object_args = args[i + 2:]
                return (subject_args, rel_type, object_args, is_negative)

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
                        "(--match-glob, --match-regex, --match-sql)"
                    )
                negated = True
            else:
                filtered.append(arg)
        return filtered, negated

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
            raise PipelineParseError("Empty pipeline stage")

        # Detect stage type from command/flags
        if args[0] == 'match' or self._is_match_stage(args):
            return self._parse_match_stage(args)
        if args[0] == 'stats':
            return self._parse_stats_stage(args)
        raise PipelineParseError(f"Unknown stage type: {args}")

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
            rel_split = self._find_relationship_split(args)
            if rel_split:
                subject_args, rel_type, object_args, is_negative = rel_split

                if not object_args:
                    flag = '--sans' if is_negative else '--via'
                    raise PipelineParseError(
                        f"{flag} requires an object pattern after the relationship type"
                    )

                # Extract --not from subject args
                subject_args, negated = self._extract_not_flag(subject_args)

                # Parse subject args
                parsed_args = self.match_parser.parse_args(subject_args)
                self._finalize_symbol_types(parsed_args)
                parsed_args.negate_pattern = negated

                # Parse object args (for pattern and types)
                object_parsed = self.match_parser.parse_args(object_args)
                self._finalize_symbol_types(object_parsed)

                # Parse result-side temporal filters from object args
                result_newerthan = None
                result_olderthan = None
                if getattr(object_parsed, 'newerthan', None):
                    result_newerthan = parse_duration(object_parsed.newerthan)
                if getattr(object_parsed, 'olderthan', None):
                    result_olderthan = parse_duration(object_parsed.olderthan)

                # --stale with --sans is not meaningful — error
                if is_negative and getattr(object_parsed, 'stale', False):
                    raise PipelineParseError(
                        "--stale cannot be combined with --sans: --sans already "
                        "selects symbols with NO relationship; --stale would be meaningless."
                    )

                # Create relationship filter
                parsed_args.relationship = RelationshipFilter(
                    relationship_type=rel_type,
                    object_pattern=object_parsed.pattern or '*',
                    object_match_syntax=getattr(object_parsed, 'match_syntax', 'glob'),
                    object_types=object_parsed.symbol_types or [],
                    is_negative=is_negative,
                    result_newerthan_seconds=result_newerthan,
                    result_olderthan_seconds=result_olderthan,
                    result_stale=getattr(object_parsed, 'stale', False),
                )

                # Merge output/format flags from object args to subject
                if object_parsed.render_type:
                    parsed_args.render_type = object_parsed.render_type
                if object_parsed.format:
                    parsed_args.format = object_parsed.format

                return PipelineStage(StageType.MATCH, parsed_args)
            else:
                # Regular match stage — extract --not if present
                args, negated = self._extract_not_flag(args)
                parsed_args = self.match_parser.parse_args(args)
                self._finalize_symbol_types(parsed_args)
                parsed_args.relationship = None
                parsed_args.negate_pattern = negated

                return PipelineStage(StageType.MATCH, parsed_args)
        except (SystemExit, argparse.ArgumentError) as exc:
            raise PipelineParseError(f"Invalid match stage arguments: {args}") from exc

    def _finalize_symbol_types(self, parsed_args) -> None:
        """Finalize symbol_types from parsed args.

        Args:
            parsed_args: Namespace from argparse
        """
        # Convert symbol_types list to single value for backward compat
        # (executor will handle the list for OR logic)
        if hasattr(parsed_args, 'symbol_types') and parsed_args.symbol_types:
            # Keep as list for OR logic, but also set symbol_type for single type
            if len(parsed_args.symbol_types) == 1:
                parsed_args.symbol_type = parsed_args.symbol_types[0]
            else:
                parsed_args.symbol_type = None  # Multiple types, use symbol_types list
        else:
            parsed_args.symbol_type = None
            parsed_args.symbol_types = []

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
            raise PipelineParseError(f"Invalid stats stage arguments: {args}") from exc

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
        parser.add_argument('-n', '--limit', type=int, default=10)
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
