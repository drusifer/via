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
### Sprint 6-7 - Status unknown, need to check

## Current Blockers
Awaiting Drew's answers to 3 questions in ARCH_REVIEW_SPRINT_8.md before proceeding with cleanup.
