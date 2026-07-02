# Sprint 27 Final Architecture Review — Test Coverage & Quality Analysis (Phase 1)

**Reviewer**: Morpheus (Tech Lead)
**Date**: 2026-07-01

## Verdict: APPROVED — Sprint 27 Phase 1 (capture) is CLOSED

## Cycle 2 (test_runs metadata) — schema/migration correctness
- `test_runs` table added cleanly via `ALL_TABLES` (`CREATE TABLE IF NOT
  EXISTS`, safe for both fresh and existing DBs). `SCHEMA_VERSION` bumped
  6→7 with a matching `schema_migrations` entry recorded — consistent with
  the existing v4/v5/v6 migration pattern in `store.py`.
- `upsert_test_run` uses `INSERT ... ON CONFLICT(test_id) DO UPDATE`,
  correctly upsert-only (verified for real by Trin: re-import updates
  timestamp in place, row count stable).
- Two pre-existing tests hardcoding `SCHEMA_VERSION == 6` were found and
  fixed rather than left broken — good catch during Cycle 2 verification.

## Cycle 3 (capture entrypoint) — final check
- No dead cruft: confirmed (Trin) that the abandoned sitecustomize/combine
  approach left no files behind.
- `_link_covered_symbols` correctly restructured to parse each file once
  (O(files)) rather than once per test (O(tests × files)) — this was a real
  bug caught during full-scale validation, not a hypothetical one; good that
  it was found and fixed before shipping rather than after.
- The `tests/via_runner.py` + `conftest.py` redirect shim is a clean piece of
  design: zero edits needed across 27 test files, and the 3 files that
  genuinely need real subprocess semantics (`tests/subprocess/`) are
  unaffected by construction (the shim only intercepts `subprocess.run`, not
  `Popen`, and explicitly excludes `mcp serve`/`-w`/`input=` invocations).
- Smith's partial-import warning (Heuristic 5) was implemented cleanly:
  `DatabaseStore.count_symbols_by_file()` is a small, reusable addition, and
  the warning is non-blocking as intended (doesn't change control flow,
  just informs).

## Requirements traceability
All 3 Phase 1 user stories from `TEST_COVERAGE_QUALITY_REQUIREMENTS.md` are met:
- US1 (run tests in one pass, per-test attribution): done via dynamic
  contexts, not literal one-process-per-test — matches the revised AC1.
- US2 (per-test coverage captured in isolation, persisted): done, reuses the
  `covered-by` query surface as directed.
- US3 (test run metadata recorded and queryable): status/duration/last-run
  captured and upserted; query surface is direct DB inspection for now (no
  dedicated CLI report) — this was explicitly left open by Cypher's AC3 as a
  future decision, not a Phase 1 requirement gap.

## Non-scope confirmed still out of scope
Phase 2 (redundancy/efficiency analysis) was not touched, per the original
requirement's explicit deferral. Correct.

## Closing
This closes the Sprint 27 planning-and-implementation cycle: Cypher → Smith
Gate 1 → Morpheus arch → Smith Gate 2 → Mouse plan → Morpheus plan review →
Neo impl (3 cycles) → Trin UAT → Smith usability → Morpheus final review.
Sprint 27 Phase 1 is done.
