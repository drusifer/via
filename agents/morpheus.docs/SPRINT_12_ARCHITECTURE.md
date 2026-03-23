# Sprint 12 — Web UI Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-22
**Status**: APPROVED by Smith (Gate 2)

---

## Summary of Decisions

| OQ | Decision |
|----|----------|
| OQ-1 | `http.server.ThreadingHTTPServer` — zero new runtime dependencies |
| OQ-2 | Single HTML file embedded as a string in `via/web/template.py` — CDN for Material Web + Mermaid.js, no build step |
| OQ-3 | Polling (5s). `/api/status` adds `last_reindex_count` int field for toast detection |
| OQ-4 | Call via's Python API directly — build `Namespace` objects, call `PipelineExecutor` in-process |
| OQ-5 | Auto-find next free port in range 7891–7900; fail with clear error if all busy |
| Ref-type UI | Dropdown maps to `-V<X>` flags; `--ref-type` text override omitted from web UI |

---

## New File Structure

```
via/
  web/
    __init__.py          # exports WebServer
    server.py            # WebServer lifecycle (ThreadingHTTPServer in daemon thread)
    handler.py           # HTTP request routing → api.query / api.status
    api/
      __init__.py
      query.py           # POST /api/query logic: JSON → PipelineExecutor → JSON
      status.py          # GET /api/status state object (updated by WatchService hook)
    template.py          # HTML SPA as Python string constant
```

**No changes to existing modules** except:
- `via/commands/index.py` — add `--port` and `--no-web` args
- `via/services/watch.py` — add `add_reindex_listener()` and `_notify_reindex_listeners()`
- `via/__main__.py` — wire WebServer start/stop around WatchService in the `index -w` path; add `--port`/`--no-web` to `via mcp serve` subparser
- `via/mcp/server.py` — wire WebServer start/stop in `run_mcp_server()` (same pattern as watch mode)

---

## Integration Sequence

```
via index -w [--port 7891]
    │
    ├─ IndexCommand parses args
    ├─ DatabaseStore opened
    ├─ WatchService constructed
    ├─ WebServer constructed (db_store, watch_service, port)
    │   ├─ Finds free port in 7891–7900
    │   └─ Registers itself as reindex listener on WatchService
    ├─ WebServer.start()       ← daemon thread, returns immediately
    ├─ Prints: "Web UI: http://localhost:7891"
    └─ WatchService.start()   ← blocks main thread until Ctrl-C
        └─ on Ctrl-C: WebServer.stop() called in _shutdown()
```

---

## Component Designs

### `via/web/server.py` — WebServer

```python
class WebServer:
    def __init__(self, db_store: DatabaseStore, port: int = 7891) -> None: ...
    def start(self) -> None:           # finds free port, starts daemon thread
    def stop(self) -> None:            # httpd.shutdown()
    def notify_reindex(self, count: int) -> None:  # increments _reindex_count
    @property
    def port(self) -> int: ...
    @property
    def reindex_state(self) -> dict: ...  # {count, last_time, last_count}
```

Port selection:
```python
for p in range(port, port + 10):
    try:
        httpd = ThreadingHTTPServer(('', p), handler)
        self._port = p
        break
    except OSError:
        continue
else:
    raise RuntimeError(
        f"No free port in range {port}–{port+9}. "
        f"Use --port to specify a different starting port."
    )
```

### `via/web/handler.py` — RequestHandler

Routes by method + path:

| Method | Path | Handler |
|--------|------|---------|
| GET | `/` | Serve `template.py` HTML string |
| GET | `/api/health` | `{"ok": true}` |
| GET | `/api/status` | `api.status.get_status(db_store, web_server)` |
| POST | `/api/query` | `api.query.run_query(db_store, body)` |
| GET | `*` | 404 |

CORS headers added to all responses: `Access-Control-Allow-Origin: *` (localhost-only tool).

### `via/web/api/query.py` — Query Execution

**Key insight**: `PipelineExecutor.execute()` returns `Optional[Iterator[MatchRecord]]`.
For the web API we bypass the render stage, collect records, and serialize manually.

```python
def run_query(db_store: DatabaseStore, body: dict) -> dict:
    stages = _build_stages(body)          # JSON → List[PipelineStage]
    executor = PipelineExecutor(db_store)
    start = time.monotonic()
    records = list(executor.execute(stages) or [])
    elapsed_ms = int((time.monotonic() - start) * 1000)

    output_format = body.get("output_format", "list")
    if output_format == "diagram":
        from via.renderers.diagram import DiagramRenderer
        mermaid = DiagramRenderer().render(iter(records))
        return {"mermaid_source": mermaid, "count": len(records),
                "format": "diagram", "elapsed_ms": elapsed_ms}
    else:
        return {"results": [_record_to_dict(r) for r in records],
                "count": len(records), "format": output_format,
                "elapsed_ms": elapsed_ms}
```

**Stage construction** (`_build_stages`):

For a non-relationship query, build one `PipelineStage(StageType.MATCH, Namespace(...))`.

For a relationship query, build one stage where the `args.relationship` is a `RelationshipFilter`
constructed from `body["relationship"]`, `body["target_pattern"]`, etc.

This reuses all existing validation logic in `PipelineExecutor` without duplicating it.

```python
def _build_stages(body: dict) -> List[PipelineStage]:
    from argparse import Namespace
    from via.pipeline.types import PipelineStage, StageType

    args = Namespace(
        pattern=body.get("pattern", "*"),
        match_syntax={"glob": "g", "regex": "r", "sql": "s"}.get(
            body.get("match_type", "glob"), "g"),
        symbol_types=body.get("symbol_types", []),
        symbol_type=body.get("symbol_types", [None])[0],
        case_insensitive=body.get("case_insensitive", False),
        limit=body.get("limit", 0) or 0,
        match_qualified=body.get("qualified", False),
        newerthan=body.get("newerthan"),
        olderthan=body.get("olderthan"),
        render_type=None,   # No render stage; we collect records directly
        relationship=None,
    )

    if body.get("relationship"):
        from via.pipeline.relationship_filter import RelationshipFilter
        from via.core.relationship_types import ReferenceType
        rel_map = {
            "inherits-from": "inherits_from", "calls": "calls",
            "imports": "imports", "references": "references",
            "has": "declares", "declares": "declares",
        }
        rel_value = rel_map.get(body["relationship"], body["relationship"])
        target_types = body.get("target_symbol_types", [])
        args.relationship = RelationshipFilter(
            relationship_type=ReferenceType(rel_value),
            object_pattern=body.get("target_pattern", "*"),
            object_types=target_types,
            invert=body.get("invert", False),
            result_stale=body.get("stale", False),
            result_newerthan_seconds=None,
            result_olderthan_seconds=None,
        )

    return [PipelineStage(stage_type=StageType.MATCH, args=args)]
```

**Record serialization**:
```python
def _record_to_dict(r: MatchRecord) -> dict:
    return {
        "symbol_name": r.symbol_name,
        "qualified_name": r.qualified_name,
        "symbol_type": r.symbol_type,
        "file_path": r.file_path,
        "line_number": r.line_number,
        "language": getattr(r, "language", None),
    }
```

### `via/web/api/status.py` — Status

```python
def get_status(db_store: DatabaseStore, web_server: WebServer) -> dict:
    counts = db_store.get_counts()   # existing method: {files, symbols}
    reindex = web_server.reindex_state
    return {
        "directory": str(db_store.root_dir),
        "file_count": counts["files"],
        "symbol_count": counts["symbols"],
        "last_indexed": db_store.get_last_indexed_iso(),  # new method (see below)
        "watching": True,
        "last_reindex_count": reindex["count"],
        "last_reindex_files": reindex["last_count"],
        "last_reindex_time": reindex["last_time"],  # ISO8601 or null
    }
```

**New `DatabaseStore` methods needed** (small additions):
- `get_counts() -> dict` — `SELECT COUNT(*) FROM files`, `SELECT COUNT(*) FROM symbols`
- `get_last_indexed_iso() -> Optional[str]` — `SELECT MAX(indexed_at) FROM files` → ISO8601 string

### `via/services/watch.py` — WatchService additions

```python
def add_reindex_listener(self, callback: Callable[[int], None]) -> None:
    self._reindex_listeners.append(callback)

def _notify_reindex_listeners(self, count: int) -> None:
    for cb in self._reindex_listeners:
        try:
            cb(count)
        except Exception:
            pass  # never crash WatchService due to listener error

# In _execute(), after successful reindex:
self._notify_reindex_listeners(files_changed_count)
```

### `via/web/template.py` — HTML SPA

Single Python string constant `HTML_TEMPLATE`. Embedded in the Python package — no file I/O at runtime.

CDN dependencies (no build step required):
- Material Web Components: `https://cdn.jsdelivr.net/npm/@material/web@latest/...` (or MDL CDN)
- Mermaid.js: `https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js`

Layout: two-column flex (controls left ~320px, results right flex-1).

All JS is vanilla ES modules or inline script — no bundler needed for the CDN approach.

---

## MCP Server Wire-Up (`via/mcp/server.py`)

`run_mcp_server()` already runs `WatchService` in a daemon thread. Add WebServer in the same pattern:

```python
def run_mcp_server(root_dir: str, db_path: str,
                   port: int = 7891, no_web: bool = False) -> int:
    ...
    watch_svc = WatchService(...)
    watch_thread = threading.Thread(target=watch_svc.start, daemon=True)
    watch_thread.start()

    web_server = None
    if not no_web:
        from via.web import WebServer
        web_server = WebServer(db_path=db_path, root_dir=root_dir, port=port)
        watch_svc.add_reindex_listener(web_server.notify_reindex)
        web_server.start()
        print(f"Web UI: http://localhost:{web_server.port}", file=sys.stderr)
        # stderr: MCP uses stdio; web URL must not pollute the MCP protocol stream

    mcp = FastMCP("via")
    ...
    mcp.run()  # blocks until client disconnects

    if web_server:
        web_server.stop()
```

**`--port` and `--no-web`** added to `via mcp serve` subparser in `__main__.py`:
```python
mcp_serve_parser.add_argument("--port", type=int, default=7891)
mcp_serve_parser.add_argument("--no-web", action="store_true")
```
These are passed through to `run_mcp_server()`.

**stderr for startup message**: MCP server communicates over stdio. Printing to stdout would corrupt the MCP protocol. All web UI messages in MCP mode go to stderr.

---

## `IndexCommand` Changes (`via/commands/index.py`)

Add two args:
```python
parser.add_argument("--port", type=int, default=7891,
    help="Web UI port (default: 7891, only with -w)")
parser.add_argument("--no-web", action="store_true",
    help="Disable web UI when using --watch")
```

---

## `__main__.py` Wire-Up

In the `index` subcommand handler, around `WatchService.start()`:

```python
web_server = None
if args.watch and not args.no_web:
    from via.web import WebServer
    web_server = WebServer(db_store=db_store, port=args.port)
    db_store_ref = db_store     # captured in closure
    watch_service.add_reindex_listener(web_server.notify_reindex)
    web_server.start()
    print(f"Web UI: http://localhost:{web_server.port}")

watch_service.start()           # blocks until Ctrl-C

if web_server:
    web_server.stop()
```

---

## Testing Strategy

| Layer | What to test |
|-------|-------------|
| `WebServer` | start/stop lifecycle; free port selection; notify_reindex increments count |
| `handler.py` | Each route returns correct Content-Type and status; 404 for unknown paths |
| `api/query.py` | `_build_stages()` for all body shapes; non-relationship query; relationship query; diagram format |
| `api/status.py` | Returns all expected keys; `last_reindex_count` increments after notify |
| `WatchService` | `add_reindex_listener` fires on re-index; listener exception does not crash watcher |
| Integration | `via index -w` with `--no-web` does NOT start server; `--port 0` triggers auto-select |

Test approach: use `unittest.mock` to mock `DatabaseStore` for unit tests.
For `WebServer` tests, use `http.client` against a real socket (pick ephemeral port 0).

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| ThreadingHTTPServer blocks on shutdown | Call `httpd.shutdown()` in stop(); it's non-blocking for daemon threads |
| DiagramRenderer called with empty records | Guard: return `{"mermaid_source": "", "count": 0, ...}` |
| `db_store.get_counts()` slow on large index | Cache for 1s in status module |
| `DatabaseStore` not thread-safe (Sprint 6 lesson) | WebServer uses its own `DatabaseStore` instance, not shared with WatchService |

---

## Thread Safety Note (Sprint 6 Lesson Applied)

Sprint 6 found SQLite thread safety issues. **Resolution for Sprint 12:**
`WebServer.api/query.py` constructs a **fresh `DatabaseStore` instance** per request using the same db path. This avoids sharing a connection across threads. Cost: one connection open/close per query — acceptable for a dev tool serving one user.

---

## Implementation Order (for Mouse)

1. `via/web/server.py` + `via/web/handler.py` — server scaffold + health endpoint (no query yet)
2. `via/web/api/status.py` + `DatabaseStore` new methods — `/api/status` working
3. `via/web/api/query.py` — `/api/query` logic (non-relationship first, then relationship)
4. `via/commands/index.py` + `via/__main__.py` — CLI wire-up, `--port`, `--no-web`
5. `via/services/watch.py` — reindex listener hook
6. `via/web/template.py` — HTML SPA (Match Card, Symbol Type Card, Output Card, basic results list)
7. HTML SPA — remaining cards (Filters, Relationships, Target Pattern) + Table + Diagram formats
8. S12-5 — Status card polling + toast
