"""
Entry point for the VIA CLI.

TLDR:
    Implements main(), the top-level dispatch function invoked by `python -m via`
    or the installed `via` console script. On startup it inspects argv to choose
    between two execution paths: pipeline syntax (flags like -mg, -tc trigger
    PipelineParser + PipelineExecutor) and subcommand syntax (index/i and
    stats/s dispatch to _run_index_command and _run_stats_command respectively).
    The index subcommand supports --watch (continuous re-indexing via WatchService)
    and --force (full re-index). Verbosity (-v through -vvvv) is forwarded to
    setup_logging() before any command runs.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import argparse
import logging
import sys
from pathlib import Path

from via.commands.stats import StatsCommand
from via.core.constants import (
    DEFAULT_DB_NAME,
    DEFAULT_INDEX_DIR,
    EXIT_ERROR,
    EXIT_KEYBOARD_INTERRUPT,
    EXIT_SUCCESS,
    VERBOSITY_DEBUG,
    VERBOSITY_NORMAL,
    VERBOSITY_QUIET,
    VERBOSITY_TRACE,
    VERBOSITY_VERBOSE,
    VERSION,
)
from via.core.logging import setup_logging
from via.core.utils import safe_print
from via.db.store import DatabaseStore
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParseError, PipelineParser
from via.services.indexing import IndexingService


def _build_pipeline_help() -> str:
    """Build pipeline help dynamically from flag groups.

    Uses the new flag groups for consistent prefix-based CLI:
    - Match: -mg (glob), -mr (regex), -ms (sql)
    - Type: -tc (class), -tf (function), -tm (method), etc.
    - Output: -oL (list), -oT (table), -oD (diagram), etc.
    - Format: -fa (ascii), -fm (markdown), -fh (html), -fp (png)
    - Relationship: -Vinh (inherits-from), -Vca (calls), etc.
    """
    from via.core.flag_groups import (
        FORMAT_FLAGS,
        MATCH_FLAGS,
        OUTPUT_FLAGS,
        RELATIONSHIP_FLAGS,
        TYPE_FLAGS,
    )

    match_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in MATCH_FLAGS)
    type_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in TYPE_FLAGS)
    output_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in OUTPUT_FLAGS)
    format_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in FORMAT_FLAGS)
    relationship_help = "\n".join(f"  {f.short}, {f.long:20} {f.help}" for f in RELATIONSHIP_FLAGS)

    return f"""\
Pipeline Syntax (alternative to subcommands):
  via -m<X> PATTERN -t<Y> [OPTIONS] [-o<Z>] [-f<W>]

Match Syntax Flags (-m<X>):
{match_help}

Symbol Type Flags (-t<X>):
{type_help}

Options:
  -n, --limit N         Limit results to N matches
  -I, --case-insensitive  Case-insensitive matching (all -m<X> patterns are case-sensitive by default)
  -Q, --qualified       Match against qualified_name instead of symbol_name
  --newerthan DURATION  Filter: symbols from files modified within DURATION (e.g. 1h, 2d, 1w)
  --olderthan DURATION  Filter: symbols from files NOT modified within DURATION (e.g. 1h, 2d)

Relationship Flags (-V<X> or --via <type> or --ref-type <type>):
{relationship_help}
  --ref-type TYPE       Relationship type: inherits-from, calls, imports, references, declares
  --stale               Filter: results older than their anchor (e.g. stale tests). Example: via -mg '*' -tc -Vinh -mg 'test_*' -tf --stale
  --invert, -iv         Invert relationship direction

Output Flags (-o<X>):
{output_help}

Format Flags (-f<X>):
{format_help}

Context Lines (for -oR, -oF):
  -A N                  Show N lines after match
  -B N                  Show N lines before match
  -C N                  Show N lines before and after

Examples:
  via index .                                        # Index current directory
  via -mg '*Test*' -tc                               # Classes matching *Test* (case-sensitive)
  via -mg '*test*' -tc -I                            # Classes matching *test* (case-insensitive)
  via -mg 'parse' -tf -n 10                          # First 10 functions with 'parse'
  via -mg '*' -tc -oT                                # All classes as table
  via -mg 'main' -tf -oR -C 3                        # Function source with context
  via stats                                          # Database statistics

Relationship Queries:
  via -mg 'Base' -tc -Vinh -mg '*' -tc               # Who inherits from Base?
  via -mg 'MyClass' -tc -Vinh -mg '*' -tc --invert   # What does MyClass inherit?
  via -mg 'helper' -tf -Vca -mg '*' -tf              # Who calls helper()?
  via -mg 'main' -tf -Vca -mg '*' -tf --invert       # What does main() call?
  via -mg 'typing' -Vimp -mg '*' -tF                 # Files importing typing
  via -mg 'MAX_SIZE' -tG -Vr -mg '*' -tf             # Who references MAX_SIZE?
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
    from via.commands.index import IndexCommand
    index_parser = subparsers.add_parser(
        "index",
        aliases=["i"],
        help="Index a directory tree",
        description=IndexCommand.get_help(),
    )
    IndexCommand.add_arguments(index_parser)

    # --- Stats subcommand ---
    stats_parser = subparsers.add_parser(
        "stats",
        aliases=["s"],
        help="Show database statistics",
        description=StatsCommand.get_help(),
    )
    StatsCommand.add_arguments(stats_parser)

    # --- Install / Uninstall / Status subcommands ---
    from via.commands.install import INSTALL_TARGETS
    target_choices = list(INSTALL_TARGETS.keys())

    install_parser = subparsers.add_parser("install", help="Install a VIA integration")
    install_parser.add_argument("target", choices=target_choices)
    install_parser.add_argument("--global", dest="global_install", action="store_true",
                                help="Install globally (~/.claude.json)")

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a VIA integration")
    uninstall_parser.add_argument("target", choices=target_choices)
    uninstall_parser.add_argument("--global", dest="global_install", action="store_true",
                                  help="Uninstall from global config")

    status_parser = subparsers.add_parser("status", help="Show VIA integration status")
    status_parser.add_argument("target", choices=target_choices)

    # --- MCP subcommand ---
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="MCP server commands",
        description="Commands for the VIA MCP server.",
    )
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", help="MCP sub-commands")

    # via mcp schema
    mcp_sub.add_parser(
        "schema",
        help="Print the via_query MCP tool schema as JSON",
    )

    # via mcp serve
    mcp_serve = mcp_sub.add_parser(
        "serve",
        help="Start the MCP stdio server",
    )
    mcp_serve.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to watch and serve (default: current directory)",
    )

    return parser


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


def _run_index_watch(db_path: Path, target_dir: Path, exclude_patterns: list) -> int:
    """Start index watch mode."""
    from via.services.watch import WatchService
    watch_logger = logging.getLogger('via.services.watch')
    watch_logger.setLevel(logging.INFO)
    for handler in logging.root.handlers:
        if handler.level > logging.INFO:
            handler.setLevel(logging.INFO)
    with DatabaseStore(str(db_path), str(target_dir)) as db_store:
        db_store.initialize_schema()
        parser_registry = ParserRegistry()
        parser_registry.register(PythonParser())
        parser_registry.register(MarkdownParser())
        indexing_service = IndexingService(db_store, parser_registry)
        watch_service = WatchService(
            indexing_service=indexing_service,
            db_store=db_store,
            root_dir=str(target_dir),
            exclude_patterns=exclude_patterns,
        )
        watch_service.start()
    return EXIT_SUCCESS


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

    # Handle --exclude patterns
    exclude_patterns = args.exclude or []

    # Watch mode
    if args.watch:
        return _run_index_watch(db_path, target_dir, exclude_patterns)

    if exclude_patterns:
        logging.info(f"Additional exclusion patterns: {exclude_patterns}")

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
                count = 0
                total_matches = None
                for record in result:
                    safe_print(str(record))
                    count += 1
                    if total_matches is None:
                        total_matches = record.total_matches

                # Warn when results were capped by the limit
                limit = getattr(stages[-1].args, 'limit', 0) or 0
                if limit > 0 and total_matches is not None and total_matches > limit:
                    print(
                        f"results 1-{count} of {total_matches} matches returned "
                        f"(--limit={limit}) use -n 0 for all results",
                        file=sys.stderr,
                    )

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
    if first_arg in ('index', 'i', 'stats', 's', 'mcp', 'install', 'uninstall', 'status', '--help', '-h', '--version'):
        return False

    # Verbosity flags are ambiguous - check what follows
    if first_arg in ('-v', '-vv', '-vvv', '-vvvv'):
        # Check if next arg is a subcommand
        if len(argv) > 1 and argv[1] in ('index', 'i'):
            return False
        # Otherwise treat as pipeline (could be stats verbose)
        return True

    # New flag groups: -m<X> match, -t<X> type, -o<X> output, -f<X> format
    # Check for any flag in argv that matches our flag groups
    from via.core.flag_groups import get_match_short_flags, get_type_short_flags
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


def _run_install_command(args: argparse.Namespace) -> int:
    """Dispatch via install/uninstall/status <target>."""
    from via.commands.install import INSTALL_TARGETS
    target_cls = INSTALL_TARGETS.get(args.target)
    if not target_cls:
        print(f"Error: Unknown install target: {args.target}", file=sys.stderr)
        return EXIT_ERROR

    target = target_cls(project_root=str(Path('.').resolve()))
    global_install = getattr(args, 'global_install', False)

    if args.command == "install":
        return target.install(global_install=global_install)
    elif args.command == "uninstall":
        return target.uninstall(global_install=global_install)
    else:  # status
        return target.status()


def _run_mcp_command(args: argparse.Namespace) -> int:
    """Dispatch via mcp <subcommand>."""
    mcp_cmd = getattr(args, 'mcp_command', None)

    if mcp_cmd == 'schema':
        import json
        from via.mcp.schema import build_tool_schema
        print(json.dumps(build_tool_schema(), indent=2))
        return EXIT_SUCCESS

    if mcp_cmd == 'serve':
        return _run_mcp_serve(getattr(args, 'directory', '.'))

    # No sub-command — print help
    print("Usage: via mcp {schema,serve}", file=sys.stderr)
    return EXIT_ERROR


def _run_mcp_serve(directory: str) -> int:
    """Start the FastMCP stdio server."""
    target_dir = Path(directory).resolve()
    index_dir = target_dir / DEFAULT_INDEX_DIR
    db_path = index_dir / DEFAULT_DB_NAME

    if not db_path.exists():
        print(f"Error: Index not found — run 'via index {directory}' first", file=sys.stderr)
        return EXIT_ERROR

    from via.mcp.server import run_mcp_server
    return run_mcp_server(str(target_dir), str(db_path))


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
    elif args.command in ("stats", "s"):
        return _run_stats_command(args)
    elif args.command == "mcp":
        return _run_mcp_command(args)
    elif args.command in ("install", "uninstall", "status"):
        return _run_install_command(args)
    elif args.command is None:
        parser.print_help()
        return EXIT_SUCCESS
    else:
        print(f"Error: Unknown command: {args.command}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())

