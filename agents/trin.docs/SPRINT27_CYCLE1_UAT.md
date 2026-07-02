# Sprint 27 Cycle 1 UAT — Per-Test Coverage Import

**Reviewer**: Trin (QA)
**Date**: 2026-07-01

## Verdict: Cycle 1 PASSES. Critical finding for Cycle 3 below.

## Cycle 1 Verification
- Unit tests pass (4/4 in `tests/unit/test_sprint16_c3.py`).
- Full suite: 1347 passed, 1 skipped.
- Real end-to-end check against this project's own `.via/index.db`: ran a
  targeted pytest subset with `--cov-context=test`, then `via coverage
  import-contexts .coverage` for real. Result: 94 `covered-by` relationships
  imported across 7 tests, correctly per-test attributed.
- Cycle 1's contract (correctly process whatever context data it's given,
  clean up stale data on re-import) is met.

## Critical Finding (blocks Cycle 3, not Cycle 1)

**30 of this project's 92 test files drive `via` by spawning it as a
subprocess** (`subprocess.run([sys.executable, "-m", "via", ...])`), not by
calling `via` code in-process. Plain `pytest --cov-context=test` — the
capture mechanism Cycle 3's `make test-coverage` target is scoped to use —
**does not measure code executed inside a subprocess at all.**

Verified directly: ran `pytest --cov=via.commands.coverage --cov-context=test`
over `tests/unit/test_sprint16_c3.py` (which exercises `coverage.py` entirely
through subprocess calls) and confirmed via `CoverageData.lines()`: **0 lines
measured** for `via/commands/coverage.py`, despite the tests passing and
genuinely exercising that code through the CLI.

Impact: if Cycle 3 ships as currently scoped, roughly a third of this
project's own tests would show as covering nothing under the new per-test
`covered-by` data — not because they don't exercise the code, but because the
capture mechanism can't see inside their subprocesses. That directly
undermines the sprint's purpose (measuring test quality/efficiency) with
systematically wrong data for a large fraction of the suite.

## Validated Fix Path (tested in this environment, not yet implemented)
1. `coverage.py` supports subprocess measurement via `COVERAGE_PROCESS_START`
   (env var pointing to a coverage config) + a `sitecustomize.py` that calls
   `coverage.process_startup()`. **Verified**: this causes subprocesses to
   write their own coverage data files (`.coverage.<host>.<pid>.<rand>`).
2. Gap: subprocess data lands under coverage.py's default context (empty),
   not tagged with which pytest test spawned it. To get per-test attribution
   for subprocess-measured code, the `sitecustomize.py` hook needs to also
   read pytest's `PYTEST_CURRENT_TEST` env var (which pytest sets
   automatically for the test's duration, and which `subprocess.run` inherits
   by default since these call sites don't override `env=`) and call
   `switch_context()` with it before `process_startup()` finishes.
3. A `coverage combine` step is then needed to merge the parallel per-process
   data files into one before running `import-contexts`.

## Recommendation
Do not sign off Cycle 3 as currently scoped in `SPRINT_27_TASKS.md` — it needs
an added task: subprocess coverage capture (sitecustomize hook + combine
step) before `make test-coverage` can be trusted. Escalating to Morpheus for
an architecture decision rather than unilaterally expanding scope.
