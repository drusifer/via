# Smith Context

**Last updated**: 2026-07-01

## Session: 2026-07-02 — Sprint 27 Phase 2 Cycle 1 Usability Test
- Wrote a real Playwright e2e spec (`tests/e2e/coverage.spec.js`, 4 tests)
  and ran it via `make test-e2e` — 26/26 pass including the new ones, real
  Chromium not jsdom.
- Actually looked at the screenshots (own rule) — D3 loaded for real in
  this environment, rendered a genuine zoomable icicle.
- Found one real, non-blocking finding: "Adequate (100%)" neutral-gray
  legend swatch has low contrast against the page background, easy to
  miss (Heuristic #1). Filed for later, not blocking.
- Confirmed the colorblind-safe scale and separate outlier visual marker
  are present as designed (couldn't visually confirm the mid/high end of
  the color range or an actual outlier marker in this pass — the e2e
  fixture has zero coverage data, everything renders at 0%/blue; Trin
  already verified those cases at the data level against the real project).
- Full report: `agents/smith.docs/SPRINT27_PHASE2_CYCLE1_USABILITY.md`.
  APPROVED WITH 1 MINOR NOTE. Cycle 1 can close.

## Session: 2026-07-01 — Sprint 27 Phase 2 Gate 2 (architecture)
- Reviewed `agents/morpheus.docs/SPRINT27_PHASE2_ARCHITECTURE.md`.
- Confirmed both Gate 1 notes addressed: colorblind-safe sequential scale +
  numeric % label (Story 1), quantitative `overlap_pct` in Story 2's
  response shape (not just visual grouping density).
- APPROVED: `agents/smith.docs/SPRINT27_PHASE2_GATE2_REVIEW.md`.
- Agreed with Morpheus's grouped-list-over-matrix/diagram default for Story
  2, and folding Story 4's mock-count into Story 3's table as a column
  rather than a new view.
- Handed to Mouse for cycle breakdown.

## Session: 2026-07-01 — Sprint 27 Phase 2 Gate 1 (user stories)
- Reviewed `agents/cypher.docs/SPRINT27_PHASE2_USER_STORIES.md` (4 stories:
  coverage heatmap, redundancy view, efficiency table, mocking signal).
- APPROVED WITH NOTES: `agents/smith.docs/SPRINT27_PHASE2_GATE1_REVIEW.md`.
- Stories tracked my own pre-work opinion closely — no major objection.
- 2 non-blocking notes carried to Morpheus's Gate 2 architecture:
  (1) heatmap must use a colorblind-safe scale + numeric % label, not
  red/green color alone (~8% of men have red-green colorblindness);
  (2) redundancy view needs a quantitative overlap %/count label, not just
  visual density — "these look similar" isn't actionable.
- Handed to Morpheus for Gate 2, including Story 4's mocking-signal OQs.

## Session: 2026-07-01 — Coverage visualization opinion (pre-Phase-2)
- User asked directly (`*chat @Smith`) for an opinion on a web-mode
  enhancement to visually inspect test coverage: redundant tests, overly
  mocked tests, uncovered code — sankey or heatmap ideas floated.
- Checked real code before opining: `via/web/static/app.js` already
  lazy-loads Mermaid and renders `data.mermaid_source` — a diagram pipeline
  exists. Sprint 27 Phase 1 schema (`covered-by` + `test_runs`) supports a
  coverage view. Grepped schema.py — zero mocking signal anywhere.
- Opinion: split into 3 separate visuals rather than one diagram —
  (1) file coverage heatmap (buildable now, cheapest win), (2) test-overlap
  matrix for redundancy (beats Sankey past ~30 nodes; we have 1217 tests),
  (3) mocking metric (blocked — data gap, needs Cypher to define the metric
  first, not a viz problem at all).
- Recommended this go through the normal Cypher -> Morpheus -> Smith
  requirement chain (new web API surface), not a quick `*impl`.
- Full doc: `agents/smith.docs/SPRINT27_PHASE2_VIZ_OPINION.md`.

## Session: 2026-07-01 — Test Coverage & Quality Analysis Gate 1
- Reviewed `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`.
- APPROVED WITH NOTES: `agents/smith.docs/TEST_COVERAGE_GATE1_REVIEW.md`.
- Value is real: lets developers see what tests actually exercise, not just suite-green.
- `tested-by` naming is consistent with existing relationship grammar (`covered-by`, `declares`, etc.) — no objection.
- 2 conditions passed to Morpheus for the architecture doc: (1) expose `tested-by` via the existing `-V<relationship>` query pattern rather than a bespoke report format (heuristic #6/#10); (2) capture run over 1300+ tests must show visible per-test progress, not run silently (heuristic #1).
- Handed to Morpheus for Gate 2 architecture.
- Morpheus's Gate 2 doc incorporated a user directive to drop the proposed `tested-by` relationship and redefine `covered-by` in place instead (one path, no back-compat shim, breaking change OK with cleanup). This exceeds Gate 1 condition 1 — zero new query surface at all.
- Gate 2 APPROVED: `agents/smith.docs/TEST_COVERAGE_GATE2_REVIEW.md`. Both Gate 1 conditions confirmed met. Flagged a docs-update note for Oracle post-ship (rename to `import-contexts`, update docs/specs + USER_GUIDE).
- Handed to Mouse for Sprint 27 phase breakdown.

## Session: 2026-07-01 — Sprint 26 Cycle 2 real UX review
- Ran `via --help`, `via index --help`, `via stats --help` for real (per own rule: never approve based on spec alone).
- `--db PATH`, verbosity flags, directory positional args all consistent across subcommands after the CLI registry refactor — no regressions or naming drift.
- Cycle 2 UX/CLI flag consistency APPROVED. Sprint 26 is now closed.

## Session: 2026-06-20 (Iteration 4) — Sprint 26 Gate 2 Review
- Reviewed architecture design in `agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md`.
- **Verdict**: APPROVED.
- **Findings**: The polymorphic registries (S26-1) and CTE optimization (S26-2) conform to heuristics. The strict validation check correction for declares queries (S26-4) improves error help text (Heuristic #9).
- Documented findings in [SPRINT_26_GATE2_REVIEW.md](file:///home/drusifer/Projects/via/agents/smith.docs/SPRINT_26_GATE2_REVIEW.md).
- Approved gate and handed off to Mouse.

## Session: 2026-06-20 (Iteration 3) — Sprint 26 Gate 1 Review
- Reviewed user stories in `agents/cypher.docs/SPRINT_26_USER_STORIES.md`.
- **Verdict**: APPROVED.
- **Findings**: S26-1 (Unified Executor/Parser) and S26-2 (Performance optimization) are aligned with HCI principles (Consistency/Efficiency). S26-3 and S26-4 stabilize testing (Error Prevention).
- Documented findings in [SPRINT_26_GATE1_REVIEW.md](file:///home/drusifer/Projects/via/agents/smith.docs/SPRINT_26_GATE1_REVIEW.md).
- Approved gate and handed off to Morpheus.

## Session: 2026-06-20 (Iteration 2) — Via Query Gauntlet Traces Re-Evaluation
- Evaluated the new UAT logs from `agents/trin.docs/via_gauntlet_trace.log` after Neo's bug fixes.
- **Verdict**: Succeeded on 14/14 scenarios. Final TES Score: 100.
- **Key Findings**: All scenarios pass. The previous empty outputs for Scenarios 3, 7, and 14 are now correctly populated and resolved. No remaining bugs.
- Approved launch and closed the judge loop.

## Session: 2026-06-20 (Iteration 1) — Via Query Gauntlet Traces Analysis
- Evaluated UAT logs from `agents/trin.docs/via_gauntlet_trace.log` covering 14 scenarios.
- **Verdict**: Succeeded on 11/14 scenarios. Final TES Score: 85. 3 scenarios (3, 7, and 14) returned empty due to query engine bugs.
- **Bugs Cataloged**:
  1. BUG-1: qualified_name of class and function symbols is stored as absolute (e.g. starting with `.home.drusifer...`) because `_calculate_qualified_name` is passed the absolute `file_info.path` instead of relative path during indexing. Also, inversion logic overrides in `_get_actual_inverted` map types/joins incorrectly for declares relationships.
  2. BUG-2: The query engine fails to resolve file-level imports (`-tF --via imports -mg 'sqlite3' -ti`) and file-to-file imports (`-tF --via imports -mg '*executor*' -tF -Q`) because external module symbols are stored with `file_path = '<external>'` and lack declares relationships in the database, causing the declares join constraint to fail on the filter side of imports queries.
- Handed off to `Neo` to fix codebase bugs (`*swe fix judge`).

## Session: 2026-06-19 — Via Query Gauntlet Traces Analysis
- Evaluated UAT logs from `agents/trin.docs/via_gauntlet_trace.log` covering 14 scenarios.
- **Verdict**: Succeeded on 11/14 scenarios. High query token-efficiency. 3 scenarios returned empty due to query engine bugs.
- **Bugs Cataloged**:
  1. `declares` type validation inversion (line 256 in [executor.py](file:///home/drusifer/Projects/via/via/pipeline/executor.py#L256)) causing crashing errors.
  2. relationship queries ignoring `-Q` / qualified name matching (line 1159 in [store.py](file:///home/drusifer/Projects/via/via/db/store.py#L1159)) causing directory-scoped queries to return empty.
- Handed off to `Neo` to fix codebase bugs.

## Sprint 25 Gate 1 Review (2026-05-06)
Full review: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`
- APPROVED WITH NOTES.
- Dart/Flutter stories are valuable because they give Flutter developers normal VIA structural navigation.
- Keep `--lang dart` as the user-facing language filter; do not introduce a separate `--lang flutter`.

## Sprint 25 Gate 2 Architecture Review (2026-05-06)
Full review: `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`
- APPROVED.
- Cycle 0 dependency spike is UX-positive because it prevents premature claims of Dart support.

## Sprint 25 Cycle 2 HCI Review (2026-05-06)
Full review: `agents/smith.docs/SPRINT_25_CYCLE_2_HCI_REVIEW.md`
- APPROVED.
- README, user guide, and MCP schema now show Dart/Flutter examples through normal VIA surfaces.

## Legacy Sprint History
- Sprint 22, 23, 20, 19, 18, 17, 16, 10, 9 usability reviews all completed and signed off.
