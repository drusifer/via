See chat_archive/CHAT-archive-2026-01-23T23-14.md
See chat_archive/CHAT-archive-2026-03-22.md

**Archive summary (chat_archive/CHAT-archive-2026-03-22.md)** — 2026-01-22 to 2026-03-20:
Sprints 1-7 coordination: Bob Protocol setup, VIA dogfood protocol, Sprints 1-7 full cycles (planning→arch→impl→UAT→review→groom→launch). Sprint 7 = MCP server mode (`via mcp serve`, `-oJ`). Sprint 8 kickoff (Line Index) begins at kept messages below.

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_27.md` (2026-11-24 18:10:14) — Sprint 27 (Test Coverage & Quality Analysis — Phase 1 Capture + Phase 2 Visualization): delivered per-test coverage import, test_runs metadata, D3 zoomable-icicle intensity heatmap (LOC sizing, outlier markers, leaf drill-down), test efficiency table with static AST Mocks column, docs/SDLC.md, and via-index 0.1.0 PyPI release.

---

---
[<small>2026-11-24 20:07:53</small>] [**User**]->[**all**] *request*:
 refine Cycle 2: identify tests that only touch mocks and nothing in the imported module

---
[<small>2026-11-24 20:07:53</small>] [**Morpheus**]->[**Neo**] *lead decide*:
 Morpheus+Neo refining Cycle 2 per user directive: adding imported_module_covered_count (covered-by symbols in test's AST-imported project modules) and mocks_only (mock_call_count > 0 and imported_module_covered_count == 0) to /api/coverage/test-efficiency and Efficiency table UI. Why: distinguish healthy isolated tests from hollow mock-only tests.

---
[<small>2026-11-24 20:11:24</small>] [**make**]->[**all**] *build*:
 Build PASSED | make test-e2e | /home/drusifer/Projects/via/build/build.out
✓  27 [chromium] › tests/e2e/app.spec.js:280:3 › UX Fixes › UX-005: initial call-to-action is hidden after query runs (2.0s)

27 passed (32.9s)

---
[<small>2026-11-24 20:11:39</small>] [**Neo**]->[**User**] *swe done*:
 Cycle 2 refined (DRY single-pass AST): added DatabaseStore.get_test_covered_file_counts() + imported_module_covered_count + mocks_only flag + Imported Covered column & mocks-only badge. 51 unit (99% cov on coverage.py) + 1 smoke + 107 JS + 27 Playwright E2E green; real .via/index.db (1423 tests, 28 mocked, 28 healthy, 0 mocks_only). Why: distinguish hollow mock-only tests from healthy isolated tests.
