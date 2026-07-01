# Sprint 7 Consolidated Documentation

This document consolidates all documentation for Sprint 7.

## Table of Contents

- [SPRINT_7_USER_STORIES.md](#sprint-7-user-storiesmd) (originally `agents/cypher.docs/SPRINT_7_USER_STORIES.md`)

- [SPRINT_7_ARCHITECTURE.md](#sprint-7-architecturemd) (originally `agents/morpheus.docs/SPRINT_7_ARCHITECTURE.md`)

- [SPRINT_7_TASKS.md](#sprint-7-tasksmd) (originally `agents/mouse.docs/SPRINT_7_TASKS.md`)


---


## SPRINT_7_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_7_USER_STORIES.md`


## Sprint 7 - MCP Mode

**Author**: Cypher (PM)
**Date**: 2026-02-11 (updated 2026-03-20 with Drew feedback + MCP spec research)
**Theme**: AI Agent Protocol Support — Make via a first-class MCP tool
**Points**: 10
**Status**: READY FOR SPRINT — Sprint 6 shipped 2026-03-19 (713 tests, 0 failures)

---

### Epic: MCP Mode

Make `via` a first-class tool for AI agents. In MCP mode, `via` acts as a Model Context Protocol server — always-current index (watch mode built-in), JSON-RPC 2.0 over stdio, and auto-configures itself into Claude Code's tool discovery path.

#### Decisions (Drew, 2026-02-11 / updated 2026-03-20)

| Decision | Answer |
|----------|--------|
| Transport | stdio (JSON-RPC 2.0) |
| Target agents | Claude Code **only** (Gemini/ChatGPT deferred to backlog) |
| Entry point | `via mcp serve` |
| Watch mode | **Always on** — `via mcp serve` implicitly runs with watch mode; index is always current |
| Query interface | Single `via_query` tool with polymorphic dispatch — CLI args as input |
| Output renderer | New `JsonRenderer` / MCP output type leveraging existing renderer architecture |
| Install command | `via install mcp` (extensible `install` namespace, not `via mcp install`) |
| Status command | `via status mcp` (polymorphic `status` namespace) |
| Result output | Raw JSON records always — agent decides how to display |
| Required MCP methods | `initialize` + `tools/list` + `tools/call` only (tools capability only) |
| Pagination | Not applicable for `tools/call` — agent controls result size via `args` (e.g. `["-n", "50"]`) |

---

### MCP Spec Research (2026-03-20)

Key facts confirmed before implementation:

| Question | Answer |
|----------|--------|
| Pagination for `tools/call`? | ❌ Not in spec — only list ops (`tools/list`) support cursor pagination. Agent sets limit via args. |
| Required methods for tools-only server? | `initialize` + `tools/list` + `tools/call`. `resources/list`, `prompts/list` optional — skip if not declaring those capabilities. |
| How does Claude Code learn tool schema? | Calls `tools/list` at session startup dynamically. Config files (`.mcp.json`) only tell Claude how to launch the server. |
| Claude Code MCP config paths? | Project scope: `.mcp.json` (project root, committed). User scope: `~/.claude.json` (home root — not `~/.claude/settings.json`). |
| `initialize` response required fields? | `protocolVersion`, `capabilities`, `serverInfo` (name + version). Client then sends `notifications/initialized`. |

---

### Current Codebase State (confirmed 2026-03-20)

| Item | Location | Status |
|------|----------|--------|
| CLI entry + subcommand dispatch | `via/__main__.py` | ✅ Exists — `mcp`, `install`, `status` subparsers to be added |
| `_run_pipeline_command()` | `via/__main__.py:363` | ✅ Exists — logic to be extracted/reused |
| `WatchService` | `via/services/watch.py` | ✅ Exists — integrate into `mcp serve` |
| Renderer architecture | `via/renderers/` | ✅ Exists — add `JsonRenderer` following existing pattern |
| `MatchRecord` | `via/core/match_record.py` | ❌ Needs `to_dict()` for JSON serialization |
| `via/mcp/` module | — | ❌ Does not exist |
| `.mcp.json` in project root | — | ❌ Does not exist |
| `install` / `status` subcommands | `via/__main__.py` | ❌ Do not exist |

---

### Story 1: MCP Server Mode (P0, 5pts)

**As an AI agent developer**, I want to run `via mcp serve` so that Claude Code can query an always-current codebase index via JSON-RPC 2.0 over stdio.

#### Acceptance Criteria

- [ ] `via mcp serve` starts: (a) WatchService in background thread, (b) JSON-RPC 2.0 listener on main thread (stdin/stdout)
- [ ] Index is always current — watch mode starts automatically; no separate `via index` needed once server is running
- [ ] Implements JSON-RPC 2.0: `initialize`, `notifications/initialized` (accept), `tools/list`, `tools/call`
- [ ] `initialize` response includes: `protocolVersion` (echoed), `capabilities: {"tools": {}}`, `serverInfo: {name: "via", version: <VERSION>}`
- [ ] `tools/list` returns single tool: `via_query` with typed input schema (see below)
- [ ] `via_query` routes through existing pipeline via new `JsonRenderer` — no separate query logic
- [ ] Results returned as JSON array of symbol objects (raw — no terminal formatting)
- [ ] Each symbol: `symbol_name`, `symbol_type`, `file_path`, `line_number`, `byte_offset`, `qualified_name`, `parent_name`
- [ ] Error responses: JSON-RPC error format `{code, message, data}` with **precise** error messages (what, why, valid alternatives)
- [ ] Stats queries (`args: ["stats"]`) work through `via_query`
- [ ] `via mcp serve` exits cleanly on stdin EOF (agent disconnect); watch service shuts down too
- [ ] All protocol events log to stderr only (`-v` flag) — stdout is protocol-only
- [ ] Database path resolved by walking up from cwd to `.via/index.db`
- [ ] If no index found: JSON-RPC error response, **not** crash: `"Index not found — run 'via index .' first"`
- [ ] Resources and prompts capabilities NOT declared (not implemented in Sprint 7)

#### Tool Schema for `via_query`

```json
{
  "name": "via_query",
  "description": "Query the VIA codebase index. Pass the same arguments you would use on the CLI (e.g., [\"-mg\", \"*Test*\", \"-tc\"] finds all test classes). Use \"-n 0\" for unlimited results.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "args": {
        "type": "array",
        "items": {"type": "string"},
        "description": "CLI args for via (same syntax as command line, excluding 'via' itself)"
      }
    },
    "required": ["args"]
  }
}
```

#### Example JSON-RPC exchanges

```
→ {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"claude-code"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"via","version":"0.7.0"}}}

→ {"jsonrpc":"2.0","method":"notifications/initialized"}
  [no response — notification]

→ {"jsonrpc":"2.0","id":2,"method":"tools/list"}
← {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"via_query",...}]}}

→ {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"via_query","arguments":{"args":["-mg","*Parser*","-tc"]}}}
← {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"[{\"symbol_name\":\"PipelineParser\",...}]"}]}}
```

#### Implementation Notes

##### New files
- `via/mcp/__init__.py`
- `via/mcp/server.py` — JSON-RPC 2.0 dispatcher + stdio loop
- `via/renderers/json_renderer.py` — new `JsonRenderer` following existing renderer pattern

##### New renderer: `JsonRenderer`
Add `JsonRenderer` to the renderer architecture (`via/renderers/`). It consumes `Iterator[MatchRecord]` and outputs a JSON array string. Registered in `RendererFactory` like all other renderers. This is the output type used when in MCP context.

##### Watch mode + server concurrency
`via mcp serve` must run two loops simultaneously:
- `WatchService` (background thread) — keeps index current
- JSON-RPC stdio loop (main thread) — handles agent requests

When JSON-RPC loop exits (stdin EOF), signal watch service to stop. **Morpheus to confirm threading strategy** — consider whether `WatchService` already supports clean shutdown via event flag.

##### MatchRecord serialization
Add `to_dict() -> dict` to `MatchRecord` in `via/core/match_record.py`. `JsonRenderer` calls this.

##### Subcommand structure in `__main__.py`
```
via mcp serve          # Story 1 — MCP server (watch + JSON-RPC)
via mcp schema         # Story 3 — print tool schema (human inspection only)
via install mcp        # Story 2 — write .mcp.json config
via install <future>   # extensible
via status mcp         # Story 2 — show MCP config status
via status <future>    # extensible (polymorphic status classes)
```

`mcp install/uninstall/status` are **not** standard MCP protocol commands — they are via management commands in a separate namespace. `via mcp` only exposes `serve` and `schema`.

---

### Story 2: MCP Auto-Configuration for Claude Code (P1, 3pts)

**As a developer**, I want `via install mcp` to automatically register via as a Claude Code tool, so I don't have to manually edit `.mcp.json` or `~/.claude.json`.

#### Acceptance Criteria

- [ ] `via install mcp` writes/updates `.mcp.json` in the project root (where `.via/` lives) — project scope
- [ ] `via install mcp --global` writes to `~/.claude.json` — user scope (all projects)
- [ ] Generated config registers `via mcp serve` as the MCP server command
- [ ] `via install mcp` is idempotent — safe to run multiple times (updates, doesn't duplicate)
- [ ] `via uninstall mcp` removes the via entry (or deletes file if via was the only entry)
- [ ] `via status mcp` prints which config locations have via registered (project / global / none)
- [ ] `via status mcp` is the polymorphic entry point — future: `via status index`, `via status watch`
- [ ] `via install mcp` prints the config path it wrote on success
- [ ] Existing entries in `.mcp.json` / `~/.claude.json` are preserved — only the via entry is touched
- [ ] `via install mcp` fails with clear error if project root (`.via/`) is not found

#### Generated `.mcp.json` format (Claude Code project scope)

```json
{
  "mcpServers": {
    "via": {
      "command": "via",
      "args": ["mcp", "serve"],
      "description": "VIA codebase index — search symbols, query relationships, get stats"
    }
  }
}
```

#### Implementation Notes

- Config paths (confirmed from MCP spec research):
  - Project: `.mcp.json` in project root (next to `.via/`)
  - User global: `~/.claude.json` (home root) — **not** `~/.claude/settings.json`
- Project root detection: reuse `find_index_db()` from `via/core/discovery.py`
- JSON parsing: `json` stdlib — no new dependencies
- `via status mcp` reads both `.mcp.json` and `~/.claude.json` for via entry
- `via install` / `via status` / `via uninstall` are new top-level subparsers in `__main__.py`
- Use polymorphic install/status classes so future targets (`via install project`, `via status index`) follow same pattern

---

### Story 3: MCP Tool Schema (P1, 2pts)

**As a developer or agent**, I want `via mcp schema` to print the complete tool schema so I can inspect what queries are available and debug agent interactions.

#### Why this is needed

Claude Code learns the schema dynamically from `tools/list` at session startup — `via mcp schema` is **not** required for Claude Code to work. Its value is for:
1. Human inspection — developers can see exactly what Claude Code is seeing
2. Debugging agent interactions — compare schema against what agent actually uses
3. Generating documentation

#### Acceptance Criteria

- [ ] `via mcp schema` outputs the same schema that `tools/list` would return — single source of truth
- [ ] Schema documents all flag groups: match, type, output, format, relationship
- [ ] Schema includes enum values for all relationship types and symbol types
- [ ] Schema includes 8+ annotated example invocations covering common use cases
- [ ] Schema is generated programmatically from `flag_groups.py` and `relationship_types.py` — not hardcoded
- [ ] `via mcp schema --format json` (default) and `--format markdown` for human-readable docs
- [ ] Schema is NOT run during `via install mcp` (Claude Code fetches it live via `tools/list`)

#### Implementation Notes

- `via/mcp/schema.py` generates schema by reading `MATCH_FLAGS`, `TYPE_FLAGS`, etc. from `flag_groups.py`
- Same schema object used in both `via mcp schema` CLI output and `server.py` `tools/list` response
- `RelationshipType` enum + `SymbolType` enum provide valid enum values

---

### Sprint 7 Summary

| Story | Points | Priority | Description | Blocked? |
|-------|--------|----------|-------------|---------|
| Story 1 | 5 | P0 | MCP server (`via mcp serve`) — watch + JSON-RPC + JsonRenderer | No |
| Story 2 | 3 | P1 | Auto-config (`via install mcp`, `via status mcp`) | No |
| Story 3 | 2 | P1 | Tool schema (`via mcp schema`) — human inspection | Depends on Story 1 |
| **Total** | **10** | | | |

**Recommended order**: Story 1 (serve + renderer) → Story 3 (schema, reuses server schema) → Story 2 (install)

**Morpheus design needed before Story 1**:
- `WatchService` thread + JSON-RPC main thread concurrency strategy
- `JsonRenderer` placement in renderer architecture
- `via install` / `via status` subcommand polymorphism design

---

### Technical Context

#### What already exists (confirmed 2026-03-20)

| Item | Location | Note |
|------|----------|------|
| CLI entry + subcommand dispatch | `via/__main__.py:123` | `mcp`, `install`, `status` parsers to add |
| `_run_pipeline_command()` | `via/__main__.py:363` | Query logic — extract and reuse |
| `WatchService` | `via/services/watch.py` | Integrate into `mcp serve` |
| Renderer base | `via/renderers/base.py` | `JsonRenderer` follows this pattern |
| `RendererFactory` | `via/renderers/factory.py` | Register `JsonRenderer` here |
| `flag_groups.py` | `via/core/flag_groups.py` | Schema generation source |
| `RelationshipType` | `via/core/relationship_types.py` | Schema enum source |
| `find_index_db()` | `via/core/discovery.py` | Reuse for project root detection in install |
| Continue.dev reference | `.continue/mcpServers/chat.yaml` | Format reference (already working) |

#### What needs to be built

- `via/mcp/__init__.py`, `via/mcp/server.py`, `via/mcp/schema.py`
- `via/renderers/json_renderer.py` — new renderer type
- `MatchRecord.to_dict()` in `via/core/match_record.py`
- `mcp` subparser + `install` subparser + `status` subparser in `via/__main__.py`
- Unit tests: JSON-RPC parsing, JsonRenderer, schema generation, install idempotency
- Integration test: full `via mcp serve` round-trip (stdin→tools/call→stdout)

---

### Resolved Questions

| # | Question | Answer (Drew + research) |
|---|----------|--------------------------|
| 1 | Single tool vs multiple typed tools? | Single `via_query` — use polymorphism internally ✅ |
| 2 | `via mcp serve` error if no index? | Yes — JSON-RPC error with precise message ✅ |
| 3 | Claude Code MCP config path? | Project: `.mcp.json`. Global: `~/.claude.json` (NOT `~/.claude/settings.json`) ✅ confirmed by research |
| 4 | Raw JSON or formatted output? | Raw JSON always ✅ |
| 5 | Handle `resources/list`, `prompts/list`? | No — don't declare those capabilities; skip entirely ✅ |
| 6 | MCP pagination for results? | Not in spec for `tools/call`. Agent sets limit via `args: ["-n", "50"]`. No MCP-level pagination. ✅ |
| 7 | `via mcp serve` implies watch mode? | Yes — always on. Watch starts automatically on server start. ✅ |


---


## SPRINT_7_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_7_ARCHITECTURE.md`


## Sprint 7 Architecture Design — MCP Mode

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-20 (rev 2 — Drew feedback incorporated)
**Status**: ✅ APPROVED — all decisions resolved. Neo cleared to implement.

---

### Responses to Drew's Comments

| # | Comment | Response |
|---|---------|----------|
| 1 | `to_dict()` in base class — SoC concern | **Agreed. Moved to `JsonRenderer`.** Records don't know about JSON. Renderer builds the dict itself — all fields are public on the dataclass. |
| 2 | `ClassMatchRecord` override unclear | **Moot.** With `to_dict()` moved to `JsonRenderer`, no override needed anywhere. |
| 3 | JSON support should be in base class, not each subclass | **Agreed.** See Design 1 — base class handles JSON, subclasses handle type-specific checks. |
| 4 | Is `_stop_event.is_set()` thread-safe? | **Yes — by design.** `threading.Event` uses an internal `Condition` (backed by a `Lock`). `is_set()`, `set()`, and `wait()` are all protected. This is the canonical Python stdlib cross-thread signal pattern. No issue here. |
| 5 | Replace `print()` with logging; stderr for errors only | **Agreed.** `output: IO` param removed from `WatchService`. All watch feedback becomes `logger.info()`/`logger.debug()`. MCP mode configures logging to a file (`~/.via/mcp.log`) or null — never touches stdout/stderr during serve. |
| 6 | DB thread safety — consider async queue | **Design below.** Recommend WAL + separate connections for Sprint 7 (WatchService is the only writer — classic single-writer/many-readers). Async queue is the right long-term architecture; flagged as Sprint 8 tech debt. **Open question #1 for Drew.** |
| 7 | Check for MCP Python SDK | **Yes — `mcp` v1.26.0 (official SDK, PyPI).** Use `FastMCP` — replaces hand-rolled `McpServer` entirely. **Open question #2: dependency footprint acceptable?** |

---

### Open Questions (need Drew sign-off before Neo starts)

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| **OQ-1** | DB concurrency: WAL + separate connections vs. async queue for Sprint 7? | ✅ **DECIDED (Drew, 2026-03-20)**: WAL + separate connections. Async queue deferred to Sprint 8 (TD-S7-1). |
| **OQ-2** | Use official `mcp` SDK (`FastMCP`)? Heavy deps: starlette, uvicorn, httpx, pydantic v2, anyio come with it. | ✅ **DECIDED (Drew, 2026-03-20)**: Use `FastMCP`. Dep weight accepted. |

---

### Design 1: `JsonRenderer` — New Output Type

#### SoC fix: `to_dict()` stays in the renderer

`MatchRecord` does **not** get a `to_dict()` method. `JsonRenderer` accesses the public dataclass fields directly:

```python
## via/renderers/json_renderer.py
import json
from typing import Iterator
from .base import Renderer
from ..core.match_record import MatchRecord

class JsonRenderer(Renderer):
    """Renders match records as a JSON array."""
    HELP = "JSON array of symbol objects. One object per match."

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        return json.dumps([self._to_dict(r) for r in records], indent=2)

    @staticmethod
    def _to_dict(r: MatchRecord) -> dict:
        return {
            'symbol_name':    r.symbol_name,
            'symbol_type':    r.symbol_type,
            'qualified_name': r.qualified_name,
            'file_path':      r.file_path,
            'line_number':    r.line_number,
            'byte_offset':    r.byte_offset,
            'byte_length':    r.byte_length,
            'parent_name':    r.parent_name,
        }
```

No changes to any `MatchRecord` class for serialization.

#### `supports_render_type()` — JSON in base class

Drew is right — since JSON is valid for all symbol types, the check belongs in the base class, not repeated in 7 subclasses. Refactor:

```python
## via/core/match_record.py — MatchRecord base class

def supports_render_type(self, render_type: RenderType) -> bool:
    """JSON is universally supported. Delegate others to subclass."""
    if render_type == RenderType.JSON:
        return True
    return self._supports_render_type(render_type)

@abstractmethod
def _supports_render_type(self, render_type: RenderType) -> bool:
    """Subclasses implement type-specific render support."""
    pass
```

Each subclass renames `supports_render_type` → `_supports_render_type`. No logic change — just restructured. This is a clean refactor Neo can do in one pass.

#### Other changes

**`via/core/match_record.py`**: Add `RenderType.JSON` to enum.

**`via/core/flag_groups.py`**: Add to `OUTPUT_FLAGS`:
```python
Flag(FlagGroup.OUTPUT, 'J', 'output-json', 'render_type', 'json', 'JSON array of symbol objects'),
```

**`via/renderers/factory.py`**: Add `RenderType.JSON → JsonRenderer()` branch.

---

### Design 2: Watch + JSON-RPC Concurrency

#### Threading model

```
Main thread (asyncio):   FastMCP event loop     ← handles stdin/stdout
Background thread:        WatchService.start()   ← watchdog + debounce timers
```

#### WatchService changes

**Remove `output: IO` parameter** — all watch feedback goes through `logging`:

```python
## BEFORE (remove)
print(f"Re-indexed: {rel} ({n_symbols} symbols)", file=self.output)

## AFTER
logger.info("Re-indexed %s (%d symbols)", rel, n_symbols)
logger.debug("Removed %s", rel)
```

**Add `handle_signals: bool = True`** — when False (MCP background mode), skip SIGINT installation. `threading.Event` is thread-safe; the stop_event pattern is confirmed correct.

**MCP mode** configures logging at startup to write to `~/.via/mcp.log` — watch events go there, never to stdout/stderr.

#### DB thread safety (OQ-1)

**Current risk**: WatchService timers (writer) + FastMCP tool calls (reader) share one `DatabaseStore`.

**Recommendation: WAL + separate DatabaseStore instances**

```
McpServer     → DatabaseStore(db_path, mode=read)    # read-only queries
WatchService  → DatabaseStore(db_path, mode=write)   # index updates
```

Enable WAL mode in `DatabaseStore.connect()`:
```python
self.conn.execute("PRAGMA journal_mode=WAL;")
```

WAL allows **one concurrent writer + unlimited concurrent readers** — exactly our access pattern. SQLite handles file-level coordination. No deadlock risk because WatchService is the **only** writer.

**Async queue deferred to Sprint 8 tech debt.** If future sprints add concurrent writers (e.g., background indexing), revisit. Document as TD-S7-1.

#### MCP serve startup sequence (using `mcp` SDK)

```python
import asyncio
import threading
from mcp.server.fastmcp import FastMCP

async def _run_mcp_serve(root_dir: str) -> int:
    db_path = find_index_db(root_dir)
    if not db_path:
        # write error to stderr and return — cannot write to stdout (protocol wire)
        print("Error: Index not found — run 'via index .' first", file=sys.stderr)
        return EXIT_ERROR

    # MCP server (read-only DB connection)
    mcp_store = DatabaseStore(str(db_path), root_dir)
    mcp_store.connect()
    mcp_store.conn.execute("PRAGMA journal_mode=WAL;")

    # FastMCP setup
    mcp = FastMCP("via", version=VERSION)

    @mcp.tool()
    def via_query(args: list[str]) -> list[dict]:
        """Query the VIA codebase index. Pass CLI args (e.g. ['-mg','*Test*','-tc'])."""
        executor = PipelineExecutor(mcp_store)
        stages = PipelineParser().parse(args)
        results = list(executor.execute(stages))
        return [JsonRenderer._to_dict(r) for r in results]

    # WatchService (write DB connection, background thread)
    watch_store = DatabaseStore(str(db_path), root_dir)
    watch_store.connect()
    watch_store.conn.execute("PRAGMA journal_mode=WAL;")
    registry = _build_registry()
    indexing_svc = IndexingService(watch_store, registry)
    watch_svc = WatchService(indexing_svc, watch_store, root_dir, handle_signals=False)

    watch_thread = threading.Thread(target=watch_svc.start, daemon=True)
    watch_thread.start()

    try:
        mcp.run(transport="stdio")   # blocks until stdin EOF
    finally:
        watch_svc.stop()
        watch_thread.join(timeout=5)
        mcp_store.close()
        watch_store.close()

    return EXIT_SUCCESS
```

#### `FastMCP` SDK — what it handles for us

```
pip install mcp   # v1.26.0, official SDK (modelcontextprotocol org)
```

Handles automatically:
- JSON-RPC 2.0 framing (read/write)
- `initialize` / `notifications/initialized` handshake
- `tools/list` response from registered tools
- `tools/call` dispatch to decorated functions
- Schema generation from Python type hints + docstrings
- stdin/stdout stdio transport

**Replaces hand-rolled `McpServer` entirely.** We only write the `@mcp.tool()` decorated function.

**Async note**: `FastMCP` is async (`anyio`). `via_query` above is sync — this is fine, `FastMCP` wraps sync tools with `asyncio.to_thread()` internally. No changes needed to `PipelineExecutor` or `DatabaseStore`.

**Dependency weight**: `anyio`, `pydantic v2`, `starlette`, `uvicorn`, `httpx` all come with `mcp`. Heavy for a stdio server. Acceptable given correctness benefit — maintaining protocol compliance by hand is risky. See OQ-2.

---

### Design 3: Install / Status / Uninstall Polymorphism

*(Unchanged from rev 1 — Drew had no comments on this section.)*

#### Pattern: Strategy + registry

```python
## via/commands/install.py
from abc import ABC, abstractmethod

class InstallTarget(ABC):
    @abstractmethod
    def install(self, global_install: bool = False) -> int: ...
    @abstractmethod
    def uninstall(self, global_install: bool = False) -> int: ...
    @abstractmethod
    def status(self) -> int: ...

class McpInstallTarget(InstallTarget):
    """Writes/reads .mcp.json (project) or ~/.claude.json (global)."""
    ...

INSTALL_TARGETS: dict[str, type[InstallTarget]] = {
    'mcp': McpInstallTarget,
}
```

CLI subparsers in `__main__.py`:
```
via install mcp [--global]
via uninstall mcp [--global]
via status mcp
```

Config paths:
- Project: `.mcp.json` (next to `.via/`)
- Global: `~/.claude.json` (**not** `~/.claude/settings.json`)

---

### Updated File Change Summary

| File | Change |
|------|--------|
| `via/core/match_record.py` | Add `RenderType.JSON`; refactor `supports_render_type` → base handles JSON, subclasses implement `_supports_render_type` |
| `via/core/flag_groups.py` | Add `-oJ` / `--output-json` to `OUTPUT_FLAGS` |
| `via/renderers/json_renderer.py` | **NEW** — `JsonRenderer` with `_to_dict()` static method |
| `via/renderers/factory.py` | Register `JsonRenderer` for `RenderType.JSON` |
| `via/services/watch.py` | Add `handle_signals` param; replace all `print()` with `logger.info/debug()`; remove `output: IO` param |
| `via/services/indexing.py` | Add `reindex_file(path)` public method (TD-1) |
| `via/db/store.py` | Add `delete_file_completely(path)` (TD-1); add WAL enable in `connect()` |
| `via/mcp/__init__.py` | **NEW** |
| `via/mcp/schema.py` | **NEW** — `build_tool_schema()` for `via mcp schema` CLI command (human inspection) |
| `via/commands/install.py` | **NEW** — `InstallTarget` ABC + `McpInstallTarget` + registry |
| `via/__main__.py` | Add `mcp` subparser (`serve`, `schema`); add `install`/`uninstall`/`status` subparsers |
| `requirements.txt` / `pyproject.toml` | Add `mcp>=1.26` dependency |

**`via/mcp/server.py` no longer needed** — `FastMCP` replaces it.

#### Implementation order for Neo

1. `RenderType.JSON` + `JsonRenderer` + `-oJ` flag + `supports_render_type` base refactor *(self-contained)*
2. TD-1: `IndexingService.reindex_file()` + `DatabaseStore.delete_file_completely()` + WAL in `connect()`
3. `WatchService` logging refactor (remove `output`, add `handle_signals`)
4. `via/mcp/schema.py` — `build_tool_schema()` *(no async deps)*
5. Wire `via mcp serve` using `FastMCP` in `__main__.py`
6. Wire `via mcp schema` in `__main__.py`
7. `via/commands/install.py` — `McpInstallTarget`
8. Wire `via install/uninstall/status` in `__main__.py`

---

### Sprint 7 Tech Debt Created

| ID | Item | When |
|----|------|------|
| TD-S7-1 | Async queue for DB access (replace WAL+separate-connections) if concurrent writers are added | Sprint 8+ |
| TD-S7-2 | `mcp` SDK dep weight — evaluate lighter stdio-only alternative if dep size becomes an issue | Sprint 8+ |


---


## SPRINT_7_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_7_TASKS.md`


## Sprint 7 Task Breakdown — MCP Mode

**Scrum Master**: Mouse
**Date**: 2026-03-20
**Sprint Points**: 10 (3 user stories)
**Architecture**: `agents/morpheus.docs/SPRINT_7_ARCHITECTURE.md` ✅ APPROVED
**Stories**: `agents/cypher.docs/SPRINT_7_USER_STORIES.md` ✅ READY

---

### Sprint Goal

Ship `via mcp serve` — an always-current MCP server that Claude Code can use to query the codebase index without Bash tool access. By end of sprint: `via install mcp` + `via mcp serve` works end-to-end in a real project.

---

### Phase Summary

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

### Phase 1 — JsonRenderer (Foundation)

**Goal**: New `-oJ` output flag producing a JSON array. Self-contained, fully testable in isolation.

#### Tasks

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

### Phase 2 — DB Correctness (TD-1)

**Goal**: Make concurrent watch+query safe before MCP serve ships. WatchService is the only writer; WAL handles read concurrency.

#### Tasks

- [x] **P2-1** Enable WAL mode in `DatabaseStore.connect()`: `PRAGMA journal_mode=WAL`
- [x] **P2-2** Add `DatabaseStore.delete_file_completely(path)` — atomic triad: delete symbols, relationships, file record in one transaction
- [x] **P2-3** Add `IndexingService.reindex_file(path)` — public method, wraps `_index_file` in a transaction
- [x] **P2-4** Update `WatchService._reindex_file()` to call `indexing_service.reindex_file()` (not private `_index_file`)
- [x] **P2-5** Update `WatchService._remove_file()` to call `db_store.delete_file_completely()` (not three separate calls)
- [x] **P2-6** Unit tests: `delete_file_completely` removes all records atomically; `reindex_file` is idempotent
- [x] **P2-7** Regression: `via index -w` still works correctly after these changes

**Gate**: Watch mode still passes all existing tests. No regressions. WAL confirmed in schema test.

---

### Phase 3 — WatchService Logging Cleanup

**Goal**: Remove the `output: IO` parameter; route all watch feedback through Python logging so MCP mode can silence or redirect it cleanly.

#### Tasks

- [x] **P3-1** Replace all `print(f"...", file=self.output)` in `WatchService` with `logger.info()` / `logger.debug()`
- [x] **P3-2** Remove `output: IO` parameter from `WatchService.__init__()` (and all callers)
- [x] **P3-3** Add `handle_signals: bool = True` parameter to `WatchService.__init__()`; skip SIGINT setup when `False`
- [x] **P3-4** Update `_run_index_command()` in `__main__.py` — remove `output=` kwarg from WatchService construction
- [x] **P3-5** Regression: `via index -w` still runs and prints watch events correctly (via logging → stderr by default)

**Gate**: `via index -w` behaviour unchanged from user perspective. No `output=` param anywhere.

---

### Phase 4 — MCP Schema

**Goal**: `via mcp schema` prints the `via_query` tool schema as JSON — human inspection tool, and single source of truth for `tools/list`.

#### Tasks

- [x] **P4-1** Create `via/mcp/__init__.py`
- [x] **P4-2** Create `via/mcp/schema.py` — `build_tool_schema() -> dict` reads `MATCH_FLAGS`, `TYPE_FLAGS`, `RELATIONSHIP_FLAGS`, `RelationshipType` enum to build the `via_query` input schema with 8+ annotated examples
- [x] **P4-3** Add `mcp` subparser to `__main__.py` with `schema` sub-subcommand
- [x] **P4-4** Wire `via mcp schema` → calls `build_tool_schema()`, prints `json.dumps(..., indent=2)`
- [x] **P4-5** Unit test: schema output is valid JSON; includes all flag groups; examples array has ≥ 8 entries

**Gate**: `via mcp schema` runs and outputs valid JSON schema. No deps on `mcp` SDK yet.

---

### Phase 5 — MCP Server (`via mcp serve`) — Story 1

**Goal**: `via mcp serve` starts FastMCP server with watch mode. Claude Code can call `via_query`. This is the core Sprint 7 deliverable.

#### Tasks

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

### Phase 6 — Install / Status — Stories 2 & 3

**Goal**: `via install mcp` writes `.mcp.json`; `via status mcp` shows config state; `via uninstall mcp` removes it.

#### Tasks

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

### Phase 7 — UAT & Integration (Trin)

**Goal**: Full end-to-end validation. Sprint 7 shipped when all gates pass.

#### Tasks

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

### Dependency Chain

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

### Task Count

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


---
