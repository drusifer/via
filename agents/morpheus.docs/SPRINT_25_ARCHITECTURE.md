# Sprint 25 Architecture - Dart / Flutter Support

**Author**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED FOR SMITH GATE 2  
**Source Stories**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`

## Architecture Summary

Add Dart support as a normal VIA language parser. Do not add a Flutter-specific query language or special execution path.

The core implementation is a new `DartParser(ParserABC)` registered beside `PythonParser`, `MarkdownParser`, and `JavaScriptParser`. It produces existing `ParseResult` entities, and `IndexingService` plus `DatabaseStore` continue to store/query those entities through the current schema.

## Dependency Decision

VIA already uses `tree-sitter` plus prebuilt language wheels for JS/TS. Dart should use tree-sitter if the implementation can load a Dart grammar reliably in this Python package.

Evidence checked during planning:

- Python `tree-sitter` provides Python bindings and documents language packages as the normal setup path.
- The upstream tree-sitter parser list includes `github.com/UserNobody14/tree-sitter-dart`, last commit listed as 2025-02-28, ABI 14, grammar.json yes, external scanner yes.
- The npm `tree-sitter-dart` package exists but is stale as a distribution channel and is not a Python wheel equivalent.

### Binding Decision

Sprint 25 must start with a short parser viability spike:

1. Prove a Python-loadable Dart tree-sitter grammar path.
2. Parse a small Dart/Flutter fixture.
3. Document the chosen dependency path in `pyproject.toml` or a local build note.

If the grammar cannot be loaded cleanly without brittle install steps, do not hand-roll the full parser in Cycle 1. Instead, return to Morpheus with one of these decisions:

- vendor/build a generated grammar artifact deliberately, or
- reduce Sprint 25 to discovery/excludes/docs plus a conservative lexical symbol scanner, or
- defer Dart parser foundation until the dependency path is stable.

## Components

### `via/parsers/dart_parser.py`

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

### Registration Points

Register `DartParser()` anywhere parsers are currently assembled:

- `via/__main__.py`
- `via/mcp/server.py`
- `via/commands/coverage.py` only if coverage imports need parseable extension parity
- any tests that construct a mixed parser registry

Update `via/__init__.py` public exports only if project policy wants every parser exported. This is optional for CLI behavior but useful for tests/programmatic users.

### Discovery And Excludes

Extend `PathFilter.DEFAULT_EXCLUDES` with Flutter/Dart build/cache noise:

- `.dart_tool/`
- `build/`
- `android/.gradle/`
- `ios/Pods/`
- `.flutter-plugins`
- `.flutter-plugins-dependencies`

`build/` may already appear indirectly in some projects; adding it explicitly is acceptable because generated build output is not source code.

### Entity Mapping

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

### Relationship Mapping

Use existing relationship types only:

- `declares`: produced by existing file-to-symbol storage flow.
- `imports`: Dart `import`, `export`, and `part` directives are stored as import-like relationships to their directive target strings.
- `inherits-from`: capture `extends`, `implements`, and `with` target names from class declarations.
- `calls`: best-effort body call extraction only; do not promise cross-file resolution.

`implements` and `with` target names should use `inherits-from` for Sprint 25 so users can ask "classes related to this interface/mixin" through the current relationship vocabulary. If a future sprint needs distinct relationship types, it should be planned separately.

### Flutter-Specific Handling

Flutter awareness stays structural:

- `StatelessWidget`, `StatefulWidget`, and `State<T>` are just base names captured by `inherits-from`.
- `build` is just a method name under a class.
- No widget tree, route graph, provider graph, or dependency injection inference.

Docs and MCP examples must say this directly.

## Query Examples To Preserve

These examples should work through ordinary VIA stages:

```text
via -mg "*" -tF --lang dart
via -mg "*Screen" -tc --lang dart
via -mg "build" -tm --lang dart -oR
via -mg "*Widget" -tc --lang dart
via -mg "*" -tc --lang dart --via inherits-from -mg "StatelessWidget" -tc
```

## Test Strategy

Use focused tests first, then one integration/UAT fixture.

Required test groups:

- `DartParser` unit tests for classes, mixins, enums, extensions, constructors, methods, functions, globals, imports, exports, parts.
- Parser error test: syntax error returns partial symbols plus `parse_error`.
- Registry/discovery test: `.dart` is parseable and `--lang dart` filters files/symbols.
- Relationship tests: `declares`, `imports`, `inherits-from`, and simple `calls`.
- Flutter fixture test: `StatelessWidget`, `StatefulWidget`, `State<T>`, and `build`.
- Regression: existing Python, JS/TS, Markdown parser tests remain unchanged.

Run verification through Makefile targets only.

## Sprint Cycles

### Cycle 0 - Parser Dependency Spike (1pt)

Prove the Dart grammar load path in Python and record the dependency/build decision.

Exit criteria:

- A minimal parser can parse one Dart fixture in a unit test or spike script.
- Morpheus approves the dependency path.
- If blocked, stop and do not start the full parser implementation.

### Cycle 1 - Discovery, Excludes, Parser Foundation (7pt)

Implement `.dart` discovery, default excludes, `DartParser`, core symbol extraction, and `--lang dart` basics.

### Cycle 2 - Flutter Value, Relationships, Docs (5pt)

Implement Flutter fixture coverage, relationships, docs, and MCP schema examples.

## Non-Goals

- Flutter semantic analyzer replacement.
- Widget tree reconstruction.
- Route graph reconstruction.
- Pub package dependency resolution.
- Cross-file call graph resolution beyond current VIA behavior.
- New Flutter-specific CLI flags.

## Risks

| Risk | Mitigation |
|---|---|
| Dart grammar dependency cannot be loaded cleanly in Python | Cycle 0 spike is a hard gate |
| Users expect Flutter semantic analysis | Docs and MCP examples state structural boundary |
| Constructor representation becomes confusing | Store as methods with `symbol_subtype="constructor"` and document query behavior |
| Directive relationships are mistaken for resolved dependencies | Docs call them directive target strings |
| Parser body traversal becomes large like old JS parser | Extract helper analyzers early if call extraction grows |

## Architecture Approval

Approved to proceed to Smith Gate 2 with the dependency spike as a required first cycle.
