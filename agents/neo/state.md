# Agent State

Keep this working-memory file current. Preserve exactly these three top-level sections; see the
State Management Protocol in `.agents/skills/bob-protocol/SKILL.md` for entry and exit steps.

## Context
- **Recent decisions:**
  - Refined Sprint 27 Phase 2 Cycle 2 per user directive ("identify tests that only touch mocks and nothing in the module that was imported" + keep it DRY).
  - Consolidated Python file reading/parsing into `_parse_python_file()` (reused by both `_extract_signature_and_docstring` and `_analyze_test_file`) and single-pass `_analyze_test_file()` returning `(mock_count, imported_project_files)` per test function (both module-level and local imports).
  - Added `DatabaseStore.get_test_covered_file_counts()` reusing `_to_relative_path()` so `get_test_efficiency()` computes `imported_module_covered_count` and `mocks_only` (`mock_call_count > 0` and `imported_module_covered_count == 0`).
  - Surfaced sortable `Imported Covered` column + `mocks only` badge (`.badge-mocks-only`, `.row-mocks-only`) in `via/web/template.py` and `via/web/static/app.js`.
- **Key findings:**
  - Verified live against `.via/index.db`: 1,423 captured tests, 28 use mocks, all 28 cover 6–12 real symbols in their imported project modules (`0 mocks_only` false positives).
  - Tests: 51 unit tests (`via/web/api/coverage.py` 99% coverage), 1 integration smoke test, 107 JS tests, 27 Playwright E2E tests — all green, Ruff clean on touched files.
- **Important notes:** Working tree is uncommitted awaiting user authorization to commit.

## Current Task
- **Status:** Complete
- **Assigned to:** Neo
- **Started:** 2026-11-24
- **Description:** Refine Sprint 27 Phase 2 Cycle 2 to detect hollow mock-only tests (`imported_module_covered_count` + `mocks_only`) cleanly and DRYly.
- **Progress:** 100% — implemented, verified across Python/JS/E2E/real DB, docs updated.
- **Blockers:** None
- **Consultations:** Morpheus (refinement design).

## Next Steps
- **Immediate next action:** Await user authorization to commit Sprint 27 changes to `main`.
- **Waiting on:** User direction
- **Planned work:** Commit/push when authorized.

---
*Last updated: 2026-11-24*
