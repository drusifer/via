# Morpheus Context

## Key Architectural Decisions

### Match Command Architecture — v5.0 (CURRENT)
- **Single `symbols` table**: Denormalized, zero-JOIN lookups
- **SymbolType/MatchOp Enums**: Pure value objects
- **MatchRecord hierarchy**: Factory-created from DB rows
- **References table**: Separate for relationship queries (calls, imports, inherits)

## Sprint History
- Sprints 1-10: SHIPPED
- Sprint 11: SHIPPED (2026-03-22) — JS/TS parser, symbol_subtype, node_modules excludes
- Sprint 12: SHIPPED (2026-03-23) — Web UI SPA, E2E Playwright tests
- Sprint 13: SHIPPED (2026-03-24) — CLI redesign: --via/--sans/--not
- Sprint 14: SHIPPED (2026-04-06) — JS calls, --lang, --subtype, web UI rel card
- Sprint 15: SHIPPED — MCP Ergonomics + Index Completeness
- Sprint 16: SHIPPED — String Intelligence + Reusable Query Workflows
- Sprint 17: SHIPPED — Link Intelligence + HTTP Bridge Primitives
- Sprint 18: SHIPPED — JS parser refactor (handler dispatcher)
- Sprint 19: SHIPPED — ViaQueryBuilder fluent API
- Sprint 20: SHIPPED — Shared query compilation seam
- Sprint 21: SHIPPED
- Sprint 22: SHIPPED — Query confidence and error recovery
- Sprint 23: SHIPPED — Recognition over recall (canned shortcuts, MCP task examples, diagram fallback)
- Test baseline: ~67 passing tests (Sprint 23 closeout)

## Sprint 24 — Result-Stage-First Query Model
**Status**: Architecture written
**Architecture**: `agents/morpheus.docs/SPRINT_24_ARCHITECTURE.md`
**Theme**: Formalize result-stage-first query model. First stage = returned results, --via/--sans = filters.

### Key Decisions
1. Swap subject/object mapping in executor (result before --via, filter after)
2. Rename RelationshipFilter fields: object_pattern → filter_pattern, object_types → filter_types
3. Support --via + --sans chain (minimum: one of each per query)
4. Rewrite all canned queries to result-first arg order
5. Handle `unused` canned query with invert_join=True for calls
6. No DB schema changes — swap is purely in how executor maps CLI args to DB args
7. No backward compatibility required

### Cycle 2 Review (2026-04-13)
- Multi-filter relationship chaining is approved.
- Parser now collects `--via`/`--sans` clauses into ordered `args.relationships` while retaining `args.relationship` for single-filter compatibility.
- Executor implements the approved architecture: first relationship clause executes as the primary DB query; subsequent clauses are applied as post-filters over the current result set.
- Tests cover parser ordering plus sequential positive and negative filters.
- Full suite passed: 1313 passed, 1 skipped, 4 warnings.

## Refactor Guidance (2026-04-08)

### Trigger
- Bob asked for a refactor plan favoring polymorphic classes over large `if`/`else` blocks, with DRY as the guiding principle.

### Decision
- Do not apply anti-branch refactoring indiscriminately.
- Best targets are:
  1. `via/parsers/javascript_parser.py` — repeated node-type dispatch across multiple passes
  2. `via/pipeline/executor.py` — query-mode branching accumulating in one orchestrator
- Explicit non-target:
  - `via/core/match_record.py` because it already embodies the correct polymorphic design

## ViaQueryBuilder Architecture (2026-04-08)
- `ViaQueryBuilder` is a fluent construction layer that compiles into existing `PipelineStage` objects
- `PipelineExecutor` remains the execution engine
- Web API is the first real adopter

## Architecture Audit (2026-02-11) — Known Tech Debt
- SMELL-1: `_get_match_metadata()` computes render widths (DB/render coupling)
- SMELL-2: `_store_call_relationships` accesses `db_store.conn` directly
- SMELL-6: 3 near-identical file-storage methods in indexing.py
- Full report: `agents/morpheus.docs/CODE_REVIEW_2026_03_21.md`

## Current Blockers
None.
