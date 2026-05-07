# Sprint 25 Cycle 1 Review - Parser Foundation

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED

## Scope Reviewed

- `DartParser(ParserABC)` and `.dart` discovery path.
- Parser registration in CLI, watch, MCP, coverage, and public exports.
- Flutter/Dart generated-directory excludes.
- Core Dart extraction for imports, exports, parts, globals, functions, classes, mixins, enums, extensions, constructors, and methods.
- `--lang dart` query support.
- Constructor subtype persistence through the shared method-symbol indexing path.

## Decision

Cycle 1 is approved.

The implementation follows the Sprint 25 architecture: Dart is added as a normal VIA parser, without a Flutter-specific query path or schema migration. The dependency remains isolated behind `tree-sitter-language-pack`, the parser emits existing `ParseResult` entity types, and storage/query behavior uses the existing language and subtype filters.

## Review Finding Closed

Morpheus review found one gap before approval: constructor methods were emitted by the parser with `symbol_subtype="constructor"`, but `IndexingService._store_class_symbols()` did not persist method subtypes. A focused red test was added first, then the shared method-symbol write path was updated to store method subtypes.

## Verification

- `make test FILE=tests/unit/test_sprint25_c1.py` - 7 passed.
- `make test FILE=tests/unit/test_indexer_symbols.py` - 12 passed.
- `make test FILE=tests/unit/test_sprint14_c2.py` - 29 passed.
- `make test FILE=tests/unit/test_sprint25_c0.py` - 1 passed.

## Notes For Cycle 2

- Add relationship verification for Dart imports and inheritance.
- Add Flutter fixture coverage for `StatefulWidget`, `State<T>`, and `build`.
- Add docs and MCP examples that clearly state the structural-only Flutter boundary.
