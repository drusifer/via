# Morpheus Next Steps

## Resume Point: Sprint 25 Cycle 2 approved

### On Resume
1. Read bottom 20 lines of `agents/CHAT.md`.
2. If continuing sprint ceremony, Mouse should prepare closeout.
3. If changes are requested, preserve the structural-only Dart/Flutter boundary and rerun focused tests plus full suite.

### Key Decisions
- Dart support remains a normal parser-registry addition, not a Flutter-specific query path.
- External unresolved inheritance anchors use `external_class` to support relationship filtering without appearing in normal project class searches.
- Dart directive relationships are directive strings, not resolved dependency graph data.
- Flutter support remains structural: no widget tree, route graph, pub dependency, or Dart analyzer inference.
- Full suite result at approval: 1324 passed, 1 skipped, 4 warnings.
