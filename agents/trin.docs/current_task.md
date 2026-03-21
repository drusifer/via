# Trin Current Task - Query Doc Fixes

## Task: Apply Drew's feedback from QUERY_DOC_REVIEW_2026_03_21.md
**Status**: COMPLETE (100%)
**Date**: 2026-03-21

## Done
- schema.py: fixed Ex02 (name-glob), Ex05 (basename pattern + note), Ex09 (method anchor + bug note)
- schema.py description: added notes on -mg basename matching and -Vr scope limit
- trin.docs/SKILL.md: fixed subclass query direction and references row
- tests/uat/test_documented_queries_uat.py: 884→894 pass, 5→2 xfail
- Remaining xfails: class-level -Vca bug (sprint 9) + -th lowercase invalid

---

# Previous Task - Relationship Regression Fix

## Task: Regression test for resolve_pending_relationships() gap
**Status**: COMPLETE (100%)
**Date**: 2026-03-21

## Root Cause
`IndexingService.index()` stored relationships as pending but never called
`resolve_pending_relationships()` before committing. All live relationship
queries returned empty. Tests called resolve directly on `DatabaseStore`,
masking the gap.

## Fix
1. Added `resolve_pending_relationships()` call in `via/services/indexing.py`
   before `commit_transaction()` (line ~190)
2. Added `tests/integration/test_indexing_resolves_relationships.py` with 3 tests:
   - `test_inheritance_queryable_after_index` — inheritance via full index()
   - `test_import_queryable_after_index` — imports via full index()
   - `test_no_pending_relationships_after_index` — pending table empty after index()

## Test Results: 837 passed, 0 failed

---

# Previous Task - Sprint 6 UAT

## Task: UAT for Sprint 6 Watch Mode
**Status**: COMPLETE (100%)
**Date**: 2026-03-19

## Result: 17/17 PASS — SIGNED OFF

## Bugs Found and Fixed

### Bug 1: SQLite thread safety (CRITICAL)
- **File**: `via/db/store.py` → `connect()`
- **Root Cause**: `sqlite3.connect()` defaults to `check_same_thread=True`. WatchService runs `_execute` in `threading.Timer` threads. DB ops silently failed.
- **Symptom**: "Re-indexed: X (0 symbols)" printed but nothing committed to DB.
- **Fix**: `sqlite3.connect(self.db_path, check_same_thread=False)`
- **Discovered via**: `tests/unit/test_watch_thread_safety.py` (diagnostic unit test)

### Bug 2: Missing symbol deletion on file remove
- **File**: `via/services/watch.py` → `_remove_file()`
- **Root Cause**: `delete_file_by_path` deletes the `files` row but symbols table has no FK CASCADE from files. Symbols were orphaned.
- **Symptom**: Deleted file's symbols still queryable after deletion.
- **Fix**: Added `self.db_store.delete_symbols_by_file(path)` before `delete_file_by_path`

## UAT Coverage
| Story | AC Tested | Result |
|-------|-----------|--------|
| S1: Startup | blocks, initial index, "Watching" msg | ✅ 3/3 |
| S2: Modify | re-indexes .py/.md, prints feedback, updates DB | ✅ 4/4 |
| S3: Create | new file indexed, in DB | ✅ 2/2 |
| S4: Delete | "Removed:", symbols gone from DB | ✅ 2/2 |
| S5: SIGINT | exit 0, "stopped" message | ✅ 2/2 |
| S6: Non-parseable | .json/.txt ignored | ✅ 2/2 |
| S7: Exclusions | --exclude suppresses reindex | ✅ 1/1 |
| S8: Resilience | syntax errors don't crash watcher | ✅ 1/1 |
