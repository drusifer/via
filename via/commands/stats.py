"""Command handler for displaying database statistics.

TLDR:
    Implements the 'via stats' CLI command.
    Key class: StatsCommand (gathers record counts, language breakdowns, and
    indexing details from DatabaseStore, outputting as text or JSON).
    Role: Database statistics reporter. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Any, Dict

from .base import CommandHandlerABC
from ..core.constants import DEFAULT_INDEX_DIR, DEFAULT_DB_NAME, EXIT_ERROR, EXIT_SUCCESS
from ..db.store import DatabaseStore


class StatsCommand(CommandHandlerABC):
    """Display database statistics."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        """Register arguments for stats subcommand."""
        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (-v for type breakdown, -vv for top files)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output as JSON",
        )
        parser.add_argument(
            "-d",
            "--directory",
            default=".",
            help="Directory containing the index (default: current directory)",
        )
        parser.add_argument(
            "--db",
            metavar="PATH",
            help="Database path (default: <dir>/.via/index.db)",
        )

    @classmethod
    def get_help(cls) -> str:
        """Return help string for stats subcommand."""
        return "Display statistics about the indexed codebase"

    def __init__(self, db_store=None):
        """Initialize with database store.

        Args:
            db_store: DatabaseStore instance (optional, resolved in run if None)
        """
        self.db = db_store

    def run(self, args: argparse.Namespace) -> int:
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
                self.db = db_store
                result = self.execute(
                    verbose=args.verbose,
                    as_json=args.json
                )
                print(result)

            return EXIT_SUCCESS

        except Exception as e:
            logging.exception("Stats command failed with exception")
            print(f"\nError: Stats failed: {e}", file=sys.stderr)
            return EXIT_ERROR

    def execute(
        self,
        verbose: int = 0,
        as_json: bool = False
    ) -> str:
        """Execute stats command.

        Args:
            verbose: 0 = summary, 1 = breakdown, 2 = detailed
            as_json: Output as JSON instead of text

        Returns:
            Formatted stats string
        """
        stats = self._gather_stats(verbose)

        if as_json:
            return json.dumps(stats, indent=2)

        return self._format_stats(stats, verbose)

    def _gather_stats(self, verbose: int) -> Dict[str, Any]:
        """Gather statistics from database.

        Args:
            verbose: Verbosity level

        Returns:
            Dict with statistics
        """
        stats: Dict[str, Any] = {}
        # Basic counts
        stats['total_symbols'] = self.db.count_symbols()
        stats['total_files'] = self.db.count_files()
        by_type = self.db.count_by_type()
        # Always include markdown header count
        stats['headers'] = by_type.get('header', 0)
        stats['functions'] = by_type.get('function', 0)
        stats['classes'] = by_type.get('class', 0)
        stats['methods'] = by_type.get('method', 0)
        stats['imports'] = by_type.get('import', 0)
        stats['globals'] = by_type.get('global', 0)
        if verbose >= 1:
            stats['by_type'] = by_type
        if verbose >= 2:
            stats['top_files'] = self.db.top_files_by_symbols(10)
        return stats

    def _format_stats(self, stats: Dict[str, Any], verbose: int) -> str:
        """Format stats as human-readable text.

        Args:
            stats: Statistics dictionary
            verbose: Verbosity level

        Returns:
            Formatted string
        """
        lines = []

        lines.append(f"Total symbols: {stats['total_symbols']}")
        lines.append(f"Total files: {stats['total_files']}")
        lines.append(f"Functions:     {stats['functions']}")
        lines.append(f"Classes:       {stats['classes']}")
        lines.append(f"Methods:       {stats['methods']}")
        lines.append(f"Imports:       {stats['imports']}")
        lines.append(f"Globals:       {stats['globals']}")
        lines.append(f"Headers:       {stats['headers']}")
        if verbose >= 1 and 'by_type' in stats:
            lines.append("")
            lines.append("By type:")
            for stype, count in stats['by_type'].items():
                lines.append(f"  {stype}: {count}")
        if verbose >= 2 and 'top_files' in stats:
            lines.append("")
            lines.append("Top files by symbol count:")
            for file_path, count in stats['top_files']:
                lines.append(f"  {count:4d}  {file_path}")
        return '\n'.join(lines)


# Keep legacy alias for backward compatibility
StatsCommandHandler = StatsCommand
