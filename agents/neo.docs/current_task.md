# Neo Current Task

**Task**: Sprint 27 Phase 2 Cycle 1 — AC7 drill-down + LOC sizing (post-closure addition)
**Status**: COMPLETE (100%) — Cycle 1 fully CLOSED
**Updated**: 2026-07-02

## Completed (this addition, on top of the already-closed base Cycle 1)
- [x] Schema v7→v8: `symbols.line_end` column + migration
      (`via/db/schema.py`, `via/db/store.py::initialize_schema`).
- [x] Threaded `line_end` through `insert_symbol()` and all 3
      `via/services/indexing.py` call sites (class/method/function) — the
      value was already computed by every parser (`FunctionEntity`/
      `ClassEntity.line_end` in `via/parsers/base.py`), just previously
      discarded.
- [x] `build_coverage_hierarchy()` now computes `loc` per leaf
      (`line_end - line_number + 1`, clamped to >=1, defaults to 1 for
      pre-migration symbols) — D3 sizes icicle leaves by this, color stays
      coverage-intensity (two independent visual dimensions, per user
      directive).
- [x] New `DatabaseStore.get_symbol_detail()` + `get_symbol_coverage_counts()`
      extended to also select `line_number`/`line_end`.
- [x] New `via/web/api/coverage.py::get_symbol_detail()` +
      `_extract_signature_and_docstring()` (mirrors
      `via/renderers/usage.py`'s existing AST re-parse pattern) +
      `_format_args()` (matches `python_parser.py`'s no-defaults-shown
      convention). Non-Python symbols degrade gracefully.
- [x] New `GET /api/coverage/symbol?id=` endpoint in `via/web/handler.py`.
- [x] Frontend: leaf click now dispatches to drill-down
      (`showSymbolDetail`/`renderSymbolDetail`) instead of zoom; ancestor
      click still zooms. New `#coverage-symbol-detail` panel
      (`template.py` markup + CSS).
- [x] Researched (not guessed) the lambda-coverage question: Python lambdas
      aren't indexed as symbols at all currently; their covered lines
      already roll into the enclosing named function/method (coverage is
      line-range-based, not symbol-based) — so lambda coverage is already
      implicitly reflected with zero extra work. A lambda as its *own* leaf
      would need new parser capability — flagged as a backlog candidate,
      not implemented.
- [x] Tests: +11 Python unit tests (100% coverage maintained on
      `coverage.py`), +9 JS tests (106 total), +1 e2e drill-down test
      (27 total e2e), +2 new real ground-truth UAT tests (LOC + docstring
      against the actual re-indexed `via` project).
- [x] Fixed 2 more pre-existing test bugs surfaced by the schema bump:
      `test_line_index.py` and `test_sprint11_c2.py` both hardcoded
      `SCHEMA_VERSION == 7`/`"7"` — fixed to compare against `SCHEMA_VERSION`
      dynamically so the next migration doesn't break them again.
- [x] Full suite: 1424 passed, 1 skipped. Re-indexed + re-captured real
      coverage data twice during this session to keep ground-truth checks
      honest against the latest code.
- [x] Updated `task.md` and `SPRINT_27_PHASE2_TASKS.md` — Cycle 1 now
      fully CLOSED (was "substantially complete, 1 AC deferred").

## Next
- Cycle 1 is done. Cycle 2 (mocking-usage signal) is next per
  `agents/mouse.docs/SPRINT_27_PHASE2_TASKS.md`, not yet started.
- Reported the lambda-coverage answer to the user directly (not just
  buried in docs) since they asked it as an open question.
