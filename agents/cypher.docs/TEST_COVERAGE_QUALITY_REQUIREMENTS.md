# Test Coverage & Quality Analysis — Requirements

**Author**: Cypher (PM)
**Date**: 2026-07-01
**Status**: DRAFT — intake from user request, not yet sequenced into a sprint

## Problem Statement

We have no precise way to measure test *quality* or *efficiency* — only whole-suite
pass/fail and an aggregate `coverage.xml` import (`via/commands/coverage.py`, shipped
Sprint 16 as `covered-by`). That aggregate import tells us which symbols are covered
by the suite as a whole, but not:
- which specific test(s) cover a given symbol
- whether a test's coverage is unique or fully redundant with other tests
- how expensive (duration) a test is relative to the coverage it contributes
- whether a test is currently passing, and when it last ran

Without this, "test quality" can't be measured — only "test exists" or "suite is green."

## Product Direction

Deliver this as two phases. Phase 1 is a pure data-capture capability with no
analysis UI — it must produce trustworthy, per-test records before any analysis
logic is built on top of them. Phase 2 (analysis) is deliberately left open until
Phase 1 data exists to validate against.

### Phase 1 — Per-Test Coverage & Metadata Capture (this requirement)

**User Story 1**: As a developer, I want to run the test suite one test at a time
(rather than as a single aggregate run) so that coverage data can be attributed to
an individual test rather than smeared across the whole suite.

- AC1: There is a runner mode that executes exactly one test case per invocation
  (test id in, pass/fail/error/skip + coverage out).
- AC2: Running "one at a time" for the full suite must be automatable (loop over
  all discovered test ids) without the user hand-picking tests.
- AC3: A single test's failure must not abort collection for the remaining tests.

**User Story 2**: As a developer, I want each test's coverage data captured in
isolation so that I can see exactly which lines/symbols that one test exercises.

- AC1: Coverage data is scoped to the single test run (not merged with other
  tests' coverage in the same file).
- AC2: Per-test coverage data is persisted (not just printed) in a form that can
  be loaded back later for Phase 2 analysis — reuse the existing `covered-by`
  import path in `via/commands/coverage.py` as the integration point rather than
  inventing a second coverage representation, if Morpheus confirms that's feasible
  per-test rather than only per-suite.

**User Story 3**: As a developer, I want test run metadata recorded per test so
I can see its current health at a glance.

- AC1: For each test, record: test id, last-run timestamp, current status
  (pass/fail/error/skip), and duration of that run.
- AC2: Re-running a test updates its record rather than appending an unbounded
  history (latest-status-per-test, not a full run log) — unless Morpheus/Neo
  determine a history table is cheap enough to justify keeping one; PM has no
  strong preference here.
- AC3: This metadata must be queryable/inspectable without reading raw coverage
  XML by hand (exact interface — CLI flag, `via` query integration, or report
  file — is a Morpheus/Neo design decision, not prescribed here).

### Phase 2 — Test Quality & Efficiency Analysis (future, not yet scoped)

Explicitly out of scope for this requirement. Once Phase 1 data exists, revisit
with concrete questions such as: which tests are fully redundant (same coverage
as another test), which tests have the worst coverage-per-second, which symbols
have zero dedicated test coverage even though the suite total is green. Do not
design Phase 2 mechanics until Phase 1 ships and real data is available to reason
about it.

## Non-Goals (Phase 1)
- No redundancy/efficiency scoring yet (Phase 2).
- No change to the existing whole-suite `coverage.xml` → `covered-by` import;
  Phase 1 is additive.
- No mandate on storage engine (SQLite table vs. JSON file vs. reuse of
  `.via/index.db`) — that is an architecture decision for Morpheus.

## Open Questions for Morpheus (architecture)
- OQ-1: Can per-test coverage be captured cheaply with `coverage.py`'s API
  (context/dynamic-context tagging) instead of literally spawning one process
  per test, given the suite has 1300+ tests?
  Note: `coverage.py` has a `--context` / dynamic contexts feature that tags
  coverage data with a label (e.g. the test id) within a single run, which may
  avoid the overhead of one-process-per-test — worth evaluating before assuming
  a fully isolated runner is required.
- OQ-2: Where does per-test metadata live — new SQLite table, or extend
  `via/db/schema.py`, or a sidecar file? Should it be queryable via the existing
  `via` query layer (consistent with `covered-by`) or is a standalone report
  sufficient for Phase 1?
- OQ-3: Which test discovery mechanism is authoritative — `unittest discover`
  (current `make test`) or is a switch to `pytest` (for its native per-test
  coverage/context support) in scope for this request?

## Suggested Sequencing
This is a meaningfully-sized capability (data model + runner changes + at least
one consumption surface). Recommend sequencing as its own sprint (tentatively
Sprint 27) rather than folding into the in-flight Sprint 26 (Tech Debt), which is
already at Cycle 2 verification. Awaiting Morpheus feasibility input on OQ-1
before final story sizing.

## Handoff
Per protocol, next stop is Smith (Gate 1 — user value/discoverability review),
then Morpheus for architecture / OQ-1..3 resolution and sizing.
