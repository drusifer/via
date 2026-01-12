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
import os
import sys
from pathlib import Path
from typing import Optional

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
from .core.logging import setup_logging
from .db.store import DatabaseStore
from .parsers.registry import ParserRegistry
from .parsers.python_parser import PythonParser
from .services.indexing import IndexingService


def _create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="via",
        description="VIA - Python codebase indexing and querying tool",
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

    # Index subcommand
    index_parser = subparsers.add_parser(
        "index",
        help="Index a directory tree",
        description="Index Python files in a directory tree, respecting .gitignore rules",
    )

    index_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to index (default: current directory)",
    )

    index_parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Watch for file changes and re-index automatically (NOT IMPLEMENTED YET)",
    )

    index_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-index of all files (ignore mtime checks)",
    )

    index_parser.add_argument(
        "--exclude",
        action="append",
        metavar="PATTERN",
        help="Additional patterns to exclude (can be specified multiple times)",
    )

    index_parser.add_argument(
        "--db",
        metavar="PATH",
        help=f"Database path (default: <dir>/{DEFAULT_INDEX_DIR}/{DEFAULT_DB_NAME})",
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

            # Initialize parser registry and register Python parser
            parser_registry = ParserRegistry()
            parser_registry.register(PythonParser())

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
            print(f"  Imports:               {stats.imports}")
            print(f"  Globals:               {stats.globals}")
            print("=" * 60)

            if stats.failed_files > 0:
                print(f"\nWarning: {stats.failed_files} files failed to index", file=sys.stderr)

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user", file=sys.stderr)
        return EXIT_KEYBOARD_INTERRUPT

    except Exception as e:
        logging.exception("Indexing failed with exception")
        print(f"\nError: Indexing failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def main() -> int:
    """
    Main entry point for VIA command-line interface.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse arguments
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
    if args.command == "index":
        return _run_index_command(args)
    elif args.command is None:
        parser.print_help()
        return EXIT_SUCCESS
    else:
        print(f"Error: Unknown command: {args.command}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
