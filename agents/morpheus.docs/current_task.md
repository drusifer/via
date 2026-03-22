# Morpheus Current Task

## Task: Sprint 9 Architecture — ReferenceType + Temporal Matcher
**Status**: COMPLETE (100%)
**Date**: 2026-03-21

## Delivered
- `SPRINT_9_ARCHITECTURE.md` — full arch spec for both blockers
- ReferenceType: rename RelationshipType→ReferenceType, add DECLARES/-Vhas, defer CLI unification to Sprint 10
- Temporal: symbols.mtime schema migration (version 5), --newerthan/--olderthan flags, duration.py parser, library API as match() params
- Implementation ordering: TD-REVIEW Phase 1 first, then Story 3/4/5, then Story 1, then Story 2a
- 5 open questions for Drew (see arch doc)

---

## Previous Task: Session 2026-03-21 — Code Quality & MCP Schema
**Status**: COMPLETE (100%)
**Date**: 2026-03-21

## What was done this session

### Lint Cleanup (with Neo)
- Fixed W0613 (unused args) in `indexing.py`, `watch.py`, `python_parser.py`
- Fixed E0401 (pylint false-positive on mcp import) via `pyproject.toml` `ignored-modules`
- Fixed E0402 (relative imports) by changing `source-roots = ["."]`
- Fixed W0621 (duplicate StatsCommand imports) in `__main__.py`
- Pylint score: 9.07 → 9.46/10

### Full Code Review
- 14 code smells identified across store.py, indexing.py, executor.py
- Report written to `agents/morpheus.docs/CODE_REVIEW_2026_03_21.md`
- 5 tech debt tickets created: TD-REVIEW-1 through TD-REVIEW-5
- Key findings: SMELL-1 (DB computes render widths), SMELL-2 (.conn access), SMELL-6 (dup file-store methods)

### via MCP -iv Fix
- Discovered `-iv` direction was wrong in ALL SKILL.md files and schema.py
- Correct rule: **KNOWN anchor goes on LEFT (before -Vxxx), `*` on RIGHT (after -Vxxx)**
- No -iv: returns things that relate TO anchor. With -iv: returns what anchor relates TO.
- Updated neo/trin/oracle/morpheus SKILL.md + mcp/schema.py

### Bug Fix: reindex_file missing resolve_pending_relationships
- TD-1 from Sprint 6 closed: `reindex_file()` now calls `resolve_pending_relationships()`
- Flushed 854 existing pending relationships (571 resolved)
- 837 tests passing

## Next
- TD-REVIEW-1 through TD-REVIEW-5 backlogged for Sprint 9+
- Sprint 9 planning next
