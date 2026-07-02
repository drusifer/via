# Current Sprint Task Board

## Sprint 26 - CLI/Executor Refactoring & Query Performance (Tech Debt)

**Status**: In Progress  
**Stories**: `agents/cypher.docs/SPRINT_26_USER_STORIES.md`  
**Architecture**: `agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md`  
**Task Plan**: `agents/mouse.docs/SPRINT_26_TASKS.md`  

### Cycle 1 - Baseline Stabilization & Unit Testing

- [x] Neo: resolve `test_invalid_container_type_raises_error` baseline test failure
- [x] Neo: resolve `test_query_filepath_imports_filepath` baseline test failure
- [x] Neo: resolve `test_sans_declares_returns_empty_markdown` baseline test failure
- [x] Neo: create dedicated unit tests for `FunctionBodyAnalyzer` in `tests/unit/test_js_body_analyzer.py`
- [x] Trin: verify baseline and new unit tests are green
- [x] Morpheus: review Cycle 1 implementation quality

### Cycle 2 - Unified Parser and Executor

- [x] Neo: refactor argparse and CLI routing in `via/__main__.py` to use command handler registry
- [x] Neo: refactor stage execution in `via/pipeline/executor.py` to use pipeline stage handler registry
- [x] Neo: unify CLI and programmatic `ViaRunner` execution paths
- [x] Trin: verify CLI routing and runner regressions (2026-07-01 — see note below on `make test` fix)
- [x] Smith: review UX/CLI flag consistency (2026-07-01 — ran `via --help`/`index --help`/`stats --help` for real, consistent)
- [x] Morpheus: review Cycle 2 architecture alignment (2026-07-01 — COMMAND_REGISTRY dispatch table, clean)

### Cycle 3 - Performance Optimization

- [x] Neo: implement nested CTE SQLite compiling for chained relationship pipeline stages in `DatabaseStore`
- [x] Neo: optimize Python-side relationship query batching for non-CTE stages
- [x] Trin: verify relationship queries and performance benchmarks (2026-07-01, full suite: 1346 passed, 1 skipped)
- [x] Morpheus: final architecture review (2026-07-01 — CTE building properly isolated, approved)

**2026-07-01 finding**: `make test` was silently broken (bob-protocol layer's generic
`unittest discover` target was shadowing the project's real pytest recipe in
`Makefile.prj` — "0 tests ran" every time it was invoked through `make`/mkf).
Fixed by reordering the include in `Makefile` so project-specific recipes win.
Re-ran for real: **1346 passed, 1 skipped, 4 warnings.** This was a shared-tooling
bug, not a Sprint 26 code defect — but it means no prior `make test` run this
sprint actually verified anything; this is the first real verification.

### Cycle 4 - Class-Based Relationship Type Hierarchy (blast-radius queries)

**Design**: `docs/DESIGN_RELATIONSHIP_HIERARCHY.md` (user-approved directly, 2026-07-01, after sitting unreviewed through 3 pings)

- [x] Neo: real polymorphic hierarchy in `via/core/relationship_types.py` (`Relation`/`Any`/`UpstreamRef`/`DownstreamRef`/leaves), `issubclass`/`__subclasses__` resolution not a lookup table
- [x] Neo: uniform `execute_relation()` entry point in the executor — no `is_category()` branching for query mechanics
- [x] Neo: `blast` canned query added
- [x] Neo: found+fixed a design-doc diagram/prose inconsistency (upstream/downstream direction was backwards in the diagram relative to its own stated definitions; verified empirically)
- [x] Trin: 20 targeted tests + full suite UAT, real end-to-end blast queries verified
- [x] Morpheus: architecture review — APPROVED
- [x] Smith: usability read — recommended removing `declares`/`declared-in` from the categories (design doc's own prose never included them, only the diagram did); Neo applied the fix
- [x] Full suite re-verified after the fix: 1372 passed, 1 skipped

### Verification

- [x] Cycle 1 baseline stabilization and body analyzer tests pass.
- [x] Cycle 2 unified parser and executor routing passes.
- [x] Cycle 3 chained query performance optimization passes.
- [x] Cycle 4 relationship hierarchy / blast-radius queries pass.
- [x] Full suite baseline is completely green (1372 passed, 1 skipped, 2026-07-01).

**Sprint 26: CLOSED (2026-07-01)** — all cycles (including Cycle 4) complete, all gates signed off with real evidence.

## Sprint 27 - Test Coverage & Quality Analysis (Phase 1: Capture) — CLOSED (2026-07-01)

**Stories**: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`
**Architecture**: `agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`
**Task Plan**: `agents/mouse.docs/SPRINT_27_TASKS.md`
**Gates**: Smith Gate 1 APPROVED WITH NOTES, Gate 2 APPROVED
**Final review**: `agents/morpheus.docs/SPRINT27_FINAL_REVIEW.md`

### Cycle 1 - Per-test coverage import (breaking, no back-compat)

- [x] Neo: retire blanket-symbol logic in `via/commands/coverage.py`, add `import-contexts` subcommand
- [x] Neo: per-test synthetic symbols + `covered-by` edges (redefined in place, no new relationship type)
- [x] Neo: clean up stale `<coverage>` symbols in the same import transaction
- [x] Trin: verify per-test `-Vcovered-by` results and no stale data survives re-import
- [x] Morpheus: review Cycle 1 — APPROVED

**Cycle 1 UAT surfaced a critical finding**: 30/92 test files drove `via` via
subprocess, invisible to `pytest --cov-context=test`. Resolved in Cycle 3 by
converting the tests, not by building subprocess-coverage capture — see
`agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`.

### Cycle 2 - Test run metadata

- [x] Neo: `test_runs` table (status/duration/last_run_at, upsert-only), `SCHEMA_VERSION` 6→7
- [x] Trin: verified upsert behavior and status capture for real against the project's own index
- [x] Morpheus: review schema/migration — APPROVED

### Cycle 3 - Capture entrypoint (scope revised: in-process test conversion, not subprocess capture)

- [x] Neo: `tests/via_runner.py` + `conftest.py` redirect shim — 27/30 subprocess-spawning test files now run in-process, zero per-file edits
- [x] Neo: moved the 3 genuine daemon/stdin-protocol tests to new `tests/subprocess/`
- [x] Neo: fixed a real O(tests × files) performance bug in the import (was re-parsing every file per test)
- [x] Neo: `make test-coverage` target + test_runs upsert wiring
- [x] Neo: added a partial-import safety warning (Smith's Heuristic 5 finding)
- [x] Trin: full UAT — 1352 passed/1 skipped, 49204 covered-by relationships across 1217 tests, 1352 test_runs rows, `make test` still clean after
- [x] Smith: usability test — APPROVED
- [x] Morpheus: final review — APPROVED, no dead cruft

**Side benefit**: full suite runtime dropped from ~174s to ~81s (no more
per-test interpreter-startup cost from the subprocess spawns).

**Phase 2 (redundancy/efficiency analysis) remains explicitly out of scope**
per the original requirement — not started.
