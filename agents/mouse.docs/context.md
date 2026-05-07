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

## Current Sprint: Sprint 25 Planned

**Latest completed sprint**: Sprint 24
**Current planned sprint**: Sprint 25 - Dart / Flutter Support
**Cycle Protocol**: Mouse plan → Neo TDD → Trin UAT → Morpheus review → Mouse archive/next entry

**Sprint 24 closeout**: `agents/mouse.docs/SPRINT_24_CLOSEOUT.md`
**Architecture spec**: `agents/morpheus.docs/SPRINT_24_ARCHITECTURE.md`
**Sprint 25 task plan**: `agents/mouse.docs/SPRINT_25_TASKS.md`
**Sprint 25 architecture**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`

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
