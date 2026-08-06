# Neo Next Steps

## Resume Point: MCP 2 migration complete

1. No implementation remains for the dependency regression.
2. Await Trin QA feedback on the MCP 2 migration.
3. If QA finds a runtime protocol issue, reproduce with the focused MCP files
   before changing code; tool registration and stdio API compatibility are
   already covered.

## Verification state
- Focused MCP tests: 17 passed.
- Fast lint is blocked by five unrelated, pre-existing findings documented in
  `FASTMCP_MCP2_MIGRATION_Summary_2026-08-06T17-30.md`.

---

## Resume Point: Sprint 27 Phase 2 Cycle 1 fully CLOSED (AC7 + LOC sizing added and verified)

## On Resume
1. Cycle 1 is done — nothing pending from it.
2. Cycle 2 (mocking-usage signal, static AST count) is next per
   `agents/mouse.docs/SPRINT_27_PHASE2_TASKS.md`, not yet started.

## Standing reminders
- Use `make test FILE=<path>` for targeted runs while iterating; full suite
  only at checkpoints.
- `make test-js`/`make test-coverage`/`make lint`/`make lint-fast`/
  `make lint-slow`/`make test-e2e`/`make test-all` are all now wired
  through `make` (none had public stubs before this cycle — `test-coverage`
  itself, Sprint 27 Phase 1's own flagship command, was unrunnable via
  plain `make` until this cycle).
- `symbols.file_path` is stored **absolute**; any new query needing a
  project-relative path must call `self._to_relative_path()`.
- Small peer-group z-score outlier detection needs leave-one-out stats
  (see `via/web/api/coverage.py::_compute_outliers`).
- `symbols.line_end` exists now (schema v8) — every parser already computes
  it (`FunctionEntity`/`ClassEntity.line_end` in `base.py`), so any new
  feature needing a symbol's line span doesn't need new parser work, just
  a SELECT.
- Hardcoded `SCHEMA_VERSION == N` literals in tests break on every
  migration — compare against the imported `SCHEMA_VERSION` constant
  instead (fixed 2 more instances of this in `test_line_index.py`/
  `test_sprint11_c2.py` this cycle; watch for more if another migration
  lands).
- After any schema/source change that should show up in coverage-heatmap
  ground-truth checks, re-run `make via_index && make test-coverage` before
  trusting `tests/uat/test_sprint27_phase2_cycle1_uat.py` — it reads
  whatever `.via/index.db` currently has, not live source.
- Reference: `agents/neo.docs/SPRINT26_CYCLE4_SUMMARY.md` for the relationship
  hierarchy design if extending it later.
