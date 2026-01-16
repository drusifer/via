# Morpheus Context - Sprint 2 Architecture

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

**Key Principles**:
- Zero JOINs (all data in symbols table)
- Zero SQL templates (same query pattern for all types)
- Zero class hierarchies
- Trivial query construction
- 3 files total: via/core/types.py, via/db/store.py, via/__main__.py

**Database Schema**:
- `symbols` table: (symbol_name, symbol_type, file_path, line_number, byte_offset, byte_length, qualified_name, parent_name)
- `references` table: (from_symbol_id, to_symbol_id, reference_type, line_number)
- `files` table: Retained for metadata only (not used by match command)

**Symbol Types**: method, class, function, filepath, filename, import, global

**Match Operators**: EXACT (=), GLOB (*,?), LIKE (%,_), REGEXP (full regex)

**Output Format**: `type:file_path:line_number:qualified_name:@byte_offset+byte_length`

**Benefits**:
- Zero JOINs = faster queries
- Trivial to add new symbol types (just enum value + indexer update)
- Trivial to add new operators (just enum value)
- Single query pattern for all types
- No polymorphism overhead
- References table enables future complex queries without affecting match performance

## Project Context

### Sprint 1 - COMPLETE ✅
- CLI index command with AST parsing
- Database schema with all entity tables
- 102/104 tests passing (98%)
- Tagged v0.1.0-mvp

### Sprint 2 - IN PROGRESS
- Focus: `via match` command (renamed from `via query`)
- Scope: Pattern matching with multiple syntaxes (glob/regex/SQL LIKE)
- Entity type filtering (method/class/function/filepath/filename/import/global)
- Simple text output only (rendering deferred to Sprint 3)

### Deferred to Sprint 3+
- `via render` command (syntax highlighting, context lines)
- `via list` command (browse entities)
- `via stats` command (database statistics)
- Multiple output formats (JSON, CSV, table)
- Boolean query operators (AND, OR, NOT)

## Current Blockers
None - architecture complete and ready for implementation.

## Notes
- User feedback emphasized simplicity: "Use database layer with SQL templates"
- Byte offset/length critical for future efficient code rendering
- Streaming results via generators for pipe support
