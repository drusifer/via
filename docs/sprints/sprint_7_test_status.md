Current test suite status as of Sprint 7 (MCP Mode) completion.

TLDR:
    Sprint 7 SHIPPED 2026-03-20. 794 tests passing (0 failures), 81%
    coverage. All Sprint 7 UAT (10/10) and existing regression tests pass.
    Lint clean (ruff + bandit). Key modules: unit, integration, acceptance,
    and uat directories under tests/.

# VIA Test Status

## Current State

**Date:** 2026-03-20
**Sprint:** 7 (MCP Mode) — COMPLETE
**Status:** ✅ 794 PASSED / 0 FAILED / 0 SKIPPED
**Coverage:** 81% overall

---

## Sprint History

| Sprint | Tests | Added | Feature |
|--------|-------|-------|---------|
| Sprint 1 | ~100 | — | Core indexing + CLI |
| Sprint 2 | ~200 | +100 | Pipeline syntax, MatchRecord polymorphism |
| Sprint 3 | ~300 | +100 | Renderers, relationships |
| Sprint 4 | ~400 | +100 | Renderer refactor, flag groups |
| Sprint 5 | ~500 | +100 | Relationship queries, --via flags |
| Sprint 6 | 713  | +213 | Watch mode, streaming, WAL mode |
| Sprint 7 | **794** | **+81** | MCP server, JsonRenderer, install commands |

---

## Test Suite Structure

```
tests/
├── unit/               # Isolated unit tests (fastest)
│   ├── test_pipeline_*.py
│   ├── test_renderers.py, test_json_renderer.py
│   ├── test_database*.py
│   ├── test_watch*.py
│   └── test_sprint7_p*.py  # Sprint 7 phase tests
├── integration/        # CLI subprocess tests (medium)
│   ├── test_cli_*.py
│   └── test_filepath_limit.py
├── acceptance/         # Sprint 1-3 acceptance tests
│   └── test_sprint{2,3}_uat.py
└── uat/               # Sprint UAT tests (end-to-end)
    ├── test_sprint5_uat.py
    ├── test_sprint6_uat.py
    └── test_sprint7_uat.py  # 10 tests — MCP mode E2E
```

---

## Sprint 7 UAT (10/10 passed)

| Test | Coverage |
|------|----------|
| `TestUAT72_InstallMcp` (3) | `via install mcp` creates `.mcp.json` |
| `TestUAT73_McpServeStarts` (2) | MCP stdio + initialize handshake |
| `TestUAT74_McpToolsCall` (2) | `tools/call via_query` returns JSON |
| `TestUAT75_SchemaMatchesToolsList` (1) | schema name == `tools/list` name |
| `TestUAT77_UninstallMcp` (2) | uninstall removes entry, preserves others |

---

## Running Tests

```bash
make test                           # Full suite
make test FILE=tests/uat/test_sprint7_uat.py   # Sprint 7 UAT only
make test ARGS="-k test_mcp"        # Pattern filter
make lint                           # Ruff + Bandit (must pass before PR)
```

---

## Code Quality

| Check | Status |
|-------|--------|
| ruff (style/imports/complexity) | ✅ Clean |
| bandit (security) | ✅ Clean (B608 suppressed — internal query builders) |
| Coverage | 81% overall |
