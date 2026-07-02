# Cypher Context - VIA Project

**Last Updated**: 2026-06-20

## Current Project
Via - Python codebase indexing and querying CLI tool

## Key Decisions Made

### Sprint 5 - SHIPPED
- STATUS: SHIPPED
- 661 tests (at time of ship), all relationship types implemented
- Docs condition cleared by Oracle

### Sprint 6 - SHIPPED (2026-03-19)
- STATUS: SHIPPED — 709 tests, 0 failures
- Watch Mode (`via index -w`) fully implemented
- Bugs found + fixed in UAT: SQLite thread safety + missing symbol deletion
- Morpheus review: APPROVED, 5 tech debt items in `morpheus.docs/SPRINT_6_REVIEW.md`
- Tech debt to address in Sprint 7: DatabaseStore.delete_file_completely(), IndexingService.reindex_file()

### Index Command Specification
- **Storage**: SQLite database at `.via/index.db`
- **Universal file indexing**: All files (metadata), parse only `.py`, `.pyx`, `.pyi`, `.md`
- **Incremental by default**: Skip unchanged files unless `--force`
- **Watch mode**: `via index -w`, watchdog, debounce 500ms, foreground only
- **10MB parse limit**

### Command Syntax Finalized
```bash
via index [-w] [-v|-vv|-vvv|-vvvv] [--force] [--exclude PATTERN] [<dir>]
```

### Roadmap (2026-03-20)
- **Sprint 7** - MCP Mode (10pts): SHIPPED 2026-03-20 (commit e714929), 794 tests, 10/10 UAT
- **Sprint 8** - Line Index (6pts): `-mL` match type with slice syntax, byte offset indexing — **STORIES READY**, needs Morpheus design
- **Sprint 9** - Container Queries (~6pts): `-Vhas` has-a relationship (container→members) + temporal matcher in via query layer
- **Sprint 10** - (planned) `prep_tldr` integration using temporal matcher (~2pts) + TBD
- User stories reviewed 2026-03-19, Sprint 9 added 2026-03-20 per Drew request

## Session 2026-03-20
- Sprint 9 user story added: `-Vhas` has-a relationship (3pts) — renamed from `-Vin` (too similar to `-Vinh`)
- Syntax: `via -mg '*service*' -tF -Vhas -tf -n 0` — files→symbols containment
- Sprint 9 Story 2 added: incremental `prep_tldr` via `--since` filter (2pts) — stores last run in `.last_run`, only re-generates data files for changed files
- Sprint 9 total now 5pts
- See `agents/cypher.docs/SPRINT_9_USER_STORIES.md`

### Story 2 — Rescoped per Drew feedback (2026-03-20)
- `files.mtime` column EXISTS (`via/db/schema.py:45`) — use for change detection ✅
- Column is `indexed_at` (NOT `last_indexed`)
- `DatabaseStore.get_files_changed_since()` NOT BUILDING — superseded by temporal matcher design
- Story 2 split into 2a (temporal matcher in via, ~3pts) + 2b (prep_tldr integration, ~2pts)
- Temporal matcher is a first-class via query capability; state (last_run) lives in via lib
- `py_files.txt`/`md_files.txt` → changed files ONLY on incremental (minimize sub-agent tokens)
- Stale data files for deleted sources → DELETE on incremental run
- Sprint 9: ~6pts (Story 1 + Story 2a); Story 2b (prep_tldr) → Sprint 10 (Drew confirmed 2026-03-20)
- Error messages project-wide standard: must state what/why/valid-alternatives

### Sprint 10 — Planned (2026-03-22)
- Sprint 10 user stories written: `agents/cypher.docs/SPRINT_10_USER_STORIES.md`
- ~8pts: S10-1 `--ref-type` (P0,3pt), S10-2 `--stale` (P1,2pt), S10-3 prep_tldr incremental (P1,2pt), TD-WATCH-1 PathFilter (P2,1pt)
- Pending: Smith review, then Morpheus arch (SPRINT_10_ARCHITECTURE.md)

### JavaScript/TypeScript Support (2026-03-22)
- User requested JS support → requirements written: `cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md`
- Proposed as Sprint 11 (~15pts, 5 stories): S11-1 discovery, S11-5 node_modules excludes, S11-2 JavaScriptParser (tree-sitter), S11-3 relationships, S11-4 --lang filter
- Uses existing ParserABC/ParserRegistry seams — no query/CLI/renderer changes needed
- 5 open questions (OQ-1 to OQ-5) for Morpheus arch review
- Pending: Smith user review gate → Morpheus arch → Neo implementation

### Sprint 14 — SHIPPED (2026-04-06, commit d96e522)
- JS/TS relationship extraction, `--lang` flag, `--subtype` flag, web UI `--via`/`--sans` UX, USER_GUIDE.md fixes
- 1178 tests, 0 failures

### Sprint 15 — SHIPPED (2026-04-08)
- Source: Smith's MCP expert review (`agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`)
- Theme: MCP ergonomics + index completeness
- 6 stories, 9pt: --slice pagination, MCP output wrapper, --lang/-tF fix, markdown declares, -Q full-path/docs clarification, --help examples
- Delivered across 3 cycles; QA and lead review passed for each cycle
- Final reported test baseline: 1235 passed, 1 skipped, 4 warnings
- Closeout doc: `agents/cypher.docs/SPRINT_15_CLOSEOUT_2026-04-08T18-24.md`
- Deferred to Sprint 16: string constants, coverage import, link indexing, canned queries
- Additional Sprint 16 backlog note: `--slice` ignored for OR'd type queries

### Sprint 16 — SHIPPED (2026-04-08)
- Source: Sprint 15 closeout + Smith MCP review + Oracle recorded decisions
- Theme: string intelligence + reusable query workflows
- Shipped scope:
  - S16-1 fix `--slice` for OR'd type queries
  - S16-2 `-ts` string constants
  - S16-3 `covered-by` coverage import
  - S16-4 canned queries
- Implementation, QA, and lead review completed on 2026-04-08
- Targeted verification baseline for ship decision: 176 passing tests
- Closeout doc: `agents/cypher.docs/SPRINT_16_CLOSEOUT_2026-04-08T19-00.md`
- Stories doc: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
- Backlog retained: link indexing, HTTP bridge, generic `--contains` search

### Sprint 17 — SHIPPED (2026-04-08)
- Theme: link intelligence + HTTP bridge primitives
- Delivered scope:
  - S17-1 URL/link indexing as `link` symbols
  - S17-2 pragmatic HTTP bridge via JS HTTP call sites
  - S17-3 `--contains` as post-match symbol-body filtering
- Intentional boundary preserved: no claim of automatic framework-aware cross-language tracing
- Verification baseline for ship decision: 138 passing targeted tests
- Stories doc: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`
- Closeout doc: `agents/cypher.docs/SPRINT_17_CLOSEOUT_2026-04-08T20-45.md`

### Sprint 18 — Planned (2026-04-08)
- Theme: polymorphic refactor, starting with JavaScript parser top-level dispatch
- Scope is intentionally bounded to structural cleanup, not new product behavior
- Story doc: `agents/cypher.docs/SPRINT_18_USER_STORIES.md`
- First slice: replace the large top-level node-type conditional in `via/parsers/javascript_parser.py` with handler objects/registry
- Deferred refactor backlog: `FunctionBodyAnalyzer` extraction and executor strategies

### Sprint 18 — SHIPPED (2026-04-08)
- Theme: polymorphic JS parser refactor
- Delivered scope:
  - S18-1 polymorphic top-level JS parser handlers
- Verification baseline for ship decision: 96 passing targeted tests
- Closeout doc: `agents/cypher.docs/SPRINT_18_CLOSEOUT_2026-04-08T21-14.md`

### Sprint 19 — Planned (2026-04-08)
- Theme: fluent builder API for programmatic via queries
- Scope is bounded to a new `ViaQueryBuilder` plus migration of the web query layer away from manual `Namespace` construction
- Story doc: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`
- Architecture source: `agents/morpheus.docs/VIA_QUERY_BUILDER_ARCHITECTURE_2026-04-08T21-22.md`

### Sprint 19 — SHIPPED (2026-04-08)
- Theme: ViaQueryBuilder
- Delivered scope:
  - S19-1 fluent programmatic query builder
  - S19-2 web API builder adoption
- Verification baseline for ship decision: 30 passing targeted tests
- Closeout doc: `agents/cypher.docs/SPRINT_19_CLOSEOUT_2026-04-08T21-37.md`

### Sprint 20 — Planned (2026-04-08)
- Theme: builder adoption + library usability
- Scope is bounded to sharing the builder seam with the CLI/query construction path and documenting `ViaQueryBuilder` as the supported Python API
- Story doc: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`
- Explicit non-scope: executor redesign and full CLI parser replacement

### Sprint 20 — SHIPPED (2026-04-08)
- Theme: builder adoption + library usability
- Delivered scope:
  - S20-1 shared CLI/programmatic query construction seam
  - S20-2 documented `ViaQueryBuilder` and `ViaRunner` as the supported Python API
- Verification baseline for ship decision: 50 passing targeted tests
- Closeout doc: `agents/cypher.docs/SPRINT_20_CLOSEOUT_2026-04-08T21-58.md`

## Blockers
None

## Deck Status Update (2026-05-06)
- User asked Cypher: "what's on deck?"
- Latest completed sprint in team state is Sprint 24, closed by Mouse on 2026-04-13.
- Sprint 24 delivered result-stage-first relationship query execution, inverse relationship types, docs/tests updates, and ordered multi-filter `--via`/`--sans` chaining.
- Final reported baseline: 1313 passed, 1 skipped, 4 warnings.
- No active Sprint 25 exists yet in Cypher state.
- Recommended next product move: plan Sprint 25 or run a focused polish/regression sprint, with HCI/UX and query confidence still the strongest product direction.
- Oracle files named by older Cypher instructions (`lessons.md`, `memory.md`) are absent; available Oracle state is `agents/oracle.docs/context.md`, `current_task.md`, and `next_steps.md`.

## Dart / Flutter Requirement Intake (2026-05-06)
- User requested new requirement: support for Flutter / Dart code.
- Product direction: treat this as the likely Sprint 25 theme.
- Story doc written: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`.
- PRD updated with planned Sprint 25 story table.
- Architecture fit: reuse `ParserABC`, `ParserRegistry`, `.dart` extension registration, `ParseResult.language`, `symbols.language`, `symbol_subtype`, and existing `--lang` / relationship query paths.
- Scope boundary: support Dart/Flutter structural indexing and query workflows, not full Flutter semantic analysis, widget tree reconstruction, route graph reconstruction, or Dart analyzer replacement.
- Gate: Smith should review user value/discoverability, then Morpheus should select parser engine and architecture.

## Runtime Request Intake (2026-04-12)
- User requested via Bob Protocol: make Via MCP serve, run index/watch, and serve the web interface.
- This is an operational execution request, not a product requirement change.
- Cypher accepted intake and handed execution to Neo.
- Acceptance criteria for the handoff:
  - Via index is refreshed.
  - Watch mode is running.
  - MCP server process is running.
  - Web interface server is running and URL is reported to the user.

## Sprint 22-24 HCI/UX Product Direction (2026-04-12)
- User requested the next few sprints focus on HCI and UX.
- Source: Smith's updated VIA MCP usability report, including regex, multi-type, and ambiguous multi-match findings.
- Story batch written: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`
- Product direction: prioritize query confidence and error recovery before adding new query power.
- Sprint 22 focus: structured errors, multi-match validation, regex UX, documented `declares` pattern.
- Sprint 23 focus: recognition-over-recall via shortcuts, MCP examples, diagram fallback, CLI help.
- Sprint 24 focus: UAT, docs recipes, error style guide, closeout review.
- User clarified command mental model for docs: first stage determines candidate result set; later `--via` / `--sans` stages filter those results by relationship to another matched set.

## Sprint 23 Planning (2026-04-12)
- Sprint 22 shipped query confidence and error recovery.
- Sprint 23 story doc written: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`.
- Theme: recognition over recall for common VIA workflows.
- Product constraint: shortcuts must be task-language and transparent; no new relationship model.
- High-risk story: `declared-in-file` must not recreate the Sprint 22 inverse `declares` docs bug.
- Gate handoff goes to Smith for HCI story review.

## Sprint 25 — SHIPPED (2026-05-07)
- **Theme**: Dart / Flutter Support
- **Scope**: structural Dart/Flutter indexing and query workflows
- **Deliverables**: `.dart` file discovery, `DartParser` foundation, Flutter-aware query value, relationships query support (`declares`, `imports`, `inherits-from`, `calls`), default exclusions for caches/builds.
- **Verification**: full test suite green with 1324 tests passing.

## Judge & Learn Feature/Fix (2026-06-20)
- **Theme**: Query engine bug resolution and CLI robustness.
- **Fixed Issues**:
  - BUG-1: Corrected type mapping and container validation for inverted declarations queries.
  - BUG-2: Resolved transitive file-level imports resolution.
  - Settle `make via` target to avoid virtual environment activation issues.
- **Verification**: full test suite passing with 1339 tests.

## Backlog Query (2026-06-20)
- User requested what's on the backlog.
- Created [BACKLOG.md](file:///home/drusifer/Projects/via/agents/cypher.docs/BACKLOG.md) to document product backlog and roadmap items.
- Recommended Boolean query operators, Interactive TUI, or a QA regression sprint.

## Sprint 26 Planning (2026-06-20)
- User requested `*bloop *plan TechDept Sprint`.
- Cypher planned Sprint 26 (theme: Tech Debt, 11pts).
- Wrote [SPRINT_26_USER_STORIES.md](file:///home/drusifer/Projects/via/agents/cypher.docs/SPRINT_26_USER_STORIES.md).
- Handed off to Smith for Gate 1 User Story Review.
- NOTE: as of 2026-07-01, Sprint 26 has progressed to Cycle 2 verification (Mouse 90%, Neo Cycle 4 design in progress) — Gate 1 evidently passed at some point; no separate closeout doc found yet for Sprint 26.

## Test Coverage & Quality Analysis — Requirement Intake (2026-07-01)
- User requested (via `*chat TO=cypher *nreq`): a precise way to explore test coverage as a means of measuring test quality/efficiency.
- Scope as stated: Phase 1 = run tests one at a time, capture per-test coverage data + metadata (last run, status, duration). Phase 2 (analysis) explicitly deferred by PM until Phase 1 data exists — not enough signal yet to design redundancy/efficiency scoring.
- Checked existing capability first: `via/commands/coverage.py` already imports a single aggregate `coverage.xml` into `covered-by` relationships (shipped Sprint 16, S16-3). That is whole-suite, not per-test — confirmed this is a genuinely new capability, not a duplicate.
- Wrote requirements: `agents/cypher.docs/TEST_COVERAGE_QUALITY_REQUIREMENTS.md` (3 user stories for Phase 1, explicit non-goals, 3 open questions for Morpheus).
- Added to `BACKLOG.md` as item 7 under Features & Capabilities — candidate for **Sprint 27** (not folded into in-flight Sprint 26).
- Key open question flagged to Morpheus: whether `coverage.py`'s dynamic-context feature can tag per-test coverage within one run, vs. needing a fully isolated one-process-per-test runner (suite has 1300+ tests, so process-per-test cost matters).
- Handoff chain per protocol: Morpheus (feasibility/OQ-1..3) → Smith (Gate 1 user value review) before this becomes a sized sprint.
- Morpheus feasibility read received 2026-07-01 (`agents/morpheus.docs/TEST_COVERAGE_FEASIBILITY_OQ1-3.md`): dynamic contexts confirmed, `tested-by` relationship + `test_runs` table proposed, add-pytest-alongside-unittest confirmed. Revised AC1 in the requirements doc to be outcome-level (per-test attribution) rather than mandating one-process-per-test. Handed to Smith for Gate 1.
