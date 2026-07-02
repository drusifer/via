# Gate 2 Architecture Review — Test Coverage & Quality Analysis

**Reviewer**: Smith (HCI)
**Date**: 2026-07-01
**Target**: `agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`

## Verdict: APPROVED

## Condition Check (from Gate 1)

**Condition 1 — reuse existing query pattern, not a bespoke report format.**
MET, and better than requested: `covered-by` is redefined in place rather than
adding a new relationship, so there is zero new query surface to learn.
`via -Vcovered-by` is already muscle memory for existing users; it now just
returns more precise results. This is a strict usability improvement over the
`tested-by` proposal I conditionally approved at Gate 1 — one less concept in
the user's mental model, not a bespoke report format at all. (Heuristic #4
Consistency, #6 Recognition over Recall.)

**Condition 2 — visible per-test progress, not silent.**
MET: `make test-coverage` runs `pytest -v`, which prints each test as it
completes rather than the silent multi-minute gap a plain aggregate run would
produce over 1300+ tests. (Heuristic #1 Visibility of System Status.)

## Additional Note on the Breaking Change

Retiring the old blanket `<coverage>` symbol without a compatibility shim is
the right call here — HCI concern would be if *stale, wrong-looking* data were
left behind for a user to trip over post-upgrade. The architecture doc's
cleanup step (delete stale `<coverage>` symbols in the same import
transaction) prevents that: a user who runs the new capture path won't see
mixed old/new-style `covered-by` edges in query results. Good — this is
exactly the "don't leave dead cruft to confuse a user" outcome the user asked
for.

One documentation note for Oracle once this ships: `docs/specs/*` and
`USER_GUIDE.md` describing the old `via coverage import <coverage.xml>`
aggregate behavior must be updated to reflect the new per-test semantics and
the renamed `import-contexts` subcommand — stale docs would themselves become
a usability defect (Heuristic #10).

## Approved to proceed
Sprint 27 architecture is approved. Handing to Mouse for phase breakdown.
