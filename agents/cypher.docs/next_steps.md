# Cypher Next Steps

## Current Status

Sprint 24 is complete. The user requested Flutter / Dart support, and Cypher drafted Sprint 25 stories.

## On Resume

1. Read bottom 20 lines of `agents/CHAT.md`.
2. Review `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`.
3. Smith should review the story set for Flutter developer value and discoverability.
4. If Smith rejects, revise the scope around the specific UX issue.
5. If Smith approves, hand to Morpheus to select parser engine and architecture.
6. Preserve scope boundary: structural Dart/Flutter indexing, not full semantic Flutter analysis.

## Deferred Backlog

- `_js_body` unit tests (low, if divergence happens)
- Executor strategy / full CLI parser replacement (large, needs explicit planning)
- Keep builder adoption and executor refactors separate unless a sprint explicitly joins them
- Performance polish for very large chained relationship post-filters only if real usage justifies it
