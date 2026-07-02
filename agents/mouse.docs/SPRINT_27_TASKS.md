# Sprint 27 Task Plan — Test Coverage & Quality Analysis (Phase 1: Capture)

**Author**: Mouse (SM)
**Date**: 2026-07-01
**Stories**: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`
**Architecture**: `agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`
**Gates**: Smith Gate 1 APPROVED WITH NOTES, Gate 2 APPROVED (both conditions met)

## Cycle 1 — Per-test coverage import (breaking, no back-compat)

- [x] Neo: retire `import_coverage_xml()`'s blanket-symbol logic in `via/commands/coverage.py`
- [x] Neo: add `import-contexts` subcommand reading coverage.py's native per-test context data (`CoverageData.contexts_by_lineno()`), replacing the `coverage.xml` parse path
- [x] Neo: create one synthetic symbol per test id (`symbol_type='test', file_path='<test>'`) and link via `covered-by` (many-to-many, not the old single blanket symbol)
- [x] Neo: in the same import transaction, delete any pre-existing `file_path='<coverage>'` symbols so stale old-style data doesn't linger (cascade-deletes their `covered-by` edges via existing FK)
- [x] Neo: registered `'test'` as a renderable symbol_type in `via/core/match_record.py` (was crashing on direct query/render, not just relationship-filter use)
- [x] Trin: verify `via -Vcovered-by <symbol>` now returns per-test results, and that no old-style `<coverage>` symbols survive a re-import (real check against this project's own index: 94 relationships across 7 tests, correct)
- [x] Morpheus: review Cycle 1 for architecture alignment — APPROVED

**Cycle 1 also surfaced a critical Cycle 3 finding** (Trin, 2026-07-01): 30/92
test files drive `via` via subprocess, and plain `pytest --cov-context=test`
measures zero code inside subprocesses. Folded into Cycle 3 below per
Morpheus's architecture revision — see `TEST_COVERAGE_ARCHITECTURE.md`.

## Cycle 2 — Test run metadata

- [x] Neo: add `test_runs` table (`test_id PK, status, duration_seconds, last_run_at`) to `via/db/schema.py` (bump `SCHEMA_VERSION` 6→7)
- [x] Neo: upsert one row per test id per run (latest status only, no history) from the pytest run's per-test outcome + duration (root `conftest.py` hook writes `.via/test_runs.json`, `import-contexts` upserts it)
- [x] Trin/Neo: 4 new tests verify upsert-not-duplicate behavior and status capture (`tests/unit/test_sprint27_c2.py`)
- [ ] Morpheus: review Cycle 2 for schema/migration correctness

## Cycle 3 — Capture entrypoint (scope revised twice, see Cycle 1 note above)

**Scope change (2026-07-01, user directive)**: instead of building subprocess
coverage capture (sitecustomize + combine), fixed the root cause — 27 of the
30 subprocess-spawning test files had no real reason to run out-of-process.
Converted them to run in-process via a shared helper; the 3 that manage a
real daemon or stdin protocol moved to `tests/subprocess/`. Full detail:
`agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`.

- [x] Neo: `tests/via_runner.py` — in-process via CLI runner (`run_via`)
- [x] Neo: `conftest.py` — `subprocess.run` redirect shim (detects `via` invocations, excludes `mcp serve`/`-w`/`input=`), zero per-test-file edits needed
- [x] Neo: moved `test_cli_watch.py`, `test_sprint6_uat.py`, `test_sprint7_uat.py` to new `tests/subprocess/` (real subprocess still required, genuinely different test tier)
- [x] Neo: fixed a real O(tests × files) performance bug found while validating at full scale — `_link_covered_symbols` was re-parsing every covered file once per test (minutes at 1300+ tests); rewrote to parse each file once
- [x] Neo: `make test-coverage` target — `pytest --cov=via --cov-context=test -v tests/` → `via coverage import-contexts .coverage` (no combine step needed)
- [x] Neo: verified end-to-end on the real project: 1351 passed in 83s (was 174s before the in-process conversion), 49204 covered-by relationships across 1217 tests, 1352 test_runs records imported
- [ ] Trin: full UAT sign-off (results above are Neo's own verification, not yet a formal Trin pass)
- [ ] Smith: usability test — actually run the command, not just review the plan
- [ ] Morpheus: final architecture review, confirm no dead cruft left from the old blanket-import path or the abandoned sitecustomize approach

## Non-scope (explicitly deferred)
- Phase 2 (redundancy/efficiency analysis) — not part of this sprint.
- Docs updates to `docs/specs/*` / `USER_GUIDE.md` for the renamed subcommand — Oracle's task at sprint close, not a Cycle task here.

## Notes
- No Tank/devops gate needed — no new env vars, services, or deployment scope.
- This plan does not touch or reorder the in-flight Sprint 26 Cycle 2/3 board.
