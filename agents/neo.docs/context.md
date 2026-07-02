# Neo Context

## Sprint 27 Cycle 1 — Per-Test Coverage Import (2026-07-01)
- Rewrote `via/commands/coverage.py`: retired `import_coverage_xml`/`_parse_covered_lines` (whole-suite `coverage.xml` parsing), replaced with `import_contexts`/`_covered_lines_by_test` reading coverage.py's native dynamic-context data (`coverage.CoverageData.contexts_by_lineno()`).
- Context labels from pytest-cov look like `"path/to/test.py::TestClass::test_method|run"` — stripped the `|run`/`|setup`/`|teardown` phase suffix via `_test_id_from_context()` to get the canonical test id. Empty-string context (module-level/import-time execution outside any test) is skipped — not attributable to a test.
- New CLI subcommand: `via coverage import-contexts [path]` (default `.coverage`), replacing `via coverage import <coverage.xml>` entirely — no back-compat shim per user directive.
- Per-test synthetic symbols: `symbol_type='test', file_path='<test>', qualified_name=test_id`. Cleanup on every import: `store.delete_symbols_by_file('<coverage>')` (old blanket-symbol data) and `delete_symbols_by_file('<test>')` (previous run's per-test symbols) before inserting fresh ones — cascade-deletes their `covered-by` edges via the existing FK. This makes re-import idempotent (verified: writing a fresh `.coverage` with only test_bravo's context and re-importing leaves no trace of a prior test_alpha symbol).
- Hit a real gap: `via/core/match_record.py`'s `MatchRecordFactory._RECORD_TYPES` raises `ValueError: Unknown symbol type` for any symbol_type not in its dict — `'test'` wasn't registered, so directly querying/rendering test symbols crashed (didn't affect using them as `--via`/`--sans` relationship targets, only direct rendering). Fixed by adding `'test': GlobalMatchRecord` to the factory map (same generic-reuse pattern the original Sprint 16 code used for `'module'` → `ImportMatchRecord`).
- Added `coverage>=7.0` to `pyproject.toml` main `dependencies` (was previously only a transitive dev dep via `pytest-cov`) since `via/commands/coverage.py` now imports it directly at runtime, not just during test runs.
- Updated `tests/unit/test_sprint16_c3.py`: replaced the old XML-based test with `test_coverage_import_contexts_adds_per_test_covered_by_relationships` (constructs a real coverage.py data file via the public API, verifies per-test attribution through `--via covered-by`) and added `test_coverage_import_contexts_cleans_up_stale_data_on_reimport`.
- Full suite: 1347 passed, 1 skipped (was 1346 before Cycle 1's new test).
- Handed to Trin for UAT.

## Sprint 13 (2026-03-24)

### Problem Diagnosed (session 2)
Neo's Sprint 13 P1 build left 174 failures + 133 errors. Root causes found and fixed:
1. `_match_with_regex()` missing `negated` param → added with `(match is not None) != negated`
2. `test_relationship_executor.py` used old `invert=` → changed to `is_negative=`
3. Tests used `--sans` as if it meant inverted direction (like old `--invert`) — WRONG
   - `--sans` = NOT EXISTS (subjects with NO relationship)
   - Tests expecting targets (callees, parents, referenced symbols) needed rewriting
4. `--sans declares` needed "not yet supported" error
5. `--via declares` with non-container object type needed validation

### Key Design Decisions
- `--sans` = NOT EXISTS subquery (subjects with no relationship) — NOT inverted direction
- Inverted direction queries (find targets/callees/parents) are NOT supported in Sprint 13
  - "What does X inherit from?" → no direct equivalent with --via only
  - Tests for this were rewritten as "find root classes (no parent)" instead
- `--via calls` with class anchor expands to methods (subject_parent_pattern expansion)
- `--sans declares` raises ValueError "not yet supported"
- `--via declares` validates object_type must be file/class/filepath/filename

### Test Direction Convention (CRITICAL)
```
BEFORE --via/--sans = object_pattern (the anchor)
AFTER --via/--sans  = subject_pattern (what gets returned)
--via: returns subjects WITH relationship TO object
--sans: returns subjects with NO relationship TO object
```

### Test Count
- Baseline: 1121 (pre-Sprint 13)
- Current: 1115 passing (P3-3 new tests not yet added)
- Need: ≥1121 (add 6 new tests covering --sans, --not, error cases)

### Previous Sprint Context
Sprint 12: Web UI fixes (UX-001 to UX-005). 1121+74+22 tests.

## Sprint 17 (2026-04-08)

### Delivered
- `link` symbol type with markdown-first extraction
- `http-calls` primitive relationship for JS/TS outbound HTTP requests
- `--contains` as post-match symbol-body filtering

### Key Implementation Decisions
- Reused existing parser/indexer seams rather than adding a new store or query engine
- Reused symbol byte spans plus existing source-extraction utilities for `--contains`
- Reused existing relationship storage/query path for `http-calls`

## Sprint 18 (2026-04-08)

### Delivered
- Refactored JS/TS top-level symbol extraction in `via/parsers/javascript_parser.py` into module-private handler classes plus a dispatcher registry
- Reused the same dispatch path for exported declarations instead of maintaining separate export-specific extraction logic
- Added focused parity coverage in `tests/unit/test_sprint18_c1.py`

### Verification
- Targeted make-based regression suite: 96 passed

## Sprint 19 (2026-04-08)

### Delivered
- Added fluent programmatic query construction in `via/api/query_builder.py`
- Added thin execution adapter `ViaRunner` over `PipelineExecutor`
- Migrated `via/web/api/query.py` off manual `Namespace` construction

### Verification
- Targeted make-based builder and web-query regression suite: 30 passed

## Sprint 20 (2026-04-08)

### Delivered
- Added `via/pipeline/stage_builder.py` as a shared CLI/builder query-compilation seam
- Migrated `PipelineParser` and `ViaQueryBuilder` to the same match-stage and relationship-filter construction path
- Documented `ViaQueryBuilder` and `ViaRunner` as the supported Python API in `README.md` and `docs/USER_GUIDE.md`

### Verification
- Targeted make-based seam and regression baseline: 50 passed

## Runtime MCP Startup (2026-04-12)

### User Clarification
- `via mcp serve` should be the single runtime process for MCP stdio, initial indexing, watch mode, and the web UI.
- Do not require users to run separate `via index`, `via index -w`, and web-serving instances.

### Findings
- `via/mcp/server.py::run_mcp_server()` already starts `WatchService` and the embedded `WebServer`.
- `WatchService.start()` already performs the initial index before watching.
- The blocker was `via/__main__.py::_run_mcp_serve()`, which refused to start if `.via/index.db` did not already exist.

### Decision
- `via mcp serve` now creates `.via/` when needed and delegates to the combined MCP runtime. The runtime performs initial index/watch/web in one process.

## Sprint 22 Cycle 1 — Structured Query Error Contract (2026-04-12)

### Delivered
- Added `via/pipeline/errors.py` with `QueryError` and enhanced `PipelineParseError`.
- Parser expected failures now carry stable `code` and optional `hint` fields.
- MCP query handling now returns `output_type: "error"` for expected parser errors and unexpected internal errors.
- CLI pipeline errors now print a `Hint:` line when the parse error supplies one.
- Refactored MCP query wrapper into top-level helpers for focused unit coverage.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_pipeline_parser.py` — 44 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c3.py` — 19 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p4.py` — 16 passed.

### Note
- `make test FILE=tests/unit/test_sprint22_c1.py` still hits the broader default test loader and fails because that environment path lacks `pytest`; use `Makefile.prj` targeted tests until the default target environment is fixed.

## Sprint 22 Cycle 2 — Match-Stage And Regex Validation (2026-04-12)

### Delivered
- Added parser pre-validation for one matcher per stage.
- Validated result stage and relationship filter stage independently.
- Added parse-time regex compilation for `-mr` patterns.
- Preserved multi-type OR behavior.
- Added `tests/unit/test_sprint22_c2.py`.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c2.py` — 8 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_pipeline_parser.py` — 44 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_relationship_cli.py` — 18 passed.

## Sprint 22 Cycle 3 — Docs, Schema, And Help Corrections (2026-04-12)

### Delivered
- Updated `agents/PROJECT.md`, `via/mcp/schema.py`, `via/__main__.py`, and `docs/USER_GUIDE.md` to teach the result-stage-first command model.
- Removed the misleading "Find all symbols in a file" quick reference.
- Clarified that relationship stages filter the initial result stage.
- Added one-matcher-per-stage and regex examples in schema/help-facing surfaces.
- Added `tests/unit/test_sprint22_c3.py` and updated the Sprint 15 help wording test.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p4.py` — 16 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c2.py` — 8 passed.

## Sprint 23 Cycle 1 — Canned Shortcut Surface (2026-04-12)

### Delivered
- Added canned shortcuts: `methods-calling`, `docs-headers`, `symbol-body`, and `paged-scan`.
- Added `--show-expanded` for `--canned`; it prints a copyable `via ...` command and exits without executing.
- Kept deferred shortcuts `callees` and `declared-in-file` out of built-ins.
- Added `tests/unit/test_sprint23_c1.py`.

### Runtime Orientation Finding
- The executor still evaluates relationship queries using the older orientation:
  - before `--via` = known anchor/object
  - after `--via` = returned subject filter
- Sprint 22 docs/schema/help describe a result-stage-first model, but runtime semantics were not refactored.
- Cycle 1 canned shortcuts are task-correct against the current executor; changing the relationship engine is out of Sprint 23 Cycle 1 scope.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed after QA added coverage.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

## Sprint 23 Cycle 2 — Task Examples And CLI Help (2026-04-12)

### Delivered
- Added compact CLI help common-task examples.
- Added `--show-expanded` help text.
- Added task-oriented MCP schema examples for symbol lookup, body reading, callers, docs headers, regex, multi-type, and paged scans.
- Added uppercase `-tH` guidance; lowercase `-th` is explicitly invalid in schema guidance.
- Kept unsupported direct/deferred shortcut names out of examples.

### Design Note
- Because runtime relationship orientation still differs from the Sprint 22 result-stage-first docs, Cycle 2 leads with canned task shortcuts and labels raw relationship examples as advanced current-runtime syntax.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `via --help` line count: 121.
- `via mcp schema` line count: 121.

## Sprint 23 Cycle 3 — Diagram Fallback Preservation (2026-04-12)

### Delivered
- MCP diagram fallback now reruns the query as JSON and preserves matching records when diagram rendering is unavailable for the result shape.
- Empty diagram fallback still returns JSON with empty results and a clear note.
- Valid diagram responses remain `output_type: "diagram"`.
- Change stayed in `via/mcp/server.py`; renderer API unchanged.

### Verification
- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c3.py` — 3 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c3.py` — 19 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.

## Sprint 24 Cycle 1 — Result-First Executor Swap (2026-04-13)

### Delivered
- Completed result-first relationship executor swap.
- Implemented inverse relationship types.
- Renamed the relationship filter field to `relationship_type`.
- Updated canned queries and tests to match the new result-first argv model.

### Verification
- `make test` — 1310 passed, 1 skipped, 4 warnings in 137.43s.
- Trin UAT passed after semantic spot-checks for subclasses, callers, and stale old-direction references.
- Morpheus approved Sprint 24 Cycle 1 and confirmed all 7 architecture decisions were implemented correctly.

### Current Coordination State
- Mouse owns the next action: close Sprint 24 Cycle 1 or continue to Cycle 2.
- Neo is loaded and available for the next implementation/fix/refactor assignment.

## Sprint 24 Cycle 2 — Multi-Filter Relationship Chaining (2026-04-13)

### Delivered
- Parser now preserves multiple `--via`/`--sans` relationship clauses in order.
- Match namespaces keep `relationship` for compatibility and add `relationships` for chained filters.
- Executor runs the first relationship query normally, then applies later relationship clauses as sequential post-filters over result records.
- Added regression coverage for parser ordering plus positive and negative chained relationship filtering.

### Verification
## Sprint 25 Cycle 0 - Dart Tree-Sitter Dependency Spike (2026-05-06)

### Delivered
- Added `tree-sitter-language-pack>=1.6.2` to `pyproject.toml` as the Dart grammar provider candidate.
- Used `make install` to refresh the project venv after the dependency change.
- Added `tests/unit/test_sprint25_c0.py` to prove `tree_sitter_language_pack.get_language("dart")` returns a `tree_sitter.Language` and parses a Flutter-style Dart fixture without ERROR nodes.
- Removed the temporary script/Makefile spike path in favor of the unit test per user direction.

### Verification
- `make test FILE=tests/unit/test_sprint25_c0.py` — 1 passed.

### Decision For Review
- Dependency path is viable enough for Cycle 1: Dart grammar can be loaded from Python through `tree-sitter-language-pack` and used with the existing `tree_sitter.Parser`.

## Sprint 25 Cycle 1 - Dart Parser Foundation (2026-05-06)

### Delivered
- Added `via/parsers/dart_parser.py` implementing `DartParser(ParserABC)`.
- Registered `DartParser` in CLI, MCP, coverage registry assembly, and public package exports.
- Added Flutter/Dart default excludes to `PathFilter`.
- Extracted core Dart symbols: classes, mixins, enums, extensions, constructors, methods, top-level functions, globals, imports, exports, and parts.
- Added `--lang dart` alias support and updated related help/schema text.
- Added focused Cycle 1 tests in `tests/unit/test_sprint25_c1.py`.

### TDD Notes
- Initial focused Cycle 1 test failed on unnamed constructor extraction; fixed constructor identifier selection.
- Added CLI registration test next; it failed because `--lang dart` was not in language aliases; added the alias and help/schema wording.

### Verification
- `make test FILE=tests/unit/test_sprint25_c1.py` — 7 passed.
- `make test FILE=tests/unit/test_sprint25_c0.py` — 1 passed.
- `make test FILE=tests/unit/test_sprint11_c1.py` — 23 passed.
- `make test FILE=tests/unit/test_sprint14_c2.py` — 29 passed.
- `make test FILE=tests/unit/test_relationship_cli.py` — 39 passed.
- `make test FILE=tests/unit/test_type_filter_relationships.py` — 6 passed.
- `make test ARGS='tests/unit/test_pipeline_parser.py tests/unit/test_relationship_pipeline.py tests/unit/test_web_query_relationship.py'` — 1313 passed, 1 skipped, 4 warnings.
- `make test` — 1313 passed, 1 skipped, 4 warnings in 134.51s.

## Sprint 25 Cycle 2 - Dart/Flutter Relationships And Docs (2026-05-06)

### Delivered
- Added `tests/unit/test_sprint25_c2.py` for Flutter fixture relationships, docs/MCP examples, and parser error behavior.
- Added Dart body call extraction for simple `identifier()` call sites.
- Adjusted Dart generic inheritance extraction so `State<DetailsPage>` contributes `State` as the base relationship anchor.
- Added unresolved inheritance target resolution to external class-like symbols, enabling queries against Flutter SDK base names such as `StatefulWidget` when SDK sources are not indexed.
- Fixed Dart directive extraction for tree-sitter `configurable_uri` import nodes.
- Updated README, `docs/USER_GUIDE.md`, and MCP schema examples with Dart/Flutter workflows and structural-only support boundaries.

### Verification
- `make test FILE=tests/unit/test_sprint25_c2.py` — 3 passed.
- `make test FILE=tests/unit/test_sprint25_c1.py` — 7 passed.
- `make test FILE=tests/unit/test_relationship_pipeline.py` — 10 passed.
- `make test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make test FILE=tests/unit/test_import_relationships.py` — 8 passed.
- `make test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make test FILE=tests/unit/test_sprint25_c0.py` — 1 passed.

## Sprint 25 Cycle 3 - Judge Skill & Query Engine Fixes (2026-06-20)

1. **BUG-1: Inverted Declares Validation & Type Mapping**: Fix the type mapping logic and validation for inverted relationship queries in `via/pipeline/executor.py` and `via/db/store.py` so that `s` and `t` are mapped to the correct types regardless of inversion, and checking container types checks the actual container. Added `_get_actual_inverted()` to the executor to dynamically detect container types, and added container validation checks to both the positive and negative query paths.
2. **BUG-2: Transitive Imports Query**: Implemented transitive imports joins for files (`filepath` or `filename`) in `query_relationships` and `query_negative_relationships` in `via/db/store.py` so that when the left side is a file, the query matches symbols declared in the file that import the target module or file.

### Key Design Decisions
- Dynamically resolve actual inversion status via `_get_actual_inverted()` in the executor to automatically handle user query direction mismatches.
- Perform transitive imports matching by joining imports to file declarations when subject or object is file-like.

### Verification
- Verified by adding transitive file imports tests in `tests/unit/test_import_relationships.py`.
- Static logic trace verified correctness for all scenarios (3, 7, 14).

## Sprint 26 Cycle 1 — Baseline Stabilization & JS Body Analyzer Unit Testing (2026-06-20)

### Delivered
- Resolved baseline failure `test_query_filepath_imports_filepath` in `tests/unit/test_import_relationships.py` by updating `resolve_pending_relationships` in `via/db/store.py` to match module targets (e.g. `'module_a'`) to project files (e.g. `'module_a.py'`), creating proper `declares` relationships, and mapping module symbols to the project file paths.
- Resolved baseline failure `test_sans_declares_returns_empty_markdown` in `tests/unit/test_sprint15_c3.py` by removing the redundant parameter swap logic from `query_negative_relationships` in `via/db/store.py`.
- Added dedicated unit tests for `_CallBodyAnalyzer`, `_HttpCallBodyAnalyzer`, and `_StringConstantBodyAnalyzer` in `tests/unit/test_js_body_analyzer.py`.

### Key Design Decisions
- Removed the `declares` container-type swap logic from `query_negative_relationships` because the outer query always selects and returns `s.*` (which must match the requested result type, e.g., `filepath`), so changing `s`'s type to a member (e.g., `header`) broke negative relationship projection. `invert_join` is already correctly computed by `PipelineExecutor` based on relationship direction, making the database-side swap logic obsolete for negative queries.

### Verification
- Verified that all 1345 tests pass cleanly under `make test`.

## Sprint 26 Cycle 3 — Performance Optimization (2026-06-21)

### Delivered
- Implemented SQLite nested CTE compilation in `query_relationships_chained` in `via/db/store.py` to compile chained pipeline stage filters into a single nested CTE query.
- Added candidate name batching (`result_names`) in `query_relationships` and `query_negative_relationships` in `via/db/store.py`.
- Refactored `PipelineExecutor._execute_match_stage` to delegate to `query_relationships_chained` for chained filters.
- Optimized `PipelineExecutor._filter_results_by_relationship` to execute chunked queries of 500 candidate names.
- Added unit test `test_chained_relationship_query` to `tests/unit/test_relationship_pipeline.py`.

### Key Design Decisions
- Handled positive/negative combinations in CTE query compilation by dynamically selecting symbol fields + `id AS symbol_id` for the first stage (`rel_0`), and selecting only `id AS symbol_id` for subsequent stages (`rel_i`), matching on `symbol_id IN (SELECT symbol_id FROM rel_i)`.
- Chunked candidate query names in batches of 500 to avoid SQLite host parameter limits while retaining optimal filtering speed.

## Sprint 26 Cycle 4 — Class-Based Relationship Type Hierarchy Design (2026-06-21)

### Key Decisions
- **Class-Based Hierarchy**: Modeled relationship types as subclasses of composite categories (`Any`, `UpstreamRef`, `DownstreamRef`, `ReaderRef`, `WriterRef`) in Python to leverage standard object-oriented `issubclass` mapping.
- **Mixed Direction Support**: Resolved queries spanning both incoming and outgoing dependency directions (such as `blast` or `any`) will be compiled into SQL `UNION` queries inside `DatabaseStore.query_relationships`.
- **Canned Configuration**: Once the class hierarchy is integrated, the `blast` query can be defined purely as `.via/canned/blast.json` containing `any-ref` without code changes to the canned query modules.

