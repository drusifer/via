# Oracle Context

**Last Updated**: 2026-03-20

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
- Sprints 1-7: COMPLETE (Sprint 7 shipped 2026-03-20, 794 tests)
- Sprint 8: Next up — TD-S7-1 (async queue), TD-S7-2 (lighter MCP), TD-3/4 carry-forward
- Sprint 9 (-Vhas): User stories written 2026-03-20

## Session 2026-03-20 Work (Sprint 6)
- 48 via/ source files updated with standardized module docstrings (Code Module form #5)
- TLDR template standardized: one marker `TLDR:` across all file types, 4-space indent, blank-line terminated
- `make tldr` updated: runs `agents/tools/tldr.py` (uses `via` for file discovery)
- README.md rewritten with correct syntax, make test rules, watch mode, relationships
- `--help` fixed: output flags standalone (not after --via), bad example removed
- `agents/templates/_template_tldr.md` — 5 forms, all consistent with rg pattern

## Session 2026-03-20 Work (Sprint 7 doc groom)
- README.md: Added -oJ flag, MCP Mode section, updated project structure and arch diagram
- TEST_STATUS.md: Full rewrite — was Jan 2026 / 465 tests, now current (794 tests, Sprint 7)
- docs/USER_GUIDE.md: Added -oJ, Watch Mode section, MCP Mode section (install/serve/schema)
- via/mcp/__init__.py: Updated docstring to Code Module TLDR form #5
