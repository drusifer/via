# Sprint 12 — Web UI for via

**Theme**: Browser-based query interface served from via watch mode
**Total Points**: ~15
**Priority**: P0 = must-ship, P1 = should-ship

---

## Background

When a user runs `via index -w`, via watches the filesystem and re-indexes on changes.
Sprint 12 adds a local web server to that watch session so the user can run queries
and browse results in a browser — no CLI flags needed.

The UI uses Material Design 3 (card-based layout). All via pipeline options are
exposed as visual controls. Query results render in multiple formats matching via's
existing output modes.

---

## Stories

### S12-1 — Web Server Launch in Watch Mode and MCP Mode (P0, 3pt)

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

### S12-2 — REST Query API (P0, 2pt)

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

### S12-3 — Query Builder UI — Controls (P0, 5pt)

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

### S12-4 — Results Display (P0, 3pt)

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

### S12-5 — Index Status Dashboard Card (P1, 2pt)

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

## Non-Goals (Sprint 12)

- No user authentication
- No multi-directory support (one watch session = one web instance)
- No query history persistence (in-memory only)
- No WebSocket push (polling is fine for MVP)
- No mobile-first design (desktop-first, responsive is a nice-to-have)
- No dark mode
- No offline mode — CDN required for Material Web and Mermaid.js (dev tool assumption)

---

## Open Questions for Morpheus

**OQ-1**: Serving strategy — embedded Python HTTP server (http.server / Flask / FastAPI) vs subprocess? Recommend FastAPI for async-friendly watch integration.

**OQ-2**: Frontend delivery — inline HTML/JS bundled in the Python package vs separate build step? Prefer single-file HTML template to avoid npm/build toolchain dependency.

**OQ-3**: Watch event → API push — MVP uses polling (≤5s cycle). SSE/WebSocket deferred to post-MVP. `/api/status` response should include a `last_reindex_count` field so the browser can detect fresh re-index events between polls and show the toast.

**OQ-4**: Query execution — call via's Python API directly (no subprocess) or shell out? Direct API is preferred for performance and type safety.

**OQ-5**: Port conflict handling — if 7891 is taken, should we auto-find next free port or fail with a clear error?

---

## Definition of Done

- `via index -w` starts web server, prints URL
- Browser at localhost:7891 shows the query builder UI
- All via pipeline args are represented in the UI
- All three output formats render correctly
- GET /api/status updates reflect fresh index data
- Tests cover: server start/stop, all API endpoints, query translation layer
- `--no-web` and `--port` flags work
- Existing watch-mode tests still pass
