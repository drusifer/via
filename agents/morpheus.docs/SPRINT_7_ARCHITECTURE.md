# Sprint 7 Architecture Design — MCP Mode

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-20 (rev 2 — Drew feedback incorporated)
**Status**: ✅ APPROVED — all decisions resolved. Neo cleared to implement.

---

## Responses to Drew's Comments

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

## Open Questions (need Drew sign-off before Neo starts)

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| **OQ-1** | DB concurrency: WAL + separate connections vs. async queue for Sprint 7? | ✅ **DECIDED (Drew, 2026-03-20)**: WAL + separate connections. Async queue deferred to Sprint 8 (TD-S7-1). |
| **OQ-2** | Use official `mcp` SDK (`FastMCP`)? Heavy deps: starlette, uvicorn, httpx, pydantic v2, anyio come with it. | ✅ **DECIDED (Drew, 2026-03-20)**: Use `FastMCP`. Dep weight accepted. |

---

## Design 1: `JsonRenderer` — New Output Type

### SoC fix: `to_dict()` stays in the renderer

`MatchRecord` does **not** get a `to_dict()` method. `JsonRenderer` accesses the public dataclass fields directly:

```python
# via/renderers/json_renderer.py
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

### `supports_render_type()` — JSON in base class

Drew is right — since JSON is valid for all symbol types, the check belongs in the base class, not repeated in 7 subclasses. Refactor:

```python
# via/core/match_record.py — MatchRecord base class

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

### Other changes

**`via/core/match_record.py`**: Add `RenderType.JSON` to enum.

**`via/core/flag_groups.py`**: Add to `OUTPUT_FLAGS`:
```python
Flag(FlagGroup.OUTPUT, 'J', 'output-json', 'render_type', 'json', 'JSON array of symbol objects'),
```

**`via/renderers/factory.py`**: Add `RenderType.JSON → JsonRenderer()` branch.

---

## Design 2: Watch + JSON-RPC Concurrency

### Threading model

```
Main thread (asyncio):   FastMCP event loop     ← handles stdin/stdout
Background thread:        WatchService.start()   ← watchdog + debounce timers
```

### WatchService changes

**Remove `output: IO` parameter** — all watch feedback goes through `logging`:

```python
# BEFORE (remove)
print(f"Re-indexed: {rel} ({n_symbols} symbols)", file=self.output)

# AFTER
logger.info("Re-indexed %s (%d symbols)", rel, n_symbols)
logger.debug("Removed %s", rel)
```

**Add `handle_signals: bool = True`** — when False (MCP background mode), skip SIGINT installation. `threading.Event` is thread-safe; the stop_event pattern is confirmed correct.

**MCP mode** configures logging at startup to write to `~/.via/mcp.log` — watch events go there, never to stdout/stderr.

### DB thread safety (OQ-1)

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

### MCP serve startup sequence (using `mcp` SDK)

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

### `FastMCP` SDK — what it handles for us

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

## Design 3: Install / Status / Uninstall Polymorphism

*(Unchanged from rev 1 — Drew had no comments on this section.)*

### Pattern: Strategy + registry

```python
# via/commands/install.py
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

## Updated File Change Summary

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

### Implementation order for Neo

1. `RenderType.JSON` + `JsonRenderer` + `-oJ` flag + `supports_render_type` base refactor *(self-contained)*
2. TD-1: `IndexingService.reindex_file()` + `DatabaseStore.delete_file_completely()` + WAL in `connect()`
3. `WatchService` logging refactor (remove `output`, add `handle_signals`)
4. `via/mcp/schema.py` — `build_tool_schema()` *(no async deps)*
5. Wire `via mcp serve` using `FastMCP` in `__main__.py`
6. Wire `via mcp schema` in `__main__.py`
7. `via/commands/install.py` — `McpInstallTarget`
8. Wire `via install/uninstall/status` in `__main__.py`

---

## Sprint 7 Tech Debt Created

| ID | Item | When |
|----|------|------|
| TD-S7-1 | Async queue for DB access (replace WAL+separate-connections) if concurrent writers are added | Sprint 8+ |
| TD-S7-2 | `mcp` SDK dep weight — evaluate lighter stdio-only alternative if dep size becomes an issue | Sprint 8+ |
