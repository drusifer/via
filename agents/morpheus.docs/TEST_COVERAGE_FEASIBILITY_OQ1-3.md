# Test Coverage & Quality Analysis — Feasibility Read (OQ-1..3)

**Author**: Morpheus (Tech Lead)
**Date**: 2026-07-01
**Responding to**: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`

## OQ-1: per-test coverage without one-process-per-test

**Verified in this environment**: `coverage.py` 7.13.4 and `pytest-cov` 7.0.0 are
already installed (pytest 9.0.2 too), even though `make test` currently runs
`python -m unittest discover`.

**Answer: yes, dynamic contexts solve this in a single run.** `coverage.py`
supports `--dynamic-context=test_function`, and `pytest-cov` exposes the same
via `--cov-context=test`. Each measured line gets tagged with the currently
running test's id inside coverage.py's own SQLite data file (a `context` table
+ per-line context linkage) — no need to fork a process per test. For a
1300+-test suite this is the only viable option; literal process-per-test
would multiply suite runtime by process-startup overhead across 1300+ tests.

**Architectural implication for AC1**: Cypher's AC1 says "a runner mode that
executes exactly one test case per invocation." Recommend relaxing this to an
outcome-level AC — *coverage is attributable per test id* — rather than
prescribing one-process-per-test as the mechanism. The dynamic-context
approach satisfies the user's actual goal (per-test attribution) at a fraction
of the cost. Flagging back to Cypher to adjust wording before Smith's gate,
since this is a product-facing AC change, not just an implementation detail.

**pytest is compatible with existing unittest-style tests** — pytest
auto-discovers `unittest.TestCase` subclasses without rewriting them, so
adopting pytest as an *additional* execution path does not require a test
rewrite.

> **Superseded 2026-07-01**: the `tested-by` relationship proposed below was
> overridden by user directive — use one path, alter `covered-by` in place
> instead of adding a second relationship type. See
> `agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md` for the current design.

## OQ-2: where per-test data lives

Two different kinds of data, two different treatments:

1. **Coverage attribution (which lines a test touches)** — reuse the existing
   `covered-by` pattern from `via/commands/coverage.py` rather than inventing a
   parallel representation. Concretely: create one synthetic symbol per test
   id (same mechanism already used for the aggregate coverage artifact
   symbol), then link source symbols to it via a relationship. Recommend a
   **distinct relationship name** (e.g. `tested-by`) rather than overloading
   `covered-by`, so aggregate-suite coverage and per-test coverage remain
   independently queryable and Sprint 16 behavior is untouched (Non-Goal in
   Cypher's doc — no changes to the existing import path, this is additive).
2. **Test run metadata (status/duration/last-run)** — does not fit the
   symbol/relationship model (it's not a code-structure fact, it churns on
   every run). Recommend a new dedicated table, e.g. `test_runs(test_id
   PRIMARY KEY, status, duration_seconds, last_run_at)`, upserted per run per
   Cypher's AC2 (latest status only, no unbounded history — agree, history
   would fight the "just measure quality" goal and bloat the DB with 1300+
   rows growing every run for no product benefit yet). Whether this table
   lives in `.via/index.db` or a separate sidecar db is a Cycle-1
   implementation detail Neo can decide; either is fine since it doesn't
   couple to the code-index schema.

## OQ-3: unittest vs. pytest as authoritative discovery

Recommend **adding** a pytest-based execution path alongside the current
`make test` (unittest discover), not replacing it in Phase 1. Rationale:
- pytest-cov's dynamic contexts are the mechanism OQ-1 depends on.
- pytest already runs the existing unittest-style suite unmodified — zero test
  rewrite cost.
- Replacing `make test` outright is a larger, separate tech-debt decision this
  requirement shouldn't be forced to make. Keep `make test` as-is; add a new
  target for the coverage-capture path.

## Sizing input for Cypher/Mouse

This is feasible within a single sprint. Rough shape once AC1 wording is
adjusted: schema + import path extension (~2-3pt), new pytest-based capture
target wired through `make` (~2pt), minimal report/query surface per US3-AC3
(~2pt). Confirms Cypher's Sprint 27 (not Sprint 26) sequencing call.

## Handoff
Back to Cypher to adjust AC1 wording per the OQ-1 finding, then proceed to
Smith for Gate 1. Full architecture doc (schema DDL, relationship naming,
Makefile target) to follow after Smith's Gate 1 approval, per normal sprint
flow.
