"""
VIA MCP server — FastMCP-based stdio server for codebase queries.

TLDR:
    run_mcp_server(root_dir, db_path) starts a FastMCP server over stdio.
    Registers a single tool: via_query(args: list[str]) -> list[dict].
    WatchService runs in a background daemon thread (handle_signals=False)
    so the FastMCP event loop owns stdin/stdout exclusively.
    MCP-mode logging goes to ~/.via/mcp.log to keep stdio clean.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import contextlib
import io
import logging
import threading
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from via.core.constants import EXIT_SUCCESS
from via.core.utils import strip_ansi
from via.db.store import DatabaseStore
from via.parsers.dart_parser import DartParser
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.api import ViaRunner
from via.mcp.schema import build_tool_schema
from via.pipeline.errors import PipelineParseError, QueryError
from via.renderers.json_renderer import JsonRenderer
from via.services.indexing import IndexingService
from via.services.watch import WatchService


_OUTPUT_TYPE_MAP = {
    '-oD': 'diagram', '--output-diagram': 'diagram',
    '-oR': 'raw', '--output-raw': 'raw',
    '-oF': 'formatted', '--output-formatted': 'formatted',
    '-oT': 'table', '--output-table': 'table',
    '-oL': 'list', '--output-list': 'list',
    '-oU': 'usage', '--output-usage': 'usage',
}
_OUTPUT_FLAGS = set(_OUTPUT_TYPE_MAP) | {'-oJ', '--output-json'}


def _build_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(MarkdownParser())
    registry.register(JavaScriptParser())
    registry.register(DartParser())
    return registry


def _configure_mcp_logging() -> None:
    """Route all logging to ~/.via/mcp.log so stdio stays clean."""
    log_dir = Path.home() / ".via"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "mcp.log"

    file_handler = logging.FileHandler(str(log_path))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    )

    root = logging.getLogger()
    # Remove existing handlers that could write to stdout/stderr
    root.handlers.clear()
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG)

    # Silence watchdog's internal inotify buffer — fires for every OS event
    # regardless of whether our handler acts on it. Not useful in MCP logs.
    logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)


def _mcp_error_response(error: QueryError) -> dict:
    """Return the structured MCP error response shape."""
    return {
        "output_type": "error",
        "result": [],
        "total": 0,
        "shown": 0,
        "error": error.to_dict(),
    }


def _detect_output_type(query_args: list) -> str:
    """Return MCP output_type requested by query args."""
    for arg in query_args:
        if arg in _OUTPUT_TYPE_MAP:
            return _OUTPUT_TYPE_MAP[arg]
    return 'json'


def _json_query_payload(runner: ViaRunner, args: list[str]) -> dict:
    """Run args as a JSON MCP query, ignoring requested output flags."""
    clean_args = [a for a in args if a not in _OUTPUT_FLAGS]
    results = list(runner.run_cli_args(clean_args) or [])
    dicts = [JsonRenderer._to_dict(r) for r in results]
    total = results[0].total_matches if results else 0
    return {"output_type": "json", "result": dicts, "total": total, "shown": len(dicts)}


def _diagram_fallback_payload(runner: ViaRunner, args: list[str]) -> dict:
    """Return JSON data when a requested diagram has no useful diagram content."""
    payload = _json_query_payload(runner, args)
    if payload["shown"]:
        payload["note"] = (
            "Diagram output was unavailable for these results; returning matching "
            "records as JSON."
        )
    else:
        payload["note"] = "No diagram content produced; returning empty JSON results."
    return payload


def _mcp_query_response(runner: ViaRunner, args: list[str], logger: logging.Logger) -> dict:
    """Run a VIA MCP query and return the MCP response wrapper."""
    try:
        output_type = _detect_output_type(args)
        if output_type == 'json':
            return _json_query_payload(runner, args)

        # Rendered output: capture stdout, strip ANSI
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            runner.run_cli_args(args)
        rendered = strip_ansi(buf.getvalue()).rstrip('\n')
        # Fall back to JSON while preserving results when a diagram cannot render.
        if output_type == 'diagram' and (
            not rendered.strip() or 'classDiagram' not in rendered
        ):
            return _diagram_fallback_payload(runner, args)
        return {"output_type": output_type, "result": rendered, "total": 0, "shown": 0}
    except PipelineParseError as exc:
        return _mcp_error_response(exc.to_query_error())
    except Exception as exc:
        logger.exception("via_query internal error: %s", exc)
        return _mcp_error_response(QueryError(
            code="internal_error",
            message="VIA query failed unexpectedly.",
            hint="Check the MCP server log for details.",
        ))


def run_mcp_server(
    root_dir: str,
    db_path: str,
    port: int = 7891,
    no_web: bool = False,
) -> int:
    """Start the FastMCP stdio server with WatchService in background thread.

    Args:
        root_dir: Root directory being served
        db_path: Path to the SQLite index database
        port: Web UI starting port (default 7891)
        no_web: If True, skip starting the web UI

    Returns:
        Exit code (EXIT_SUCCESS or EXIT_ERROR)
    """
    _configure_mcp_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP server for %s", root_dir)

    registry = _build_registry()

    # WatchService write connection — owns schema initialization/migration
    watch_store = DatabaseStore(db_path, root_dir)
    watch_store.connect()
    watch_store.initialize_schema()

    # MCP read-only connection — schema already initialized by watch_store
    mcp_store = DatabaseStore(db_path, root_dir)
    mcp_store.connect()
    runner = ViaRunner(mcp_store)

    indexing_svc = IndexingService(watch_store, registry)
    watch_svc = WatchService(
        indexing_service=indexing_svc,
        db_store=watch_store,
        root_dir=root_dir,
        handle_signals=False,
    )

    watch_thread = threading.Thread(target=watch_svc.start, daemon=True)
    watch_thread.start()

    # Start web UI in daemon thread (stderr — stdout is the MCP protocol stream)
    web_server = None
    if not no_web:
        from via.web import WebServer
        web_server = WebServer(port=port, db_path=db_path, index_root=root_dir)
        watch_svc.add_reindex_listener(web_server.notify_reindex)
        web_server.start()
        import sys as _sys
        print(f"Web UI: http://localhost:{web_server.port}", file=_sys.stderr)

    mcp = FastMCP("via")

    _schema = build_tool_schema()

    @mcp.tool(description=_schema["description"])
    def via_query(args: list[str]) -> dict:
        return _mcp_query_response(runner, args, logger)

    @mcp.tool(description="Query the codebase using a natural language English query. Translates the query deterministicly into a VIA pipeline command and executes it.")
    def via_ask(query: str) -> dict:
        from via.pipeline.natural_query import LarkNaturalQueryParser
        from via.pipeline.errors import PipelineParseError
        try:
            parser = LarkNaturalQueryParser()
            compiled_args = parser.parse(query)
        except PipelineParseError as exc:
            return _mcp_error_response(exc.to_query_error())
        except Exception as exc:
            logger.exception("via_ask internal error: %s", exc)
            from via.pipeline.errors import QueryError
            return _mcp_error_response(QueryError(
                code="internal_error",
                message="VIA natural query translation failed unexpectedly.",
                hint="Check the MCP server log for details.",
            ))
        return _mcp_query_response(runner, compiled_args, logger)

    try:
        mcp.run(transport="stdio")
    finally:
        if web_server:
            web_server.stop()
        watch_svc.stop()
        watch_thread.join(timeout=5)
        mcp_store.close()
        watch_store.close()
        logger.info("MCP server stopped.")

    return EXIT_SUCCESS
