# Neo Context (2026-03-21)

## Current State
- 837 tests passing
- Pylint: 9.46/10
- Sprint 8 shipped: line index (-mL), relationship queries live
- TD-1 closed: `reindex_file()` now calls `resolve_pending_relationships()`

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

## via MCP Relationship Queries (VERIFIED 2026-03-21)
- **KNOWN anchor LEFT (before -Vxxx), `*` RIGHT (after -Vxxx)**
- No -iv: returns things that relate TO anchor (callers, subclasses, importers)
- With -iv: returns what anchor relates TO (callees, base classes, imported modules)
- Working example: `["-mg", "Renderer", "-tc", "-Vinh", "-mg", "*", "-tc"]` → all subclasses ✓

## Tech Debt Backlog (CODE_REVIEW_2026_03_21.md)
- TD-REVIEW-1: Remove `_get_match_metadata()`, push column width to TableRenderer
- TD-REVIEW-2: Add `DatabaseStore.get_symbol_id()`, remove `.conn` access in IndexingService
- TD-REVIEW-3: Simplify `delete_file_completely` (trust FK CASCADE)
- TD-REVIEW-4: Extract `_upsert_raw_file()`, merge 3 file-storage methods
- TD-REVIEW-5: Merge `_store_call_relationships` + `_store_reference_relationships`
