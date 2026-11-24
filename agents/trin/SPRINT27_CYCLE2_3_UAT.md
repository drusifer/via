# Sprint 27 Cycles 2 & 3 UAT

**Reviewer**: Trin (QA)
**Date**: 2026-07-01

## Verdict: PASSES

## Cycle 2 — test_runs metadata
- Real data check against the project's own index: 1352 rows in `test_runs`,
  matching 1351 passed + 1 skipped exactly.
- Status breakdown: `{'pass': 1351, 'skip': 1}` — correct.
- **Upsert behavior verified for real** (not just unit tests): ran a targeted
  subset re-import, confirmed row count stayed at 1352 (no duplication) and
  the re-run test's `last_run_at` timestamp updated in place.

## Cycle 3 — in-process conversion + capture entrypoint
- `tests/subprocess/` (3 files, 30 tests) verified passing in their new
  location, confirmed none of their real subprocess/daemon calls got
  accidentally redirected by the conftest.py shim.
- No dead cruft found: confirmed the abandoned sitecustomize/combine
  approach was fully removed (`find` for `*sitecustomize*`/`*coverage_subprocess*`
  returns nothing).
- Full `make test-coverage` run against the real project: 1351 passed, 1
  skipped in ~83s; 49204 `covered-by` relationships across 1217 tests; 1352
  `test_runs` rows. Confirmed `make test` still passes cleanly afterward.

## One finding for Smith (not blocking, UX note)
`via coverage import-contexts` does a full replace of `<test>` symbols on
every import (per Cycle 1's cleanup design, and per Cypher's AC2 requiring
"full suite captured in one pass"). This is correct and by design, but there
is no warning if someone runs it against a **partial** coverage data file
(e.g. `.coverage` from a targeted subset run) — I did this during UAT and it
silently wiped the other 1327 tests' data until I restored it. `make
test-coverage` itself is safe (always runs the full `tests/` dir, no FILE
override), but the underlying `via coverage import-contexts <path>` command
has no guard if invoked directly against a partial file. Flagging for
Smith's usability pass — worth a decision on whether this needs a warning or
is acceptable as "advanced command, trust the input."

## Handoff
Both cycles pass. Handing to Smith for the usability test.
