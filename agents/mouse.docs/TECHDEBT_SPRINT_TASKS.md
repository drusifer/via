# Tech Debt Sprint - Task Breakdown

**Created by**: Mouse (SM)
**Date**: 2026-02-13
**Reference**: morpheus.docs/ARCH_REVIEW_SPRINT_8.md

---

## Sprint Goal
Remove ~570 lines of dead code before Sprints 6-8. Clean foundation for Watch Mode, MCP, and Line Index features.

---

## Phase 1: Dead Code Removal (P0)

### Task 1.1: Remove Legacy Tables from schema.py
**Assignee**: @Neo
**Est**: 1 pt
**Files**: `via/core/schema.py`

- [ ] Remove `functions` table CREATE statement
- [ ] Remove `classes` table CREATE statement
- [ ] Remove `imports` table CREATE statement
- [ ] Remove `globals` table CREATE statement
- [ ] Remove `log_statements` table CREATE statement
- [ ] Remove `markdown_headings` table CREATE statement
- [ ] Verify schema still initializes correctly

**Acceptance**: `via index .` works, no errors on fresh DB

---

### Task 1.2: Remove Legacy Indexes from schema.py
**Assignee**: @Neo
**Est**: 1 pt
**Files**: `via/core/schema.py`

- [ ] Remove 12 indexes associated with legacy tables
- [ ] Keep indexes for `symbols`, `files`, `symbol_references`, `pending_relationships`

**Acceptance**: Index creation doesn't error, queries still fast

---

### Task 1.3: Remove Legacy CRUD from store.py
**Assignee**: @Neo
**Est**: 3 pts
**Files**: `via/core/store.py`

- [ ] Remove `insert_function()` method
- [ ] Remove `insert_class()` method
- [ ] Remove `insert_import()` method
- [ ] Remove `insert_global()` method
- [ ] Remove `get_functions_by_file()` method
- [ ] Remove `get_functions_by_name()` method
- [ ] Remove `get_classes_by_file()` method
- [ ] Remove `get_classes_by_name()` method
- [ ] Remove `get_imports_by_file()` method
- [ ] Remove `get_globals_by_file()` method
- [ ] Remove any other legacy table accessors

**Acceptance**: ~350 lines removed, no import errors

---

### Task 1.4: Remove _store_entities() from indexing.py
**Assignee**: @Neo
**Est**: 2 pts
**Files**: `via/services/indexing.py`

- [ ] Remove `_store_entities()` method (~70 lines)
- [ ] Remove all calls to `_store_entities()`
- [ ] Verify `_store_symbols()` is the only path for symbol storage
- [ ] Clean up any orphaned imports

**Acceptance**: Indexing still works, only `symbols` table populated

---

### Task 1.5: Rewrite Affected Tests
**Assignee**: @Neo
**Est**: 3 pts
**Files**: `tests/test_database.py`, `tests/test_indexing_service.py`

- [ ] Identify tests that use legacy tables
- [ ] Rewrite tests to verify `symbols` table instead
- [ ] Remove tests that only verify legacy table writes
- [ ] Add test: verify legacy tables no longer exist in schema
- [ ] Run full test suite, fix any failures

**Acceptance**: `make test` passes, no legacy table references in tests

---

### Task 1.6: Remove Legacy Match Subcommand
**Assignee**: @Neo
**Est**: 2 pts
**Files**: `via/__main__.py`, `via/commands/match.py`

- [ ] Verify `via match` subcommand is unused (grep for usage)
- [ ] Remove `_run_match_command()` from `__main__.py` (~70 lines)
- [ ] Remove match subcommand parser registration
- [ ] Remove `via/commands/match.py` if fully dead
- [ ] Clean up imports

**Acceptance**: `via -mg '*' -tc` still works, `via match` removed

---

### Task 1.7: Final Verification
**Assignee**: @Trin
**Est**: 1 pt

- [ ] Run full test suite: `make test`
- [ ] Run indexing on via codebase: `via index .`
- [ ] Run sample queries: `-mg '*' -tc`, `-mr '.*Service' -tc`, etc.
- [ ] Verify line count reduction (~500+ lines removed)
- [ ] No regressions in functionality

**Acceptance**: All tests pass, via works as before, code is leaner

---

## Phase 1 Summary

| Task | Points | Assignee | Status |
|------|--------|----------|--------|
| 1.1 Remove legacy tables | 1 | Neo | [ ] |
| 1.2 Remove legacy indexes | 1 | Neo | [ ] |
| 1.3 Remove legacy CRUD | 3 | Neo | [ ] |
| 1.4 Remove _store_entities | 2 | Neo | [ ] |
| 1.5 Rewrite tests | 3 | Neo | [ ] |
| 1.6 Remove match subcommand | 2 | Neo | [ ] |
| 1.7 Final verification | 1 | Trin | [ ] |
| **Total** | **13** | | |

---

## Phase 2: Layering Fixes (P1) - After Phase 1

| Task | Points | Description |
|------|--------|-------------|
| 2.1 | 2 | Extract `_get_match_metadata()` to MatchQueryHelper |
| 2.2 | 2 | Wire executor to use helper, pass metadata to renderers |

---

## Phase 3: DRY Consolidation (P2) - After Phase 2

| Task | Points | Description |
|------|--------|-------------|
| 3.1 | 2 | Extract PatternMatcher utility |
| 3.2 | 1 | Extract common renderer metadata to base class |
| 3.3 | 1 | Fix schema version numbering |

---

## Execution Order

```
Task 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7
                                         ↓
                                   Phase 1 Done
                                         ↓
                                   Sprint 6 Ready
```

**Note**: Tasks 1.1-1.4 can be done in sequence (each builds on prior). Task 1.5 (tests) should come after schema/store changes. Task 1.6 is independent. Task 1.7 is final QA gate.
