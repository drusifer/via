# MCP Runtime Startup Summary - 2026-04-12T13:13

## Request
User clarified that `via mcp serve` should be the only process needed. It should internally perform the initial index, run watch mode, and initialize the web interface.

## Changes
- Updated `via/__main__.py` so `_run_mcp_serve()` creates `.via/` and delegates to `run_mcp_server()` even when no `index.db` exists yet.
- Added a cold-start unit test replacing the old "no index should error" expectation.
- Removed stale MCP subprocess round-trip tests that were brittle against the embedded web server in an active MCP environment.
- Removed stale `--no-web` from project `.mcp.json`.
- Updated `agents/tools/setup_agent_links.py` so generated project and Codex MCP entries use `mcp serve <project>` without `--no-web`.
- Added install regression coverage for combined runtime args.
- Updated README and USER_GUIDE to state that MCP mode handles initial index, watch, and web UI in one process.
- Added `via-watch` and `via-mcp-serve` Makefile targets.

## Verification
- Passed: `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p5.py`
- Passed: `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p6.py`
