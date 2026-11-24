# Smith — Opinion: Coverage Visualization Enhancement (pre-Sprint 27 Phase 2)

**Date**: 2026-07-01
**Requested by**: User, direct `*chat @Smith`
**Status**: Opinion only — not a gate review (no stories/architecture exist yet to gate)

## What exists today (checked, not assumed)

- Web mode (`via/web/`) already has an SPA with a diagram output mode: `app.js`
  lazy-loads Mermaid from a CDN and renders `data.mermaid_source` via
  `mermaid.render()`. So a graph/diagram rendering pipeline is real, not
  hypothetical.
- Data model from Sprint 27 Phase 1: `covered-by` relationship (per-test
  synthetic symbols, many-to-many symbol↔test) + `test_runs` table (status,
  duration, last_run_at per test id). Verified against this project's own
  index: 49204 `covered-by` relationships across 1217 tests.
- There is **no data on mocking** anywhere in the schema. "Overly mocked
  tests" cannot be answered from what Sprint 27 captured — that's a
  different instrumentation problem (e.g. counting `Mock()`/`patch()` call
  sites per test, or tracking assertion count vs. mock-call count as a
  ratio). Flagging this now so it doesn't get silently assumed free.

## The three questions need three different visual answers — don't force one diagram

Treating "redundant tests," "overly mocked tests," and "uncovered code" as
one visualization is a Heuristic #6 (recognition over recall) problem in
reverse: one chart optimized for three different questions ends up
answering none of them well. My read, mapped to what's actually buildable:

### 1. Code lacking coverage → heatmap. Buildable now, cheapest win.
This is the classic case (Codecov/Istanbul-style treemap or file-tree heat
overlay). File/module as the unit, color = coverage %. This doesn't need
Mermaid or a new dependency — it can be a colored variant of the *existing*
table/list output, keyed off `covered-by` counts per file. Lowest-risk,
highest-immediate-value piece. I'd ship this first.

### 2. Redundant tests → needs aggregation, and Sankey is the wrong default at this scale.
Sankey diagrams communicate *flow volume between a small number of
categories* well. They fall over past ~20-30 nodes — at 1217 tests they'd
render as an unreadable hairball, violating Heuristic #8 (minimalist
design / aesthetic-and-minimalist). Two fixes if you still want a
flow-style view:
- Aggregate to **test file** or **test class**, not individual test id, as
  the node granularity.
- Make it a drill-down (start collapsed at module level, expand on click)
  rather than one static full-graph render — this also reuses the existing
  Mermaid infra instead of requiring a new charting library.

Redundancy itself (two tests covering the *same* symbol set) is really a
set-similarity question, which a heatmap/matrix (test × symbol, clustered)
answers more directly than a Sankey does. Worth deciding which question
matters more: "which tests overlap with which" (matrix) vs. "how does
coverage flow from tests into modules" (Sankey). I'd lead with the matrix.

### 3. Overly mocked tests → not a visualization gap, a data gap.
No amount of chart work fixes this — the underlying signal doesn't exist
yet. This needs to go back through Cypher (what counts as "overly mocked"?
mock-call-count vs assertion-count ratio? per-test or per-file?) before any
UI work makes sense. Recommend explicitly scoping this in vs. cutting it
from Phase 2, rather than promising a viz for data we don't have.

## Recommendation

- Don't jump straight to `*impl` — this is new query/API surface (the web
  API only exposes existing query results today, per `via/web/api/query.py`,
  not aggregate coverage summaries), so it needs the normal
  Cypher (requirements) → Morpheus (architecture/API shape) → Smith (gate)
  chain like Phase 1 got. Skipping it is exactly the risk the team already
  flagged Phase 2 for ("out of scope until a fresh requirement").
- Suggested phase scope, in priority order: (1) file-level coverage heatmap
  — buildable now from existing data, (2) test-overlap/redundancy matrix
  aggregated at file/class granularity, (3) mocking-quality metric — blocked
  on Cypher defining what "overly mocked" means before any viz is designed.
- Sankey isn't off the table, but I'd use it for a drill-down "tests →
  modules" flow view (aggregated), not as the answer to redundancy or
  mocking.

@User / @Cypher: if you want to move forward, this reads like a normal
`*plan sprint`-scale requirement (new web API endpoints + new frontend
viz), not a quick `*impl`.
