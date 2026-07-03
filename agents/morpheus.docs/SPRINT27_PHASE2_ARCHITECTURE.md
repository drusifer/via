# Sprint 27 Phase 2 — Architecture: Test Quality Visualization

**Author**: Morpheus (Tech Lead)
**Date**: 2026-07-01 (REVISED same day per user directive merging Stories 1/2)
**Reviewing**: `agents/cypher.docs/SPRINT27_PHASE2_USER_STORIES.md`
**Gate 1**: APPROVED WITH NOTES (`agents/smith.docs/SPRINT27_PHASE2_GATE1_REVIEW.md`),
re-confirmation pending on this revision.

## Revision note (2026-07-01)

User clarified the redundancy question is symbol-side fan-in (which symbols
are covered by unusually many tests), not test-side overlap, and wants it
merged with the coverage heatmap into one intensity metric aggregated
through the real code hierarchy, rendered with D3 (standard hierarchical
example, e.g. zoomable icicle/treemap) rather than a custom build. This
**replaces the old Story 1 + Story 2 sections below with a single Story 1
(revised) section.** Net effect: simpler and lower-risk than the original
plan — the pairwise Jaccard-bucketing algorithm (the riskiest part of the
old Story 2) is gone entirely, replaced by one `GROUP BY` plus a hierarchy
rollup.

Confirmed hierarchy is buildable from existing columns, no schema change:
`symbols.file_path` (directory segments = package levels, filename =
module), `symbols.symbol_type` ('class'/'method'/'function'), and
`symbols.parent_name` (set to the owning class name for methods — see
`via/services/indexing.py:413` `parent_name=cls.name`; `None` for
module-level classes/functions). This is enough to reconstruct
package → module → class → method/function nesting for any depth of
subpackage without new capture work.

## Data confirmed available (checked against real code/schema)

- `symbols` table has one row per test id with `symbol_type='test'` (see
  `via/commands/coverage.py`, `match_record.py` registration).
- `symbol_references`: `covered-by` edges are `from_symbol_id` = source code
  symbol, `to_symbol_id` = the synthetic test symbol
  (`store.insert_relationship(symbol_id, _test_symbol(test_id), 'covered-by')`
  in `coverage.py:128`). Grouping by `to_symbol_id` gives "what this test
  covers"; grouping by `from_symbol_id` gives "what covers this symbol".
- `test_runs(test_id PK, status, duration_seconds, last_run_at)` — one row
  per test, upsert-only, no history.
- Web API pattern (`via/web/api/*.py`, routed in `handler.py`): one function
  per concern, fresh `DatabaseStore` connection per call (Sprint 6 thread-
  safety rule), plain dict return for JSON serialization.

No schema changes needed for Stories 1-3 — this is a pure read/aggregation
layer on Phase 1 data.

## Story 1 (revised) — Hierarchical test-intensity heatmap

**New API**: `GET /api/coverage/hierarchy` → nested tree, pre-aggregated
server-side (D3's `d3.hierarchy()` wants a tree, not a flat list — cheaper
to build it once in Python than repeatedly in the browser).

**Step 1 — per-symbol intensity** (leaf nodes: functions/methods; classes
get their own row too for symbols directly in the class body, e.g. class
attributes, but the primary leaves are function/method):
```sql
SELECT s.id, s.symbol_name, s.symbol_type, s.file_path, s.parent_name
FROM symbols s
WHERE s.symbol_type IN ('function', 'method', 'class')
```
joined against:
```sql
SELECT sr.from_symbol_id AS symbol_id, COUNT(DISTINCT sr.to_symbol_id) AS covering_test_count
FROM symbol_references sr
WHERE sr.reference_type = 'covered-by'
GROUP BY sr.from_symbol_id
```
`intensity_pct = covering_test_count * 100` (0 tests = 0%, 1 = 100%, 2 = 200%).

**Step 2 — hierarchy build (Python)**: for each symbol, derive its path:
`file_path.split('/')[:-1]` = package levels (arbitrary depth) →
`file_path` = module → `parent_name` (if set) = class → symbol itself =
method/function. Build a tree keyed on this path; each ancestor node's
`intensity_pct` = mean of its descendant leaves' `intensity_pct` (not sum —
averaging keeps package/module level values on the same 0-N00% scale as
leaves, so the color scale is consistent at every zoom level).

**Step 3 — outlier/hotspot detection (Python, per Cypher AC5)**: group
leaf symbols into peer buckets by `(symbol_type, is_constructor_like)`
where `is_constructor_like = symbol_name in ('__init__', '__new__',
'__post_init__', '__call__', ...)` (naming-convention check, no new
capture). Within each bucket, compute a z-score or percentile for each
symbol's `covering_test_count`; flag symbols above a threshold (e.g.
z > 2, or top 1%) as `is_outlier: true` in the response. This keeps
constructors from being flagged just for being constructors, while still
catching a constructor that's outlying even for a constructor.

Response shape (recursive):
```json
{"name": "via", "type": "package", "intensity_pct": 118.4,
 "children": [
   {"name": "pipeline", "type": "package", "intensity_pct": 95.2, "children": [
     {"name": "executor.py", "type": "module", "intensity_pct": 130.0, "children": [
       {"name": "PipelineExecutor", "type": "class", "intensity_pct": 140.0, "children": [
         {"name": "run", "type": "method", "intensity_pct": 800.0,
          "covering_test_count": 8, "is_outlier": true}
       ]}
     ]}
   ]}
 ]}
```

**Frontend**: lazy-load D3 v7 from CDN, same pattern `app.js` already uses
for Mermaid (`mermaidReady` flag / dynamic `<script>` tag). New output mode
alongside list/table/diagram. Use D3's **zoomable icicle** example as the
starting template (depth-hierarchy reads more clearly than a treemap's
area-proportional layout for package→module→class→method navigation) —
`d3.hierarchy(data)` + `d3.partition()` + click-to-zoom, all standard D3
patterns, not custom-built rendering.

**Color scale (Smith Gate 1/2 notes)**: diverging scale centered at 100%
(1 covering test = adequate baseline) — cooler toward 0% (gaps, most
concerning at the low end), warmer toward high multiples (duplication).
Clip the visual scale at a cap (e.g. 300%) so a few extreme hotspots don't
wash out the gap-vs-adequate distinction in the rest of the tree; always
show the exact numeric `intensity_pct` in a label/tooltip regardless of
where it falls on the clipped scale — never rely on color alone.

**Drill-down (AC7)**: clicking a low/zero-intensity leaf re-runs the
*existing* query pipeline (`-tf -mg <file_path> --sans covered-by` or
equivalent) through the existing `/api/query` endpoint and existing list
rendering — no new result format.

## Story 3 — Test efficiency table

**New API**: `GET /api/coverage/test-efficiency`

```sql
SELECT tr.test_id, tr.status, tr.duration_seconds, tr.last_run_at,
       COUNT(sr.from_symbol_id) AS covered_symbol_count
FROM test_runs tr
LEFT JOIN symbols test_sym ON test_sym.symbol_name = tr.test_id
                          AND test_sym.symbol_type = 'test'
LEFT JOIN symbol_references sr ON sr.to_symbol_id = test_sym.id
                               AND sr.reference_type = 'covered-by'
GROUP BY tr.test_id;
```
Response: `[{test_id, status, duration_seconds, covered_symbol_count,
symbols_per_second}]`, `symbols_per_second` computed in Python
(`covered_symbol_count / duration_seconds`, guard divide-by-zero).

**Frontend**: sortable table, reusing the existing table-render/sort
machinery already in `app.js` (`sortCol`/`sortAsc`/`renderTable` — this
story needs zero new rendering code, just a new data source).

Build this alongside Story 1 (shares the `/api/coverage/*` namespace and
DatabaseStore query patterns) — cheapest sequencing per Cypher.

## Story 4 — Mocking-heaviness signal (feasibility only, per Gate 1)

**OQ-1 answer**: Static AST approach is cheap and fits naturally into
existing indexing. `via`'s Python parser already visits function/method
bodies to extract symbols — a `Call` node visitor counting
`unittest.mock.patch`/`Mock(`/`MagicMock(`/`@patch` usages per test function
is a small, additive extension to the existing AST walk, not a new
subsystem. Rough estimate: 1-2pt.

**OQ-2 answer**: Recommend NOT building (b) runtime instrumentation this
sprint. It requires runner changes (tracking real `Mock` call counts during
execution, not just static usage) comparable in scope to all of Phase 1 —
disproportionate for a signal we haven't validated is useful yet. Do (a),
look at the real numbers against this project's own test suite, and only
consider (b) if (a) proves too noisy.

**Recommendation to Mouse**: Story 4 = 1 cycle, scoped to (a) only:
- Add mock-usage count as a new per-symbol attribute (or a lightweight
  separate query), surfaced as a column/annotation on the Story 3 efficiency
  table (mock_call_count next to duration/coverage) rather than a standalone
  new view — reuses Story 3's UI, no new rendering surface needed.
- No threshold/scoring logic (e.g., "this test is BAD") — raw count only,
  consistent with Cypher's non-goal of no automated judgment.

## Sequencing recap (revised)

1. Story 1 (hierarchical D3 heatmap) — now the larger single chunk of work
   (tree-build + outlier stats + D3 integration), but architecturally
   simpler/lower-risk than the old Story 1+2 split (no pairwise/Jaccard
   algorithm). ~4-5pt.
2. Story 3 (efficiency table) — cheap, reuses `/api/coverage/*` namespace
   and query patterns from Story 1. ~1-2pt.
3. Story 4 (mock-count column on Story 3's table) — small addition once
   Story 3 ships. ~1-2pt.

No Tank/devops gate — no new env vars, services, or deployment surface.

## Handoff

To Smith for Gate 2 re-confirmation (this revision changes the UX approach
materially from the original approved design — matrix/grouped-list is gone,
replaced by a D3 zoomable icicle; check the color-scale and outlier-labeling
notes are still satisfied above), then to Mouse for cycle re-breakdown.
