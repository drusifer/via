# Sprint 25 Consolidated Documentation

This document consolidates all documentation for Sprint 25.

## Table of Contents

- [SPRINT_25_DART_FLUTTER_USER_STORIES.md](#sprint-25-dart-flutter-user-storiesmd) (originally `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`)

- [SPRINT_25_ARCHITECTURE.md](#sprint-25-architecturemd) (originally `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`)

- [SPRINT_25_CYCLE_0_REVIEW.md](#sprint-25-cycle-0-reviewmd) (originally `agents/morpheus.docs/SPRINT_25_CYCLE_0_REVIEW.md`)

- [SPRINT_25_CYCLE_1_REVIEW.md](#sprint-25-cycle-1-reviewmd) (originally `agents/morpheus.docs/SPRINT_25_CYCLE_1_REVIEW.md`)

- [SPRINT_25_CYCLE_2_REVIEW.md](#sprint-25-cycle-2-reviewmd) (originally `agents/morpheus.docs/SPRINT_25_CYCLE_2_REVIEW.md`)

- [SPRINT_25_PLAN_REVIEW.md](#sprint-25-plan-reviewmd) (originally `agents/morpheus.docs/SPRINT_25_PLAN_REVIEW.md`)

- [SPRINT_25_CYCLE_2_HCI_REVIEW.md](#sprint-25-cycle-2-hci-reviewmd) (originally `agents/smith.docs/SPRINT_25_CYCLE_2_HCI_REVIEW.md`)

- [SPRINT_25_GATE1_REVIEW.md](#sprint-25-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`)

- [SPRINT_25_GATE2_REVIEW.md](#sprint-25-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`)

- [SPRINT_25_TASKS.md](#sprint-25-tasksmd) (originally `agents/mouse.docs/SPRINT_25_TASKS.md`)

- [SPRINT_25_CYCLE_2_SUMMARY_2026-05-06T23-31.md](#sprint-25-cycle-2-summary-2026-05-06t23-31md) (originally `agents/neo.docs/SPRINT_25_CYCLE_2_SUMMARY_2026-05-06T23-31.md`)

- [SPRINT_25_CYCLE_2_UAT_Summary_2026-05-06T23-38.md](#sprint-25-cycle-2-uat-summary-2026-05-06t23-38md) (originally `agents/trin.docs/SPRINT_25_CYCLE_2_UAT_Summary_2026-05-06T23-38.md`)


---


## SPRINT_25_DART_FLUTTER_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`


## Sprint 25 User Stories — Dart And Flutter Support

**Author**: Cypher  
**Date**: 2026-05-06  
**Status**: DRAFT — pending Smith review and Morpheus architecture  
**Theme**: Extend VIA to index and query Dart/Flutter codebases  
**Estimated Points**: ~13pts

---

### Background

The user requested support for Flutter / Dart code. VIA already has the right product seam for this: `ParserABC`, `ParserRegistry`, language-specific parsers, `ParseResult.language`, `symbols.language`, `symbol_subtype`, and existing query/output stages.

The product goal is not to become a Flutter analyzer or language server. The goal is to make Dart and Flutter projects searchable through the same low-token VIA workflows that work today for Python, JavaScript, TypeScript, and Markdown.

### Product Goal

A developer or AI agent can index a Flutter project, find Dart files and symbols, inspect raw source for specific classes/functions, and ask basic relationship questions without manually falling back to broad text search.

### Scope

#### In Scope

- Dart source files: `.dart`
- Language filter: `--lang dart`
- Core symbol extraction:
  - classes
  - mixins
  - enums
  - extensions
  - top-level functions
  - class methods
  - constructors
  - top-level variables/constants
  - imports, exports, and parts
- Flutter-relevant symbol discovery:
  - `Widget`, `StatelessWidget`, `StatefulWidget`, and `State<T>` subclasses are queryable as normal classes with subtype metadata where feasible
  - `build` methods are queryable as methods
- Relationships:
  - `declares` from file to symbol
  - `imports` for `import`, `export`, and `part` directives
  - `inherits-from` for `extends`, `implements`, and `with` where the parser can extract the target names
  - best-effort `calls` within function/method bodies
- Flutter project exclusions:
  - `.dart_tool/`
  - `build/`
  - `.flutter-plugins`
  - `.flutter-plugins-dependencies`
  - platform build caches such as `android/.gradle/` and `ios/Pods/`
- Documentation and MCP examples for Dart/Flutter workflows

#### Out Of Scope

- Full semantic Dart analysis or type resolution
- Cross-file call graph resolution beyond existing VIA relationship behavior
- Widget tree reconstruction
- Route graph reconstruction
- Pub package dependency resolution beyond indexing import/export/part strings
- Parsing generated files differently from user files unless they are excluded by defaults or `.gitignore`
- YAML parsing for `pubspec.yaml` as a symbol source

### Product Constraints

- Preserve the result-stage-first relationship model:

  ```text
  via <result stage> [--via|--sans REL <filter stage>]
  ```

- Do not introduce a Flutter-specific query language.
- Dart support must use the same parser registry, database, query, and renderer paths as other languages.
- Parser failures must be partial and recoverable: return valid symbols when possible and set `parse_error`.
- Generated/vendor/cache content should not pollute default results.
- Architecture must verify the parser engine choice. A maintained Dart AST/tree-sitter grammar is preferred, but Morpheus owns the final technical selection.

---

### S25-1: Dart File Discovery And Language Filtering

**Priority**: P0  
**Estimate**: 2pts

**As a** developer indexing a Flutter project,  
**I want** `.dart` files discovered and tagged as Dart,  
**so that** I can query Dart files and symbols without custom include patterns.

#### Acceptance Criteria

- [ ] A Dart parser registers `.dart` through `ParserRegistry`.
- [ ] `via index <flutter-project>` marks `.dart` files parseable.
- [ ] Indexed Dart symbols use `language = "dart"`.
- [ ] `via -mg "*" -tF --lang dart` returns Dart files.
- [ ] `via -mg "*" -tc --lang dart` returns Dart classes only.
- [ ] Existing Python, JS/TS, and Markdown language filters are unchanged.
- [ ] Tests cover mixed Python/JS/TS/Dart fixtures with `--lang dart`.

---

### S25-2: Dart Parser Foundation

**Priority**: P0  
**Estimate**: 5pts

**As a** developer navigating Dart code,  
**I want** VIA to extract Dart symbols,  
**so that** I can search classes, methods, functions, imports, and constants from CLI/MCP.

#### Required Symbols

| Dart Construct | VIA Symbol Type | Notes |
|---|---|---|
| `class Foo {}` | `class` | `symbol_subtype = null` |
| `mixin Foo {}` | `class` | `symbol_subtype = "mixin"` |
| `enum Foo {}` | `class` | `symbol_subtype = "enum"` |
| `extension Foo on Bar {}` | `class` | `symbol_subtype = "extension"` |
| `void main() {}` | `function` | Top-level function |
| `Widget build(...) {}` | `method` | Method under class/state class |
| `Foo(...)` | `method` | Constructor, subtype or name must make constructor discoverable |
| `const foo = ...` | `global` | Top-level variable/constant |
| `import 'package:x/y.dart';` | `import` | Module string preserved |
| `export 'x.dart';` | `import` | `symbol_subtype = "export"` if supported |
| `part 'x.g.dart';` | `import` | `symbol_subtype = "part"` if supported |

#### Acceptance Criteria

- [ ] `DartParser` implements `ParserABC`.
- [ ] `can_parse()` returns true only for `.dart`.
- [ ] `parse()` returns a `ParseResult` with Dart classes, methods, functions, imports, and globals.
- [ ] Line numbers are 1-indexed and byte offsets match UTF-8 source ranges.
- [ ] Syntax-error files return partial symbols plus `parse_error`; they do not crash indexing.
- [ ] Oversized files respect the existing 10MB parse limit.
- [ ] Tests cover classes, mixins, enums, extensions, constructors, top-level functions, methods, imports, exports, parts, globals, and syntax-error partial parse.

---

### S25-3: Flutter-Aware Query Value

**Priority**: P1  
**Estimate**: 2pts

**As a** Flutter developer,  
**I want** common Flutter structures to be easy to find,  
**so that** I can navigate app screens and widgets quickly.

#### Acceptance Criteria

- [ ] `StatelessWidget`, `StatefulWidget`, and `State<T>` subclasses are indexed as classes with inherited base names captured.
- [ ] `build` methods are indexed as methods under their owning classes.
- [ ] Users can find widgets with normal queries, for example:

  ```text
  via -mg "*Widget" -tc --lang dart
  via -mg "build" -tm --lang dart
  ```

- [ ] `--via inherits-from` can find classes related to common Flutter base classes where the source explicitly names the base.
- [ ] Docs state the boundary clearly: VIA indexes Flutter code structure; it does not infer widget trees or runtime navigation graphs.
- [ ] Tests include a small Flutter-style fixture with `StatelessWidget`, `StatefulWidget`, `State<T>`, and `build`.

---

### S25-4: Dart Relationships

**Priority**: P1  
**Estimate**: 3pts

**As a** developer asking relationship questions in Dart,  
**I want** imports, declarations, inheritance, and calls represented with existing VIA relationship types,  
**so that** Dart queries behave like other supported languages.

#### Acceptance Criteria

- [ ] `declares` links each Dart file to parsed top-level symbols.
- [ ] `imports` links Dart files to `import`, `export`, and `part` targets.
- [ ] `inherits-from` captures `extends`, `implements`, and `with` targets.
- [ ] `calls` captures best-effort function/method calls inside Dart bodies.
- [ ] Relationship queries use existing `--via` / `--sans` stages.
- [ ] Tests prove Dart relationship results are queryable through existing executor paths.

---

### S25-5: Flutter Project Hygiene And Documentation

**Priority**: P0  
**Estimate**: 1pt

**As a** developer indexing Flutter apps,  
**I want** generated caches and dependency folders excluded by default,  
**so that** my index stays focused on source I own.

#### Acceptance Criteria

- [ ] Default excludes include Flutter/Dart cache and build artifacts:
  - `.dart_tool/`
  - `build/`
  - `android/.gradle/`
  - `ios/Pods/`
  - `.flutter-plugins`
  - `.flutter-plugins-dependencies`
- [ ] `.gitignore` remains respected.
- [ ] Docs list Dart/Flutter as supported and show concise examples:

  ```text
  via -mg "*" -tF --lang dart
  via -mg "*Screen" -tc --lang dart
  via -mg "build" -tm --lang dart -oR
  ```

- [ ] MCP schema examples include at least one Dart/Flutter task.
- [ ] Tests confirm default excludes prevent Flutter build/cache files from entering discovered parseable source.

---

### Definition Of Done

- [ ] Smith approves the Dart/Flutter stories for user value and discoverability.
- [ ] Morpheus approves parser engine, dependency strategy, and relationship mapping.
- [ ] Mouse breaks the work into short cycles, preferably discovery/parser first and relationships/docs second.
- [ ] Neo implements through existing parser registry/query pipeline paths.
- [ ] Trin verifies mixed-language regression coverage and Flutter fixture UAT.
- [ ] Documentation and MCP schema teach Dart support without implying full Flutter semantic analysis.

---

### Recommended Sprint Split

| Cycle | Scope | Points |
|---|---|---:|
| 1 | S25-1 discovery/lang + S25-2 parser foundation + S25-5 excludes/docs stub | 8 |
| 2 | S25-3 Flutter-aware value + S25-4 relationships + docs/MCP examples | 5 |

### Gate Handoff

@Smith: Please review Sprint 25 stories for Flutter/Dart user value. Focus on whether the scope gives Flutter developers useful navigation without overpromising semantic Flutter analysis.


---


## SPRINT_25_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`


## Sprint 25 Architecture - Dart / Flutter Support

**Author**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED FOR SMITH GATE 2  
**Source Stories**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`

### Architecture Summary

Add Dart support as a normal VIA language parser. Do not add a Flutter-specific query language or special execution path.

The core implementation is a new `DartParser(ParserABC)` registered beside `PythonParser`, `MarkdownParser`, and `JavaScriptParser`. It produces existing `ParseResult` entities, and `IndexingService` plus `DatabaseStore` continue to store/query those entities through the current schema.

### Dependency Decision

VIA already uses `tree-sitter` plus prebuilt language wheels for JS/TS. Dart should use tree-sitter if the implementation can load a Dart grammar reliably in this Python package.

Evidence checked during planning:

- Python `tree-sitter` provides Python bindings and documents language packages as the normal setup path.
- The upstream tree-sitter parser list includes `github.com/UserNobody14/tree-sitter-dart`, last commit listed as 2025-02-28, ABI 14, grammar.json yes, external scanner yes.
- The npm `tree-sitter-dart` package exists but is stale as a distribution channel and is not a Python wheel equivalent.

#### Binding Decision

Sprint 25 must start with a short parser viability spike:

1. Prove a Python-loadable Dart tree-sitter grammar path.
2. Parse a small Dart/Flutter fixture.
3. Document the chosen dependency path in `pyproject.toml` or a local build note.

If the grammar cannot be loaded cleanly without brittle install steps, do not hand-roll the full parser in Cycle 1. Instead, return to Morpheus with one of these decisions:

- vendor/build a generated grammar artifact deliberately, or
- reduce Sprint 25 to discovery/excludes/docs plus a conservative lexical symbol scanner, or
- defer Dart parser foundation until the dependency path is stable.

### Components

#### `via/parsers/dart_parser.py`

New parser implementing `ParserABC`.

Responsibilities:

- `get_supported_extensions()` returns `{'.dart'}`.
- `can_parse()` checks `.dart` only.
- `language_name` returns `"dart"`.
- `parse(file_path, content)` returns `ParseResult(file_path=file_path, language="dart")`.
- Enforce existing 10MB size limit behavior.
- Return partial symbols plus `parse_error` on grammar/syntax failures.

Implementation style should mirror `JavaScriptParser`:

- lazy parser initialization
- per-process parser singleton, safe for multiprocessing workers
- helper analyzers for body-level calls if call extraction grows beyond a small traversal
- no database writes inside the parser

#### Registration Points

Register `DartParser()` anywhere parsers are currently assembled:

- `via/__main__.py`
- `via/mcp/server.py`
- `via/commands/coverage.py` only if coverage imports need parseable extension parity
- any tests that construct a mixed parser registry

Update `via/__init__.py` public exports only if project policy wants every parser exported. This is optional for CLI behavior but useful for tests/programmatic users.

#### Discovery And Excludes

Extend `PathFilter.DEFAULT_EXCLUDES` with Flutter/Dart build/cache noise:

- `.dart_tool/`
- `build/`
- `android/.gradle/`
- `ios/Pods/`
- `.flutter-plugins`
- `.flutter-plugins-dependencies`

`build/` may already appear indirectly in some projects; adding it explicitly is acceptable because generated build output is not source code.

#### Entity Mapping

Map Dart constructs into existing entity types:

| Dart construct | Entity | Notes |
|---|---|---|
| class | `ClassEntity` | normal class |
| mixin | `ClassEntity` | `symbol_subtype="mixin"` |
| enum | `ClassEntity` | `symbol_subtype="enum"` |
| extension | `ClassEntity` | `symbol_subtype="extension"` |
| top-level function | `FunctionEntity` | no class parent |
| method | `FunctionEntity` | parent class set through existing store flow |
| constructor | `FunctionEntity` | name should be `ClassName` or `ClassName.named`; set `symbol_subtype="constructor"` |
| top-level variable/constant | `GlobalEntity` | include type/value where cheap |
| import/export/part directive | `ImportEntity` | preserve raw target string |

No schema migration is needed. `symbol_subtype` already exists.

#### Relationship Mapping

Use existing relationship types only:

- `declares`: produced by existing file-to-symbol storage flow.
- `imports`: Dart `import`, `export`, and `part` directives are stored as import-like relationships to their directive target strings.
- `inherits-from`: capture `extends`, `implements`, and `with` target names from class declarations.
- `calls`: best-effort body call extraction only; do not promise cross-file resolution.

`implements` and `with` target names should use `inherits-from` for Sprint 25 so users can ask "classes related to this interface/mixin" through the current relationship vocabulary. If a future sprint needs distinct relationship types, it should be planned separately.

#### Flutter-Specific Handling

Flutter awareness stays structural:

- `StatelessWidget`, `StatefulWidget`, and `State<T>` are just base names captured by `inherits-from`.
- `build` is just a method name under a class.
- No widget tree, route graph, provider graph, or dependency injection inference.

Docs and MCP examples must say this directly.

### Query Examples To Preserve

These examples should work through ordinary VIA stages:

```text
via -mg "*" -tF --lang dart
via -mg "*Screen" -tc --lang dart
via -mg "build" -tm --lang dart -oR
via -mg "*Widget" -tc --lang dart
via -mg "*" -tc --lang dart --via inherits-from -mg "StatelessWidget" -tc
```

### Test Strategy

Use focused tests first, then one integration/UAT fixture.

Required test groups:

- `DartParser` unit tests for classes, mixins, enums, extensions, constructors, methods, functions, globals, imports, exports, parts.
- Parser error test: syntax error returns partial symbols plus `parse_error`.
- Registry/discovery test: `.dart` is parseable and `--lang dart` filters files/symbols.
- Relationship tests: `declares`, `imports`, `inherits-from`, and simple `calls`.
- Flutter fixture test: `StatelessWidget`, `StatefulWidget`, `State<T>`, and `build`.
- Regression: existing Python, JS/TS, Markdown parser tests remain unchanged.

Run verification through Makefile targets only.

### Sprint Cycles

#### Cycle 0 - Parser Dependency Spike (1pt)

Prove the Dart grammar load path in Python and record the dependency/build decision.

Exit criteria:

- A minimal parser can parse one Dart fixture in a unit test or spike script.
- Morpheus approves the dependency path.
- If blocked, stop and do not start the full parser implementation.

#### Cycle 1 - Discovery, Excludes, Parser Foundation (7pt)

Implement `.dart` discovery, default excludes, `DartParser`, core symbol extraction, and `--lang dart` basics.

#### Cycle 2 - Flutter Value, Relationships, Docs (5pt)

Implement Flutter fixture coverage, relationships, docs, and MCP schema examples.

### Non-Goals

- Flutter semantic analyzer replacement.
- Widget tree reconstruction.
- Route graph reconstruction.
- Pub package dependency resolution.
- Cross-file call graph resolution beyond current VIA behavior.
- New Flutter-specific CLI flags.

### Risks

| Risk | Mitigation |
|---|---|
| Dart grammar dependency cannot be loaded cleanly in Python | Cycle 0 spike is a hard gate |
| Users expect Flutter semantic analysis | Docs and MCP examples state structural boundary |
| Constructor representation becomes confusing | Store as methods with `symbol_subtype="constructor"` and document query behavior |
| Directive relationships are mistaken for resolved dependencies | Docs call them directive target strings |
| Parser body traversal becomes large like old JS parser | Extract helper analyzers early if call extraction grows |

### Architecture Approval

Approved to proceed to Smith Gate 2 with the dependency spike as a required first cycle.


---


## SPRINT_25_CYCLE_0_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_25_CYCLE_0_REVIEW.md`


## Sprint 25 Cycle 0 Review - Dart Parser Dependency Path

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Scope**: Dependency viability spike  
**Verdict**: APPROVED

### Reviewed

- `pyproject.toml`
- `tests/unit/test_sprint25_c0.py`
- Trin UAT result: `make test FILE=tests/unit/test_sprint25_c0.py` — 1 passed

### Decision

The Dart parser dependency path is approved for Cycle 1.

`tree-sitter-language-pack>=1.6.2` is acceptable for Sprint 25 because the targeted unit test proves:

- the package is installable through project dependencies;
- `get_language("dart")` returns a `tree_sitter.Language`;
- the resulting parser can parse a Flutter-style Dart fixture without ERROR nodes.

### Binding Guidance For Cycle 1

- Implement `DartParser` against `tree_sitter_language_pack.get_language("dart")`.
- Keep parser initialization lazy and per-process, matching `JavaScriptParser`.
- Preserve graceful `ImportError`/dependency failure behavior by returning `ParseResult.parse_error`.
- Do not add relationships beyond what Cycle 1 needs for symbol extraction and `--lang dart`; deeper relationship coverage belongs to Cycle 2.
- Add unit coverage for the parser foundation before integration wiring.

### Handoff

@Neo: Proceed with Sprint 25 Cycle 1 parser foundation.


---


## SPRINT_25_CYCLE_1_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_25_CYCLE_1_REVIEW.md`


## Sprint 25 Cycle 1 Review - Parser Foundation

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED

### Scope Reviewed

- `DartParser(ParserABC)` and `.dart` discovery path.
- Parser registration in CLI, watch, MCP, coverage, and public exports.
- Flutter/Dart generated-directory excludes.
- Core Dart extraction for imports, exports, parts, globals, functions, classes, mixins, enums, extensions, constructors, and methods.
- `--lang dart` query support.
- Constructor subtype persistence through the shared method-symbol indexing path.

### Decision

Cycle 1 is approved.

The implementation follows the Sprint 25 architecture: Dart is added as a normal VIA parser, without a Flutter-specific query path or schema migration. The dependency remains isolated behind `tree-sitter-language-pack`, the parser emits existing `ParseResult` entity types, and storage/query behavior uses the existing language and subtype filters.

### Review Finding Closed

Morpheus review found one gap before approval: constructor methods were emitted by the parser with `symbol_subtype="constructor"`, but `IndexingService._store_class_symbols()` did not persist method subtypes. A focused red test was added first, then the shared method-symbol write path was updated to store method subtypes.

### Verification

- `make test FILE=tests/unit/test_sprint25_c1.py` - 7 passed.
- `make test FILE=tests/unit/test_indexer_symbols.py` - 12 passed.
- `make test FILE=tests/unit/test_sprint14_c2.py` - 29 passed.
- `make test FILE=tests/unit/test_sprint25_c0.py` - 1 passed.

### Notes For Cycle 2

- Add relationship verification for Dart imports and inheritance.
- Add Flutter fixture coverage for `StatefulWidget`, `State<T>`, and `build`.
- Add docs and MCP examples that clearly state the structural-only Flutter boundary.


---


## SPRINT_25_CYCLE_2_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_25_CYCLE_2_REVIEW.md`


## Sprint 25 Cycle 2 Review - Flutter Value, Relationships, Docs

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED

### Scope Reviewed

- Dart/Flutter fixture coverage for `StatefulWidget`, `State<T>`, `build`, directives, declares, inheritance, and calls.
- Dart parser changes for simple body call extraction, directive URI extraction, and generic base-name extraction.
- Relationship storage behavior for unresolved external inheritance anchors.
- README, user guide, and MCP schema examples.
- Trin UAT and Smith HCI approval.

### Decision

Cycle 2 is approved.

The implementation keeps the Sprint 25 architecture intact: Dart/Flutter support uses the normal parser registry, `ParseResult`, symbol table, existing relationship types, language filtering, output formats, and MCP schema. No Flutter-specific query flags or semantic analyzer behavior were introduced.

### Review Finding Closed

Final architecture review found one user-facing risk: unresolved Flutter SDK base classes were initially represented as ordinary `class` symbols. That made relationship queries work, but could pollute normal class searches with external SDK names.

The fix stores unresolved inheritance anchors as `external_class`, maps them for relationship target matching, and keeps ordinary `-tc` class searches scoped to indexed project classes. A focused regression was added to `tests/unit/test_sprint25_c2.py`.

### Verification

- `make test FILE=tests/unit/test_sprint25_c2.py` - 3 passed.
- `make test FILE=tests/unit/test_relationship_pipeline.py` - 10 passed.
- `make test FILE=tests/unit/test_database_match.py` - 40 passed.
- `make test` - 1324 passed, 1 skipped, 4 warnings.

### Notes

- `build/` is excluded only for roots with `pubspec.yaml`, preserving non-Flutter discovery behavior.
- Dart imports, exports, and parts remain directive strings, not resolved package dependencies.
- Flutter support remains structural: no widget tree, route graph, pub dependency, or Dart analyzer inference.


---


## SPRINT_25_PLAN_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_25_PLAN_REVIEW.md`


## Sprint 25 Plan Review - Dart / Flutter Support

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Plan**: `agents/mouse.docs/SPRINT_25_TASKS.md`  
**Verdict**: APPROVED

### Review Summary

Mouse's sprint plan matches the approved architecture and preserves the critical dependency gate. The plan is safe to start.

### Findings

- Cycle 0 correctly blocks parser implementation until the Dart grammar can be loaded from Python.
- Cycle 1 is bounded to parser foundation, registration, excludes, core symbol extraction, and `--lang dart`.
- Cycle 2 correctly waits for parser foundation before relationships, Flutter fixtures, docs, and MCP schema examples.
- Smith is included in Cycle 2 for the user-facing support-boundary wording.
- Root `task.md` reflects the same cycle structure as the detailed Mouse plan.

### Binding Guidance For Neo

- Start with Cycle 0 only.
- Do not implement the full Dart parser until the dependency path is proven and reviewed.
- Use the existing `JavaScriptParser` lazy parser pattern where possible.
- Keep all work on existing VIA surfaces: `ParserABC`, `ParserRegistry`, `ParseResult`, language filters, relationships, docs/MCP examples.
- If Cycle 0 shows dependency risk, stop and hand the decision back to Morpheus instead of inventing a workaround mid-implementation.

### Handoff

@Neo: Begin Sprint 25 Cycle 0 dependency spike.


---


## SPRINT_25_CYCLE_2_HCI_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_25_CYCLE_2_HCI_REVIEW.md`


## Sprint 25 Cycle 2 HCI Review - Dart/Flutter Docs

**Reviewer**: Smith  
**Date**: 2026-05-06  
**Status**: APPROVED

### Review Scope

- README Dart/Flutter positioning.
- User guide Dart/Flutter examples and support boundary.
- MCP schema Dart/Flutter examples and support boundary.
- Trin UAT result for Cycle 2.

### Verdict

APPROVED.

The docs and MCP schema satisfy the Sprint 25 user-facing constraints:

- `--lang dart` is the visible language filter.
- Dart/Flutter examples use normal VIA surfaces: `-tF`, `-tc`, `-tm`, `--via inherits-from`, and `-oR`.
- Dart imports, exports, and parts are described as directive strings, not resolved package dependencies.
- Flutter support is framed as structural indexing and querying, not semantic Flutter analysis.
- The docs explicitly say VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.

### HCI Notes

- **Consistency and Standards**: Approved. No Flutter-only flags were added.
- **Match Between System and Real World**: Approved. Examples use user-recognizable Flutter terms: `StatefulWidget`, `build`, and `*Screen`.
- **Recognition Rather Than Recall**: Approved. MCP schema now includes concrete Dart/Flutter examples for agents.
- **Help and Documentation**: Approved. Boundary wording prevents users from mistaking VIA for a Flutter analyzer.

### Residual Risk

Relationship query syntax remains cognitively heavy, but Sprint 25 improves recognition by adding concrete examples. A future sprint could add a canned Flutter-oriented shortcut only if it expands transparently to ordinary VIA query args.


---


## SPRINT_25_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`


## Sprint 25 Gate 1 HCI Review — Dart / Flutter Support

**Reviewer**: Smith  
**Date**: 2026-05-06  
**Artifact**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Verdict**: APPROVED WITH NOTES

### Summary

The story set gives Flutter and Dart users a useful, believable first sprint: structural indexing, normal VIA queries, basic relationships, and Flutter project hygiene. It avoids the common product trap of promising semantic Flutter analysis or widget tree reconstruction.

### HCI Findings

#### Approved

- **Match between system and real world**: The stories use user-facing Dart/Flutter terms (`Widget`, `build`, `.dart`, `StatelessWidget`) while keeping the actual query model consistent with VIA.
- **Consistency and standards**: The stories preserve `--lang`, `-tc`, `-tm`, `--via`, and existing output behavior instead of inventing a Flutter-only surface.
- **Recognition rather than recall**: Documentation/MCP examples for Flutter workflows are included in S25-5.
- **Error prevention**: Default excludes for `.dart_tool/`, `build/`, Gradle, and Pods reduce noisy indexes in real Flutter projects.
- **Help and documentation**: The explicit boundary statement prevents users from assuming VIA is a Dart analyzer.

#### Notes For Morpheus

- Keep `--lang dart` as the only language spelling for this sprint unless aliases are already supported by the current language filter. Do not introduce both `dart` and `flutter` as language filters.
- Avoid Flutter-specific flags in Sprint 25. Users should learn normal VIA queries first.
- Architecture should decide whether constructors are stored as normal methods named `ClassName` or with a `constructor` subtype. The user-visible behavior must be documented either way.
- `import`, `export`, and `part` should be clearly explained as directive strings, not resolved package dependencies.
- If the Dart parser dependency is weaker than JS/TS tree-sitter support, docs must say "best-effort Dart parser" until UAT proves stability.

### Gate Decision

Gate 1 is approved. Proceed to Morpheus architecture.

### Handoff

@Morpheus: Design Sprint 25 architecture for Dart/Flutter support. Preserve the structural-indexing boundary and use existing VIA query surfaces.


---


## SPRINT_25_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`


## Sprint 25 Gate 2 UX Review - Dart / Flutter Architecture

**Reviewer**: Smith  
**Date**: 2026-05-06  
**Artifact**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`  
**Verdict**: APPROVED

### Summary

The architecture protects the user experience by making parser dependency viability a hard first cycle. That prevents a half-working Dart parser from being presented as full Flutter support.

### UX Assessment

- **Consistency and standards**: Approved. Dart uses normal VIA parser, language, relationship, and output surfaces.
- **Match between system and real world**: Approved. Flutter terms are treated as source-code structures users already recognize.
- **Error prevention**: Approved. Cycle 0 blocks full implementation until the grammar path is proven.
- **Help and documentation**: Approved with a required doc note: Dart imports/exports/parts are directive strings, not resolved package dependencies.
- **Recognition rather than recall**: Approved. The preserved examples are concrete and should be carried into docs/MCP schema.

### Required UX Notes For Implementation

- Keep the visible language filter as `--lang dart`.
- Do not add Flutter-specific flags in Sprint 25.
- If Cycle 0 fails and the sprint is rescoped, tell the user plainly; do not bury the limitation in a test note.
- Documentation must include the structural boundary: no widget tree, route graph, or semantic analyzer behavior.
- Constructor query behavior must be documented once Neo implements the chosen representation.

### Gate Decision

Gate 2 is approved. Proceed to Mouse sprint planning.

### Handoff

@Mouse: Break Sprint 25 into short cycles using Morpheus architecture. Keep Cycle 0 as a hard dependency gate before parser implementation.


---


## SPRINT_25_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_25_TASKS.md`


## Sprint 25 Tasks - Dart / Flutter Support

**Scrum Master**: Mouse  
**Date**: 2026-05-06  
**Status**: Planned  
**Architecture**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`  
**Stories**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Gate 1**: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`  
**Gate 2**: `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`

### Sprint Goal

Make Dart/Flutter projects searchable through normal VIA structural indexing and query workflows, without promising Flutter semantic analysis.

### Cycle Plan

#### Cycle 0 - Parser Dependency Spike (1pt)

**Owner flow**: Neo -> Trin -> Morpheus  
**Purpose**: Prove the Dart grammar can be loaded from Python before full parser work starts.

- [ ] Neo: identify viable Python-loadable Dart tree-sitter grammar path.
- [ ] Neo: add minimal spike fixture or test that parses a Dart/Flutter snippet.
- [ ] Neo: document dependency/build decision for Morpheus.
- [ ] Trin: verify the spike result and failure behavior.
- [ ] Morpheus: approve dependency path or stop/rescope Sprint 25.

**Hard gate**: If Cycle 0 fails, do not start Cycle 1.

#### Cycle 1 - Discovery, Excludes, Parser Foundation (7pt)

**Owner flow**: Neo -> Trin -> Morpheus

- [ ] Neo: add `DartParser(ParserABC)` with `.dart` support and lazy parser setup.
- [ ] Neo: register `DartParser` in CLI/MCP parser assembly points.
- [ ] Neo: add Flutter/Dart default excludes to `PathFilter`.
- [ ] Neo: extract classes, mixins, enums, extensions, constructors, methods, top-level functions, globals, imports, exports, and parts.
- [ ] Neo: support `--lang dart` for file and symbol queries through existing language fields.
- [ ] Trin: run focused parser/discovery/language-filter tests.
- [ ] Morpheus: review parser integration and dependency boundaries.

#### Cycle 2 - Flutter Value, Relationships, Docs (5pt)

**Owner flow**: Neo -> Trin -> Smith -> Morpheus

- [ ] Neo: add Flutter-style fixture coverage for `StatelessWidget`, `StatefulWidget`, `State<T>`, and `build`.
- [ ] Neo: store/query Dart `declares`, `imports`, `inherits-from`, and best-effort `calls` relationships.
- [ ] Neo: update docs and MCP schema examples for Dart/Flutter workflows.
- [ ] Trin: run relationship, docs/schema, and mixed-language regression verification.
- [ ] Smith: run HCI review of docs/examples and support-boundary wording.
- [ ] Morpheus: final architecture review.

### Acceptance Gates

- [ ] Cycle 0 proves dependency path before parser foundation.
- [ ] `via -mg "*" -tF --lang dart` returns Dart files.
- [ ] `via -mg "*Screen" -tc --lang dart` returns Dart classes.
- [ ] `via -mg "build" -tm --lang dart -oR` returns Flutter-style build methods.
- [ ] Dart directives are documented as directive strings, not resolved dependencies.
- [ ] Docs explicitly state no widget tree, route graph, pub dependency resolution, or semantic analyzer behavior.
- [ ] Existing Python, JS/TS, Markdown tests remain green.

### Blockers

None at sprint start. Primary risk is Cycle 0 dependency viability.

### First Handoff

@Morpheus: Review this sprint plan against architecture. If approved, hand Cycle 0 to Neo.


---


## SPRINT_25_CYCLE_2_SUMMARY_2026-05-06T23-31.md

**Original Location**: `agents/neo.docs/SPRINT_25_CYCLE_2_SUMMARY_2026-05-06T23-31.md`


## Sprint 25 Cycle 2 Summary - 2026-05-06T23:31

### Scope

Implemented Dart/Flutter relationship value, fixture coverage, and docs/MCP examples.

### Delivered

- Added `tests/unit/test_sprint25_c2.py`.
- Added Flutter-style fixture coverage for `StatefulWidget`, `State<T>`, `build`, imports/parts, and a best-effort Dart call.
- Added Dart body call extraction for simple `identifier()` call sites inside functions and methods.
- Adjusted Dart base extraction so generic base names such as `State<DetailsPage>` index as `State`, not `State, DetailsPage`.
- Resolved external inheritance anchors by creating external class-like symbols for unresolved `inherits-from` targets such as Flutter SDK base classes.
- Fixed Dart directive extraction for `configurable_uri` import nodes.
- Updated README, user guide, and MCP schema examples for Dart/Flutter workflows and the structural-only boundary.

### Verification

- `make test FILE=tests/unit/test_sprint25_c2.py` - 3 passed.
- `make test FILE=tests/unit/test_sprint25_c1.py` - 7 passed.
- `make test FILE=tests/unit/test_relationship_pipeline.py` - 10 passed.
- `make test FILE=tests/unit/test_sprint23_c2.py` - 4 passed.
- `make test FILE=tests/unit/test_import_relationships.py` - 8 passed.
- `make test FILE=tests/unit/test_sprint22_c3.py` - 4 passed.
- `make test FILE=tests/unit/test_sprint25_c0.py` - 1 passed.

### Notes

- The implementation preserves the normal VIA parser, relationship, docs, and MCP surfaces. No Flutter-specific flags were added.
- Dart imports, exports, and parts remain directive strings; they are not package-resolution results.
- Flutter support remains structural and does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.


---


## SPRINT_25_CYCLE_2_UAT_Summary_2026-05-06T23-38.md

**Original Location**: `agents/trin.docs/SPRINT_25_CYCLE_2_UAT_Summary_2026-05-06T23-38.md`


## Sprint 25 Cycle 2 UAT Summary - 2026-05-06T23:38

### Result

PASS.

### Scope Verified

- Dart/Flutter fixture coverage for `StatefulWidget`, `State<T>`, `build`, directives, declares, inheritance, and best-effort calls.
- Dart docs and MCP examples include visible Dart/Flutter workflows.
- Docs state that Dart directives are directive strings, not resolved dependencies.
- Docs state that VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.
- Existing discovery behavior remains compatible with non-Flutter projects.
- Full test suite is green.

### Verification

- `make test FILE=tests/unit/test_sprint25_c2.py` - 3 passed.
- `make test FILE=tests/unit/test_discovery.py` - 12 passed.
- `make test FILE=tests/unit/test_sprint25_c1.py` - 7 passed.
- `make test` - 1324 passed, 1 skipped, 4 warnings.

### Finding

Initial full-suite run found one regression: adding a global `build/` exclude broke `test_discover_without_gitignore`, which expects non-Flutter `build/` directories to be discoverable when `.gitignore` is ignored. The fix scopes `build/` exclusion to roots containing `pubspec.yaml`; Flutter projects still exclude `build/`, while generic projects keep prior discovery behavior.


---
