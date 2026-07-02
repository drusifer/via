# Test Coverage & Quality Analysis — Architecture (Gate 2)

**Author**: Morpheus (Tech Lead)
**Date**: 2026-07-01
**Sprint**: 27 (candidate)
**Supersedes**: OQ-2 answer in `TEST_COVERAGE_FEASIBILITY_OQ1-3.md` (proposed a
new `tested-by` relationship — overridden by user directive to use one path).

## Decision: redefine `covered-by`, no second relationship type

Per user direction, `covered-by` is altered in place to carry per-test
precision instead of adding a parallel `tested-by` relationship. One
relationship type, one query surface, no back-compat shim.

**Bonus finding**: `covered-by` is already a registered first-class
relationship (`via/core/relationship_types.py:27`, `COVERED_BY = 'covered-by'`)
wired into the existing `-V<relationship>` query flag. Redefining its
semantics in place means **Smith's Gate 1 condition #1 (reuse the existing
query pattern, no bespoke report format) is satisfied automatically** — no new
CLI surface needs to be built at all. Users query per-test coverage the exact
same way they already query `covered-by` today.

## What changes (breaking, by user direction)

### Old behavior (Sprint 16, `via/commands/coverage.py`)
- `via coverage import <coverage.xml>` parses a single aggregate `coverage.xml`.
- Creates ONE synthetic symbol (`symbol_type='module', file_path='<coverage>'`)
  representing "the suite as a whole."
- Every covered source symbol gets one `covered-by` edge to that one symbol.
- Result: binary "is this covered by the suite at all" — no per-test info.

### New behavior
- Capture run uses `pytest` + `pytest-cov` with `--cov-context=test`
  (coverage.py dynamic contexts) — one instrumented run, not one process per
  test (per OQ-1 finding). coverage.py's own SQLite data file records which
  test id touched which line.
- Import step reads coverage.py's per-context data directly (via its data
  API — `CoverageData.contexts_by_lineno()`/context table) instead of parsing
  `coverage.xml`, since plain XML has no context/test-id information.
- Instead of one blanket `<coverage>` symbol, create **one synthetic symbol
  per test id** (`symbol_type='test', file_path='<test>', qualified_name=test_id`).
- Every covered source symbol gets a `covered-by` edge to the specific test
  symbol(s) that covered it — many-to-many, replacing the old one-symbol
  fan-in.
- `via -Vcovered-by` now returns *which test(s)* cover a symbol, not just "the
  suite." Aggregate "is this covered at all" becomes "does this symbol have
  any `covered-by` edge" — same query shape as before, strictly more
  informative result.

### Cleanup required (no back-compat, but no dead cruft either)
Per user: breaking changes are fine as long as we clean up after.
1. Retire `import_coverage_xml()`'s blanket-symbol logic in
   `via/commands/coverage.py` entirely — replace with the per-test-context
   import described above. Do not keep the old function alongside as a
   fallback.
2. Any existing `.via/index.db` with old-style `<coverage>` blanket symbols
   and their `covered-by` edges is stale under the new semantics. Add a
   cleanup step to the new import path: delete pre-existing
   `file_path='<coverage>'` symbols (and their now-orphaned `covered-by`
   edges cascade-delete automatically per the existing FK `ON DELETE CASCADE`
   on `symbol_references`) before writing new per-test data.
3. Update any docs referencing the old aggregate-only coverage import
   (`docs/specs/*`, `USER_GUIDE.md` if it mentions `coverage import`) to
   describe the new per-test semantics — Oracle's job once this ships.
4. Search codebase/tests for any hardcoded assumption of a single `<coverage>`
   symbol (e.g. tests asserting exactly one coverage symbol exists) and update
   them — Neo's job during implementation, flagged here so it isn't missed.

## Test run metadata (status/duration/last-run)

Unchanged from the feasibility read: doesn't fit the symbol/relationship
model (churns every run, not a code-structure fact). New table:

```sql
CREATE TABLE IF NOT EXISTS test_runs (
    test_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,          -- pass | fail | error | skip
    duration_seconds REAL NOT NULL,
    last_run_at TEXT NOT NULL      -- ISO8601
);
```
Upserted per run (latest status only, no history table) — matches Cypher's
AC2 preference and keeps this from growing unbounded across 1300+ tests.

## Capture path (Makefile)

**Revised 2026-07-01, twice.** First revision (superseded): Trin's Cycle 1
UAT found 30 of this project's 92 test files drove `via` by spawning it as a
subprocess, which `pytest --cov-context=test` can't measure inside — the plan
at that point was a `sitecustomize.py` + `COVERAGE_PROCESS_START` + `coverage
combine` mechanism to make subprocess coverage attributable.

**Second revision (shipped): the user chose the simpler root fix instead —
stop spawning subprocesses.** 27 of those 30 files were one-shot CLI
invocations with no real reason to run out-of-process; converted them to run
via `via.__main__.main()` in-process instead (see `tests/via_runner.py` and
the `subprocess.run` redirect shim in `conftest.py`, which transparently
detects `['via', ...]` / `[sys.executable, '-m', 'via', ...]` invocations and
routes them in-process — existing test files needed zero edits). The
remaining 3 files that manage a real background daemon (`via index -w`) or
talk to a server over stdin (`via mcp serve`) genuinely need a real
subprocess and were moved to `tests/subprocess/` to make that explicit. This
made the whole sitecustomize/combine mechanism unnecessary — plain
`pytest --cov-context=test` now measures everything except those 3 files'
literal subprocess calls, which is a much smaller and better-justified gap
than the original 30. Side benefit: full suite runtime dropped from ~174s to
~82s (no more interpreter-startup cost per one-shot CLI test).

Final target, additive to (not replacing) `make test`:

```makefile
test-coverage: install-dev
	. ${VENV_ACTIVATE} && pytest --cov=via --cov-context=test -v tests/
	. ${VENV_ACTIVATE} && python -m via coverage import-contexts .coverage
```

No sitecustomize hook, no `COVERAGE_PROCESS_START`, no combine step needed.

`-v` (pytest verbose) satisfies Smith's Gate 1 condition #2 — visible
per-test progress instead of a silent multi-minute run over 1300+ tests.
`import-contexts` is a new subcommand replacing the old `import` (renamed to
make clear it consumes coverage.py's native context data, not `coverage.xml`).

## Sizing (revised 2026-07-01, second pass)
Was ~6-7pt, then briefly ~9-10pt when subprocess capture (sitecustomize +
combine) looked necessary. Converting 27 test files to run in-process instead
(one shared helper, zero per-file edits needed thanks to the conftest.py
redirect shim) turned out cheaper than building and maintaining the
subprocess-coverage machinery, and fixed a real O(tests × files) performance
bug in `_link_covered_symbols` along the way (was re-parsing every covered
file once per test — minutes at 1300+ tests; fixed to parse each file once).
Net: back down near the original ~6-7pt estimate.

## Handoff
This is the Gate 2 architecture. Sending to Smith to confirm the revised
single-path design still meets both Gate 1 conditions before Mouse plans
Sprint 27 phases.
