# Sprint 27 Phase 2 — Test Quality Visualization: User Stories

**Author**: Cypher (PM)
**Date**: 2026-07-01
**Status**: REVISED per user directive — ready for Smith Gate 1 re-confirmation
**Seeds**: User request (`*chat @Smith`, 2026-07-01) + Smith's opinion
(`agents/smith.docs/SPRINT27_PHASE2_VIZ_OPINION.md`) + user clarification
(2026-07-01) reframing redundancy detection and merging it with the coverage
heatmap.

## Revision note (2026-07-01)

The user clarified 3 points that change Story 1 and Story 2 materially:

1. "Redundancy" is not about comparing tests to each other — it's about
   finding **symbols (methods/functions) covered by an unusually large
   number of different tests**, i.e. outliers/hotspots on the *symbol* side.
   Some symbols (constructors, etc.) are expected to run often and should
   not be flagged just for having high fan-in.
2. Aggregate using a reasonable code hierarchy: package → module → class →
   method/function (arbitrary depth, not a fixed 4 levels).
3. The heatmap's metric is coverage **intensity**, not binary coverage:
   value = how many distinct tests cover a symbol, expressed as a %
   (tested once = 100%, tested twice = 200%, untested = 0%), aggregated
   (averaged) up the hierarchy. One heatmap now shows both gaps (near 0%)
   and duplication hotspots (well over 100%) on the same navigable view.
   Must use an existing visualization library (D3), starting from a
   standard example (e.g. zoomable icicle/treemap) rather than a custom
   build.

**This replaces the original Story 1 (binary coverage heatmap) and Story 2
(test-pair overlap grouping) with a single unified story below.** Story 3
and Story 4 are unchanged.

## Story 1 (revised) — Hierarchical test-intensity heatmap (web mode)

As a developer, I want a navigable heatmap of test-coverage intensity across
the codebase hierarchy (package → module → class → method/function), where
color reflects how many tests exercise each unit, so I can spot both
undertested code and hotspots of duplicated test effort in one view.

- AC1: Intensity metric = count of distinct covering tests per symbol
  (`covered-by` fan-in), expressed as a % (1 test = 100%, 2 = 200%, 0 = 0%).
  Computed from existing Phase 1 data — no new capture step.
- AC2: Aggregated bottom-up through the real code hierarchy (directory
  nesting → module/file → class → method/function) — arbitrary depth, not
  forced into exactly 4 levels. Each ancestor node's value is the mean
  intensity % of its descendants.
- AC3: Navigable/drill-down from package down to method (zoom or expand),
  not a flat list.
- AC4: Built with an existing off-the-shelf viz library (D3) using a
  standard hierarchical example (zoomable icicle or treemap) as the
  starting point — no custom-built visualization from scratch.
- AC5: Hotspot/outlier detection distinguishes symbols expected to run
  often (constructors and similar, identified by naming convention) from
  genuine anomalies — compare each symbol's intensity against the
  distribution for its own peer group, not one global threshold.
- AC6: Color scale stays legible with extreme outliers present (clip/cap
  the visual scale) and the exact numeric value is always available on
  hover — carries forward Smith's original "never color alone" note.
- AC7: Drilling into a low- or zero-coverage leaf reuses the existing
  query/result rendering (no new result format) — same principle as the
  original AC3.

**Confidence**: High. Simpler than the original two-story split — one
`GROUP BY` on existing fan-in data plus hierarchy rollup, no pairwise
comparison, no Jaccard bucketing risk.

## Story 3 — Test efficiency view (coverage per second) — unchanged

As a developer, I want to see which tests cost the most runtime relative to
the coverage they contribute, so I can find slow tests that aren't pulling
their weight.

- AC1: Web mode surfaces, per test, its `test_runs.duration_seconds` against
  its `covered-by` count (a simple ratio or sortable table is sufficient —
  this does not need a novel chart type).
- AC2: Sortable/filterable so the worst offenders surface without manual
  scanning.
- AC3: Uses only data that exists today (`test_runs` + `covered-by`) — no new
  capture step.

**Confidence**: High. Cheapest of the stories data-wise; mostly a UI/API-
surface question.

## Story 4 — Mocking-heaviness signal — unchanged, NOT YET READY TO BUILD

As a developer, I want to know which tests rely heavily on mocking rather
than exercising real code, so I can find tests that give false coverage
confidence.

**This story is intentionally incomplete.** Per Smith's opinion, no schema
captures mocking today. Two candidate approaches, for Morpheus to assess
feasibility/cost on before this becomes a committed story:

- (a) **Static approximation**: AST-count `unittest.mock.patch`/`Mock()`/
  `MagicMock()` usages per test file at index time.
- (b) **Runtime instrumentation**: track actual mock call counts vs.
  assertion counts during a real test run. More precise, more invasive.

PM recommendation unchanged: evaluate (a) first; do not scope numeric AC
until Morpheus reports back on which approach is viable.

## Non-Goals (Phase 2, all stories)

- No automated "delete this test" or "this file needs more tests" actions —
  this is an inspection/insight tool, not an enforcement tool.
- No new coverage *capture* mechanism for Stories 1/3 — pure consumption of
  Phase 1 data.
- Story 4 does not commit to a specific mocking metric yet.
- No custom-built visualization — Story 1 must use an existing library
  (D3) and a standard hierarchical chart pattern.

## Suggested Sequencing (for Mouse, pending Gate 1/Gate 2 re-confirmation)

1. Story 1 (hierarchical intensity heatmap) — now the bulk of the work
   given the D3 integration, but architecturally simpler than the original
   Story 2 (no pairwise/Jaccard risk). Ship first.
2. Story 3 (efficiency table) — cheap, reuses same API surface work as
   Story 1.
3. Story 4 (mocking signal) — spike/feasibility only in this sprint; not a
   committed deliverable until Morpheus reports back.

## Handoff

To Smith for Gate 1 re-confirmation given the revised metric/merge (original
Gate 1 approved the old 3-story split; this is materially different enough
to warrant a quick re-check, not a silent carry-forward).
