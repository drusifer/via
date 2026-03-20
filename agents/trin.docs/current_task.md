# Trin Current Task - Sprint 6 UAT

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
