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

## Sprint 9 Architecture Decisions (2026-03-21)

### ReferenceType
- `symbol_references.reference_type` column already EXISTS — no DB schema change for the type discriminator
- `RelationshipType` → rename to `ReferenceType` (aligns Python with DB column name)
- Add `DECLARES = 'declares'` to enum; map `-Vhas` to it
- `_store_declares_relationships()`: no parser changes — uses `file_path` + `parent_name`
- CLI unification (`--ref-type <value>` for raw column queries) → deferred Sprint 10

### Temporal Matcher
- `symbols.mtime REAL` — schema migration needed (SCHEMA_VERSION 4 → 5)
- `symbols.mtime` set from file's `st_mtime` at index time; watch events update only symbols in changed file
- CLI flags: `--newerthan <duration>` / `--olderthan <duration>` (global modifiers, not per-stage)
- Duration format: `1h`, `2d`, `1w`, `30m`, `30s`
- Library API: add `newerthan_seconds`/`olderthan_seconds` params to existing `match()`
- Duration parser: `via/core/duration.py`
- Full arch doc: `agents/morpheus.docs/SPRINT_9_ARCHITECTURE.md`

### Implementation Order
TD-REVIEW Phase 1 → Stories 3+4+5 → Story 1 → Story 2a

## Sprint 10 Architecture Decisions (2026-03-22)

### S10-1: `--ref-type`
- Third relationship specifier: detected in `_find_relationship_split()` alongside `-Vinh` and `--via`
- Added to `match_parser` with `choices=` for help visibility (pre-parsed, not used at parse time)
- Error message lists valid values from `ReferenceType.get_value_map()`

### S10-2: `--stale`
- Add `mtime: Optional[float]` and `anchor_mtime: Optional[float]` to `MatchRecord` base
- `query_relationships()` SQL JOINs both anchor and result mtime columns
- `result_stale: bool` field on `RelationshipFilter`; executor post-filters
- `--stale` parsed from object_args side of relationship query

### S10-3: `prep_tldr` Incremental
- Last-run file: `.via/prep_tldr_last_run` (float seconds via `time.time()`)
- Add proper argparse: positional `root`, `--force`/`-f` flag
- Use `MAX(mtime)` per file from `symbols` table for incremental selection
- Stale data files for deleted sources: removed on incremental run too

### TD-WATCH-1: PathFilter
- New `via/core/path_filter.py` — `PathFilter(root_dir, respect_gitignore, extra_patterns)`
- Public API: `should_include_dir(parent, dirname)`, `should_include_file(path)`
- `FileDiscovery` delegates to `PathFilter`; `WatchService` constructs own `PathFilter`
- Removes private method access (`self._discovery._should_include_*`) from `WatchService`

### Full arch doc: `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`

## Current Blockers
None. Sprint 10 arch complete. Pending Smith Gate 2 approval.

### Temporal Matcher — Key Design Points (updated 2026-03-21)
- `--newerthan`/`--olderthan` are PER-STAGE, not global
- Both flags added to `match_parser`; available on subject AND object sides of relationship queries
- Object-side temporal routed via new fields on `RelationshipFilter`: `result_newerthan_seconds`, `result_olderthan_seconds`
- Cross-stage mtime comparison (`--stale`, "tests older than their class") → Sprint 10
- Duration: human-friendly strings at CLI; library accepts raw float seconds
- mtime never NULL; schema migration only forward (no backward compat)
