"""
CLI argument and help provider for the 'index' subcommand.

TLDR:
    Defines IndexCommand, which implements ArgumentProvider and HelpProvider
    for the 'via index' subcommand. Registers the directory positional
    argument plus --watch, --force, --exclude, and --db flags. No indexing
    logic lives here; this class is purely the argparse glue consumed by the
    CLI dispatcher.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
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
            help="Watch for file changes and re-index automatically",
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
        parser.add_argument(
            "--port",
            type=int,
            default=7891,
            metavar="PORT",
            help="Web UI port when using --watch (default: 7891)",
        )
        parser.add_argument(
            "--no-web",
            action="store_true",
            help="Disable the web UI when using --watch",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Index a directory tree, respecting .gitignore rules."
