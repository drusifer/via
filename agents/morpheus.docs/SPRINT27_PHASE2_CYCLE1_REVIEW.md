# Morpheus — Code Review: Sprint 27 Phase 2 Cycle 1

**Date**: 2026-07-02
**Reviewing**: Neo's implementation, Trin's UAT
**Verdict**: APPROVED

## Architecture alignment

`via/web/api/coverage.py` matches `SPRINT27_PHASE2_ARCHITECTURE.md` closely:
the 3-step build (per-symbol intensity → hierarchy nesting → leave-one-out
outlier detection), the class-row-dropping fix for the double-counting
problem I flagged in the architecture doc, and the true flattened-mean
rollup (not mean-of-child-means) are all present and match the design.
`DatabaseStore.get_symbol_coverage_counts()`/`get_test_efficiency_data()`
follow the existing `@require_connection` + raw-SQL-in-DatabaseStore
pattern used throughout the file. The handler wiring
(`_handle_coverage_hierarchy`/`_handle_coverage_test_efficiency`) is a
verbatim structural match to the existing `_handle_status` pattern — fresh
`DatabaseStore` per request, no shortcuts.

## Real bugs Neo/Trin found and fixed — assessed, not just trusted

- **Leave-one-out z-score fix**: verified the reasoning is correct.
  Including a candidate in its own group stats caps z at `sqrt(n-1)`
  (a real, non-obvious statistical trap) — the fix and the
  `_MIN_PEER_GROUP_SIZE = 10` guard against small-sample noise are both
  sound and well-commented with the *why*, not just the *what*.
- **Absolute-path bug**: confirmed by reading `core/discovery.py` myself —
  `FileInfo.path` is genuinely documented as absolute. The fix (relativizing
  in `get_symbol_coverage_counts()` via the existing private
  `_to_relative_path()` helper) is the right layer for it — DatabaseStore
  already owns `index_root`, and this keeps the pure `build_coverage_hierarchy()`
  function decoupled from any path-resolution concern.
- **Makefile `test:`/`test-coverage` shadowing**: reviewed the include-order
  fix. Moving `-include Makefile.prj` to parse last so its recipes win over
  the generic bob-protocol defaults is correct and matches how GNU Make
  actually resolves duplicate target recipes (last one parsed wins, with a
  warning) — not a workaround, the actual right fix. Good that it's
  commented with the "why" (this is a subtle Make behavior, not obvious to
  a future reader).

## One non-blocking style note

`build_coverage_hierarchy()` uses `id(leaf)` (Python object identity) as
part of a dict key to keep leaf nodes distinct from sibling package/module/
class nodes in the same `children` dict. It works and is correctly
commented, but it's an unusual pattern — a plain list of children per node
(rather than overloading one dict for both named subpackages and anonymous
leaves) would read slightly more conventionally. Not worth blocking on;
flagging for if this function gets touched again.

## Test quality

Trin's ground-truth cross-check (real CLI `-Vcovered-by` query vs. the new
endpoint, on this project's own re-indexed, re-captured data) is exactly
the right level of verification for a data-transformation feature like
this — it validates the real query path end-to-end, independent of the
code under test. Neo's leave-one-out unit tests correctly use realistic
peer-group sizes (10, not the original 4-5 that triggered small-sample
noise) rather than just lowering the bar to make a contrived test pass.

## Handoff

Approved. Per `agents/mouse.docs/SPRINT_27_PHASE2_TASKS.md`, the remaining
Cycle 1 gate is Smith's usability test (real browser — D3 rendering,
colorblind-safe scale, the separate outlier marker) before this cycle
formally closes.
