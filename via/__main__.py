"""
Entry point for VIA CLI.

TLDR:
    Provides main() entry point for the via command-line tool. Handles argument
    parsing and dispatches to subcommands (index, query, render). Supports
    verbosity levels (-v through -vvvv), watch mode, and force re-indexing.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import argparse
import logging
import sys
from pathlib import Path


from .core.constants import (
    VERSION,
    DEFAULT_INDEX_DIR,
    DEFAULT_DB_NAME,
    VERBOSITY_QUIET,
    VERBOSITY_NORMAL,
    VERBOSITY_VERBOSE,
    VERBOSITY_DEBUG,
    VERBOSITY_TRACE,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_KEYBOARD_INTERRUPT,
)
from .core.utils import safe_print
from .core.logging import setup_logging
from .core.types import SymbolType, MatchOp
from .db.store import DatabaseStore
from .parsers.registry import ParserRegistry
from .parsers.python_parser import PythonParser
from .parsers.markdown_parser import MarkdownParser
from .commands.stats import StatsCommand
from .services.indexing import IndexingService
from .pipeline.parser import PipelineParser, PipelineParseError
from .pipeline.executor import PipelineExecutor


def _build_pipeline_help() -> str:
    """Build pipeline help dynamically from flag groups.

    Uses the new flag groups for consistent prefix-based CLI:
    - Match: -mg (glob), -mr (regex), -ms (sql)
    - Type: -tc (class), -tf (function), -tm (method), etc.
    - Output: -oL (list), -oT (table), -oD (diagram), etc.
    - Format: -fa (ascii), -fm (markdown), -fh (html), -fp (png)
    """
    from .core.flag_groups import MATCH_FLAGS, TYPE_FLAGS, OUTPUT_FLAGS, FORMAT_FLAGS

    match_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in MATCH_FLAGS)
    type_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in TYPE_FLAGS)
    output_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in OUTPUT_FLAGS)
    format_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in FORMAT_FLAGS)

    return f"""\
Pipeline Syntax (alternative to subcommands):
  via -m<X> PATTERN -t<Y> [OPTIONS] [--via -o<Z> -f<W>]

Match Syntax Flags (-m<X>):
{match_help}

Symbol Type Flags (-t<X>):
{type_help}

Options:
  -n, --limit N         Limit results to N matches
  -I, --case-insensitive  Case-insensitive matching
  -Q, --qualified       Match against qualified_name instead of symbol_name

Output Flags (after --via, -o<X>):
{output_help}

Format Flags (-f<X>):
{format_help}

Context Lines (for -oR, -oF):
  -A N                  Show N lines after match
  -B N                  Show N lines before match
  -C N                  Show N lines before and after

Examples:
  via -mg '*Test*' -tc              # Classes matching *Test*
  via -mg 'parse' -tf -n 10         # First 10 functions with 'parse'
  via -mg '*' -tc --via -oD -fm     # Class diagram in Markdown
  via -mr '^test_.*' -tf --via -oU  # Find usages of test functions
  via -mg '*Install*' -tH           # Headers containing 'Install'
  via stats                         # Show database statistics
"""


def _create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="via",
        description="VIA - Python codebase indexing and querying tool",
        epilog=_build_pipeline_help(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"via {VERSION}",
    )

    # Verbosity flags
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="Increase verbosity (-v, -vv, -vvv, -vvvv for more detail)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Index subcommand ---
    from .commands.index import IndexCommand
    index_parser = subparsers.add_parser(
        "index",
        aliases=["i"],
        help="Index a directory tree",
        description=IndexCommand.get_help(),
    )
    IndexCommand.add_arguments(index_parser)

    # --- Match subcommand ---
    from .commands.match import MatchCommand
    match_parser = subparsers.add_parser(
        "match",
        aliases=["m"],
        help="Search indexed code using pattern matching",
        description=MatchCommand.get_help(),
    )
    MatchCommand.add_arguments(match_parser)

    # --- Stats subcommand ---
    from .commands.stats import StatsCommand
    stats_parser = subparsers.add_parser(
        "stats",
        aliases=["s"],
        help="Show database statistics",
        description=StatsCommand.get_help(),
    )
    StatsCommand.add_arguments(stats_parser)

    return parser


def _determine_match_op(args: argparse.Namespace) -> MatchOp:
    """Determine match operator from command-line flags.

    Args:
        args: Parsed command-line arguments

    Returns:
        MatchOp enum value
    """
    if args.regex:
        return MatchOp.REGEXP
    if args.sql:
        return MatchOp.LIKE
    return MatchOp.GLOB


def _progress_callback(message: str, current: int, total: int) -> None:
    """
    Simple progress callback that prints to stdout.

    Args:
        message: Progress message
        current: Current item number
        total: Total items
    """
    if total > 0:
        percent = (current / total) * 100
        print(f"\r{message}: {current}/{total} ({percent:.1f}%)", end="", flush=True)
    else:
        print(f"\r{message}: {current}", end="", flush=True)


def _run_index_command(args: argparse.Namespace) -> int:
    """
    Execute the index command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    # Resolve directory
    target_dir = Path(args.directory).resolve()

    if not target_dir.exists():
        print(f"Error: Directory does not exist: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    if not target_dir.is_dir():
        print(f"Error: Not a directory: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    # Determine database path
    if args.db:
        db_path = Path(args.db)
    else:
        index_dir = target_dir / DEFAULT_INDEX_DIR
        index_dir.mkdir(exist_ok=True)
        db_path = index_dir / DEFAULT_DB_NAME

    logging.info(f"Indexing directory: {target_dir}")
    logging.info(f"Database path: {db_path}")

    # Check for watch mode (not implemented yet)
    if args.watch:
        print("Error: Watch mode (-w) is not implemented yet", file=sys.stderr)
        return EXIT_ERROR

    # TODO: Handle --exclude patterns (add to FileDiscovery)
    if args.exclude:
        logging.info(f"Additional exclusion patterns: {args.exclude}")
        print("Warning: --exclude patterns not fully implemented yet", file=sys.stderr)

    try:
        # Initialize database with context manager
        with DatabaseStore(str(db_path), str(target_dir)) as db_store:
            # Initialize schema
            db_store.initialize_schema()

            # Initialize parser registry and register parsers
            parser_registry = ParserRegistry()
            parser_registry.register(PythonParser())
            parser_registry.register(MarkdownParser())

            # Initialize indexing service
            indexing_service = IndexingService(db_store, parser_registry)

            # Run indexing
            print(f"Indexing {target_dir}...")
            stats = indexing_service.index(
                str(target_dir),
                force=args.force,
                progress_callback=_progress_callback,
            )

            # Print newline after progress
            print()

            # Print summary
            print("\n" + "=" * 60)
            print("INDEXING COMPLETE")
            print("=" * 60)
            print(f"Total files discovered:  {stats.total_files}")
            print(f"Files indexed:           {stats.indexed_files}")
            print(f"Files skipped:           {stats.skipped_files}")
            print(f"Oversized files:         {stats.oversized_files}")
            print(f"Failed files:            {stats.failed_files}")
            print(f"Duration:                {stats.duration_seconds:.2f}s")
            print()
            print(f"Entities extracted:")
            print(f"  Functions:             {stats.functions}")
            print(f"  Classes:               {stats.classes}")
            print(f"  Methods:               {getattr(stats, 'methods', 0)}")
            print(f"  Imports:               {stats.imports}")
            print(f"  Globals:               {stats.globals}")
            print(f"  Headers:               {getattr(stats, 'headers', 0)}")
            print("=" * 60)

            if stats.failed_files > 0:
                print(f"\nWarning: {stats.failed_files} files failed to index", file=sys.stderr)

            # After indexing, run stats command for normalized output
            from via.commands.stats import StatsCommand
            print("\nVIA STATS (normalized):")
            stats_cmd = StatsCommand(db_store)
            print(stats_cmd.execute(verbose=0, as_json=False))

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user", file=sys.stderr)
        return EXIT_KEYBOARD_INTERRUPT

    except Exception as e:
        logging.exception("Indexing failed with exception")
        print(f"\nError: Indexing failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def _run_match_command(args: argparse.Namespace) -> int:
    """
    Execute the match command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    # Resolve directory
    target_dir = Path(args.directory).resolve()

    if not target_dir.exists():
        print(f"Error: Directory does not exist: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    # Determine database path
    if args.db:
        db_path = Path(args.db)
    else:
        index_dir = target_dir / DEFAULT_INDEX_DIR
        db_path = index_dir / DEFAULT_DB_NAME

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        print(f"Run 'via index' first to create the index.", file=sys.stderr)
        return EXIT_ERROR

    # Determine match operator from flags
    match_op = _determine_match_op(args)

    # Parse symbol type
    try:
        symbol_type = SymbolType[args.type.upper()]
    except KeyError:
        print(f"Error: Invalid symbol type: {args.type}", file=sys.stderr)
        return EXIT_ERROR

    try:
        # Open database
        with DatabaseStore(str(db_path), str(target_dir)) as db_store:
            # Execute match
            results = db_store.match(
                symbol_type=symbol_type,
                match_op=match_op,
                pattern=args.pattern,
                case_sensitive=not args.case_insensitive,
                limit=args.limit,
            )

            # Stream results
            count = 0
            for result in results:
                print(result)
                count += 1

            # Log count if verbose
            if count == 0:
                logging.info("No matches found")
            else:
                logging.info(f"Found {count} matches")

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user", file=sys.stderr)
        return EXIT_KEYBOARD_INTERRUPT

    except Exception as e:
        logging.exception("Match command failed with exception")
        print(f"\nError: Match failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def _run_stats_command(args: argparse.Namespace) -> int:
    """
    Execute the stats command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code
    """
    # Resolve directory
    target_dir = Path(args.directory).resolve()

    if not target_dir.exists():
        print(f"Error: Directory does not exist: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    # Determine database path
    if args.db:
        db_path = Path(args.db)
    else:
        index_dir = target_dir / DEFAULT_INDEX_DIR
        db_path = index_dir / DEFAULT_DB_NAME

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        print(f"Run 'via index' first to create the index.", file=sys.stderr)
        return EXIT_ERROR

    try:
        with DatabaseStore(str(db_path), str(target_dir)) as db_store:
            cmd = StatsCommand(db_store)
            result = cmd.execute(
                verbose=args.verbose,
                as_json=args.json
            )
            print(result)

        return EXIT_SUCCESS

    except Exception as e:
        logging.exception("Stats command failed with exception")
        print(f"\nError: Stats failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def _run_pipeline_command(argv: list, directory: str = ".") -> int:
    """
    Execute a pipeline command.

    Args:
        argv: Command line arguments for the pipeline
        directory: Working directory for database lookup

    Returns:
        Exit code
    """
    # Resolve directory
    target_dir = Path(directory).resolve()

    # Determine database path
    index_dir = target_dir / DEFAULT_INDEX_DIR
    db_path = index_dir / DEFAULT_DB_NAME

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        print(f"Run 'via index' first to create the index.", file=sys.stderr)
        return EXIT_ERROR

    try:
        # Parse pipeline stages
        pipeline_parser = PipelineParser()
        stages = pipeline_parser.parse(argv)

        if not stages:
            print("Error: No pipeline stages specified", file=sys.stderr)
            return EXIT_ERROR

        # Open database and execute pipeline
        with DatabaseStore(str(db_path), str(target_dir)) as db_store:
            executor = PipelineExecutor(db_store)
            result = executor.execute(stages)

            # If executor returns iterator (no render stage), print results
            if result is not None:
                for record in result:
                    safe_print(str(record))

        return EXIT_SUCCESS

    except PipelineParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        return EXIT_ERROR

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user", file=sys.stderr)
        return EXIT_KEYBOARD_INTERRUPT

    except Exception as e:
        logging.exception("Pipeline execution failed")
        print(f"\nError: Pipeline failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def _is_pipeline_syntax(argv: list) -> bool:
    """
    Check if argv uses pipeline syntax (vs subcommand syntax).

    Pipeline syntax starts with flags like -mg, -tc, -tm, etc.
    Subcommand syntax starts with 'index', 'match', etc.

    Args:
        argv: Command line arguments (without program name)

    Returns:
        True if pipeline syntax detected
    """
    if not argv:
        return False

    first_arg = argv[0]

    # Known subcommands use subcommand syntax
    if first_arg in ('index', 'match', 'm', 'stats', '--help', '-h', '--version'):
        return False

    # Verbosity flags are ambiguous - check what follows
    if first_arg in ('-v', '-vv', '-vvv', '-vvvv'):
        # Check if next arg is a subcommand
        if len(argv) > 1 and argv[1] in ('index', 'match', 'm'):
            return False
        # Otherwise treat as pipeline (could be stats verbose)
        return True

    # New flag groups: -m<X> match, -t<X> type, -o<X> output, -f<X> format
    # Check for any flag in argv that matches our flag groups
    from .core.flag_groups import get_match_short_flags, get_type_short_flags
    match_flags = get_match_short_flags()  # {'-mg', '-mr', '-ms'}
    type_flags = get_type_short_flags()    # {'-tc', '-tf', '-tm', ...}

    for arg in argv:
        if arg in match_flags or arg in type_flags:
            return True
        # Also check long forms
        if arg.startswith('--match-') or arg.startswith('--type-'):
            return True

    # Stats command can also be pipeline
    if first_arg == 'stats':
        return True

    return False


def main() -> int:
    """
    Main entry point for VIA command-line interface.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    argv = sys.argv[1:]

    # Check if using pipeline syntax
    if _is_pipeline_syntax(argv):
        return _run_pipeline_command(argv)

    # Otherwise use subcommand syntax
    parser = _create_parser()
    args = parser.parse_args()

    # Map verbosity count to levels
    verbosity_map = {
        0: VERBOSITY_QUIET,
        1: VERBOSITY_NORMAL,
        2: VERBOSITY_VERBOSE,
        3: VERBOSITY_DEBUG,
        4: VERBOSITY_TRACE,
    }
    verbosity = verbosity_map.get(args.verbosity, VERBOSITY_TRACE)

    # Setup logging
    setup_logging(verbosity)

    # Dispatch to subcommand
    if args.command in ("index", "i"):
        return _run_index_command(args)
    elif args.command in ("match", "m"):
        return _run_match_command(args)
    elif args.command in ("stats", "s"):
        return _run_stats_command(args)
    elif args.command is None:
        parser.print_help()
        return EXIT_SUCCESS
    else:
        print(f"Error: Unknown command: {args.command}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
