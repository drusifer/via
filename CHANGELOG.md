# Changelog
TLDR: Detailed record of project features, fixes, and sprint-based milestones.


All notable changes to **via** are documented here.

---

## [Unreleased]

### Added

- **Sprint 28 — Hygiene, CI/Security, Coverage UX Polish & Domain Model**
  - GitHub Actions push/PR CI workflow (`.github/workflows/ci.yml`) with least-privilege `permissions: { contents: read }`, SHA-pinned actions, Python 3.10/3.12 (`ruff check via/`, `pytest`, `via --help`), Node 22 (`npm ci`, `npm test`), and SHA-256-verified `gitleaks` commit-range secret scanning.
  - Build-time dependency security scan Makefile targets (`security-scan-python` via `pip-audit`, `security-scan-npm` via `npm audit --audit-level=high`, and aggregate `security-scan`), with all Python (0 vulns) and npm (0 vulns; Vitest upgraded to `^5.1.1`) advisories remediated.
  - Canonical Domain Model document (`docs/DOMAIN.md`, linked from `README.md`) capturing VIA's four bounded contexts, ubiquitous language glossary, Mermaid context map and lifecycle diagram, aggregate invariants, domain events, and documented architectural drifts.
  - Web UI Coverage **Efficiency** empty-state hint (`#coverage-efficiency-empty`) guiding users to run `make test-coverage` while keeping sortable column headers visible, plus higher-contrast `"Adequate (100%)"` legend swatch (`#legend-mid`).
  - Refactored all Ruff complexity/hygiene findings across `via/` (`via/db/store.py` and 6 CLI/pipeline modules) so `ruff check via/` and `make lint-fast` exit 0 cleanly; added `node_modules/` to `.gitignore` and untracked 1,041 vendored files from git.

- **Sprint 27 — Test Coverage & Quality Analysis (Phase 1 & Phase 2)**
  - Per-test coverage capture (`via coverage import-contexts`, `make test-coverage`) storing per-test `covered-by` relationships and `test_runs` metadata (status, duration, last-run).
  - Web UI **Coverage** view with D3 zoomable-icicle intensity heatmap (leaf size = lines of code via schema v8 `symbols.line_end`, color = coverage intensity % on a colorblind-safe blue→orange scale, peer-relative outlier marker, leaf drill-down with signature & docstring via `GET /api/coverage/symbol`).
  - Web UI **Efficiency** sortable table (`GET /api/coverage/test-efficiency`) showing test duration, covered symbols, **Imported Covered** (`imported_module_covered_count`), symbols/sec, and static AST **Mocks** count (`mock_call_count`), flagging `mocks_only` tests that touch mocks while covering 0 symbols in their imported project modules.
  - Project SDLC governance doc (`docs/SDLC.md`) and gitleaks pre-commit hook (`.githooks/pre-commit`, `make install-hooks`).
  - PyPI trusted-publishing pipeline for `via-index` (`make release`, hardened `.github/workflows/publish.yml`).

### Changed

- Migrated MCP server mode from the removed MCP 1.x `FastMCP` import to the
  MCP 2.x `mcp.server.MCPServer` API.
- Raised the runtime requirement to Python 3.10+ and the MCP dependency to
  `mcp>=2.0`.
- Dropped legacy BobProtocol targets from `Makefile` in favor of `bobp make <target>`.

## Sprint 12: Web UI + UX Polish

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
