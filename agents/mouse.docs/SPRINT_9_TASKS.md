# Sprint 9 Task Breakdown

**Scrum Master**: Mouse
**Sprint Theme**: ReferenceType architecture, `-Vhas`, temporal matching with per-symbol timestamps, tech debt phase 1
**Points**: ~15
**Architecture**: FULLY RESOLVED by Morpheus (see `morpheus.docs/SPRINT_9_ARCHITECTURE.md`)
**Date**: 2026-03-21

---

## Cycle Protocol

Each cycle: **Mouse plan** → **Neo TDD** → **Trin UAT** → **Mouse plan** (next task)

After Neo completes a phase, Trin runs UAT. Mouse then picks next task.
User does `/clear` between cycles to keep context clean.

---

## Implementation Order (from Morpheus arch doc)

### Phase 1: Tech Debt — MUST come first (cleans up files Story 1/2a will touch)

| Task | Story | Points | Status | Blocker |
|------|-------|--------|--------|---------|
| TD-REVIEW-2 | Add `DatabaseStore.get_symbol_id()` | 1 | ⬜ TODO | none |
| TD-REVIEW-5 | Merge `_store_call` + `_store_ref` methods | 1 | ⬜ TODO | none |
| TD-REVIEW-3 | Simplify `delete_file_completely` (trust CASCADE) | 0.5 | ⬜ TODO | none |
| TD-REVIEW-4 | Extract `_upsert_raw_file()` | 0.5 | ⬜ TODO | none |
| TD-REVIEW-1 | Move column widths to `TableRenderer` | 1 | ⬜ TODO | none |

### Phase 2: Stories 3, 4, 5 — No dependencies, parallel-ready

| Task | Story | Points | Status | Notes |
|------|-------|--------|--------|-------|
| Story 3 | Expand `-Vr` reference tracking | 3 | ⬜ TODO | Parser change, 5 xfail tests → pass |
| Story 4 | Fix class anchor bug for `-Vca` | 1 | ⬜ TODO | Executor change, 1 xfail test → pass |
| Story 5 | `-Q` full-path matching for file symbols | 1 | ⬜ TODO | store.py + executor, 1 xfail test → pass |

### Phase 3: Story 1 — Depends on TD-REVIEW-2 + TD-REVIEW-5

| Task | Story | Points | Status | Notes |
|------|-------|--------|--------|-------|
| Story 1 | `-Vhas` has-a relationship (DECLARES) | 3 | ⬜ TODO | Blocked until Phase 1 complete |

### Phase 4: Story 2a — Schema migration, independent of Phase 3

| Task | Story | Points | Status | Notes |
|------|-------|--------|--------|-------|
| Story 2a | Temporal matcher + per-symbol timestamps | 4 | ⬜ TODO | Schema migration SCHEMA_VERSION 4→5 |

---

## Task Detail Summaries

### TD-REVIEW-2: `DatabaseStore.get_symbol_id()`
**File**: `via/db/store.py`, `via/services/indexing.py:478,501`
**Problem**: `IndexingService` calls `self.db_store.conn.execute(...)` directly — bypasses abstraction.
**Fix**: Add `get_symbol_id(name, symbol_type, file_path, parent_name) -> Optional[int]` to `DatabaseStore`.
**Tests**: Existing tests must still pass. Add unit test for `get_symbol_id`.

### TD-REVIEW-5: Merge `_store_call` + `_store_ref`
**File**: `via/services/indexing.py:472–516`
**Problem**: Near-identical methods differing only in attribute names and `rel_type`.
**Fix**: Single `_store_relationships(symbols, rel_type, get_related_names)` method.
**Tests**: Existing 837 tests must still pass.

### TD-REVIEW-3: Simplify `delete_file_completely`
**File**: `via/db/store.py:357–384, 1089–1127`
**Problem**: Manually deletes `symbol_references` rows that FK CASCADE already handles.
**Fix**: Delete from `symbols` only → cascade handles references. Audit/remove `delete_relationships_for_file`.
**Tests**: Watch mode integration tests must pass.

### TD-REVIEW-4: Extract `_upsert_raw_file()`
**File**: `via/services/indexing.py:560–616`
**Problem**: `_store_unparsed_file`, `_store_oversized_file`, `_store_file_with_error` — identical skeleton.
**Fix**: Single `_upsert_raw_file(file_info, *, unparsed=False, oversized=False, error=None)`.
**Tests**: Existing indexing tests must pass.

### TD-REVIEW-1: Move column widths to `TableRenderer`
**File**: `via/db/store.py:553–595`, `via/renderers/`
**Problem**: Every `match()` call fires extra SQL for column widths — even for `-oR` (raw) output.
**Fix**: Remove `_get_match_metadata()`. `TableRenderer` computes widths during first pass. `total_matches` lazy.
**Tests**: Table output tests must pass. Raw output tests must NOT fire extra SQL.

### Story 3: Expand `-Vr` Reference Tracking
**File**: `via/parsers/python_parser.py`
**Scope**: Track class base names, decorators, module-level usages, function signature type annotations, class-body type annotations.
**xfail tests**: 5 tests in `tests/uat/test_documented_queries_uat.py` (Finding 5) → must PASS.
**Tests**: No regression in existing reference query behavior.

### Story 4: Fix Class Anchor Bug for `-Vca`
**File**: `via/pipeline/executor.py`
**Problem**: `-tc` anchor for `-Vca` returns empty — call relationships stored on method symbols, not class.
**Fix**: When anchor is `-tc` for `-Vca`, executor expands to include all methods where `parent_name = class_name`.
**xfail tests**: 1 test in `test_documented_queries_uat.py` (Finding 2) → must PASS.
**Also update**: `schema.py` example 9, SKILL.md files.

### Story 5: `-Q` Full-Path Matching for File Symbols
**Files**: `via/db/store.py`, `via/pipeline/executor.py`
**Problem**: `-mg` matches basename only. For `-tF`, `qualified_name = full_path`.
**Fix**: When `-Q` flag set and symbol type is filepath/filename, match on `qualified_name` instead of `symbol_name`.
**xfail tests**: 1 test in `test_documented_queries_uat.py` (Finding 1 Option C) → must PASS.
**Also update**: `schema.py` Ex05.

### Story 1: `-Vhas` Has-A Relationship (DECLARES)
**Files**: `via/core/relationship_types.py`, `via/core/flag_groups.py`, `via/services/indexing.py`, `via/pipeline/executor.py`
**Steps**:
1. Rename `RelationshipType` → `ReferenceType` in `relationship_types.py` (update all imports)
2. Add `DECLARES = 'declares'` to enum
3. Add `-Vhas`/`--via-has` to `flag_groups.py` → maps to `ReferenceType.DECLARES`
4. Add `_store_declares_relationships()` to `IndexingService` (no parser changes)
5. Add `DECLARES` dispatch branch in `PipelineExecutor._execute_relationship_query()`
6. Container type validation with precise error messages
**Tests**: All Story 1 acceptance criteria; xfail tests from Story 1 → PASS.

### Story 2a: Temporal Matcher + Per-Symbol Timestamps
**Files**: `via/db/schema.py`, `via/db/store.py`, `via/services/indexing.py`, `via/pipeline/parser.py`, `via/pipeline/executor.py`, NEW: `via/core/duration.py`
**Steps**:
1. Schema migration: `ALTER TABLE symbols ADD COLUMN mtime REAL` (SCHEMA_VERSION 4→5)
2. Add `idx_symbols_mtime` index
3. Update `IndexingService` to set `mtime` from file `st_mtime` on insert
4. Add `--newerthan`/`--olderthan` flags to `_create_match_parser()` in `parser.py`
5. Add `result_newerthan_seconds`/`result_olderthan_seconds` to `RelationshipFilter`
6. Update `executor.py` to pass temporal params to `db.match()` and `db.query_relationships()`
7. Create `via/core/duration.py` with `parse_duration()`
8. Add `newerthan_seconds`/`olderthan_seconds` params to `DatabaseStore.match()`
9. Add `query_symbols_changed_since()` / `query_symbols_changed_before()` library API
**Tests**: Temporal query integration tests; duration parsing unit tests; schema migration test.

---

## Current Cycle

**Cycle 1**: Phase 1 TD-REVIEW batch (TD-REVIEW-2 + TD-REVIEW-5 together, then TD-REVIEW-3 + TD-REVIEW-4, then TD-REVIEW-1)
**Neo**: Implement all 5 TD-REVIEW items (they're small — batch them)
**Trin**: UAT on TD-REVIEW batch — no regressions, 837 tests still passing

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ⬜ TODO | Not started |
| 🔵 IN PROGRESS | Neo working on it |
| 🔴 BLOCKED | Waiting on dependency |
| 🟡 UAT | With Trin for review |
| ✅ DONE | Complete and tested |
