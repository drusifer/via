# Cypher Current Task

**Task**: Test Coverage & Quality Analysis — Requirement Intake
**Status**: IN PROGRESS (33% — requirements written, awaiting Morpheus feasibility + Smith gate)
**Updated**: 2026-07-01

## User Request
User request via `*chat TO=cypher *nreq`: a precise way to explore test coverage as
a means of measuring test quality and efficiency. Phase 1 = run tests one at a time,
capture per-test coverage data + metadata (last run, status, duration). Phase 2 =
analysis, deliberately left unscoped until Phase 1 data exists.

## Current Product State
- Requirements written: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`
  (3 Phase 1 user stories + AC, non-goals, 3 open questions for Morpheus).
- Added as backlog item 7 in `BACKLOG.md`, flagged as Sprint 27 candidate.
- Confirmed this doesn't duplicate the existing whole-suite `covered-by` coverage
  import (`via/commands/coverage.py`, Sprint 16) — that's aggregate, this is per-test.
- Posted to CHAT.md, addressed to Morpheus for OQ-1 feasibility (coverage.py
  dynamic contexts vs. one-process-per-test isolation, given 1300+ tests).

## Completed
- [x] Logged user request to CHAT.md.
- [x] Checked existing coverage tooling before writing requirements (avoided duplicate work).
- [x] Wrote `TEST_COVERAGE_QUALITY_REQUIREMENTS.md`.
- [x] Updated `BACKLOG.md`.
- [x] Posted handoff to Morpheus in CHAT.md.

## Next
- Awaiting Morpheus's feasibility read on OQ-1..3.
- Then hand to Smith for Gate 1 (user value/discoverability) review before this
  becomes a sized sprint.

## Note on Sprint 26
Sprint 26 (Tech Debt) planning, which this task file previously tracked at 50%,
has since progressed independently — Mouse/Neo state shows it's now at Cycle 2
verification. That thread is not owned by this task file going forward; see
Mouse's `current_task.md` for its live status.
