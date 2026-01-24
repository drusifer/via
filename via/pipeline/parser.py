"""Pipeline parser using argparse for flag parsing."""
import argparse
from typing import List
from via.pipeline.types import StageType, PipelineStage
from via.core.flag_groups import (
    MATCH_FLAGS, TYPE_FLAGS, OUTPUT_FLAGS, FORMAT_FLAGS,
    get_match_short_flags, get_type_short_flags
)


class PipelineParseError(Exception):
    """Raised when pipeline parsing fails."""
    pass


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
        """Split argv into segments at each --via flag.

        Args:
            argv: Command line arguments

        Returns:
            List of argument segments (empty segments filtered out)
        """
        segments = [[]]
        for arg in argv:
            if arg == '--via':
                segments.append([])
            else:
                segments[-1].append(arg)

        # Filter out empty segments
        return [s for s in segments if s]

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
        elif args[0] == 'stats':
            return self._parse_stats_stage(args)
        else:
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
            if args[0] == 'match':
                args = args[1:]

            parsed_args = self.match_parser.parse_args(args)

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

            return PipelineStage(StageType.MATCH, parsed_args)
        except (SystemExit, argparse.ArgumentError) as e:
            raise PipelineParseError(f"Invalid match stage arguments: {args}")

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
        except (SystemExit, argparse.ArgumentError):
            raise PipelineParseError(f"Invalid stats stage arguments: {args}")

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
        parser.add_argument('-I', '--case-insensitive', dest='case_insensitive', action='store_true', default=False)
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
