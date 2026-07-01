"""Command handler for starting the Model Context Protocol (MCP) server.

TLDR:
    Implements the 'via mcp' CLI command.
    Key class: McpCommandHandler (starts the stdio MCP server using McpServer).
    Role: Model Context Protocol command handler. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
import argparse
import sys

from .base import CommandHandlerABC
from ..core.constants import EXIT_ERROR, EXIT_SUCCESS


class McpCommandHandler(CommandHandlerABC):
    """Handler for MCP server commands."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        mcp_sub = parser.add_subparsers(dest="mcp_command", help="MCP sub-commands")

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
        mcp_serve.add_argument(
            "--port",
            type=int,
            default=7891,
            metavar="PORT",
            help="Web UI port (default: 7891)",
        )
        mcp_serve.add_argument(
            "--no-web",
            action="store_true",
            help="Disable the web UI",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Manage and start the VIA MCP server"

    def run(self, args: argparse.Namespace) -> int:
        if args.mcp_command == "schema":
            import json
            from via.mcp.schema import build_tool_schema
            print(json.dumps(build_tool_schema(), indent=2))
            return EXIT_SUCCESS
        elif args.mcp_command == "serve":
            return self._run_mcp_serve(
                directory=args.directory,
                port=args.port,
                no_web=args.no_web,
            )
        else:
            print("Error: mcp requires a subcommand", file=sys.stderr)
            return EXIT_ERROR

    def _run_mcp_serve(self, directory: str, port: int = 7891, no_web: bool = False) -> int:
        """Start the MCP server."""
        from pathlib import Path
        from via.core.constants import DEFAULT_INDEX_DIR, DEFAULT_DB_NAME
        from via.mcp.server import run_mcp_server
        target_dir = Path(directory).resolve()
        index_dir = target_dir / DEFAULT_INDEX_DIR
        index_dir.mkdir(exist_ok=True)
        db_path = index_dir / DEFAULT_DB_NAME
        try:
            return run_mcp_server(
                root_dir=str(target_dir),
                db_path=str(db_path),
                port=port,
                no_web=no_web,
            )
        except Exception as e:
            print(f"Error starting MCP server: {e}", file=sys.stderr)
            return EXIT_ERROR
