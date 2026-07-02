# Sprint 27 Usability Test — Test Coverage & Quality Analysis

**Reviewer**: Smith (HCI)
**Date**: 2026-07-01

## Verdict: APPROVED, with one small recommended follow-up (non-blocking)

## What I ran
- `via coverage --help` and `via coverage import-contexts --help` — both
  clear, accurate, self-documenting. No jargon, states the default path.
- Reviewed `make test-coverage`'s actual terminal output (from Trin's run):
  visible per-test progress via pytest's `-v`, then two clear summary lines
  ("Imported per-test covered-by relationships: N across M tests" / "Imported
  test run metadata: M tests"). Meets Gate 1 condition #2 (visibility).
- Confirmed `via -Vcovered-by` needs no new syntax to learn — exactly the
  `-V<relationship>` pattern users already know. Meets Gate 1 condition #1.

## On Trin's partial-import finding (Heuristic #5, Error Prevention)
Agree this is a real gap. Silently replacing a full per-test dataset with a
tiny subset — with zero warning — is exactly the kind of "no sharp edges"
violation I hold the line on. Recommend a lightweight guard: before deleting
existing `<test>` symbols, compare the count being replaced against the
count about to be inserted; if the new count is dramatically smaller (e.g.
the import would drop from 1200+ tracked tests to a handful), print a
warning like:

```
Warning: this import covers 25 tests, but 1217 were previously tracked.
Continuing will remove per-test data for tests not in this import.
Re-run against the full suite's coverage file if that isn't intended.
```

This is a warning, not a hard block — legitimate use cases exist (shrinking
suite, intentional subset workflows) and `make test-coverage` itself already
avoids the footgun by always running the full `tests/` tree. Non-blocking for
Sprint 27 sign-off, but cheap enough to fix now rather than file as backlog —
recommend Neo add it before Morpheus's final review closes the sprint.

## Approved to proceed
Sprint 27 capture layer is usability-approved. Handing to Morpheus for final
architecture review; suggest the warning above gets folded in first if easy.
