# Sprint 25 User Stories — Dart And Flutter Support

**Author**: Cypher  
**Date**: 2026-05-06  
**Status**: DRAFT — pending Smith review and Morpheus architecture  
**Theme**: Extend VIA to index and query Dart/Flutter codebases  
**Estimated Points**: ~13pts

---

## Background

The user requested support for Flutter / Dart code. VIA already has the right product seam for this: `ParserABC`, `ParserRegistry`, language-specific parsers, `ParseResult.language`, `symbols.language`, `symbol_subtype`, and existing query/output stages.

The product goal is not to become a Flutter analyzer or language server. The goal is to make Dart and Flutter projects searchable through the same low-token VIA workflows that work today for Python, JavaScript, TypeScript, and Markdown.

## Product Goal

A developer or AI agent can index a Flutter project, find Dart files and symbols, inspect raw source for specific classes/functions, and ask basic relationship questions without manually falling back to broad text search.

## Scope

### In Scope

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

### Out Of Scope

- Full semantic Dart analysis or type resolution
- Cross-file call graph resolution beyond existing VIA relationship behavior
- Widget tree reconstruction
- Route graph reconstruction
- Pub package dependency resolution beyond indexing import/export/part strings
- Parsing generated files differently from user files unless they are excluded by defaults or `.gitignore`
- YAML parsing for `pubspec.yaml` as a symbol source

## Product Constraints

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

## S25-1: Dart File Discovery And Language Filtering

**Priority**: P0  
**Estimate**: 2pts

**As a** developer indexing a Flutter project,  
**I want** `.dart` files discovered and tagged as Dart,  
**so that** I can query Dart files and symbols without custom include patterns.

### Acceptance Criteria

- [ ] A Dart parser registers `.dart` through `ParserRegistry`.
- [ ] `via index <flutter-project>` marks `.dart` files parseable.
- [ ] Indexed Dart symbols use `language = "dart"`.
- [ ] `via -mg "*" -tF --lang dart` returns Dart files.
- [ ] `via -mg "*" -tc --lang dart` returns Dart classes only.
- [ ] Existing Python, JS/TS, and Markdown language filters are unchanged.
- [ ] Tests cover mixed Python/JS/TS/Dart fixtures with `--lang dart`.

---

## S25-2: Dart Parser Foundation

**Priority**: P0  
**Estimate**: 5pts

**As a** developer navigating Dart code,  
**I want** VIA to extract Dart symbols,  
**so that** I can search classes, methods, functions, imports, and constants from CLI/MCP.

### Required Symbols

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

### Acceptance Criteria

- [ ] `DartParser` implements `ParserABC`.
- [ ] `can_parse()` returns true only for `.dart`.
- [ ] `parse()` returns a `ParseResult` with Dart classes, methods, functions, imports, and globals.
- [ ] Line numbers are 1-indexed and byte offsets match UTF-8 source ranges.
- [ ] Syntax-error files return partial symbols plus `parse_error`; they do not crash indexing.
- [ ] Oversized files respect the existing 10MB parse limit.
- [ ] Tests cover classes, mixins, enums, extensions, constructors, top-level functions, methods, imports, exports, parts, globals, and syntax-error partial parse.

---

## S25-3: Flutter-Aware Query Value

**Priority**: P1  
**Estimate**: 2pts

**As a** Flutter developer,  
**I want** common Flutter structures to be easy to find,  
**so that** I can navigate app screens and widgets quickly.

### Acceptance Criteria

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

## S25-4: Dart Relationships

**Priority**: P1  
**Estimate**: 3pts

**As a** developer asking relationship questions in Dart,  
**I want** imports, declarations, inheritance, and calls represented with existing VIA relationship types,  
**so that** Dart queries behave like other supported languages.

### Acceptance Criteria

- [ ] `declares` links each Dart file to parsed top-level symbols.
- [ ] `imports` links Dart files to `import`, `export`, and `part` targets.
- [ ] `inherits-from` captures `extends`, `implements`, and `with` targets.
- [ ] `calls` captures best-effort function/method calls inside Dart bodies.
- [ ] Relationship queries use existing `--via` / `--sans` stages.
- [ ] Tests prove Dart relationship results are queryable through existing executor paths.

---

## S25-5: Flutter Project Hygiene And Documentation

**Priority**: P0  
**Estimate**: 1pt

**As a** developer indexing Flutter apps,  
**I want** generated caches and dependency folders excluded by default,  
**so that** my index stays focused on source I own.

### Acceptance Criteria

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

## Definition Of Done

- [ ] Smith approves the Dart/Flutter stories for user value and discoverability.
- [ ] Morpheus approves parser engine, dependency strategy, and relationship mapping.
- [ ] Mouse breaks the work into short cycles, preferably discovery/parser first and relationships/docs second.
- [ ] Neo implements through existing parser registry/query pipeline paths.
- [ ] Trin verifies mixed-language regression coverage and Flutter fixture UAT.
- [ ] Documentation and MCP schema teach Dart support without implying full Flutter semantic analysis.

---

## Recommended Sprint Split

| Cycle | Scope | Points |
|---|---|---:|
| 1 | S25-1 discovery/lang + S25-2 parser foundation + S25-5 excludes/docs stub | 8 |
| 2 | S25-3 Flutter-aware value + S25-4 relationships + docs/MCP examples | 5 |

## Gate Handoff

@Smith: Please review Sprint 25 stories for Flutter/Dart user value. Focus on whether the scope gives Flutter developers useful navigation without overpromising semantic Flutter analysis.
