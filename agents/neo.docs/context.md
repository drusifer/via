# Neo Context (2026-03-21)

## Current State
- 893 tests passing, 1 xfailed
- Sprint 9 Cycle 2 complete: Stories 3, 4, 5 done
- Baseline: 884→893 (+9: 8 new tests + 1 xfail fixed)

## Key Patterns

### Qualified Names
`_calculate_qualified_name(file_path, entity_name, parent_class)` in `indexing.py`

### Transaction Pattern
Use `db_store.begin_transaction()` / `commit_transaction()` / `rollback_transaction()` — never raw `cursor.execute("BEGIN")`

### File Upsert Pattern
`get_file_by_path()` → if existing: `update_file()` else: `insert_file()`

### Relationship Resolution
- `insert_pending_relationship()` during indexing
- `resolve_pending_relationships()` after ALL symbols indexed (called in both `index()` and `reindex_file()`)

### `_store_relationships()` (NEW — Sprint 9 TD-REVIEW-5)
Merged replacement for old `_store_call_relationships` + `_store_reference_relationships`:
```python
self._store_relationships(
    file_info, parse_result.calls, 'calls',
    lambda c: (c.caller_type, c.caller_parent, c.caller_name, c.callee_name),
)
```

### FK CASCADE
`symbol_references` has FK CASCADE on `symbols(id)`. Deleting a symbol automatically removes its relationships. `delete_file_completely()` now relies on this.

### Window Function for total_matches
`match()` uses `COUNT(*) OVER ()` in SELECT to get total_matches without a pre-query. Regex path (`_match_with_regex`) does not set total_matches (no buffering).

## via MCP Relationship Queries (VERIFIED 2026-03-21)
- **KNOWN anchor LEFT (before -Vxxx), `*` RIGHT (after -Vxxx)**
- No -iv: returns things that relate TO anchor (callers, subclasses, importers)
- With -iv: returns what anchor relates TO (callees, base classes, imported modules)

## Sprint 9 Phase 1 Done
All 5 TD-REVIEW items complete. Files modified:
- `via/db/store.py` — added `get_symbol_id()`, removed `_get_match_metadata()`, removed `delete_relationships_for_file()`, simplified `delete_file_completely()`, added window function to `match()`
- `via/services/indexing.py` — `_store_relationships()` replaces two old methods, `_upsert_raw_file()` replaces three old methods
- `via/renderers/table.py` — computes column widths from actual data now
- `tests/unit/test_database_streaming.py` — removed 9 stale metadata tests
- `tests/unit/test_relationships.py` — removed `test_delete_relationships_for_file`

## Sprint 9 Cycle 2 Done — Key Decisions

### Story 4: Class Anchor Fix (executor.py + store.py)
- `subject_parent_pattern` added to `query_relationships` for `s.parent_name GLOB ?`
- Executor: detects `rel_type='calls' + subject_type='class'` → transforms to method+parent lookup

### Story 5: Filepath Qualified Name (indexing.py)
- `file_info.path` is ABSOLUTE. Was stored as `qualified_name` → broken for `-Q` path patterns
- Fix: `os.path.relpath(file_info.path, db_store.index_root)` for filepath `qualified_name`

### Story 3: Expanded -Vr (python_parser.py + indexing.py)
- 3 new extraction methods: `_extract_class_structural_references`, `_extract_decorator_references`, `_extract_annotation_references`
- Class-level refs use `referencer_type='class'` → `_store_relationships` updated to handle 'class' actor type
- Fixture: `extras.py` added to UAT project (AnnotatedClass, decorated_func)

## Next Sprint 9 Work (Cycle 3)
- Story 1: `-Vhas` / DECLARES — rename RelationshipType→ReferenceType, add DECLARES, add _store_declares_relationships()
