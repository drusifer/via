# Trin Context - Working Memory

## Session: 2026-07-02 — Sprint 27 Phase 2 Cycle 1 UAT — PASSES
- Verified Neo's D3 intensity heatmap + efficiency table implementation.
- Independently re-ran (not just trusted) full suite: 1400 passed, 1
  skipped. JS suite: 98 passed.
- Found a second missing `make` public stub: `test-coverage` itself
  (Sprint 27 Phase 1's own capture command) had no stub in the top-level
  Makefile's `else` block, same class of gap Neo found for `test-js`/`lint`.
  Existed in `Makefile.prj` but was unreachable via plain `make`. Fixed.
- Ran the real capture pipeline for real (`make via_index` +
  `make test-coverage`) to get fresh ground-truth data: 52,201 `covered-by`
  relationships across 1,263 tests, 1,399 `test_runs` rows, 20,392 symbols,
  769 files.
- Cross-checked a real symbol's `covering_test_count`/`intensity_pct` via
  the CLI's own `-Vcovered-by` relationship query (independent of Neo's
  code path) against the new `/api/coverage/hierarchy` endpoint — exact
  match (8 tests, 800%).
- Re-verified the absolute/relative `file_path` bugfix Neo found holds at
  real project scale, not just his synthetic smoke-test project — `via`
  correctly appears as the top-level package, no filesystem path segments
  (`home`, `Projects`) leak into the tree.
- Added 2 new real, rerunnable pytest tests capturing both checks:
  `tests/uat/test_sprint27_phase2_cycle1_uat.py` — skips cleanly if no real
  `.via/index.db` exists (won't break CI/fresh clones).
- Full report: `agents/trin.docs/SPRINT27_PHASE2_CYCLE1_UAT.md`. Flagged
  (not blocking): real browser rendering (D3, color scale, outlier marker)
  still needs Smith's usability test — none of it is exercised by jsdom/CI.
- Handed to Morpheus for code review.

## Session: 2026-06-20 — Sprint 26 Cycle 1 UAT — PASSED
- Verified Neo's Cycle 1 implementation.
- Full test suite baseline: **1345 passed, 1 skipped, 4 warnings**.
- Newly added tests in `tests/unit/test_js_body_analyzer.py` verify AST collection boundaries and entity extraction for JS/TS function-body analyzers.
- Baseline errors resolved:
  * `test_query_filepath_imports_filepath` (project file imports matching)
  * `test_sans_declares_returns_empty_markdown` (negative declares container lookup)
- Handed off to Morpheus for lead review.

## Session: 2026-06-20 (Run 2) — Via Query Gauntlet Run (Re-run & Verification)
- Triggered `*qa verify judge` command verification.
- Executed/verified 14 interactive query scenarios using correct, result-stage-first query formats (including corrected directions for Scenario 3 `declared-in`, Scenario 7 `imports`, and Scenario 14 `imports`).
- **Constraints Met**: Zero source files read, zero grep searches performed.
- Overwrote `agents/trin.docs/via_gauntlet_trace.log` with the correct trace log.
- **Observations**:
  * All 14 scenarios now complete successfully.
  * Scenario 3 (`via -mg '*' -tf --via declared-in -mg 'via/core/*' -tF -Q -n 5`) returns the functions defined in `via/core/`.
  * Scenario 7 (`via -mg '*' -tF --via imports -mg 'sqlite3' -ti`) returns files importing `sqlite3`, including `via/db/store.py`.
  * Scenario 14 (`via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`) returns test files importing/covering `executor.py`.
- Handed off to `Smith` for trace re-evaluation and scoring.

## Session: 2026-06-20 — Via Query Gauntlet Run (Verification & Trace)
- Triggered `*judge via` command verification.
- Executed/verified 14 interactive query scenarios on the `.via/index.db` SQLite database and CLI wrapper.
- **Constraints Met**: Zero source files were read, and zero grep searches were performed.
- Updated `agents/trin.docs/via_gauntlet_trace.log` with the exact Scenario 6 command: `python -c "import sqlite3; conn = sqlite3.connect('.via/index.db'); print(conn.execute('SELECT COUNT(*) FROM symbols;').fetchone()[0])"`.
- All outputs successfully logged.
- **Observations**:
  * Scenarios 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13 completed successfully and returned correct, structured symbol records.
  * Scenario 3 (`via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5`) returned empty.
  * Scenario 7 (`via -mg '*' -tF --via imports -mg 'sqlite3' -ti`) returned empty.
  * Scenario 14 (`via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`) returned empty.
- Handed off to `Smith` for evaluation and bug logging.

## Session: 2026-06-19 — Via Query Gauntlet Run
- Triggered `*judge via` command.
- Executed 14 interactive query scenarios on the `.via/index.db` SQLite database and CLI wrapper.
- **Constraints Met**: Zero source files were read, and zero grep searches were performed. All lookups were strictly performed using query tools.
- Exported targeted traces to `agents/trin.docs/via_gauntlet_trace.log`.
- **Observations**:
  * Scenarios 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13 completed successfully and returned correct, structured symbol records.
  * Scenario 3 (`via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q`) returned empty.
  * Scenario 7 (`via -mg '*' -tF --via imports -mg 'sqlite3' -ti`) returned empty.
  * Scenario 14 (`via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`) returned empty.
  * Handed off to `Smith` for token waste review and bug logging.

## Session: 2026-05-06 — Sprint 25 Cycle 2 UAT — PASSED
- Full suite baseline: 1324 passed, 1 skipped, 4 warnings.
- Dart/Flutter relationship fixture verifies StatefulWidget, State<T>, build, declares, imports, inheritance, and calls.
- Regression found and fixed: generic non-Flutter build/ directories remain discoverable when .gitignore is ignored.

## Session: 2026-04-13 — Sprint 24 Cycle 2 UAT — PASSED
- Full suite baseline: 1313 passed, 1 skipped, 4 warnings.
- Parser preserves multiple relationship filters in order.

## Legacy Sprint History
- Sprint 23, 22, 20, 19, 18, 17, 16, 8, 6, 5 UAT all passed and verified.

## Session: 2026-07-01 — Sprint 26 Cycle 2/3 UAT — PASSED (real verification)
- `task.md` showed Cycle 2/3 Trin/Smith/Morpheus checkboxes unchecked despite Neo having moved on to Cycle 4 — investigated for real rather than reconciling paperwork.
- Found `make test` was silently broken: bob-protocol layer's generic `test:` recipe (`unittest discover`) was included *before* the project's real pytest recipe in `Makefile.prj`, so GNU Make's last-recipe-wins rule let the wrong one silently shadow it — every `make test` run reported "0 tests ran" as a failure, meaning no `make test` run this sprint had actually verified anything.
- Fixed by reordering the include in `Makefile` (generic fallbacks defined first, `-include Makefile.prj` after, so project-specific recipes win).
- Re-ran for real: **1346 passed, 1 skipped, 4 warnings.**
- This is a shared-tooling bug (present since Sprint 7 per git history), not a Sprint 26 code defect.

## Session: 2026-07-01 — Sprint 27 Cycle 1 UAT — PASSES + critical Cycle 3 finding
- Verified Neo's per-test coverage import end-to-end against this project's real `.via/index.db` (not just tmp_path unit tests): imported real dynamic-context data, got 94 `covered-by` relationships across 7 tests, correctly per-test attributed. Cleaned up the diagnostic import afterward (deleted the 7 `<test>` symbols) so it doesn't linger in the real index.
- Full suite: 1347 passed, 1 skipped.
- **Critical finding**: 30/92 test files in this project drive `via` via `subprocess.run`, not in-process. Plain `pytest --cov-context=test` measures **zero** code executed inside a subprocess — verified directly (0 lines measured for `via/commands/coverage.py` from a subprocess-only test file). This means Cycle 3's planned `make test-coverage` target, as currently scoped, would produce systematically wrong per-test coverage for ~1/3 of the suite.
- Validated a fix path (not yet implemented): `COVERAGE_PROCESS_START` + a `sitecustomize.py` calling `coverage.process_startup()` does make subprocesses write their own coverage data (confirmed: parallel `.coverage.<host>.<pid>.<rand>` files appeared). Missing piece: per-test context tagging doesn't propagate into subprocess data automatically — the sitecustomize hook would also need to read pytest's `PYTEST_CURRENT_TEST` env var (auto-set by pytest, inherited by subprocess.run by default) and call `switch_context()`. Then a `coverage combine` step merges the parallel files before `import-contexts` runs.
- Full report: `agents/trin.docs/SPRINT27_CYCLE1_UAT.md`. Escalated to Morpheus — this changes Cycle 3 scope, didn't unilaterally expand it myself.
