# Mouse Context - Sprint Status

**Last Updated**: 2026-05-06

## Sprint Status

| Sprint | Theme | Status | Tests |
|--------|-------|--------|-------|
| 1 | Core Indexing | ✅ SHIPPED | — |
| 2 | Match & Query | ✅ SHIPPED | — |
| 3 | Pipeline & Renderers | ✅ SHIPPED | — |
| 4 | Tech Debt | ✅ SHIPPED | — |
| 5 | Relationships | ✅ SHIPPED | 661 |
| 6 | Watch Mode | ✅ SHIPPED | 713 |
| 7 | MCP Mode | ✅ SHIPPED | 794 |
| 8 | Line Index | ✅ SHIPPED | 837 |
| 9 | ReferenceType + -Vhas + Temporal | ✅ SHIPPED | 908 |
| 10 | --ref-type + --stale + prep_tldr incr + PathFilter | ✅ SHIPPED | 983 |
| 11 | JavaScript/TypeScript indexing | ✅ SHIPPED | — |
| 12 | Web query surface | ✅ SHIPPED | — |
| 13 | Web UX / follow-up delivery | ✅ SHIPPED | — |
| 14 | Query extensions + usability fixes | ✅ SHIPPED | 1178 |
| 15 | MCP ergonomics + index completeness | ✅ SHIPPED | 1235 |
| 16 | String intelligence + reusable query workflows | ✅ SHIPPED | 176 targeted |
| 17 | Link intelligence + HTTP bridge primitives | ✅ SHIPPED | 138 targeted |
| 18 | Polymorphic JS parser refactor | ✅ SHIPPED | 96 targeted |
| 19 | ViaQueryBuilder | ✅ SHIPPED | 30 targeted |
| 20 | Builder adoption + library usability | ✅ SHIPPED | 50 targeted |
| 21 | JS body analyzer + MCP runner adoption | ✅ SHIPPED | — |
| 22 | Query confidence + error recovery | ✅ SHIPPED | 197 targeted |
| 23 | Recognition over recall | ✅ SHIPPED | 67 targeted |
| 24 | Result-stage-first query model | ✅ SHIPPED | 1313 full-suite |

## Current Sprint: Sprint 26 Planned

**Latest completed sprint**: Sprint 25
**Current planned sprint**: Sprint 26 - CLI/Executor Refactoring & Query Performance (Tech Debt)
**Cycle Protocol**: Mouse plan → Neo TDD → Trin UAT → Morpheus review → Mouse archive/next entry

**Sprint 25 closeout**: `agents/mouse.docs/SPRINT_25_CLOSEOUT.md`
**Architecture spec**: `agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md`
**Sprint 26 task plan**: `agents/mouse.docs/SPRINT_26_TASKS.md`
**Sprint 26 architecture**: `agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md`

### Sprint 24 Cycle Status

| Cycle | Phase | Assigned | Status |
|-------|-------|----------|--------|
| 1 | Result-first executor + inverse types + docs/tests | Neo → Trin → Morpheus | Approved |
| 2 | Multi-filter relationship chaining | Neo → Trin → Morpheus | Approved |

## Team Notes
- Use `make` skill (not raw Bash) for all test runs — team rule
- Activate venv before Python/via commands
- Sprint 22 must preserve query semantics while improving error clarity.
- Highest-risk areas: valid empty results vs invalid query errors, multi-type regression, and docs accidentally implying inverse `declares`.
- Executor redesign and shortcut syntax remain out of scope.
- Sprint 22 closeout: `agents/mouse.docs/SPRINT_22_CLOSEOUT.md`
- Final tracked baseline: 197 targeted passing tests across QA gates.
- Smith approved final HCI wording.
- Sprint 23 planned around recognition over recall.
- Sprint 23 must use `--canned` as the single shortcut surface.
- Do not ship fake `callees` or `declared-in-file` support.
- Sprint 23 closeout: `agents/mouse.docs/SPRINT_23_CLOSEOUT.md`
- Final tracked baseline: 67 targeted passing tests across QA gates.
- Follow-up risk: reconcile relationship runtime orientation with the user-facing command model.
- Sprint 24 closeout: `agents/mouse.docs/SPRINT_24_CLOSEOUT.md`
- Final tracked baseline: 1313 passed, 1 skipped, 4 warnings.
- Result-stage-first runtime orientation is now implemented.
- Multi-filter relationship chaining is implemented with parser ordering and executor post-filter tests.
- Sprint 25 planned for Dart/Flutter structural indexing.
- Sprint 25 Cycle 0 is a hard dependency spike: prove Python-loadable Dart tree-sitter grammar before parser implementation.

## Sprint 26 Cycle 1 - Completed (2026-06-20)
- Neo fixed baseline failures and added JS body analyzer unit tests.
- Trin verified that all 1345 tests are green.
- Morpheus reviewed and approved.
- Closed Cycle 1. Ready to launch Cycle 2.

## Sprint 26 Cycle 2 - Code Complete (2026-06-21)
- Neo refactored argparse parser and stage executor to use polymorphic registries (`COMMAND_REGISTRY` and `STAGE_REGISTRY`).
- Neo unified CLI and programmatic `ViaRunner` execution paths.
- Baseline test suite is fully verified green (1345 passed).
- Pending formal QA verification and Tech Lead review signatures.
- NOTE: `task.md` shows Cycle 3 items already checked off by Neo (CTE query optimization) even though this context predates that — reconcile actual Cycle 2/3 status against `task.md` directly next time this thread is picked up, rather than trusting this file alone.

## Sprint 27 Planning — Test Coverage & Quality Analysis (2026-07-01)
- Cypher → Morpheus (feasibility + architecture) → Smith (Gate 1 + Gate 2, both approved) chain completed for a new requirement: per-test coverage capture + test run metadata.
- Key design point from Morpheus's architecture: `covered-by` is redefined in place (per-test synthetic symbols) rather than adding a new relationship — per explicit user directive, no back-compat shim, breaking change with in-transaction cleanup of old blanket `<coverage>` data.
- Broke Sprint 27 into 3 cycles: (1) per-test `covered-by` import + old-data cleanup, (2) `test_runs` metadata table, (3) `make test-coverage` entrypoint + full UAT.
- Plan doc: `agents/mouse.docs/SPRINT_27_TASKS.md`; mirrored into `task.md` below the Sprint 26 board.
- Sprint 27 is queued behind Sprint 26 (which is still open, Cycle 2/3 unresolved) — did not reorder or touch the Sprint 26 board.
- No Tank/devops gate needed — no new env vars, services, or deploy scope.
- Handed to Morpheus for plan-vs-architecture review.

## Sprint 26 Closure (2026-07-01) — real verification
- Per user request, had Trin/Morpheus/Smith actually verify Cycle 2/3 instead of trusting stale state files.
- Found + fixed a real `make test` bug (bob-protocol layer's generic `unittest discover` target was shadowing the project's real pytest recipe due to Makefile include order — present since Sprint 7, not a Sprint 26 defect).
- Re-verified: 1346 passed, 1 skipped. All Cycle 2/3 gates (Trin, Smith, Morpheus) now genuinely signed off in `task.md`.
- **Sprint 26 is CLOSED.**
- Sprint 27 is now unblocked (per user's stated preference: wait for Sprint 26 to close before starting Sprint 27) but not yet started.
