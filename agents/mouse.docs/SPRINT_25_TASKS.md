# Sprint 25 Tasks - Dart / Flutter Support

**Scrum Master**: Mouse  
**Date**: 2026-05-06  
**Status**: Planned  
**Architecture**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`  
**Stories**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`  
**Gate 1**: `agents/smith.docs/SPRINT_25_GATE1_REVIEW.md`  
**Gate 2**: `agents/smith.docs/SPRINT_25_GATE2_REVIEW.md`

## Sprint Goal

Make Dart/Flutter projects searchable through normal VIA structural indexing and query workflows, without promising Flutter semantic analysis.

## Cycle Plan

### Cycle 0 - Parser Dependency Spike (1pt)

**Owner flow**: Neo -> Trin -> Morpheus  
**Purpose**: Prove the Dart grammar can be loaded from Python before full parser work starts.

- [ ] Neo: identify viable Python-loadable Dart tree-sitter grammar path.
- [ ] Neo: add minimal spike fixture or test that parses a Dart/Flutter snippet.
- [ ] Neo: document dependency/build decision for Morpheus.
- [ ] Trin: verify the spike result and failure behavior.
- [ ] Morpheus: approve dependency path or stop/rescope Sprint 25.

**Hard gate**: If Cycle 0 fails, do not start Cycle 1.

### Cycle 1 - Discovery, Excludes, Parser Foundation (7pt)

**Owner flow**: Neo -> Trin -> Morpheus

- [ ] Neo: add `DartParser(ParserABC)` with `.dart` support and lazy parser setup.
- [ ] Neo: register `DartParser` in CLI/MCP parser assembly points.
- [ ] Neo: add Flutter/Dart default excludes to `PathFilter`.
- [ ] Neo: extract classes, mixins, enums, extensions, constructors, methods, top-level functions, globals, imports, exports, and parts.
- [ ] Neo: support `--lang dart` for file and symbol queries through existing language fields.
- [ ] Trin: run focused parser/discovery/language-filter tests.
- [ ] Morpheus: review parser integration and dependency boundaries.

### Cycle 2 - Flutter Value, Relationships, Docs (5pt)

**Owner flow**: Neo -> Trin -> Smith -> Morpheus

- [ ] Neo: add Flutter-style fixture coverage for `StatelessWidget`, `StatefulWidget`, `State<T>`, and `build`.
- [ ] Neo: store/query Dart `declares`, `imports`, `inherits-from`, and best-effort `calls` relationships.
- [ ] Neo: update docs and MCP schema examples for Dart/Flutter workflows.
- [ ] Trin: run relationship, docs/schema, and mixed-language regression verification.
- [ ] Smith: run HCI review of docs/examples and support-boundary wording.
- [ ] Morpheus: final architecture review.

## Acceptance Gates

- [ ] Cycle 0 proves dependency path before parser foundation.
- [ ] `via -mg "*" -tF --lang dart` returns Dart files.
- [ ] `via -mg "*Screen" -tc --lang dart` returns Dart classes.
- [ ] `via -mg "build" -tm --lang dart -oR` returns Flutter-style build methods.
- [ ] Dart directives are documented as directive strings, not resolved dependencies.
- [ ] Docs explicitly state no widget tree, route graph, pub dependency resolution, or semantic analyzer behavior.
- [ ] Existing Python, JS/TS, Markdown tests remain green.

## Blockers

None at sprint start. Primary risk is Cycle 0 dependency viability.

## First Handoff

@Morpheus: Review this sprint plan against architecture. If approved, hand Cycle 0 to Neo.
