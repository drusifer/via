# Neo Current Task

## Task: Sprint 7 — MCP Mode
**Status**: COMPLETE
**Date**: 2026-03-20

## What was built

### P1 — JsonRenderer
- `via/renderers/json_renderer.py` — `JsonRenderer` with `_to_dict()` static method
- `RenderType.JSON` added to enum
- `supports_render_type` refactored: base class handles JSON universally, subclasses implement `_supports_render_type`
- `-oJ` / `--output-json` flag added to `OUTPUT_FLAGS`
- `RendererFactory` registers `JsonRenderer`

### P2 — DB Correctness
- `DatabaseStore.connect()` now enables WAL mode (`PRAGMA journal_mode=WAL`)
- `DatabaseStore.delete_file_completely(path)` — atomic triad in single transaction
- `IndexingService.reindex_file(file_info)` — public method wrapping delete+index

### P3 — WatchService Logging Cleanup
- `output: IO` parameter removed from `WatchService.__init__()`
- `handle_signals: bool = True` parameter added
- All `print()` calls replaced with `logger.info()`/`logger.debug()`
- `_reindex_file` calls `indexing_service.reindex_file()` (not `_index_file`)
- `_remove_file` calls `db_store.delete_file_completely()` (not 3 separate calls)

### P4 — MCP Schema
- `via/mcp/__init__.py` created
- `via/mcp/schema.py` — `build_tool_schema()` with 10 examples
- `via mcp schema` CLI command added

### P5 — MCP Serve
- `mcp>=1.26` added to `pyproject.toml` dependencies
- `via/mcp/server.py` — `run_mcp_server(root_dir, db_path)` using FastMCP
- `via mcp serve [directory]` CLI command added
- Output flags stripped from `via_query` args (MCP always returns dicts)

### P6 — Install / Status
- `via/commands/install.py` — `InstallTarget` ABC + `McpInstallTarget` + `INSTALL_TARGETS` registry
- `via install mcp`, `via uninstall mcp`, `via status mcp` CLI commands added

### P7 — UAT
- `tests/uat/test_sprint7_uat.py` — 10 UAT tests, all passing

## Test Results
- 794 passed, 0 failed (was 713 at Sprint 6 start, +81 new tests)

## Next Sprint
- Sprint 8: Async queue for DB (TD-S7-1), lighter MCP transport option (TD-S7-2)
