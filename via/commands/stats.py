"""
Stats command for database statistics.

TLDR:
    Provides statistics about the VIA index database including symbol counts,
    file counts, and breakdowns by type. Supports verbose mode and JSON output.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import json
import argparse
from typing import Dict, Any, Optional
from ..core.interfaces import ArgumentProvider, HelpProvider


class StatsCommand(ArgumentProvider, HelpProvider):
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

    def __init__(self, db_store):
        """Initialize with database store.

        Args:
            db_store: DatabaseStore instance
        """
        self.db = db_store

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
