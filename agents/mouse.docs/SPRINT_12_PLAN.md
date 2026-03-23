# Sprint 12 — Phase Plan

**Theme**: Web UI for via (served from watch mode)
**Stories**: S12-1 through S12-5
**Points**: ~15
**Phases**: 8 (1-3 tasks each — short iterations)

---

## Phase Overview

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

## Phase 1 — Server Scaffold + Health (1pt)

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

## Phase 2 — Status API + DB Methods (1.5pt)

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

## Phase 3 — Query API (Non-Relationship) (2pt)

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

## Phase 4 — CLI Wire-Up + WatchService Hook (2pt)

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

## Phase 5 — Query API (Relationship + Diagram) (1pt)

**Goal**: `POST /api/query` supports relationship queries and diagram output.
**Files**:
- `via/web/api/query.py` (extend)

**Tasks**:
1. Extend `_build_stages()` to build `RelationshipFilter` from body fields
2. Add diagram branch: call `DiagramRenderer().render()` → return `mermaid_source`
3. Tests: relationship query (inherits-from, calls, has), invert, stale, diagram format

**Exit criteria**: relationship query with `target_pattern` returns results; diagram returns `mermaid_source` string

---

## Phase 6 — HTML SPA: Core Controls + List Output (4pt)

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

## Phase 7 — HTML SPA: Relationships, Table, Diagram (3pt)

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

## Phase 8 — Status Dashboard Card + Toast (2pt) [P1]

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

## Task Assignment

All phases: **Neo** implements → **Trin** UAT → **Morpheus** reviews.

Phase order is strict (each phase depends on previous).

---

## Sprint 12 task.md format

```
[x] Phase N: <description>
  [x] Task 1
  [x] Task 2
```
