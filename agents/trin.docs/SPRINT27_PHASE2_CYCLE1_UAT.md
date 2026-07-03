# Trin — Sprint 27 Phase 2 Cycle 1 UAT

**Date**: 2026-07-02
**Reviewing**: Neo's hierarchical D3 test-intensity heatmap + efficiency table
**Verdict**: PASSES

## What I verified independently (not just re-reading Neo's numbers)

1. **Re-ran the full suite myself**: 1400 passed, 1 skipped (1398 before my 2
   additional UAT tests below). Re-ran `make test-js`: 98 passed.
2. **Found another real infra gap while trying to get real coverage data**:
   `test-coverage` — the actual Sprint 27 Phase 1 flagship capture command —
   had no public `make` stub either, same class of bug Neo just fixed for
   `test-js`/`lint`. It existed in `Makefile.prj` but `make test-coverage`
   would have failed with "No rule to make target" for anyone trying it
   fresh. Added the stub.
3. **Ran the real capture pipeline for real**: `make via_index` (re-indexed
   the project so it reflects Cycle 1's new source) then `make test-coverage`
   (real pytest run + real `import-contexts`). Produced fresh real data:
   52,201 `covered-by` relationships across 1,263 tests, 1,399 `test_runs`
   rows, over 20,392 symbols / 769 files.
4. **Ground-truth cross-check against the CLI, not the ORM**: picked a real
   symbol (`DatabaseStore.get_symbol_coverage_counts`, Neo's own new method),
   got its covering-test count via `via -mg 'get_symbol_coverage_counts' -tm
   --via covered-by -mg '*'` (8 distinct covering tests, counted from raw
   CLI output — the same relationship-query path a real user would use, not
   Neo's own code), then confirmed `/api/coverage/hierarchy` reports the
   identical `covering_test_count: 8` and `intensity_pct: 800.0` for that
   symbol. Real data agrees with real data via an independent path.
5. **Re-verified the absolute/relative path fix at real scale**: Neo's own
   smoke test only proved the fix on a synthetic 1-package temp project.
   I confirmed it also holds on the real, much deeper `via` tree — `via`
   appears correctly as a top-level package in the response, and none of the
   filesystem path segments (`home`, `Projects`, etc.) leak in as spurious
   top-level nodes.
6. Wrote both checks as real, rerunnable pytest tests —
   `tests/uat/test_sprint27_phase2_cycle1_uat.py` (skips cleanly if
   `.via/index.db` doesn't exist, so it won't break CI/a fresh clone, but
   is there for next time). Per user request: real pytest, not a one-off
   script.

## Verdict rationale

Everything Neo claimed checks out against independent, real-data
verification — not just re-running his own tests. The two infra gaps found
(`test-coverage`'s missing stub, on top of Neo's `test-js`/`lint` fixes)
were real and are now fixed, not just noted. No regressions: full suite
green before and after my additions.

## Not covered by this UAT (flagging, not blocking)

- **Real browser rendering** (D3 zoomable icicle, colorblind-safe scale,
  the separate outlier visual marker) — none of this is exercised by
  jsdom/CI, same limitation the existing Mermaid diagram already has. This
  needs Smith's usability test in an actual browser before sign-off.
- I did not do a broad statistical sanity-scan of outlier flags across the
  *entire* real codebase (e.g., "are any ordinary constructors getting
  flagged in practice") — Neo's synthetic unit tests cover the specific
  known-good/known-bad cases, and my one real symbol cross-check didn't
  happen to hit an outlier. Worth a quick manual glance next time someone's
  in the web UI, not a blocker for this gate.

## Handoff

To Morpheus for code review, per the Cycle 1 checklist in
`agents/mouse.docs/SPRINT_27_PHASE2_TASKS.md`. After Morpheus, Smith's
usability test (real browser) is still outstanding before Cycle 1 fully
closes.
