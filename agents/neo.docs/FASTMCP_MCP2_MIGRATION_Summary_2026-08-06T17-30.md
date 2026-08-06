# MCP 2 Migration Summary — 2026-08-06 17:30

## Problem

`pyproject.toml` allowed MCP 2.0, but `via/mcp/server.py` imported the removed
MCP 1 path `mcp.server.fastmcp.FastMCP`. Pytest therefore failed during
collection with `ModuleNotFoundError`.

## Fix

- Raised the dependency floor to `mcp>=2.0` and VIA's Python floor to 3.10,
  matching MCP 2's runtime requirement.
- Migrated the server to `from mcp.server import MCPServer`.
- Preserved stdio transport and tool decorators, which remain supported by
  MCPServer 2.0.
- Extracted `_build_mcp_app()` so tool registration can be tested without
  starting watch, web, or stdio services.
- Added a regression test asserting an MCPServer instance registers both
  `via_query` and `via_ask`.

## Verification

- `make -f Makefile.prj test FILE='tests/unit/test_sprint22_c1.py tests/unit/test_sprint23_c3.py tests/unit/test_sprint25_c1.py' V=-v`
  — 17 passed.
- `make -f Makefile.prj lint-fast V=-v` reached Ruff but failed on five
  pre-existing findings in `via/commands/ask.py`,
  `via/pipeline/natural_query.py`, and `via/pipeline/stage_builder.py`.
- `git diff --check` passed.
