# Neo Context

## Post-Sprint Defect Fixes (2026-03-22)

### UX-001: MCP Schema stale text
- `via/mcp/schema.py:54` — "Full-path matching not yet supported" → now documents `-Q` flag
- 1 test added: `test_schema_description_mentions_Q_flag_for_full_path`

### UX-002: Diagram arrows missing in relationship queries
- Root cause: `ClassMatchRecord.base_classes` never populated from DB (parent names in `symbol_references`, not `symbols`)
- Fix: LEFT JOIN with GROUP_CONCAT in `match()`, `_match_with_regex()`, `query_relationships()` in store.py
- `create_from_row()` splits `base_names` → `base_classes` list for class records
- `diagram.py`: removed `if base in class_names` guard + unused `class_names` set
- 1 test added: `test_render_inheritance_arrow_when_parent_not_in_result_set`
- **Key lesson**: `symbols` table has NO base class column — inheritance lives in `symbol_references` only

## Sprint 10 — Cycle 2 Complete (2026-03-22)

### Key Decisions Made

1. **`query_relationships` SQL**: Added `anchor_alias` variable (`"t" if select_from == "s" else "s"`) to correctly fetch anchor mtime regardless of invert flag.

2. **`executor.py` materialization**: Changed `query_relationships` return from a generator pass-through to `list()` + `iter()` so the stale post-filter can inspect all results. Minimal overhead for typical relationship query result sets.

3. **Error check for `--stale` with no mtime**: Checks `all(r.mtime is None for r in results)` — only raises if ALL results lack mtime. Partial None: those records just fail the filter condition and are excluded.

4. **`get_changed_files` None handling**: When `MAX(mtime)` returns NULL (file has no indexed symbols), treat as "changed" (0.0 < last_run would wrongly skip; explicit None check solves it).

5. **prep_tldr incremental stale cleanup**: Incremental mode removes data files for source paths no longer in the current file set. Full mode wipes all (existing behavior preserved).

### Files Modified
- `via/core/match_record.py` — factory passes mtime
- `via/db/store.py` — query_relationships SQL + anchor_mtime
- `via/pipeline/relationship_filter.py` — result_stale field
- `via/pipeline/parser.py` — --stale flag + result_stale wiring
- `via/pipeline/executor.py` — --stale post-filter
- `agents/tools/prep_tldr.py` — incremental mode + argparse

### Test count
931 → 948 (+17)
