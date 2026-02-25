"""
IndexCommand: CLI argument and help provider for 'index' subcommand.
"""
import argparse

from ..core.interfaces import ArgumentProvider, HelpProvider


class IndexCommand(ArgumentProvider, HelpProvider):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "directory",
            nargs="?",
            default=".",
            help="Directory to index (default: current directory)",
        )
        parser.add_argument(
            "-w",
            "--watch",
            action="store_true",
            help="Watch for file changes and re-index automatically (NOT IMPLEMENTED YET)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-index of all files (ignore mtime checks)",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            metavar="PATTERN",
            help="Additional patterns to exclude (can be specified multiple times)",
        )
        parser.add_argument(
            "--db",
            metavar="PATH",
            help="Database path (default: <dir>/.via/index.db)",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Index a directory tree, respecting .gitignore rules."
