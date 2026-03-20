# Sprint 6 Architecture Review — Watch Mode

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-19
**Status**: SIGNED OFF with tech debt items recorded

---

## Verdict: APPROVED

Sprint 6 ships a correct, well-tested Watch Mode. Architecture is sound. Two bugs were caught by Trin's UAT and fixed before sign-off. Tech debt items below are non-blocking.

---

## What's Good

| Area | Assessment |
|------|-----------|
| Observer pattern | `_ViaEventHandler` delegates cleanly to `WatchService` — no business logic in the event handler |
| Debounce | `threading.Lock` + `threading.Timer` pattern is correct and minimal |
| SIGINT | Save/restore original handler, `threading.Event`-driven loop — textbook |
| Error resilience | Exceptions in `_execute` are caught; watcher survives parse errors |
| TDD | 30 unit + integration tests. 17 UAT scenarios. Both bugs caught pre-ship |
| Thread safety fix | `check_same_thread=False` in `DatabaseStore.connect()` is the right call |

---

## Tech Debt (Non-Blocking)

### TD-1: No transaction in `_reindex_file` (MEDIUM)

`WatchService._reindex_file` calls `indexing_service._index_file()` directly, bypassing the `begin_transaction / commit_transaction` wrapper used by `IndexingService.index()`.

**Risk**: If the process is killed mid-reindex, the DB can be left in partial state — old symbols deleted, new ones only partially inserted.

**Fix (Sprint 7 or 8)**: Either:
- Expose a `IndexingService.reindex_file(file_info)` method that wraps `_index_file` in a transaction, OR
- Add `begin_transaction / commit_transaction` around the `_index_file` call in `_reindex_file`

### TD-2: `WatchService` takes redundant `db_store` parameter (LOW)

`db_store` is already accessible via `indexing_service.db_store`. Passing it separately creates a potential for divergence.

**Fix**: Remove `db_store` parameter. Access via `self.indexing_service.db_store` internally.

### TD-3: Lazy imports inside methods (LOW)

```python
# In _reindex_file:
from via.core.discovery import DiscoveredFile

# In __init__:
import pathspec
```

Move both to module-level imports. Lazy imports mask dependencies.

### TD-4: `_discovery._should_include_file` is a private call (LOW)

`WatchService._is_watched_file` calls `self._discovery._should_include_file(path)` — accessing a private method of `FileDiscovery`. Should be public API.

**Fix**: Add `FileDiscovery.should_include(path: str) -> bool` public method.

### TD-5: `IOBase` imported but unused (TRIVIAL)

```python
from io import IOBase  # line 17 — never used
```

Remove.

---

## Bug Post-Mortem

### Bug 1: SQLite `check_same_thread=True` (CRITICAL — FIXED)

**Root Cause**: `threading.Timer` callbacks run in a thread different from the one that created the DB connection. SQLite's default `check_same_thread=True` raises a `ProgrammingError` which was silently caught, resulting in no-op reindexes ("Re-indexed: X (0 symbols)").

**Lesson**: Any service using `threading.Timer` or `ThreadPoolExecutor` for DB work must have `check_same_thread=False`. This should be documented in DatabaseStore.

**Fix applied**: `sqlite3.connect(self.db_path, check_same_thread=False)`

### Bug 2: Missing `delete_symbols_by_file` in `_remove_file` (MEDIUM — FIXED)

**Root Cause**: `symbols` table has no `FOREIGN KEY` to `files` (by design — denormalized). `delete_file_by_path` deletes the `files` row but leaves orphaned symbols.

**Lesson**: Any code deleting a file from the index must call the deletion triad: `delete_relationships_for_file` → `delete_symbols_by_file` → `delete_file_by_path`. This pattern should be a single `delete_file_completely(path)` method on DatabaseStore.

**Fix applied**: Added `self.db_store.delete_symbols_by_file(path)` to `_remove_file`.

---

## Architectural Recommendation for TD-2 + Bug 2

Add a `DatabaseStore.delete_file_completely(path)` method that encapsulates the deletion triad. This eliminates the risk of callers forgetting one of the three steps:

```python
def delete_file_completely(self, path: str) -> None:
    """Remove file, its symbols, and its relationships from the index."""
    self.delete_relationships_for_file(path)
    self.delete_symbols_by_file(path)
    self.delete_file_by_path(path)
```

And similarly, expose `IndexingService.reindex_file(path)` as a public method to replace the `_index_file` private call in WatchService.

---

## Sprint 6 Final State

| Metric | Value |
|--------|-------|
| Tests added | 48 (27 unit + 1 diagnostic + 3 integration + 17 UAT) |
| Total tests | 709 |
| Coverage | 83% |
| Bugs found in UAT | 2 |
| Bugs fixed before ship | 2 |
| Regressions | 0 |
