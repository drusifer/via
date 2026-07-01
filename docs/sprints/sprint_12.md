# Sprint 12 Consolidated Documentation

This document consolidates all documentation for Sprint 12.

## Table of Contents

- [SPRINT_12_SMITH_REVIEW.md](#sprint-12-smith-reviewmd) (originally `agents/cypher.docs/SPRINT_12_SMITH_REVIEW.md`)

- [SPRINT_12_USER_STORIES.md](#sprint-12-user-storiesmd) (originally `agents/cypher.docs/SPRINT_12_USER_STORIES.md`)

- [SPRINT_12_ARCHITECTURE.md](#sprint-12-architecturemd) (originally `agents/morpheus.docs/SPRINT_12_ARCHITECTURE.md`)

- [SPRINT_12_PLAN.md](#sprint-12-planmd) (originally `agents/mouse.docs/SPRINT_12_PLAN.md`)


---


## SPRINT_12_SMITH_REVIEW.md

**Original Location**: `agents/cypher.docs/SPRINT_12_SMITH_REVIEW.md`


## Sprint 12 — Smith Review

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Status**: APPROVED WITH NOTES — revisions required before Morpheus arch

---

### Verdict: Approved with Required Revisions

Stories are solid overall. Two issues must be resolved before Morpheus arch; one item is a note for Morpheus.

---

### Issue 1 (REQUIRED) — S12-3: Missing Two-Stage Pattern for Relationship Queries

**Problem**: via's relationship queries require TWO match patterns:
```bash
via -mg '*service*' -tF -Vhas -mg 'test_*' -tf
       ↑ anchor                    ↑ target
```
The UI has ONE Match Card. A user trying to run any relationship query would have no way to specify the second (target) pattern. This is not a nice-to-have — relationship queries are broken without it.

**Required fix**: Add a second "Target Pattern" section to the Relationships Card (or a second Match Card that conditionally appears when a relationship type is selected):
- Target match type dropdown (Glob/Regex/SQL)
- Target pattern text input
- Target symbol types toggle-button group

When relationship = "(none)", the target section is hidden.

---

### Issue 2 (REQUIRED) — S12-2: `results` array has no schema

**Problem**: `POST /api/query` response is `{ "results": [...] }` but the shape of each result object is unspecified. The frontend renderer (S12-4) needs to know what fields to expect.

**Required fix**: Define the result object schema in S12-2 AC:
```json
{
  "symbol_name": str,
  "qualified_name": str,
  "symbol_type": str,
  "file_path": str,
  "line_number": int,
  "language": str
}
```
For diagram format, `results` may instead be `{ "mermaid_source": str }` — clarify this.

---

### Issue 3 (REQUIRED) — S12-5 vs Non-Goals Contradiction

**Problem**: S12-5 AC says "status updates within 1s of re-index completion" for the toast. Non-Goals says "No WebSocket push (polling is fine for MVP)." These are contradictory — 5s polling cannot deliver 1s toast.

**Required fix**: Choose one:
- Option A: Relax S12-5 AC to "within one poll cycle (≤5s)" — keeps polling-only simple.
- Option B: Add SSE (Server-Sent Events) as in-scope for S12-5 specifically (push re-index events, not full WebSocket). Move this to OQ-3 resolution.

Recommend Option A for MVP simplicity.

---

### Note for Morpheus — S12-3: Dual relationship controls are confusing

The Relationships Card has both:
- Dropdown: relationship type (`-V<X>` flags)
- Text input: "Ref type override" (`--ref-type`)

These are redundant to a user. Recommend the UI exposes only the dropdown; Morpheus should decide whether `--ref-type` maps to the dropdown or is dropped from the web UI entirely.

---

### What's Good

- S12-1: Clean integration with watch mode. `--no-web` escape hatch is exactly right.
- S12-2: CORS, health endpoint, elapsed_ms — all the right production details.
- S12-4: Empty state, error state, loading spinner — solid UX basics covered.
- S12-5 status card (P1): Excellent idea. "3 seconds ago" relative time is the right UX.
- Non-goals list is clear and prevents scope creep.
- Open questions for Morpheus are well-formed.

---

### Required Actions (Cypher)

1. Add two-stage pattern to S12-3 Relationships Card spec
2. Add `results` object schema to S12-2 AC
3. Resolve S12-5 vs Non-Goals contradiction (pick Option A or B)
4. Add note re: `--ref-type` UI simplification for Morpheus

Once revised, re-post for Smith final approve. Fast-track — changes are additive, no story restructuring needed.


---


## SPRINT_12_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_12_USER_STORIES.md`


## Sprint 12 — Web UI for via

**Theme**: Browser-based query interface served from via watch mode
**Total Points**: ~15
**Priority**: P0 = must-ship, P1 = should-ship

---

### Background

When a user runs `via index -w`, via watches the filesystem and re-indexes on changes.
Sprint 12 adds a local web server to that watch session so the user can run queries
and browse results in a browser — no CLI flags needed.

The UI uses Material Design 3 (card-based layout). All via pipeline options are
exposed as visual controls. Query results render in multiple formats matching via's
existing output modes.

---

### Stories

#### S12-1 — Web Server Launch in Watch Mode and MCP Mode (P0, 3pt)

**As a** developer running `via index -w` or `via mcp serve`,
**I want** a local HTTP server to start automatically on port 7891,
**So that** I can open `http://localhost:7891` in my browser without any extra steps.

**Acceptance Criteria:**
- `via index -w` starts a web server alongside the watcher (threaded)
- `via mcp serve` starts a web server alongside the MCP stdio server (threaded)
- Server is available at `http://localhost:7891` by default in both modes
- `--port PORT` flag overrides the port for both commands (default 7891)
- `--no-web` flag disables the web server for both commands
- Ctrl+C (watch mode) and MCP client disconnect (mcp mode) shut down the web server cleanly
- Startup message: `Web UI: http://localhost:7891` (to stderr in MCP mode to avoid polluting stdio)
- Server does NOT start for `via index` without `-w`

**Out of scope**: authentication, HTTPS, multi-user

---

#### S12-2 — REST Query API (P0, 2pt)

**As a** web UI,
**I want** a JSON API to run queries and check index status,
**So that** the browser can display results without shelling out.

**Acceptance Criteria:**
- `POST /api/query` — accepts a JSON body with via pipeline args, returns JSON results
  - Body schema: `{ "match_type": "glob"|"regex"|"sql", "pattern": str, "symbol_types": [...], "limit": int, "case_insensitive": bool, "qualified": bool, "relationship": str|null, "invert": bool, "stale": bool, "output_format": "list"|"table"|"diagram", "newerthan": str|null, "olderthan": str|null, "target_match_type": "glob"|"regex"|"sql"|null, "target_pattern": str|null, "target_symbol_types": [...] }`
  - Response (list/table): `{ "results": [{"symbol_name": str, "qualified_name": str, "symbol_type": str, "file_path": str, "line_number": int, "language": str}, ...], "count": int, "format": "list"|"table", "elapsed_ms": int }`
  - Response (diagram): `{ "mermaid_source": str, "count": int, "format": "diagram", "elapsed_ms": int }`
- `GET /api/status` — returns `{ "directory": str, "file_count": int, "symbol_count": int, "last_indexed": ISO8601, "watching": bool }`
- `GET /api/health` — returns `{ "ok": true }`
- All endpoints return `Content-Type: application/json`
- CORS headers set for `localhost` origins

---

#### S12-3 — Query Builder UI — Controls (P0, 5pt)

**As a** developer,
**I want** a Material Design card-style interface with visual controls for all via pipeline args,
**So that** I can build and run queries without memorising flag syntax.

**Acceptance Criteria (UX):**

Layout: single-page app, two columns (controls left, results right) on wide screens; stacked on narrow.

**Match Card:**
- Dropdown: match type → Glob / Regex / SQL LIKE
- Text input: pattern (placeholder: `*service*`)
- Toggle: Case-insensitive (-I)
- Toggle: Qualified names (-Q)

**Symbol Type Card:**
- Toggle-button group (multi-select): Class · Function · Method · Import · Global · File Path · File Name · Markdown Header

**Filters Card:**
- Number input: Limit (-n), default empty (no limit)
- Text input: Newer than (`--newerthan`, e.g. `1h`)
- Text input: Older than (`--olderthan`, e.g. `2d`)

**Relationships Card:**
- Dropdown: Relationship type → (none) · inherits-from · calls · imports · references · has · declares
- Toggle: Invert direction (`--invert`)
- Toggle: Stale only (`--stale`)
- Note: `--ref-type` text override is NOT exposed in UI — dropdown maps to relationship flags directly (Morpheus to decide translation)

**Target Pattern Card** (conditionally shown when relationship ≠ "(none)"):
- Dropdown: Target match type → Glob / Regex / SQL LIKE
- Text input: Target pattern (placeholder: `test_*`)
- Toggle-button group (multi-select): target symbol types (same options as Symbol Type Card)

**Output Card:**
- Button group: List · Table · Diagram

**Actions:**
- Primary button: **Run Query** → POST /api/query → display results
- Secondary button: **Reset** → clear all controls to defaults

**Status bar** (top): shows directory, file count, symbol count, last index time — from GET /api/status (polled every 5s)

---

#### S12-4 — Results Display (P0, 3pt)

**As a** developer,
**I want** query results shown in the selected output format with nice formatting,
**So that** I can read symbol data without parsing raw CLI text.

**Acceptance Criteria:**

**List format** (`-oL`):
- Each result is a Material card: symbol name (bold), file path (muted), line number, type badge (colored chip)
- Results scrollable, count shown in header

**Table format** (`-oT`):
- Responsive data table: columns = Name · Type · File · Line
- Client-side sort on any column header click
- Sticky header

**Diagram format** (`-oD`):
- Render Mermaid diagram in-browser using mermaid.js
- Fallback: show raw diagram text in a `<pre>` block if mermaid fails to parse

**Common:**
- Loading spinner shown while query is in-flight
- Error card shown on API error (message + suggestion)
- Empty state card: "No results. Try broadening your pattern."
- Result count shown: "42 results (12ms)"

---

#### S12-5 — Index Status Dashboard Card (P1, 2pt)

**As a** developer,
**I want** a live status card showing what's indexed and watch activity,
**So that** I know the index is up-to-date before trusting query results.

**Acceptance Criteria:**
- Persistent status card (top of page or sidebar):
  - Indexed directory (absolute path)
  - File count / Symbol count
  - Last indexed timestamp (relative: "3 seconds ago")
  - Watch status indicator: green dot "Watching" / grey "Idle"
- Status updates live: poll `GET /api/status` every 5 seconds
- Status updates within one poll cycle (≤5s) of re-index completion
- "Re-indexed 3 files" toast notification appears on next poll after a re-index event (≤5s delay)

---

### Non-Goals (Sprint 12)

- No user authentication
- No multi-directory support (one watch session = one web instance)
- No query history persistence (in-memory only)
- No WebSocket push (polling is fine for MVP)
- No mobile-first design (desktop-first, responsive is a nice-to-have)
- No dark mode
- No offline mode — CDN required for Material Web and Mermaid.js (dev tool assumption)

---

### Open Questions for Morpheus

**OQ-1**: Serving strategy — embedded Python HTTP server (http.server / Flask / FastAPI) vs subprocess? Recommend FastAPI for async-friendly watch integration.

**OQ-2**: Frontend delivery — inline HTML/JS bundled in the Python package vs separate build step? Prefer single-file HTML template to avoid npm/build toolchain dependency.

**OQ-3**: Watch event → API push — MVP uses polling (≤5s cycle). SSE/WebSocket deferred to post-MVP. `/api/status` response should include a `last_reindex_count` field so the browser can detect fresh re-index events between polls and show the toast.

**OQ-4**: Query execution — call via's Python API directly (no subprocess) or shell out? Direct API is preferred for performance and type safety.

**OQ-5**: Port conflict handling — if 7891 is taken, should we auto-find next free port or fail with a clear error?

---

### Definition of Done

- `via index -w` starts web server, prints URL
- Browser at localhost:7891 shows the query builder UI
- All via pipeline args are represented in the UI
- All three output formats render correctly
- GET /api/status updates reflect fresh index data
- Tests cover: server start/stop, all API endpoints, query translation layer
- `--no-web` and `--port` flags work
- Existing watch-mode tests still pass


---


## SPRINT_12_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_12_ARCHITECTURE.md`


## Sprint 12 — Web UI Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-22
**Status**: APPROVED by Smith (Gate 2)

---

### Summary of Decisions

| OQ | Decision |
|----|----------|
| OQ-1 | `http.server.ThreadingHTTPServer` — zero new runtime dependencies |
| OQ-2 | Single HTML file embedded as a string in `via/web/template.py` — CDN for Material Web + Mermaid.js, no build step |
| OQ-3 | Polling (5s). `/api/status` adds `last_reindex_count` int field for toast detection |
| OQ-4 | Call via's Python API directly — build `Namespace` objects, call `PipelineExecutor` in-process |
| OQ-5 | Auto-find next free port in range 7891–7900; fail with clear error if all busy |
| Ref-type UI | Dropdown maps to `-V<X>` flags; `--ref-type` text override omitted from web UI |

---

### New File Structure

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

### Integration Sequence

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

### Component Designs

#### `via/web/server.py` — WebServer

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

#### `via/web/handler.py` — RequestHandler

Routes by method + path:

| Method | Path | Handler |
|--------|------|---------|
| GET | `/` | Serve `template.py` HTML string |
| GET | `/api/health` | `{"ok": true}` |
| GET | `/api/status` | `api.status.get_status(db_store, web_server)` |
| POST | `/api/query` | `api.query.run_query(db_store, body)` |
| GET | `*` | 404 |

CORS headers added to all responses: `Access-Control-Allow-Origin: *` (localhost-only tool).

#### `via/web/api/query.py` — Query Execution

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

#### `via/web/api/status.py` — Status

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

#### `via/services/watch.py` — WatchService additions

```python
def add_reindex_listener(self, callback: Callable[[int], None]) -> None:
    self._reindex_listeners.append(callback)

def _notify_reindex_listeners(self, count: int) -> None:
    for cb in self._reindex_listeners:
        try:
            cb(count)
        except Exception:
            pass  # never crash WatchService due to listener error

## In _execute(), after successful reindex:
self._notify_reindex_listeners(files_changed_count)
```

#### `via/web/template.py` — HTML SPA

Single Python string constant `HTML_TEMPLATE`. Embedded in the Python package — no file I/O at runtime.

CDN dependencies (no build step required):
- Material Web Components: `https://cdn.jsdelivr.net/npm/@material/web@latest/...` (or MDL CDN)
- Mermaid.js: `https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js`

Layout: two-column flex (controls left ~320px, results right flex-1).

All JS is vanilla ES modules or inline script — no bundler needed for the CDN approach.

---

### MCP Server Wire-Up (`via/mcp/server.py`)

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

### `IndexCommand` Changes (`via/commands/index.py`)

Add two args:
```python
parser.add_argument("--port", type=int, default=7891,
    help="Web UI port (default: 7891, only with -w)")
parser.add_argument("--no-web", action="store_true",
    help="Disable web UI when using --watch")
```

---

### `__main__.py` Wire-Up

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

### Testing Strategy

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

### Risk Register

| Risk | Mitigation |
|------|-----------|
| ThreadingHTTPServer blocks on shutdown | Call `httpd.shutdown()` in stop(); it's non-blocking for daemon threads |
| DiagramRenderer called with empty records | Guard: return `{"mermaid_source": "", "count": 0, ...}` |
| `db_store.get_counts()` slow on large index | Cache for 1s in status module |
| `DatabaseStore` not thread-safe (Sprint 6 lesson) | WebServer uses its own `DatabaseStore` instance, not shared with WatchService |

---

### Thread Safety Note (Sprint 6 Lesson Applied)

Sprint 6 found SQLite thread safety issues. **Resolution for Sprint 12:**
`WebServer.api/query.py` constructs a **fresh `DatabaseStore` instance** per request using the same db path. This avoids sharing a connection across threads. Cost: one connection open/close per query — acceptable for a dev tool serving one user.

---

### Implementation Order (for Mouse)

1. `via/web/server.py` + `via/web/handler.py` — server scaffold + health endpoint (no query yet)
2. `via/web/api/status.py` + `DatabaseStore` new methods — `/api/status` working
3. `via/web/api/query.py` — `/api/query` logic (non-relationship first, then relationship)
4. `via/commands/index.py` + `via/__main__.py` — CLI wire-up, `--port`, `--no-web`
5. `via/services/watch.py` — reindex listener hook
6. `via/web/template.py` — HTML SPA (Match Card, Symbol Type Card, Output Card, basic results list)
7. HTML SPA — remaining cards (Filters, Relationships, Target Pattern) + Table + Diagram formats
8. S12-5 — Status card polling + toast


---


## SPRINT_12_PLAN.md

**Original Location**: `agents/mouse.docs/SPRINT_12_PLAN.md`


## Sprint 12 — Phase Plan

**Theme**: Web UI for via (served from watch mode)
**Stories**: S12-1 through S12-5
**Points**: ~15
**Phases**: 8 (1-3 tasks each — short iterations)

---

### Phase Overview

| Phase | Tasks | Stories | Points | Dependencies |
|-------|-------|---------|--------|-------------|
| 1 | Server scaffold + health endpoint | S12-1 | 1 | none |
| 2 | Status API + DB methods | S12-1, S12-2 | 1.5 | Phase 1 |
| 3 | Query API (non-relationship) | S12-2 | 2 | Phase 2 |
| 4 | CLI wire-up + WatchService hook | S12-1 | 1.5 | Phase 3 |
| 5 | Query API (relationship + diagram) | S12-2 | 1 | Phase 4 |
| 6 | HTML SPA — core controls + list output | S12-3, S12-4 | 4 | Phase 5 |
| 7 | HTML SPA — relationship/target + table + diagram | S12-3, S12-4 | 3 | Phase 6 |
| 8 | Status dashboard card + toast (S12-5) | S12-5 | 2 | Phase 7 |

---

### Phase 1 — Server Scaffold + Health (1pt)

**Goal**: WebServer class exists, starts, serves health endpoint, stops cleanly.
**Files**:
- `via/web/__init__.py`
- `via/web/server.py`
- `via/web/handler.py`

**Tasks**:
1. Create `via/web/` module with `WebServer(db_store, port=7891)`
   - `start()` → finds free port 7891-7900, starts `ThreadingHTTPServer` in daemon thread
   - `stop()` → `httpd.shutdown()`
   - `port` property
2. `handler.py`: `GET /api/health` → `{"ok": true}`, CORS headers on all responses
3. Tests: WebServer start/stop, port auto-selection, health endpoint returns 200

**Exit criteria**: `WebServer` starts, `/api/health` returns `{"ok": true}`, stops on `.stop()`

---

### Phase 2 — Status API + DB Methods (1.5pt)

**Goal**: `/api/status` returns live index info.
**Files**:
- `via/web/api/__init__.py`
- `via/web/api/status.py`
- `via/db/store.py` (add `get_counts()`, `get_last_indexed_iso()`)

**Tasks**:
1. Add `DatabaseStore.get_counts() -> dict` — `{files: int, symbols: int}`
2. Add `DatabaseStore.get_last_indexed_iso() -> Optional[str]` — `MAX(indexed_at)` as ISO8601
3. `via/web/api/status.py`: `get_status(db_store, web_server) -> dict`
4. Wire `GET /api/status` in handler
5. Tests: get_counts, get_last_indexed_iso, status endpoint

**Exit criteria**: `GET /api/status` returns all required fields including `last_reindex_count`

---

### Phase 3 — Query API (Non-Relationship) (2pt)

**Goal**: `POST /api/query` works for simple match queries (list + table formats).
**Files**:
- `via/web/api/query.py`

**Tasks**:
1. `_build_stages(body) -> List[PipelineStage]` for non-relationship queries
2. `_record_to_dict(r: MatchRecord) -> dict` serializer
3. `run_query(db_store, body) -> dict` — fresh DB connection per request
4. Wire `POST /api/query` in handler, parse JSON body
5. Tests: glob/regex/sql match types, symbol_types list, limit, case_insensitive, qualified, newerthan/olderthan

**Exit criteria**: `POST /api/query {"match_type":"glob","pattern":"*","symbol_types":["function"]}` returns results list

---

### Phase 4 — CLI Wire-Up + WatchService Hook (2pt)

**Goal**: `via index -w` AND `via mcp serve` start web server. `--no-web` and `--port` work for both.
**Files**:
- `via/commands/index.py`
- `via/services/watch.py`
- `via/__main__.py`
- `via/mcp/server.py`

**Tasks**:
1. Add `--port PORT` and `--no-web` to `IndexCommand` (`via/commands/index.py`)
2. Add `add_reindex_listener(callback)` + `_notify_reindex_listeners(count)` to `WatchService`
3. Wire WebServer start/stop in `__main__.py` index handler (around `watch_service.start()`)
4. Add `--port` and `--no-web` to `via mcp serve` subparser in `__main__.py`
5. Wire WebServer start/stop in `run_mcp_server()` in `via/mcp/server.py` (print to stderr)
6. Tests: `--no-web` skips server for both modes; `--port` overrides; reindex listener fires; listener exception does not crash watcher; MCP mode prints URL to stderr not stdout

**Exit criteria**: `via index -w` prints `Web UI: http://localhost:7891` to stdout; `via mcp serve` prints to stderr; Ctrl-C stops both

---

### Phase 5 — Query API (Relationship + Diagram) (1pt)

**Goal**: `POST /api/query` supports relationship queries and diagram output.
**Files**:
- `via/web/api/query.py` (extend)

**Tasks**:
1. Extend `_build_stages()` to build `RelationshipFilter` from body fields
2. Add diagram branch: call `DiagramRenderer().render()` → return `mermaid_source`
3. Tests: relationship query (inherits-from, calls, has), invert, stale, diagram format

**Exit criteria**: relationship query with `target_pattern` returns results; diagram returns `mermaid_source` string

---

### Phase 6 — HTML SPA: Core Controls + List Output (4pt)

**Goal**: Browser shows a working query builder with Match Card, Symbol Type Card, Output Card, and List results.
**Files**:
- `via/web/template.py`

**Tasks**:
1. HTML skeleton: two-column flex layout (controls 320px left, results right)
2. Match Card: match type dropdown, pattern input, case-insensitive toggle, qualified toggle
3. Symbol Type Card: multi-select toggle-button group (8 types)
4. Output Card: List / Table / Diagram button group
5. Run Query + Reset buttons; fetch `POST /api/query`; display List format results as cards
6. Inline CSS: Material Design 3 color tokens via CDN; CDN error fallback message
7. Tests: serve HTML returns 200; contains key UI element IDs; JS fetch → mock API

**Exit criteria**: Open browser at localhost:7891, run a glob query, see results as cards

---

### Phase 7 — HTML SPA: Relationships, Table, Diagram (3pt)

**Goal**: Full UI — all cards, all output formats render correctly.
**Files**:
- `via/web/template.py` (extend)

**Tasks**:
1. Filters Card: limit input, newerthan input, olderthan input
2. Relationships Card: relationship type dropdown, invert toggle, stale toggle
3. Target Pattern Card: conditionally shown when relationship ≠ none; target match type + pattern + symbol types
4. Table format: render results in sortable `<table>` with sticky header; sort on column click
5. Diagram format: call `mermaid.initialize()`, render `mermaid_source`; `<pre>` fallback on parse error

**Exit criteria**: relationship query with target pattern returns results in all 3 formats

---

### Phase 8 — Status Dashboard Card + Toast (2pt) [P1]

**Goal**: S12-5 — live status card, polling, re-index toast.
**Files**:
- `via/web/template.py` (extend)

**Tasks**:
1. Status bar at top: directory, file count, symbol count, last indexed ("N seconds ago"), watch indicator
2. Poll `GET /api/status` every 5s; update status bar
3. Detect `last_reindex_count` change → show toast "Re-indexed N files" (auto-dismiss 3s)
4. Tests: status poll updates bar; toast appears on count change

**Exit criteria**: file change while watching → status bar updates within 5s → toast appears

---

### Task Assignment

All phases: **Neo** implements → **Trin** UAT → **Morpheus** reviews.

Phase order is strict (each phase depends on previous).

---

### Sprint 12 task.md format

```
[x] Phase N: <description>
  [x] Task 1
  [x] Task 2
```


---
