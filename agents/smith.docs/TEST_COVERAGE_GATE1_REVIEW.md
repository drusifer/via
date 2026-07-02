# Gate 1 User Story Review — Test Coverage & Quality Analysis

**Reviewer**: Smith (HCI)
**Date**: 2026-07-01
**Target**: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`

## Verdict: APPROVED WITH NOTES

## Value Assessment
Real user value — "is my suite actually testing what it claims to" is a
question developers currently can't answer with this tool. The Phase
1/Phase 2 split is the right call: shipping capture-only first avoids
speculative analysis UI built on data nobody has looked at yet (heuristic
#5, error prevention — prevents building the wrong analysis before the data
shape is known).

## HCI Notes

**HEURISTIC: #2 Match Between System and Real World**
`tested-by` alongside the existing `covered-by` reads naturally as "this
symbol is tested-by this test" vs. "this symbol is covered-by the suite" —
consistent grammar with existing relationship names (`declares`, `imports`,
`inherits-from`, `calls`, `has`). No objection to the naming Morpheus proposed.

**HEURISTIC: #6 Recognition Rather Than Recall / #10 Help and Documentation**
US3-AC3 currently leaves the consumption surface fully open ("CLI flag, via
query integration, or report file"). Recommend narrowing before Gate 2: if
`tested-by` is a real relationship in the symbol graph, it should be
queryable through the *existing* `via -Vtested-by` style relationship flag
users already know from `covered-by`/`declares`/etc. — not a bespoke new
report format users have to learn separately. A second, standalone
status/duration report is fine *in addition*, but the coverage-attribution
half should reuse the query mental model users already have. Please make
this explicit in the architecture doc rather than leaving it open-ended.

**HEURISTIC: #1 Visibility of System Status**
For AC2 ("full suite captured in one pass"), the capture run over 1300+
tests will take real wall-clock time. Recommend the new Makefile target
show visible progress (test counts as they run) rather than a silent long
pause — consistent with existing `via index -w` and test-run conventions
elsewhere in this tool. Not a blocker, just a note for the architecture doc.

## Discoverability
No new top-level concept for users to learn beyond "there's now a
`tested-by` relationship you can query like any other" plus a small
status/duration report. Low learning cost. Approved.

## Conditions for Gate 1 Pass
1. Architecture doc (Gate 2) must state which query surface exposes
   `tested-by` (recommend reusing `-V<relationship>` flag pattern).
2. Capture run must show visible per-test progress, not silent execution.

Both are addressable in Morpheus's architecture doc — not required to loop
back to Cypher.
