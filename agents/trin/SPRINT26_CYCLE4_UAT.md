# Sprint 26 Cycle 4 UAT — Relationship Type Hierarchy

**Reviewer**: Trin (QA)
**Date**: 2026-07-01

## Verdict: PASSES

## Verification
- `make test FILE=tests/unit/test_sprint26_c4.py` — 20/20 passed.
- `make test` (full suite) — 1372 passed, 1 skipped.
- Real end-to-end blast-radius queries against a scratch project with
  calls/imports/inherits-from relationships confirmed:
  - `upstream-ref` of a symbol returns its dependents (callers).
  - `downstream-ref` of a symbol returns its dependencies (callees).
  - `any-ref` returns both directions, correctly merged and deduped.
- Direct single-relationship-type queries (`--via calls`, `--via declares`,
  etc.) confirmed unaffected — same results as before Cycle 4.
- Confirmed `--sans` + category and chained + category both raise clear
  errors rather than silently producing wrong results.

## Finding for Smith (usability, not blocking)
`any-ref`/`upstream-ref`/`downstream-ref` include `declares`/`declared-in`
per the approved design doc's diagram. In practice this means a blast-radius
query on a function returns not just its callers/callees but also its
containing file (as both a `filepath` and `filename` symbol entry) via the
structural containment relationship. This is correct per the approved
design, but may be noisier than a user expects from "blast radius" (which
usually implies call-graph/code-dependency impact, not "which file are you
in"). Worth a usability read — could be intentional (declares/declared-in
were explicitly in the diagram) or worth a follow-up story to let blast
exclude structural relationships.

## Handoff
Handing to Morpheus for architecture review — flagging in particular the
design-doc inconsistency Neo found and fixed (diagram vs. prose disagreement
on upstream/downstream direction) since Morpheus should be aware even though
the design doc itself was user-approved directly.
