# Sprint 25 Cycle 2 HCI Review - Dart/Flutter Docs

**Reviewer**: Smith  
**Date**: 2026-05-06  
**Status**: APPROVED

## Review Scope

- README Dart/Flutter positioning.
- User guide Dart/Flutter examples and support boundary.
- MCP schema Dart/Flutter examples and support boundary.
- Trin UAT result for Cycle 2.

## Verdict

APPROVED.

The docs and MCP schema satisfy the Sprint 25 user-facing constraints:

- `--lang dart` is the visible language filter.
- Dart/Flutter examples use normal VIA surfaces: `-tF`, `-tc`, `-tm`, `--via inherits-from`, and `-oR`.
- Dart imports, exports, and parts are described as directive strings, not resolved package dependencies.
- Flutter support is framed as structural indexing and querying, not semantic Flutter analysis.
- The docs explicitly say VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.

## HCI Notes

- **Consistency and Standards**: Approved. No Flutter-only flags were added.
- **Match Between System and Real World**: Approved. Examples use user-recognizable Flutter terms: `StatefulWidget`, `build`, and `*Screen`.
- **Recognition Rather Than Recall**: Approved. MCP schema now includes concrete Dart/Flutter examples for agents.
- **Help and Documentation**: Approved. Boundary wording prevents users from mistaking VIA for a Flutter analyzer.

## Residual Risk

Relationship query syntax remains cognitively heavy, but Sprint 25 improves recognition by adding concrete examples. A future sprint could add a canned Flutter-oriented shortcut only if it expands transparently to ordinary VIA query args.
