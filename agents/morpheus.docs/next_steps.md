# Morpheus Next Steps

## Immediate - Ready for Execution

### Phase 1: Dead Code Removal (~500 lines)
1. Remove 6 legacy tables from schema.py
2. Remove 12 legacy indexes from schema.py
3. Remove legacy CRUD from store.py (~350 lines)
4. Remove _store_entities() from indexing.py (~70 lines)
5. Rewrite affected tests to use symbols table
6. Remove _run_match_command() from __main__.py (~70 lines)
7. Remove commands/match.py if fully dead

### Phase 2: Layering Fixes
8. Extract _get_match_metadata() to MatchQueryHelper utility
9. Executor calls helper, passes metadata to renderers
10. DB layer no longer knows about rendering

### Phase 3: DRY Consolidation
11. Extract PatternMatcher utility (shared SQL + Python matching)
12. Extract common renderer metadata pattern to base class
13. Reconcile schema version numbering

## Sprint 7 — Handoff to Neo

Architecture design is in `SPRINT_7_ARCHITECTURE.md`. Neo implements in this order:

1. `MatchRecord.to_dict()` + `RenderType.JSON` + `JsonRenderer` + `-oJ` flag
2. TD-1: `IndexingService.reindex_file()` + `DatabaseStore.delete_file_completely()`
3. `WatchService` `handle_signals: bool = True` param
4. `via/mcp/schema.py` — `build_tool_schema()`
5. `via/mcp/server.py` — `McpServer`
6. Wire `via mcp serve` + `via mcp schema` in `__main__.py`
7. `via/commands/install.py` — `McpInstallTarget` + `InstallTarget` ABC
8. Wire `via install/uninstall/status` in `__main__.py`

Trin: test list in SPRINT_7_ARCHITECTURE.md.

## Architecture Review Document (Sprint 8 prep)
`agents/morpheus.docs/ARCH_REVIEW_SPRINT_8.md`
