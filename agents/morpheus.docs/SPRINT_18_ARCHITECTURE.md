# Sprint 18 Architecture — Polymorphic JS Parser Refactor

**Author**: Morpheus  
**Date**: 2026-04-08  
**Sprint**: Sprint 18 — Polymorphic JS Parser Refactor  
**Input**: `agents/cypher.docs/SPRINT_18_USER_STORIES.md`, `agents/smith.docs/SPRINT_18_GATE1_REVIEW.md`, `agents/morpheus.docs/POLYMORPHIC_REFACTOR_PLAN_2026-04-08T20:52.md`, `agents/morpheus.docs/POLYMORPHIC_REFACTOR_CLASSES_2026-04-08T20:58.md`

## Verdict

Proceed with a single-file, single-pass refactor in `via/parsers/javascript_parser.py`.

## Design Goals

1. Remove the large top-level node-type conditional from symbol extraction.
2. Preserve identical parse behavior for current JS/TS symbol support.
3. Reuse the same dispatch path for exported declarations instead of maintaining a second extraction branch.
4. Keep the refactor local; do not introduce a multi-file framework for one sprint slice.

## Chosen Shape

### Dispatcher + handler objects

Introduce a module-private dispatcher and handler set:

- `_TopLevelSymbolHandler`
- `_ImportStatementHandler`
- `_FunctionDeclarationHandler`
- `_ClassDeclarationHandler`
- `_InterfaceDeclarationHandler`
- `_EnumDeclarationHandler`
- `_VariableDeclarationHandler`
- `_TypeAliasDeclarationHandler`
- `_ExportDeclarationHandler`
- `_TopLevelSymbolExtractor`

These stay private because Sprint 18 is about controlling internal complexity, not publishing a new extension API.

### One handler per semantic family

Each handler owns one stable node family:

- imports
- functions
- classes
- TS interfaces and enums
- top-level variable declarations
- TS type aliases
- export wrappers

### Export wrappers recurse through the same dispatcher

`export_statement` and `export_default_declaration` should unwrap children and delegate them back into the dispatcher. They should not contain a second copy of extraction logic.

## Explicit Non-Goals

1. No executor strategy classes in Sprint 18.
2. No `FunctionBodyAnalyzer` extraction in Sprint 18.
3. No CLI, index-schema, or query behavior changes.
4. No new public extension surface for parser plugins.

## Risk Areas

1. Exported declarations losing parity under the wrapper handler.
2. TS-only declarations being omitted from the registry.
3. Refactor pressure spreading into later parser passes in the same sprint.

## Verification Requirements

1. Add a representative regression fixture covering import, function, class, interface, enum, type alias, variable declaration, and exported declarations.
2. Keep existing Sprint 11/14/16/17 JavaScript parser tests green.

## Implementation Handoff

Mouse should plan this as a single short cycle. Neo should implement the handler registry in `via/parsers/javascript_parser.py`, add targeted regression tests, and stop there.
