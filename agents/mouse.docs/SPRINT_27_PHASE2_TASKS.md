# Sprint 27 Phase 2 Task Plan — Test Quality Visualization

**Author**: Mouse (SM)
**Date**: 2026-07-01 (REVISED same day — Cycle 2 dissolved, folded into Cycle 1)
**Stories**: `agents/cypher.docs/SPRINT27_PHASE2_USER_STORIES.md` (revised)
**Architecture**: `agents/morpheus.docs/SPRINT27_PHASE2_ARCHITECTURE.md` (revised)
**Gates**: Smith Gate 1 APPROVED WITH NOTES, Gate 2 APPROVED, Gate
re-confirmation APPROVED WITH 2 NEW NOTES (`agents/smith.docs/SPRINT27_PHASE2_GATE_RECONFIRM.md`)

## Revision note

User reframed redundancy detection as symbol-side test-fan-in outliers
(not test-to-test overlap) and merged it with the coverage heatmap into one
hierarchical intensity view (package → module → class → method), built with
D3. The old Cycle 2 (test-overlap grouping, Jaccard-bucketing) is dissolved
— that algorithm no longer exists in the design. Its work is absorbed into
Cycle 1 below. Cycle numbering shifts: old Cycle 3 (mock signal) is now
Cycle 2.

## Cycle 1 — Hierarchical test-intensity heatmap (D3) + test efficiency table

- [ ] Neo: `GET /api/coverage/hierarchy` (`via/web/api/coverage.py`, new
      file) — per-symbol `covering_test_count`/`intensity_pct` query, Python
      hierarchy build from `file_path`/`symbol_type`/`parent_name` (package →
      module → class → method/function, arbitrary depth), returns nested
      tree per architecture doc's response shape
- [ ] Neo: outlier detection — group leaf symbols by `(symbol_type,
      is_constructor_like)` peer buckets, compute z-score/percentile,
      flag `is_outlier: true` on anomalies (constructors excluded from
      being flagged just for being constructors)
- [ ] Neo: `GET /api/coverage/test-efficiency` — per-test duration vs.
      covered-symbol-count, `symbols_per_second` computed in Python
      (guard divide-by-zero for 0-duration/0-coverage tests)
- [ ] Neo: wire both routes into `via/web/handler.py`'s `do_GET`
- [ ] Neo: frontend — lazy-load D3 v7 from CDN (same pattern as existing
      Mermaid lazy-load in `app.js`), new heatmap output mode using a
      **zoomable icicle** (`d3.hierarchy` + `d3.partition` + click-to-zoom)
      as the starting template — no custom-built visualization
- [ ] Neo: color scale — diverging, centered at 100%, using a
      **colorblind-safe blue↔orange hue pair** (not red/green, not left as
      unconstrained "warm/cool") — per Smith's re-confirm note 2. Clip the
      visual scale at a cap (e.g. 300%); always show the exact numeric
      `intensity_pct` in a label/tooltip regardless of clipping
- [ ] Neo: **`is_outlier` gets its own explicit visual marker** (e.g.
      border/icon) independent of the color fill — per Smith's re-confirm
      note 1 (peer-relative outlier status and absolute color value can
      disagree; color alone would mislead)
- [ ] Neo: frontend — sortable efficiency table reusing existing
      `sortCol`/`sortAsc`/table-render machinery in `app.js`
- [x] Neo: heatmap drill-down on a leaf (Cypher AC7), resolved per user
      directive 2026-07-02: clicking a leaf shows qualified name, signature,
      and docstring (functions/methods; degrades gracefully for classes/
      non-Python). New `GET /api/coverage/symbol?id=` endpoint,
      `DatabaseStore.get_symbol_detail()`, on-demand AST re-parse (mirrors
      `via/renderers/usage.py`'s existing docstring-extraction pattern).
- [x] Neo: leaf sizing changed to lines-of-code (was uniform); color stays
      coverage-intensity — per user directive. Required schema v7→v8
      (`symbols.line_end`), threaded from the parsers' already-computed
      `line_end` field (previously discarded, zero new parsing work).
- [ ] Trin: UAT — verify `intensity_pct` matches manual `-Vcovered-by`
      counts on a sample of symbols; verify hierarchy rollup (mean, not
      sum) is correct at each level; verify outlier flag excludes ordinary
      constructors but catches a planted synthetic outlier; verify
      efficiency sort/filter against real data
- [ ] Smith: usability test — actually load web UI, confirm the blue/orange
      scale + numeric labels + separate outlier marker are all real (not
      just documented), confirm zoomable icicle navigation is discoverable
- [ ] Morpheus: review Cycle 1 for architecture alignment

## Cycle 2 — Mocking-usage signal (static AST count)

- [ ] Neo: extend existing Python AST walk to count
      `unittest.mock.patch`/`Mock(`/`MagicMock(`/`@patch` usages per test
      function (additive to existing symbol extraction, not a new pass)
- [ ] Neo: surface `mock_call_count` as an added column on the Cycle 1
      efficiency table response/UI — no new view
- [ ] Neo: explicitly no threshold/scoring — raw count only, per Cypher's
      non-goal (no automated judgment)
- [ ] Trin: UAT — spot-check mock counts against a few known test files
- [ ] Smith: usability test — is a raw count useful/legible without a
      threshold, or does it need a caveat/tooltip
- [ ] Morpheus: review Cycle 2, confirm no scope crept into runtime
      instrumentation (explicitly out per architecture doc)

## Non-scope (explicitly deferred)
- Runtime mock-call instrumentation (architecture OQ-2: skip this sprint).
- Automated "delete this test" / "add tests here" actions.
- Test-suite-to-code-area Sankey view — parked in `BACKLOG.md` item 8,
  revisit only if the test-organization-vs-code-structure question comes up
  after this ships.

## Notes
- No Tank/devops gate needed — no new env vars, services, or deployment
  scope (confirmed in architecture doc).
- Cycle 1 is now the larger single chunk of work (tree-build + outlier
  stats + D3 integration) but is architecturally lower-risk than the
  original 2-cycle plan — no pairwise/Jaccard algorithm to get wrong.
