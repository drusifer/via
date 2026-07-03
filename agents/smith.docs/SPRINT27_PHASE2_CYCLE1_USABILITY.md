# Smith — Usability Test: Sprint 27 Phase 2 Cycle 1

**Date**: 2026-07-02
**Method**: Real browser, not spec-reading (own rule). Added a Playwright
e2e spec (`tests/e2e/coverage.spec.js`) and ran it via `make test-e2e`
against a real Chromium instance — 26/26 e2e tests pass (22 existing + 4
new). Reviewed the actual rendered screenshots
(`tests/e2e/screenshots/ux-10-coverage-heatmap.png`,
`ux-11-coverage-efficiency.png`), not just the DOM assertions.
**Verdict**: APPROVED WITH 1 MINOR NON-BLOCKING NOTE

## What I actually saw

D3 loaded for real (CDN was reachable from this environment) and rendered
a genuine zoomable icicle — not the no-D3 text fallback. Nav toggle (Query
↔ Coverage), subnav toggle (Heatmap ↔ Efficiency), the legend, and the
efficiency table (with a default sort indicator on "Test") all render and
behave correctly in a real browser.

The e2e fixture project has no captured coverage data (it's a tiny sample
project, never run through `make test-coverage`), so every symbol shows
0%/gap (deep blue) — this screenshot doesn't exercise the mid-scale
(adequate, neutral) or high-scale (hotspot, orange) colors, or a real
outlier's dashed marker. Trin already verified those work correctly via
data-level checks against the real `via` project's own captured coverage
(ground-truth cross-check, 800% intensity case) — I'm not re-litigating
that, just noting my screenshot alone doesn't visually confirm the
full color range.

## Finding (non-blocking): "Adequate (100%)" legend swatch has low contrast

The neutral-gray legend swatch (`rgb(240, 240, 240)`, representing the
100%/adequate baseline) is nearly invisible against the page's background
(`--md-sys-color-surface: #f8f9fa`) in the screenshot — only the 1px
outline border distinguishes it, and it's easy to miss at a glance. This is
a real Heuristic #1 (visibility of system status) nit: a legend entry that
blends into the background undermines the point of having a legend. Doesn't
block — the color itself is intentionally neutral by design (100% = nothing
alarming), and the label text is still legible. Recommend a slightly darker
neutral (e.g. one shade off pure `#f0f0f0`, or a visible border weight
bump) next time this view is touched, not urgent enough to hold up Cycle 1.

## Everything else confirmed good

- Colorblind-safe blue/orange (not red/green) — confirmed as designed at
  the 0% end; trust the data-level verification (Trin, Morpheus) for the
  rest of the range since I can't populate real hotspot data in the e2e
  fixture.
- Separate outlier visual marker (dashed border swatch) is present and
  legible in the legend, independent of any color fill — matches my
  original gate re-confirm note.
- Nav discoverability: "Query"/"Coverage" buttons are clearly labeled and
  positioned consistently with the existing output-format toggle pattern
  users already know from the query view.

## Handoff

Approved. Cycle 1 can close. The legend-contrast note is filed here for
whoever next touches this view — not a blocker, not re-opening the cycle.
