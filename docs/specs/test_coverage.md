# Test Coverage & Quality Visualization

TL;DR: Capture per-test coverage via `via coverage import-contexts`, query it like any other relationship (`-Vcovered-by`), and browse it visually in the web UI's Coverage view (intensity heatmap, efficiency table, leaf drill-down).

## Table of Contents

- [Capturing Coverage](#capturing-coverage)
- [Querying Coverage](#querying-coverage)
- [Web UI Coverage View](#web-ui-coverage-view)

---

## Capturing Coverage

VIA can attribute test coverage to the *specific test* that produced it,
not just "the suite as a whole." This uses `coverage.py`'s dynamic-context
feature (`--cov-context=test`), so no test rewriting or per-process
isolation is needed even for large suites.

```bash
make test-coverage
```

This is a two-step pipeline (see `Makefile.prj`):

```bash
pytest --cov=via --cov-context=test -v tests/
via coverage import-contexts .coverage
```

`import-contexts` reads the coverage.py data file (`.coverage` by default)
and:
- Links every covered symbol to a synthetic `test` symbol per test id via
  the `covered-by` relationship (many-to-many — a symbol can be covered by
  several tests, a test covers many symbols).
- Upserts per-test run metadata (status, duration, last-run timestamp) into
  a `test_runs` table, if `.via/test_runs.json` is present (written by the
  project's `conftest.py` pytest hook).

**Breaking import, not additive**: re-running `import-contexts` replaces
prior per-test data outright (no accumulation of stale runs). There is no
separate "whole-suite aggregate" mode — `covered-by` always means "covered
by this specific test."

## Querying Coverage

Once captured, coverage is just another relationship — use it with the
normal `--via`/`-V` syntax (see
[Relationships & Container Filters](relationships_and_filters.md)):

```bash
# Which tests cover this function?
via -mg 'process_payment' -tf --via covered-by -mg '*'

# Which symbols does a specific test cover?
via -mg 'test_process_payment_success' -mg '*' --via covers -mg '*'

# Functions with zero test coverage despite a green suite
via -mg '*' -tf --sans covered-by -mg '*'
```

## Web UI Coverage View

The web UI (`via index -w`) has a **Coverage** nav toggle alongside the
normal query builder, with two sub-views:

- **Heatmap**: a navigable, zoomable icicle diagram (package → module →
  class → method/function). Leaf size = lines of code; leaf color = test
  coverage intensity (a colorblind-safe blue→orange scale, blue = gap,
  neutral = adequate, orange = duplication hotspot — never color alone,
  the exact percentage always shows in a tooltip). Leaves whose fan-in is
  statistically unusual vs. their peers (e.g. a method tested far more than
  comparable methods) get a separate dashed-border marker, independent of
  color. Clicking an ancestor node (package/module/class) zooms in;
  clicking a leaf (method/function) drills down to show its qualified
  name, signature, and docstring (re-extracted from source on demand).
- **Efficiency**: a sortable table of test duration vs. symbols covered
  (symbols-per-second), for spotting slow tests that aren't pulling their
  weight.

Backing API: `GET /api/coverage/hierarchy`, `GET /api/coverage/test-efficiency`,
`GET /api/coverage/symbol?id=<id>`.
