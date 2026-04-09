# Mouse Context - Sprint Status

**Last Updated**: 2026-04-08

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

## Current Sprint: Sprint 20 Shipped

**Latest completed sprint**: Sprint 20
**Cycle Protocol**: Mouse plan → Neo TDD → Trin UAT → Morpheus review → Mouse archive/next entry

**Sprint 20 task file**: `agents/mouse.docs/SPRINT_20_TASKS.md`
**Architecture spec**: `agents/morpheus.docs/SPRINT_20_ARCHITECTURE.md`
**User stories**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`

### Sprint 20 Cycle Status

| Cycle | Phase | Assigned | Status |
|-------|-------|----------|--------|
| 1 | S20-1 | Neo → Trin → Morpheus | ✅ COMPLETE |
| 2 | S20-2 | Neo → Trin → Morpheus | ✅ COMPLETE |

## Team Notes
- Use `make` skill (not raw Bash) for all test runs — team rule
- Activate venv before Python/via commands
- Sprint 20 must preserve CLI semantics while reducing builder/CLI drift
- Highest-risk parity areas: default limits, relationship behavior, and docs/export mismatch
- Executor redesign remains backlog, not Sprint 20 scope
- Sprint 20 archived with a 50-test targeted make baseline
