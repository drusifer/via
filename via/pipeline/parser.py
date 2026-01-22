"""Pipeline parser using argparse for flag parsing."""
import argparse
from typing import List
from via.pipeline.types import StageType, PipelineStage


class PipelineParseError(Exception):
    """Raised when pipeline parsing fails."""
    pass


class PipelineParser:
    """Parse command line into pipeline stages using argparse.

    Uses separate ArgumentParser instances for each stage type (match, render, stats)
    with exit_on_error=False to prevent sys.exit() calls.
    """

    def __init__(self):
        """Initialize parsers for each stage type."""
        self.match_parser = self._create_match_parser()
        self.render_parser = self._create_render_parser()
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
        elif args[0] == 'render' or self._is_render_stage(args):
            return self._parse_render_stage(args)
        elif args[0] == 'stats':
            return self._parse_stats_stage(args)
        else:
            raise PipelineParseError(f"Unknown stage type: {args}")

    def _is_match_stage(self, args: List[str]) -> bool:
        """Check if args indicate a match stage."""
        match_flags = {'-m', '-g', '-r', '-s', '-c', '-f', '-i', '-G', '-F', '-N'}
        return any(arg in match_flags for arg in args)

    def _is_render_stage(self, args: List[str]) -> bool:
        """Check if args indicate a render stage."""
        # Check for output flags like -oL, -oT, -oD, etc.
        return any(arg.startswith('-o') and len(arg) > 2 for arg in args)

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

            # Expand combined shorthand flags (e.g., -mg -> -m -g)
            args = self._expand_combined_flags(args)

            parsed_args = self.match_parser.parse_args(args)
            return PipelineStage(StageType.MATCH, parsed_args)
        except (SystemExit, argparse.ArgumentError):
            raise PipelineParseError(f"Invalid match stage arguments: {args}")

    def _parse_render_stage(self, args: List[str]) -> PipelineStage:
        """Parse render stage using argparse.

        Args:
            args: Arguments for render stage

        Returns:
            PipelineStage with StageType.RENDER

        Raises:
            PipelineParseError: If parsing fails
        """
        try:
            # Remove 'render' if present (for long form)
            if args[0] == 'render':
                args = args[1:]

            # Expand combined shorthand flags (e.g., -rTm -> -rT -m)
            args = self._expand_combined_flags(args)

            parsed_args = self.render_parser.parse_args(args)
            return PipelineStage(StageType.RENDER, parsed_args)
        except (SystemExit, argparse.ArgumentError):
            raise PipelineParseError(f"Invalid render stage arguments: {args}")

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

    def _expand_combined_flags(self, args: List[str]) -> List[str]:
        """Expand combined shorthand flags for argparse.

        Match shortcuts:
            -mg -c '*' -> -g '*' -c (move pattern to follow -g)
            -mr -m '^foo' -> -r '^foo' -m (move pattern to follow -r)
            -ms -f 'bar%' -> -s 'bar%' -f (move pattern to follow -s)

        Render shortcuts:
            -rTm -> -rT -m (render table in markdown)
            -rDh -> -rD -h (render diagram in html)

        Args:
            args: Original arguments

        Returns:
            Arguments with combined flags expanded
        """
        expanded = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ['-mg', '-mr', '-ms']:
                # Match shorthand - need to find pattern and reorder
                # Pattern is the next non-flag argument after type flags
                syntax_flag = {'-mg': '-g', '-mr': '-r', '-ms': '-s'}[arg]

                # Find the pattern (first non-flag arg after current position)
                pattern_idx = None
                for j in range(i + 1, len(args)):
                    if not args[j].startswith('-'):
                        pattern_idx = j
                        break

                if pattern_idx is None:
                    # No pattern found, just add the syntax flag
                    expanded.append(syntax_flag)
                else:
                    # Add syntax flag and pattern together
                    expanded.append(syntax_flag)
                    expanded.append(args[pattern_idx])

                    # Add type flags between current and pattern
                    for j in range(i + 1, pattern_idx):
                        expanded.append(args[j])

                    # Skip to after pattern
                    i = pattern_idx
            elif arg.startswith('-o') and len(arg) >= 3 and not arg.startswith('--'):
                # Output shorthand: -oTm, -oDh, etc.
                if len(arg) == 3:
                    # Just output type: -oT
                    expanded.append(arg)
                elif len(arg) == 4:
                    # Output type + format: -oTm -> -oT -m
                    expanded.append(f'-o{arg[2]}')  # -oT
                    expanded.append(f'-{arg[3]}')    # -m
                else:
                    # Unknown format, keep as-is
                    expanded.append(arg)
            else:
                expanded.append(arg)
            i += 1
        return expanded

    def _create_match_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for match stage.

        Returns:
            ArgumentParser configured for match stage
        """
        parser = argparse.ArgumentParser(
            add_help=False,
            exit_on_error=False
        )

        # Symbol type (mutually exclusive via action='store_const')
        parser.add_argument('-t', '--type', dest='symbol_type',
                          choices=['class', 'method', 'function', 'import', 'global', 'filepath', 'filename'])
        parser.add_argument('-c', '--class', dest='symbol_type', action='store_const', const='class')
        parser.add_argument('-m', '--method', dest='symbol_type', action='store_const', const='method')
        parser.add_argument('-f', '--function', dest='symbol_type', action='store_const', const='function')
        parser.add_argument('-i', '--import', dest='symbol_type', action='store_const', const='import')
        parser.add_argument('-G', '--global', dest='symbol_type', action='store_const', const='global')
        parser.add_argument('-F', '--file', dest='symbol_type', action='store_const', const='filepath')
        parser.add_argument('-N', '--filename', dest='symbol_type', action='store_const', const='filename')

        # Match syntax (mutually exclusive)
        syntax_group = parser.add_mutually_exclusive_group()
        syntax_group.add_argument('-g', '--glob', dest='pattern', metavar='PATTERN')
        syntax_group.add_argument('-r', '--regex', dest='pattern', metavar='PATTERN')
        syntax_group.add_argument('-s', '--sql', dest='pattern', metavar='PATTERN')

        # Options
        parser.add_argument('-I', '--case-insensitive', dest='case_insensitive', action='store_true', default=False)
        parser.add_argument('-n', '--limit', type=int, default=10)

        return parser

    def _create_render_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for render stage.

        Returns:
            ArgumentParser configured for render stage
        """
        parser = argparse.ArgumentParser(
            add_help=False,
            exit_on_error=False
        )

        # Output type (mutually exclusive) - use -o to avoid collision with -r (regex)
        output_group = parser.add_mutually_exclusive_group()
        output_group.add_argument('-oL', '--list', dest='render_type', action='store_const', const='list')
        output_group.add_argument('-oT', '--table', dest='render_type', action='store_const', const='table')
        output_group.add_argument('-oD', '--diagram', dest='render_type', action='store_const', const='diagram')
        output_group.add_argument('-oU', '--usage', dest='render_type', action='store_const', const='usage')
        output_group.add_argument('-oR', '--raw', dest='render_type', action='store_const', const='raw')
        output_group.add_argument('-oF', '--formatted', dest='render_type', action='store_const', const='formatted')

        # Output format
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument('-a', '--ascii', dest='format', action='store_const', const='ascii')
        format_group.add_argument('-m', '--md', dest='format', action='store_const', const='md')
        format_group.add_argument('-h', '--html', dest='format', action='store_const', const='html')
        format_group.add_argument('-p', '--png', dest='format', action='store_const', const='png')

        # Context lines (for raw/formatted render)
        parser.add_argument('-A', '--after-context', dest='after_context', type=int, default=0)
        parser.add_argument('-B', '--before-context', dest='before_context', type=int, default=0)
        parser.add_argument('-C', '--context', type=int)

        # Theme
        parser.add_argument('--theme', type=str)

        # Delimiters (enabled by default for renderers that support comments)
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
