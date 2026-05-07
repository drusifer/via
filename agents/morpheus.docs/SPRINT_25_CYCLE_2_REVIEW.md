# Sprint 25 Cycle 2 Review - Flutter Value, Relationships, Docs

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Status**: APPROVED

## Scope Reviewed

- Dart/Flutter fixture coverage for `StatefulWidget`, `State<T>`, `build`, directives, declares, inheritance, and calls.
- Dart parser changes for simple body call extraction, directive URI extraction, and generic base-name extraction.
- Relationship storage behavior for unresolved external inheritance anchors.
- README, user guide, and MCP schema examples.
- Trin UAT and Smith HCI approval.

## Decision

Cycle 2 is approved.

The implementation keeps the Sprint 25 architecture intact: Dart/Flutter support uses the normal parser registry, `ParseResult`, symbol table, existing relationship types, language filtering, output formats, and MCP schema. No Flutter-specific query flags or semantic analyzer behavior were introduced.

## Review Finding Closed

Final architecture review found one user-facing risk: unresolved Flutter SDK base classes were initially represented as ordinary `class` symbols. That made relationship queries work, but could pollute normal class searches with external SDK names.

The fix stores unresolved inheritance anchors as `external_class`, maps them for relationship target matching, and keeps ordinary `-tc` class searches scoped to indexed project classes. A focused regression was added to `tests/unit/test_sprint25_c2.py`.

## Verification

- `make test FILE=tests/unit/test_sprint25_c2.py` - 3 passed.
- `make test FILE=tests/unit/test_relationship_pipeline.py` - 10 passed.
- `make test FILE=tests/unit/test_database_match.py` - 40 passed.
- `make test` - 1324 passed, 1 skipped, 4 warnings.

## Notes

- `build/` is excluded only for roots with `pubspec.yaml`, preserving non-Flutter discovery behavior.
- Dart imports, exports, and parts remain directive strings, not resolved package dependencies.
- Flutter support remains structural: no widget tree, route graph, pub dependency, or Dart analyzer inference.
