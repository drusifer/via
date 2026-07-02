# Morpheus Context

## Sprint 25 - Dart / Flutter Support Architecture (2026-05-06)
- Architecture written: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`.
- Decision: add Dart as a normal `ParserABC` implementation through existing parser registry, indexing, DB, query, and renderer paths.
- No Flutter-specific query language or flags in Sprint 25.
- Parser engine preference is tree-sitter, but dependency viability is a hard Cycle 0 gate because Dart does not currently have the same clean Python language-wheel story as JS/TS.
- Required Cycle 0: prove Python-loadable Dart grammar path before full parser implementation.
- Entity mapping uses existing `ClassEntity`, `FunctionEntity`, `GlobalEntity`, and `ImportEntity`; constructors are methods with `symbol_subtype="constructor"`.
- Relationship mapping uses existing `declares`, `imports`, `inherits-from`, and `calls`; `implements`/`with` map to `inherits-from` for Sprint 25.
- Structural Flutter awareness only: widgets/base classes/build methods, no widget tree or route graph inference.
- Sprint plan reviewed and approved: `agents/morpheus.docs/SPRINT_25_PLAN_REVIEW.md`.
- Mouse's cycle structure is approved: Cycle 0 dependency spike, Cycle 1 parser foundation, Cycle 2 relationships/docs.

## Sprint 25 Cycle 0 Review (2026-05-06)
- Review written: `agents/morpheus.docs/SPRINT_25_CYCLE_0_REVIEW.md`.
- Dependency path APPROVED.
- `tree-sitter-language-pack>=1.6.2` can load Dart and parse a Flutter-style fixture through `tree_sitter.Parser`.
- Neo may proceed to Cycle 1 parser foundation using `tree_sitter_language_pack.get_language("dart")`.

## Sprint 25 Cycle 1 Review (2026-05-06)
- Review written: `agents/morpheus.docs/SPRINT_25_CYCLE_1_REVIEW.md`.
- Parser foundation APPROVED.
- Dart is integrated as a normal `ParserABC` implementation with `.dart` discovery, CLI/MCP registration, Flutter/Dart excludes, and `--lang dart`.
- Review found and closed one indexing gap: method `symbol_subtype` values are now persisted, so Dart constructors remain queryable with subtype filters after indexing.
- Cycle 2 should focus on relationship coverage, Flutter fixture breadth, docs, and MCP examples.

## Sprint 25 Cycle 2 Review (2026-05-06)
- Review written: `agents/morpheus.docs/SPRINT_25_CYCLE_2_REVIEW.md`.
- Cycle 2 APPROVED.
- Dart/Flutter relationships use existing `declares`, `imports`, `inherits-from`, and `calls` types.
- External unresolved inheritance anchors are stored as `external_class` so Flutter SDK bases can be relationship targets without polluting normal project class searches.
- Docs and MCP examples preserve the structural-only support boundary.
- Full suite passed: 1324 passed, 1 skipped, 4 warnings.

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

## Sprint 26 Architecture design & Plan Review (2026-06-20)
- User requested Sprint 26 Architecture (Tech Debt Sprint).
- Drafted and finalized [SPRINT_26_ARCHITECTURE.md](file:///home/drusifer/Projects/via/agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md).
- Handed off to Smith for Gate 2 review; approved by Smith.
- Reviewed and approved Mouse's task breakdown. Wrote [SPRINT_26_PLAN_REVIEW.md](file:///home/drusifer/Projects/via/agents/morpheus.docs/SPRINT_26_PLAN_REVIEW.md).
- Handed off to Neo for Cycle 1 implementation.

## Sprint 26 Cycle 1 Review (2026-06-20)
- Review written: [SPRINT_26_CYCLE_1_REVIEW.md](file:///home/drusifer/Projects/via/agents/morpheus.docs/SPRINT_26_CYCLE_1_REVIEW.md).
- Cycle 1 implementation APPROVED.
- Baseline query engine failures (declares validation, filepath imports, empty markdown declares) resolved and verified.
- New unit tests for JS body analyzer subclasses implemented and verified.
- Handing off to Mouse to close Cycle 1.
- NOTE: as of 2026-07-01, Sprint 26 has progressed to Cycle 2 (Mouse verification 90%, Neo Cycle 4 design in progress) without a Morpheus-authored update in this file for Cycles 2-4 — reconcile with Mouse/Neo state before doing further Sprint 26 review work.

## Test Coverage & Quality Analysis — Feasibility Read (2026-07-01)
- Cypher requested feasibility input on 3 open questions before Smith's Gate 1, re: new requirement `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md`.
- Verified in-repo: `coverage.py` 7.13.4, `pytest` 9.0.2, `pytest-cov` 7.0.0 all already installed as deps, even though `make test` currently runs `unittest discover`.
- **OQ-1 (feasibility of per-test coverage)**: YES via coverage.py/pytest-cov dynamic contexts (`--cov-context=test`) — attributes coverage per test id within a single run, no process-per-test needed. Critical for cost given 1300+ tests. Recommended Cypher relax AC1 wording from "one process per invocation" to an outcome-level "coverage attributable per test id".
- **OQ-2 (storage)**: two different concerns — (a) coverage attribution should reuse the existing symbol/relationship pattern from `via/commands/coverage.py`'s aggregate `covered-by` import, but via a **new relationship name `tested-by`** (not overloading `covered-by`) so the existing Sprint 16 aggregate import stays untouched; (b) test run metadata (status/duration/last-run) doesn't fit the symbol model — new `test_runs(test_id PK, status, duration_seconds, last_run_at)` table, upserted per run (no history table — matches Cypher's AC2 preference).
- **OQ-3 (runner)**: add a pytest-based capture path alongside the existing `make test` (unittest discover), don't replace it — pytest auto-discovers unittest.TestCase subclasses so no test rewrite needed.
- Sizing estimate given to Cypher/Mouse: feasible in one sprint (~6-7pt), confirms Sprint 27 sequencing (not folded into in-flight Sprint 26).
- Full writeup: `agents/morpheus.docs/TEST_COVERAGE_FEASIBILITY_OQ1-3.md`.
- Handed back to Cypher to adjust AC1 wording, then Smith for Gate 1. Full architecture doc (schema DDL, relationship naming, Makefile target) deferred until after Gate 1 approval, per normal sprint flow.
- Smith Gate 1: APPROVED WITH NOTES (2 conditions: reuse `-V<relationship>` query surface, visible per-test progress).
- **User directive (2026-07-01, overrides my earlier `tested-by` proposal)**: do not add a second relationship type — alter `covered-by` itself for per-test precision. One path, no back-compat shim, breaking changes OK as long as we clean up dead cruft after.
- Wrote Gate 2 architecture: `agents/morpheus.docs/TEST_COVERAGE_ARCHITECTURE.md`. Key points: `covered-by` redefined to link source symbols to one synthetic symbol *per test id* (was: one blanket `<coverage>` symbol). Since `covered-by` is already registered in `via/core/relationship_types.py` and wired into `-V`, Smith's Gate 1 condition 1 is satisfied for free — no new CLI surface. Old blanket-symbol import path in `via/commands/coverage.py` is retired outright (not kept as fallback); cleanup step deletes stale `<coverage>` symbols (cascade-deletes their edges via existing FK) in the same import transaction. New `test_runs` table for status/duration/last-run (upsert, no history). New `make test-coverage` target using `pytest -v --cov-context=test` satisfies Gate 1 condition 2 (visible progress).
- Handed to Smith to confirm Gate 2 given the revised single-path design.
- Smith Gate 2: APPROVED (`agents/smith.docs/TEST_COVERAGE_GATE2_REVIEW.md`), both Gate 1 conditions confirmed met.
- Mouse broke Sprint 27 into 3 cycles (`agents/mouse.docs/SPRINT_27_TASKS.md`); queued behind in-flight Sprint 26.
- Reviewed Mouse's plan against the architecture doc: APPROVED, all decisions map 1:1 to tasks (`agents/morpheus.docs/SPRINT_27_PLAN_REVIEW.md`). This closes the `*plan sprint` bloop chain for this requirement — Cypher → Smith Gate1 → Morpheus arch → Smith Gate2 → Mouse plan → Morpheus review, no Tank gate needed.
- Execution (`*impl cycle-1`) is queued, not started — waits for Sprint 26 to close first.

## Sprint 26 Closure (2026-07-01) — real verification, not paperwork
- Per user request, actually verified Sprint 26 Cycle 2/3 rather than trusting stale state files.
- Trin found `make test` silently broken: bob-protocol Makefile's generic `unittest discover` target shadowed the project's real pytest recipe in `Makefile.prj` due to include order (bug present since Sprint 7). Fixed by reordering the include so project-specific recipes win — see `Makefile` diff.
- Re-verified for real: 1346 passed, 1 skipped.
- Reviewed actual Cycle 2/3 code: `COMMAND_REGISTRY` (via/__main__.py) and `STAGE_REGISTRY` (via/pipeline/handlers.py) are clean dispatch-table refactors; CTE query building (`_build_relationship_cte_sql`, `_build_negative_relationship_cte_sql`) properly isolated in `DatabaseStore`. APPROVED.
- Smith ran `via --help`/`index --help`/`stats --help` for real and confirmed no CLI regressions from the registry refactor. APPROVED.
- Sprint 26 is now CLOSED in `task.md`. Sprint 27 is unblocked but not started — user said wait for Sprint 26 to close before starting Sprint 27, which has now happened.

## Sprint 27 Cycle 1 Review + Cycle 3 Scope Decision (2026-07-01)
- Reviewed Neo's Cycle 1 implementation (`via/commands/coverage.py` rewrite, `match_record.py` 'test' type registration): clean, properly isolated, reuses existing `DatabaseStore` helpers (`delete_symbols_by_file`, `get_symbol_id`, `insert_relationship`). APPROVED.
- Trin's UAT surfaced a critical finding: 30/92 test files drive `via` via subprocess; `pytest --cov-context=test` measures zero code inside subprocesses. Decided to fold subprocess coverage capture into Cycle 3 rather than defer it — shipping without it would misreport ~1/3 of the suite as uncovered, undermining the sprint's whole purpose. Trin already validated the fix mechanism (sitecustomize + `PYTEST_CURRENT_TEST` context propagation + `coverage combine`), so this is bounded scope (+2-3pt), not open-ended research.
- Updated `TEST_COVERAGE_ARCHITECTURE.md` (Capture path section) and `agents/mouse.docs/SPRINT_27_TASKS.md` / `task.md` Cycle 3 scope accordingly.
- Handed to Neo to implement Cycle 3 with the expanded scope.

## Sprint 27 CLOSED (2026-07-01) — final summary
- User overrode the subprocess-coverage-capture plan (sitecustomize + combine) in favor of the root fix: 27 of 30 subprocess-spawning test files had no real reason to run out-of-process. Converted via a shared in-process runner + a transparent `conftest.py` redirect shim (zero per-file edits); the 3 genuine daemon/stdin-protocol tests moved to `tests/subprocess/`.
- A real O(tests × files) performance bug surfaced during full-scale validation (import was re-parsing every covered file once per test, 6+ minutes) — found and fixed before shipping.
- Smith's Heuristic 5 finding (partial-import data loss with no warning) was fixed immediately (`DatabaseStore.count_symbols_by_file` + a non-blocking warning) rather than backlogged.
- Side benefit: full suite runtime dropped ~174s → ~81s.
- Cycle 2 schema/migration reviewed and approved (SCHEMA_VERSION 6→7, upsert-only `test_runs`).
- Full final review: `agents/morpheus.docs/SPRINT27_FINAL_REVIEW.md`. Sprint 27 Phase 1 (capture) is CLOSED. Phase 2 (analysis) remains explicitly out of scope until a fresh requirement.
