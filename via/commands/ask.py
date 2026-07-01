"""Command handler for natural language search queries.

TLDR:
    Implements the 'via ask' / 'via q' CLI command.
    Key class: AskCommandHandler (translates natural language to standard via args
    using LarkNaturalQueryParser, then executes the compiled pipeline).
    Role: Natural language query handler. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
import argparse
import sys
from pathlib import Path

from .base import CommandHandlerABC
from ..core.constants import EXIT_ERROR, EXIT_SUCCESS


class AskCommandHandler(CommandHandlerABC):
    """Handler for natural language query command."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "query",
            help="Natural language query string",
        )
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Print the compiled VIA CLI arguments and exit",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Query the codebase using natural language"

    def run(self, args: argparse.Namespace) -> int:
        from via.pipeline.natural_query import LarkNaturalQueryParser
        from via.pipeline.errors import PipelineParseError
        from via.__main__ import _run_pipeline_command

        try:
            parser = LarkNaturalQueryParser()
            compiled_args = parser.parse(args.query)
        except PipelineParseError as e:
            print(f"PipelineParseError: {e}", file=sys.stderr)
            return EXIT_ERROR
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return EXIT_ERROR

        if args.dry_run:
            # Double quote arguments containing wildcards for shell safety
            quoted_args = [f'"{t}"' if any(c in t for c in "*?[]'^$()") else t for t in compiled_args]
            command = " ".join(["via"] + quoted_args)
            print(command)
            return EXIT_SUCCESS

        return _run_pipeline_command(compiled_args)


# Keep legacy alias/names for consistency
AskCommand = AskCommandHandler
