# Morpheus Context

## Key Architectural Decisions

### Match Command Architecture — v5.0 (CURRENT)
- **Single `symbols` table**: Denormalized, zero-JOIN lookups
- **SymbolType/MatchOp Enums**: Pure value objects
- **MatchRecord hierarchy**: Factory-created from DB rows
- **References table**: Separate for relationship queries (calls, imports, inherits)

## Architecture Audit (2026-02-11) — Known Tech Debt
- SMELL-1: `_get_match_metadata()` in store.py computes render column widths (DB/render coupling)
- SMELL-2: `_store_call_relationships` accesses `db_store.conn` directly (abstraction bypass)
- SMELL-3+4: `delete_file_completely` and `delete_relationships_for_file` duplicate FK CASCADE work
- SMELL-6: 3 near-identical file-storage methods in indexing.py
- Full report: `agents/morpheus.docs/CODE_REVIEW_2026_03_21.md`
- TD tickets: TD-REVIEW-1 through TD-REVIEW-5

## via MCP Relationship Query Syntax (VERIFIED 2026-03-21)
**Correct rule**: KNOWN anchor goes on LEFT (before `-Vxxx`), `*` on RIGHT (after `-Vxxx`)
- No `-iv`: returns things that relate TO the anchor (callers, subclasses, importers)
- With `-iv`: returns what the anchor relates TO (callees, base classes, imported modules)

Examples that WORK:
- Subclasses of Renderer: `["-mg", "Renderer", "-tc", "-Vinh", "-mg", "*", "-tc"]`
- Callers of count_symbols: `["-mg", "count_symbols", "-tm", "-Vca", "-mg", "*", "-tm"]`
- Who imports via.db.store: `["-mg", "via.db.store", "-Vimp", "-mg", "*"]`
- What index() calls: `["-mg", "index", "-tm", "-Vca", "-iv", "-mg", "*", "-tm"]`

## Sprint History
- Sprints 1-5: COMPLETE
- Sprint 6: SHIPPED (2026-03-19) — WatchService, incremental indexing
- Sprint 7: SHIPPED (2026-03-20) — MCP Mode, FastMCP, JsonRenderer
- Sprint 8: SHIPPED (2026-03-21) — Line index (-mL), relationship queries live

## Session 2026-03-21 — MCP + Watch Hardening + Code Quality
- `resolve_pending_relationships()` now called in `reindex_file()` (TD-1 closed)
- `-iv` syntax corrected in all SKILL.md files and mcp/schema.py
- Pylint score 9.07 → 9.46/10
- 14 code smells identified, 5 TD tickets created

## Current Blockers
None.
