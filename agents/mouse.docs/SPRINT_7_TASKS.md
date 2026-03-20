# Sprint 7 Task Breakdown — MCP Mode

**Scrum Master**: Mouse
**Date**: 2026-03-20
**Sprint Points**: 10 (3 user stories)
**Architecture**: `agents/morpheus.docs/SPRINT_7_ARCHITECTURE.md` ✅ APPROVED
**Stories**: `agents/cypher.docs/SPRINT_7_USER_STORIES.md` ✅ READY

---

## Sprint Goal

Ship `via mcp serve` — an always-current MCP server that Claude Code can use to query the codebase index without Bash tool access. By end of sprint: `via install mcp` + `via mcp serve` works end-to-end in a real project.

---

## Phase Summary

| Phase | Name | Owner | Gates | Pts |
|-------|------|-------|-------|-----|
| P1 | JsonRenderer | Neo | -oJ CLI works, unit tests pass | — |
| P2 | DB Correctness (TD-1) | Neo | WAL on, reindex_file public+transactional | — |
| P3 | WatchService Cleanup | Neo | -w still works, logging replaces print | — |
| P4 | MCP Schema | Neo | `via mcp schema` outputs valid JSON | — |
| P5 | MCP Serve | Neo | stdio round-trip test passes | Story 1 |
| P6 | Install / Status | Neo | `via install mcp` creates .mcp.json | Story 2+3 |
| P7 | UAT | Trin | All tests pass, Claude Code integration verified | 10pts done |

---

## Phase 1 — JsonRenderer (Foundation)

**Goal**: New `-oJ` output flag producing a JSON array. Self-contained, fully testable in isolation.

### Tasks

- [x] **P1-1** Add `RenderType.JSON = 'json'` to `RenderType` enum in `via/core/match_record.py`
- [x] **P1-2** Refactor `supports_render_type()` in `MatchRecord` base class:
  - Base class returns `True` for `RenderType.JSON` (universal)
  - Abstract method renamed to `_supports_render_type()` for type-specific checks
  - All subclasses: rename method accordingly (no logic change)
- [x] **P1-3** Create `via/renderers/json_renderer.py` — `JsonRenderer` with `_to_dict()` static method
- [x] **P1-4** Add `-oJ` / `--output-json` to `OUTPUT_FLAGS` in `via/core/flag_groups.py`
- [x] **P1-5** Register `JsonRenderer` in `via/renderers/factory.py`
- [x] **P1-6** Unit tests: `JsonRenderer` output is valid JSON, all fields present, None serializes as null
- [x] **P1-7** Integration smoke test: `via -mg '*' -tc -oJ` returns JSON array

**Gate**: `via -mg '*' -tc -oJ` works on CLI. All new tests pass. Existing tests unbroken.

---

## Phase 2 — DB Correctness (TD-1)

**Goal**: Make concurrent watch+query safe before MCP serve ships. WatchService is the only writer; WAL handles read concurrency.

### Tasks

- [x] **P2-1** Enable WAL mode in `DatabaseStore.connect()`: `PRAGMA journal_mode=WAL`
- [x] **P2-2** Add `DatabaseStore.delete_file_completely(path)` — atomic triad: delete symbols, relationships, file record in one transaction
- [x] **P2-3** Add `IndexingService.reindex_file(path)` — public method, wraps `_index_file` in a transaction
- [x] **P2-4** Update `WatchService._reindex_file()` to call `indexing_service.reindex_file()` (not private `_index_file`)
- [x] **P2-5** Update `WatchService._remove_file()` to call `db_store.delete_file_completely()` (not three separate calls)
- [x] **P2-6** Unit tests: `delete_file_completely` removes all records atomically; `reindex_file` is idempotent
- [x] **P2-7** Regression: `via index -w` still works correctly after these changes

**Gate**: Watch mode still passes all existing tests. No regressions. WAL confirmed in schema test.

---

## Phase 3 — WatchService Logging Cleanup

**Goal**: Remove the `output: IO` parameter; route all watch feedback through Python logging so MCP mode can silence or redirect it cleanly.

### Tasks

- [x] **P3-1** Replace all `print(f"...", file=self.output)` in `WatchService` with `logger.info()` / `logger.debug()`
- [x] **P3-2** Remove `output: IO` parameter from `WatchService.__init__()` (and all callers)
- [x] **P3-3** Add `handle_signals: bool = True` parameter to `WatchService.__init__()`; skip SIGINT setup when `False`
- [x] **P3-4** Update `_run_index_command()` in `__main__.py` — remove `output=` kwarg from WatchService construction
- [x] **P3-5** Regression: `via index -w` still runs and prints watch events correctly (via logging → stderr by default)

**Gate**: `via index -w` behaviour unchanged from user perspective. No `output=` param anywhere.

---

## Phase 4 — MCP Schema

**Goal**: `via mcp schema` prints the `via_query` tool schema as JSON — human inspection tool, and single source of truth for `tools/list`.

### Tasks

- [x] **P4-1** Create `via/mcp/__init__.py`
- [x] **P4-2** Create `via/mcp/schema.py` — `build_tool_schema() -> dict` reads `MATCH_FLAGS`, `TYPE_FLAGS`, `RELATIONSHIP_FLAGS`, `RelationshipType` enum to build the `via_query` input schema with 8+ annotated examples
- [x] **P4-3** Add `mcp` subparser to `__main__.py` with `schema` sub-subcommand
- [x] **P4-4** Wire `via mcp schema` → calls `build_tool_schema()`, prints `json.dumps(..., indent=2)`
- [x] **P4-5** Unit test: schema output is valid JSON; includes all flag groups; examples array has ≥ 8 entries

**Gate**: `via mcp schema` runs and outputs valid JSON schema. No deps on `mcp` SDK yet.

---

## Phase 5 — MCP Server (`via mcp serve`) — Story 1

**Goal**: `via mcp serve` starts FastMCP server with watch mode. Claude Code can call `via_query`. This is the core Sprint 7 deliverable.

### Tasks

- [x] **P5-1** Add `mcp>=1.26` to project dependencies (`pyproject.toml` / `requirements.txt`)
- [x] **P5-2** Create `via/mcp/server.py` — `run_mcp_server(root_dir)` async function:
  - Creates two `DatabaseStore` instances (one per thread — WAL mode)
  - Starts `WatchService` in background thread (`handle_signals=False`)
  - Configures logging to `~/.via/mcp.log` (watch events off stdout/stderr)
  - Registers `@mcp.tool() via_query(args: list[str]) -> list[dict]` using `JsonRenderer`
  - Calls `mcp.run(transport="stdio")`
- [x] **P5-3** Add `serve` sub-subcommand to `mcp` subparser in `__main__.py`; dispatch to `asyncio.run(run_mcp_server(...))`
- [x] **P5-4** Error handling: if no `.via/index.db` found → print to stderr + return `EXIT_ERROR` (never write to stdout)
- [x] **P5-5** Integration test: feed mock JSON-RPC `tools/call` to stdin, assert JSON response on stdout
- [x] **P5-6** Integration test: `initialize` → `tools/list` → `tools/call` full round-trip
- [x] **P5-7** Verify `via mcp serve` exits cleanly on stdin EOF (watch thread stops)

**Gate**: Full stdio JSON-RPC round-trip passes. `via mcp schema` schema matches `tools/list` response.

---

## Phase 6 — Install / Status — Stories 2 & 3

**Goal**: `via install mcp` writes `.mcp.json`; `via status mcp` shows config state; `via uninstall mcp` removes it.

### Tasks

- [x] **P6-1** Create `via/commands/install.py`:
  - `InstallTarget` ABC with `install()`, `uninstall()`, `status()` methods
  - `McpInstallTarget(InstallTarget)` — reads/writes `.mcp.json` (project) and `~/.claude.json` (global)
  - `INSTALL_TARGETS = {'mcp': McpInstallTarget}` registry
- [x] **P6-2** Add `install`, `uninstall`, `status` subparsers to `__main__.py`:
  - Each takes positional `target` arg (`choices=list(INSTALL_TARGETS)`)
  - `install`/`uninstall` take `--global` flag
- [x] **P6-3** `McpInstallTarget.install()`: detect project root via `find_index_db()`; write/merge `mcpServers.via` in `.mcp.json`; idempotent
- [x] **P6-4** `McpInstallTarget.uninstall()`: remove `mcpServers.via` key; delete file if empty
- [x] **P6-5** `McpInstallTarget.status()`: check both `.mcp.json` and `~/.claude.json`; print found/not-found for each
- [x] **P6-6** Unit tests: install creates file; re-install doesn't duplicate; uninstall removes entry; status reports correctly
- [x] **P6-7** Unit test: install with existing `.mcp.json` (other entries) preserves them

**Gate**: `via install mcp` creates valid `.mcp.json`. Claude Code can load it. All install unit tests pass.

---

## Phase 7 — UAT & Integration (Trin)

**Goal**: Full end-to-end validation. Sprint 7 shipped when all gates pass.

### Tasks

- [x] **P7-1** All existing tests still pass (`make test` — 713+ passing, 0 failures)
- [x] **P7-2** UAT: `via install mcp` in the via project → `.mcp.json` created
- [x] **P7-3** UAT: `via mcp serve` starts, watch mode active (check log file)
- [x] **P7-4** UAT: send mock `tools/call` with `{"args": ["-mg", "*", "-tc"]}` → valid JSON response
- [x] **P7-5** UAT: `via mcp schema` output matches `tools/list` response (diff should be empty)
- [x] **P7-6** UAT: modify a source file while server is running → re-index fires (verify in log)
- [x] **P7-7** UAT: `via uninstall mcp` removes the config
- [x] **P7-8** Update test count baseline in Mouse context

**Gate**: All UAT cases pass. `make test` green. Sprint 7 = SHIPPED.

---

## Dependency Chain

```
P1 (JsonRenderer)
  └─ P5 (MCP Serve) depends on JsonRenderer
P2 (DB Correctness)
  └─ P5 (MCP Serve) depends on WAL + reindex_file
P3 (WatchService cleanup)
  └─ P5 (MCP Serve) depends on handle_signals param
P4 (MCP Schema)
  └─ P5 (MCP Serve) depends on build_tool_schema()
  └─ P6 (Install) — independent, can run parallel to P5
P5 + P6 → P7 (UAT)
```

**P1–P4 can be done in any order** (all independent). **P5 requires P1–P4 complete.** **P6 independent of P5.** **P7 requires P5+P6.**

---

## Task Count

| Phase | Tasks | Testable After |
|-------|-------|----------------|
| P1 | 7 | P1 complete |
| P2 | 7 | P2 complete |
| P3 | 5 | P3 complete |
| P4 | 5 | P4 complete |
| P5 | 7 | P5 complete |
| P6 | 7 | P6 complete |
| P7 | 8 | P7 = done |
| **Total** | **46** | |
