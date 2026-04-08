# Changelog
TLDR: Detailed record of project features, fixes, and sprint-based milestones.


All notable changes to **via** are documented here.

---

## [Unreleased] — Sprint 12: Web UI + UX Polish

**Released:** 2026-03-23

### Added

- **Web interface** (`via web`) — full-featured single-page app served at `http://localhost:<port>/`
  - Left controls panel: match type, pattern, case-insensitive, qualified names, symbol type chips, filters (limit, newer-than, older-than), relationship, output format toggle
  - Right results panel: list cards, sortable table, Mermaid diagram
  - Status bar: indexed directory, file/symbol counts, last-indexed time-ago, watch indicator
  - Toast notification on live re-index
- **JavaScript/TypeScript test suite** (Vitest + jsdom) — 74 unit tests covering all app.js exported functions
- **Playwright E2E tests** — 22 tests covering status bar, query flow, output formats, reset, error handling, and UX regression suite

### Fixed (UX Polish — Smith Review)

- **UX-001** — Result count now uses correct singular/plural: "1 result" vs "N results"
- **UX-002** — Temporal filter placeholders changed from `1h`/`2d` (looked like active values) to `e.g. 1h`/`e.g. 2d`
- **UX-003** — Run Query / Reset button row is now `position: sticky` at the bottom of the controls panel — always reachable without scrolling
- **UX-004** — File paths in results are now relative to the indexed root (e.g. `example.py:4` instead of `/home/user/.../example.py:4`)
- **UX-005** — Results panel shows "Enter a pattern and click Run Query to search." on first load instead of blank space

### Known Issues (P3 — deferred)

- UX-006: Mermaid diagram renders left-anchored in wide canvas
- UX-007: Watch dot in status bar is small (6–8px); no pulse animation
- UX-008: Table File column dominates width; Name/Type columns cramped

---

## [0.1.0] — Sprints 1–11

- Symbol indexing (Python, TypeScript/JavaScript, C/C++, Markdown)
- CLI: `via query`, `via index`, `via watch`, `via status`, `via serve`
- MCP server (`via mcp serve`) — Claude Desktop integration
- Relationship queries (inherits-from, calls, imports, references, has, declares)
- Temporal filters (`--newerthan`, `--olderthan`), stale detection (`--stale`)
- SQLite-backed index with thread-safe connection pooling
- JSON, table, diagram output formats
