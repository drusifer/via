"""
MatchCommand: CLI argument and help provider for 'match' subcommand.
"""
import argparse
from ..core.interfaces import ArgumentProvider, HelpProvider
from ..core.match_record import MatchRecordFactory

class MatchCommand(ArgumentProvider, HelpProvider):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        # Add the symbol type filter argument
        type_choices = list(MatchRecordFactory._RECORD_TYPES.keys())
        parser.add_argument(
            "-t",
            "--type",
            dest="type",
            choices=type_choices,
            help=f"Filter by symbol type: {', '.join(type_choices)}",
        )
        
        # Add the pattern positional argument
        parser.add_argument(
            "pattern",
            help="Pattern to match (wildcards depend on match syntax)",
        )
        
        # Add syntax flags (note: -r is reserved for render types, so regex has no short form)
        syntax_group = parser.add_mutually_exclusive_group()
        syntax_group.add_argument(
            "-g",
            "--glob",
            action="store_true",
            default=True,
            help="Use glob pattern matching (default, * and ? wildcards)",
        )
        syntax_group.add_argument(
            "--regex",
            action="store_true",
            help="Use regex pattern matching",
        )
        syntax_group.add_argument(
            "-s",
            "--sql",
            action="store_true",
            help="Use SQL LIKE pattern matching (% and _ wildcards)",
        )
        
        # Add qualifier flags
        parser.add_argument(
            "-I",
            "--case-insensitive",
            action="store_true",
            help="Case-insensitive matching",
        )
        parser.add_argument(
            "-n",
            "--limit",
            type=int,
            metavar="N",
            help="Limit results to N matches",
        )
        parser.add_argument(
            "--db",
            metavar="PATH",
            help="Database path (default: <dir>/.via/index.db)",
        )
        parser.add_argument(
            "-d",
            "--directory",
            default=".",
            help="Directory containing the index (default: current directory)",
        )
        
        # Add render type flags (mutually exclusive)
        render_group = parser.add_mutually_exclusive_group()
        render_group.add_argument(
            "-rL",
            "--list",
            dest="render_type",
            action="store_const",
            const="list",
            help="Render results as list (type:file:line:name)",
        )
        render_group.add_argument(
            "-rT",
            "--table",
            dest="render_type",
            action="store_const",
            const="table",
            help="Render results as table",
        )
        render_group.add_argument(
            "-rD",
            "--diagram",
            dest="render_type",
            action="store_const",
            const="diagram",
            help="Render results as UML diagram (classes only)",
        )
        render_group.add_argument(
            "-rU",
            "--usage",
            dest="render_type",
            action="store_const",
            const="usage",
            help="Render usage/references for results",
        )
        render_group.add_argument(
            "-rR",
            "--raw",
            dest="render_type",
            action="store_const",
            const="raw",
            help="Render as source code",
        )
        
        # Add output format flags (mutually exclusive)
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument(
            "-a",
            "--ascii",
            dest="format",
            action="store_const",
            const="ascii",
            help="Output format: ASCII (terminal with colors)",
        )
        format_group.add_argument(
            "-m",
            "--md",
            dest="format",
            action="store_const",
            const="md",
            help="Output format: Markdown",
        )
        format_group.add_argument(
            "--html",
            dest="format",
            action="store_const",
            const="html",
            help="Output format: HTML",
        )
        format_group.add_argument(
            "-p",
            "--png",
            dest="format",
            action="store_const",
            const="png",
            help="Output format: PNG image",
        )
        
        # Add context control flags
        parser.add_argument(
            "-A",
            "--after",
            dest="after",
            type=int,
            default=0,
            metavar="N",
            help="Show N lines after symbol (for raw render)",
        )
        parser.add_argument(
            "-B",
            "--before",
            dest="before",
            type=int,
            default=0,
            metavar="N",
            help="Show N lines before symbol (for raw render)",
        )
        parser.add_argument(
            "-C",
            "--context",
            dest="context",
            type=int,
            metavar="N",
            help="Show N lines before and after symbol (same as -B N -A N)",
        )

    @classmethod
    def get_help(cls) -> str:
        help_str = "Match symbols in the indexed codebase using glob, regex, or SQL LIKE patterns.\n\nSupported symbol types:\n"
        for type_name, record_cls in MatchRecordFactory._RECORD_TYPES.items():
            help_str += f"  - {type_name}: {record_cls.get_help()}\n"
        return help_str
