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

import logging
import threading
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from via.core.constants import EXIT_SUCCESS
from via.db.store import DatabaseStore
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParser
from via.mcp.schema import build_tool_schema
from via.renderers.json_renderer import JsonRenderer
from via.services.indexing import IndexingService
from via.services.watch import WatchService


def _build_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(MarkdownParser())
    registry.register(JavaScriptParser())
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

    # Output flags that cause the executor to render (returns None) — strip them
    _OUTPUT_FLAGS = {'-oL', '-oT', '-oD', '-oU', '-oR', '-oF', '-oJ',
                     '--output-list', '--output-table', '--output-diagram',
                     '--output-usage', '--output-raw', '--output-formatted', '--output-json'}

    _schema = build_tool_schema()

    @mcp.tool(description=_schema["description"])
    def via_query(args: list[str]) -> list[dict]:
        try:
            # Strip output-format flags — MCP always returns JSON dicts
            clean_args = [a for a in args if a not in _OUTPUT_FLAGS]
            stages = PipelineParser().parse(clean_args)
            executor = PipelineExecutor(mcp_store)
            results = list(executor.execute(stages) or [])
            return [JsonRenderer._to_dict(r) for r in results]
        except Exception as exc:
            logger.error("via_query error: %s", exc)
            return []

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
