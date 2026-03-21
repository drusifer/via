# Morpheus Context - Architecture Review 2026-02-11

## Key Architectural Decisions

### Match Command Architecture Evolution
- **v1.0**: Complex TypeHandler + PatternMatcher class hierarchies with registries
- **v2.0**: Simplified to thin DataStore.match() layer with direct SQL mapping
- **v3.0**: Polymorphic design with SymbolType and MatchOp class hierarchies
- **v4.0 FINAL**: Pure Enums + SQL templates (CURRENT)

### v5.0 Architecture (Denormalized - CURRENT)
**Date**: 2026-01-13

**Core Design**:
- **Single `symbols` table**: Denormalized table eliminates ALL JOINs
- **Simple query pattern**: `SELECT * FROM symbols WHERE symbol_type = ? AND symbol_name {op} ?`
- **SymbolType Enum**: Just string values (method, class, function, etc.)
- **MatchOp Enum**: Provides (op_name, sql_op, needs_escaping)
- **MatchResult Dataclass**: Includes byte_offset and byte_length for direct file seeking
- **References table**: Separate table for future relationship queries (calls, imports, inherits)

## Architecture Audit (2026-02-11)

### Dead Weight Identified
- 6 legacy tables (functions, classes, imports, globals, log_statements, markdown_headings) are created and some are written to but NEVER queried in production
- All production queries use the denormalized `symbols` table
- Legacy table getters in store.py only called from test code
- ~500 lines removable across schema.py, store.py, indexing.py

### Layering Issues
- `_get_match_metadata()` in store.py computes rendering column widths (DB knows about rendering)
- `PipelineExecutor` has deep knowledge of renderer internals

### Duplication
- Pattern matching logic exists in both store.py (SQL) and executor.py (Python)

### What's Clean
- Renderer hierarchy (base, context options, source extraction)
- Pipeline architecture (parser, executor, types)
- SymbolType/MatchOp enums
- MatchRecord hierarchy
- RendererFactory

## Project Context

### Sprints 1-5 - COMPLETE
### Sprint 6 — SHIPPED (2026-03-19), Sprint 7 — SHIPPED (2026-03-20, commit e714929)

### Sprint 6 Review (2026-03-19)
- STATUS: APPROVED — see `SPRINT_6_REVIEW.md`
- 2 bugs found+fixed in UAT: `check_same_thread=False` on DatabaseStore, missing `delete_symbols_by_file` in `_remove_file`
- 5 tech debt items: TD-1 (no transaction in _reindex_file) is most important
- Recommend `DatabaseStore.delete_file_completely()` + `IndexingService.reindex_file()` for Sprint 7

## Sprint 7 Architecture (2026-03-20) — SHIPPED
- Design in `SPRINT_7_ARCHITECTURE.md` (rev 2, approved)
- Key decisions: FastMCP SDK, WAL+separate-connections, logging replaces print(), to_dict() in JsonRenderer
- TD-S7-1 (async queue), TD-S7-2 (lighter MCP) deferred to Sprint 8+

## Sprint 8 Architecture (2026-03-20) — APPROVED
- Design in `SPRINT_8_ARCHITECTURE.md`
- Key decisions:
  - New `line_offsets` table (FK→files, CASCADE delete, PRIMARY KEY file_id+line_number)
  - SCHEMA_VERSION 3 → 4 with migration
  - `-mL` as optional arg on match parser (NOT in MATCH_FLAGS mutex group)
  - Line slice is relative to matched symbol's start line
  - `_apply_line_slice()` in PipelineExecutor updates byte_offset/byte_length post-match
  - Zero changes to RawRenderer/FormattedRenderer — they already use byte ranges
  - Negative indices (last N lines) deferred — TD-S8-1
- 3 OQs for Drew: OQ-1 (relative vs absolute — recommend relative), OQ-2 (which files — recommend parsed=True), OQ-3 (negative indices — defer)

## Sprint 8 — SHIPPED (2026-03-21)

## Session 2026-03-21 — MCP + Watch Hardening

### Decisions Made
- `resolve_pending_relationships()` now called in `IndexingService.index()` before commit (was missing — all live relationship queries returned empty)
- MCP server (`via/mcp/server.py`) now calls `watch_store.initialize_schema()` on startup — handles DB migration for old DBs. Only watch_store does it (one writer owns schema).
- MCP tool description now served from `build_tool_schema()` — agents discover all flags+examples via MCP protocol
- `WatchService` switched from `recursive=True` to non-recursive per-directory watches using `FileDiscovery._should_include_dir()` to prune excluded dirs at the OS level
- `_ViaEventHandler` now handles `on_created` for directories to dynamically add watches
- `watchdog.observers.inotify_buffer` silenced to WARNING in MCP logging config
- All persona SKILL.md files updated with via MCP + relationship query guidance
- TD-WATCH-1 backlogged: extract `PathFilter` from `FileDiscovery`

## Current Blockers
None.
