# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `.agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:**
  - Verified Sprint 27 Phase 2 Cycle 2 (static AST mock-usage count column on coverage efficiency table).
  - Removed obsolete `bobp`-migrated tool tests (`tests/unit/test_prep_tldr.py`, `tests/unit/test_session_trace.py`, and `TestS10_3_PrepTldrIncremental` in `tests/uat/test_documented_queries_uat.py`) whose target scripts moved into `bobp` during `bobp update .`.
- **Key findings:**
  - Real repo spot-check: scanned all 109 test files in `tests/`, found 30 test functions with mock usages; verified `tests/unit/test_watch_service.py::TestStartupShutdown::test_start_runs_initial_index` has exact count `3` (`patch`, `MagicMock`, `patch.object`).
  - Full Python suite: 1409 passed, 1 skipped (0 regressions; 84% total coverage; `via/web/api/coverage.py` 98%, `via/web/template.py` 100%).
  - JS unit tests: 107 passed (3 files).
- **Important notes:** `tests/uat/test_sprint27_phase2_cycle1_uat.py` skips when `.via/index.db` lacks captured coverage; Cycle 1 + Cycle 2 unit/smoke/JS/E2E tests all pass cleanly.

## Current Task
- **Status:** Complete
- **Assigned to:** Trin
- **Started:** 2026-11-24
- **Description:** Sprint 27 Phase 2 Cycle 2 UAT verification and obsolete bobp-tool test cleanup.
- **Progress:** 100% passed; handed off to Switch for Cycle 2 security review.
- **Blockers:** None
- **Consultations:** None

## Next Steps
- **Immediate next action:** Await Switch security review, Morpheus review, and Sprint 27 close-out.
- **Waiting on:** Switch (`*sec review`)
- **Planned work:** Participate in Sprint 27 retrospective.

---
*Last updated: 2026-11-24*
