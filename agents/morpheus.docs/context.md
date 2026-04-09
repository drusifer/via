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
- Test baseline: 1178 Python + 74 JS + 22 E2E

## Sprint 15 — MCP Ergonomics + Index Completeness
**Status**: Shipped
**Architecture**: `morpheus.docs/SPRINT_15_ARCHITECTURE.md`

## Sprint 16 — String Intelligence + Reusable Query Workflows
**Status**: Shipped
**Stories**: `cypher.docs/SPRINT_16_USER_STORIES.md` (8pt, 4 stories)
**Architecture**: `morpheus.docs/SPRINT_16_ARCHITECTURE.md`
**Review**: `agents/morpheus.docs/SPRINT_16_REVIEW_2026-04-08T19:00.md`

### Key Decisions
1. S16-1: propagate `--slice` offset/limit through OR'd multi-type query path
2. S16-2: `-ts` is a structured `string_constant` symbol type, not generic text search
3. S16-2: store `references` relationship from string constants to enclosing symbol/file anchor
4. S16-3: support `coverage.xml` only in Sprint 16; import as `covered-by`
5. S16-4: `--canned` expands into ordinary via argv; no second query engine
6. Sprint 16 delivered as architected; no redesign needed during implementation

## Sprint 17 — Link Intelligence + HTTP Bridge Primitives
**Status**: Shipped
**Stories**: `cypher.docs/SPRINT_17_USER_STORIES.md` (7pt, 3 stories)
**Architecture**: `agents/morpheus.docs/SPRINT_17_ARCHITECTURE.md`
**Review**: `agents/morpheus.docs/SPRINT_17_REVIEW_2026-04-08T20:45.md`

### Key Decisions
1. S17-1: add `link` as a first-class symbol type, starting with markdown link extraction
2. S17-2: expose JS/TS outbound HTTP calls via a primitive `http-calls` relationship
3. S17-2: do not promise automatic backend route resolution in Sprint 17
4. S17-3: implement `--contains` as a post-match body filter over symbol byte spans
5. S17-3: return symbols, not grep-style line snippets
6. Reuse existing parser/index/executor seams; no full-text index or second query engine

## Refactor Guidance (2026-04-08)

### Trigger
- Bob asked for a refactor plan favoring polymorphic classes over large `if`/`else` blocks, with DRY as the guiding principle.

### Decision
- Do not apply anti-branch refactoring indiscriminately.
- Best targets are:
  1. `via/parsers/javascript_parser.py` — repeated node-type dispatch across multiple passes
  2. `via/pipeline/executor.py` — query-mode branching accumulating in one orchestrator
- Lower priority:
  - `via/renderers/factory.py` if the renderer matrix keeps growing
- Explicit non-target:
  - `via/core/match_record.py` because it already embodies the correct polymorphic design

### Proposed Class Architecture
- JS parser:
  - `JavaScriptTopLevelHandler`
  - `ImportNodeHandler`
  - `FunctionNodeHandler`
  - `ClassNodeHandler`
  - `VariableDeclarationHandler`
  - `TypeDeclarationHandler`
  - `ExportWrapperHandler`
  - `JavaScriptParseSinks`
  - `FunctionBodyAnalyzer`
- Pipeline executor:
  - `MatchExecutionStrategy`
  - `PlainMatchStrategy`
  - `RelationshipMatchStrategy`
  - `NegativeRelationshipStrategy`
  - `RecordFilter`
  - `ContainsBodyFilter`
  - `LineSliceFilter`

## Sprint 18 Architecture (2026-04-08)
- Approved a bounded first slice in `agents/morpheus.docs/SPRINT_18_ARCHITECTURE.md`
- Decision: keep the refactor local to `via/parsers/javascript_parser.py`
- Use module-private handler objects plus a dispatcher registry for top-level symbol extraction
- Export wrappers must delegate back into the same dispatcher path
- Deferred: `FunctionBodyAnalyzer` and executor strategies

## Sprint 18 Review (2026-04-08)
- APPROVED: `agents/morpheus.docs/SPRINT_18_REVIEW_2026-04-08T21:14.md`
- Implementation matched the local refactor architecture and did not expand scope into executor work

## ViaQueryBuilder Architecture (2026-04-08)
- Trigger: Bob requested a fluent code-level API because the current via API is too CLI-shaped for programmatic use
- Decision: add `ViaQueryBuilder` as a fluent construction layer that compiles into existing `PipelineStage` objects
- Keep `PipelineExecutor` as the execution engine; do not create a second query engine
- Recommended shape: `ViaQueryBuilder`, `RelationshipQueryBuilder`, immutable `ViaQuery`, thin `ViaRunner`
- Best first adopter: `via/web/api/query.py`, which currently hand-builds `argparse.Namespace`

## Sprint 19 Architecture (2026-04-08)
- Approved Sprint 19 delivery in `agents/morpheus.docs/SPRINT_19_ARCHITECTURE.md`
- New API package: `via/api/`
- Builder compiles to existing `PipelineStage` compatibility seam rather than changing executor internals
- Web API is the first real adopter and should stop hand-building `Namespace`

## Sprint 19 Review (2026-04-08)
- APPROVED: `agents/morpheus.docs/SPRINT_19_REVIEW_2026-04-08T21:37.md`
- Implementation matched the additive builder architecture and kept executor semantics intact

## Architecture Audit (2026-02-11) — Known Tech Debt
- SMELL-1: `_get_match_metadata()` computes render widths (DB/render coupling)
- SMELL-2: `_store_call_relationships` accesses `db_store.conn` directly
- SMELL-6: 3 near-identical file-storage methods in indexing.py
- Full report: `agents/morpheus.docs/CODE_REVIEW_2026_03_21.md`

## Current Blockers
None. Sprint 17 shipped; awaiting next sprint intake.
