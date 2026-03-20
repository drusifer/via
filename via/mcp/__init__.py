"""
VIA MCP (Model Context Protocol) server package.

TLDR:
    Exposes `via mcp serve` (FastMCP stdio server) and `via mcp schema`
    (tool schema inspector). server.py runs WatchService in a background
    daemon thread and registers the via_query tool via FastMCP, routing
    args through PipelineExecutor + JsonRenderer. schema.py provides
    build_tool_schema() used by both tools/list and the schema CLI command.
    Entry points wired in via/__main__.py under the `mcp` subparser.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""
