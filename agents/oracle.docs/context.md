# Oracle Context

**Last Updated**: 2026-03-19

## Recent Work
- Sprint 6 Watch Mode shipped 2026-03-19
- Two bugs found in UAT and fixed (see Sprint 6 section below)

## Key Files
- `docs/USER_GUIDE.md` - Main user-facing documentation
- `via/__main__.py` - CLI entry point with --help epilog
- `via/core/flag_groups.py` - Flag definitions
- `via/services/watch.py` - WatchService (Sprint 6, new)
- `via/db/store.py` - DatabaseStore

## Lessons Learned (Sprint 6)

### L1: SQLite + threading.Timer = check_same_thread=False required
`DatabaseStore.connect()` uses `sqlite3.connect(db_path, check_same_thread=False)`.
Any code calling DB from a thread other than the one that created the connection REQUIRES this.
`threading.Timer`, `threading.Thread`, `ThreadPoolExecutor` all trigger this.
**Symptom**: Silent failure — exceptions caught by outer try/except, operations report "0 symbols".
**Diagnostic**: Unit test calling target method from `threading.Timer`, assert DB state after.

### L2: Symbols table is NOT cascade-linked to files table
`symbols.file_path` is a plain TEXT column — no FK to `files`.
Deleting a file record does NOT cascade to symbols.
**Pattern for complete file deletion**:
```python
db_store.delete_relationships_for_file(path)  # symbol_references
db_store.delete_symbols_by_file(path)          # symbols
db_store.delete_file_by_path(path)             # files
```
TD item: add `DatabaseStore.delete_file_completely(path)` to encapsulate this triad.

### L3: IndexingService._index_file() bypasses transactions
WatchService calls `indexing_service._index_file()` directly — no transaction wrapper.
Risk: partial reindex if killed mid-operation.
TD item: expose `IndexingService.reindex_file(path)` with begin/commit_transaction.

## Sprint Status Summary
- Sprints 1-6: COMPLETE
- Sprint 7 (MCP Mode): User stories written, under Drew review
- Sprint 8 (Line Index): User stories written, not yet started
