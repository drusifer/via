# Current Sprint Task Board

## Sprint 25 - Dart / Flutter Support

**Status**: Complete  
**Architecture**: `agents/morpheus.docs/SPRINT_25_ARCHITECTURE.md`  
**Task Plan**: `agents/mouse.docs/SPRINT_25_TASKS.md`  
**Closeout**: `agents/mouse.docs/SPRINT_25_CLOSEOUT.md`

### Cycle 0 - Parser Dependency Spike

- [x] Neo: prove Python-loadable Dart tree-sitter grammar path
- [x] Neo: parse minimal Dart/Flutter fixture in spike test
- [x] Trin: verify dependency spike result
- [x] Morpheus: approve dependency path or stop/rescope

### Cycle 1 - Discovery, Excludes, Parser Foundation

- [x] Neo: implement `DartParser(ParserABC)` with `.dart` support
- [x] Neo: register Dart parser in CLI/MCP parser assembly
- [x] Neo: add Flutter/Dart default excludes
- [x] Neo: extract Dart core symbols and support `--lang dart`
- [x] Trin: verify parser/discovery/language-filter tests
- [x] Morpheus: review Cycle 1 architecture alignment

### Cycle 2 - Flutter Value, Relationships, Docs

- [x] Neo: add Flutter fixture coverage
- [x] Neo: implement Dart declares/imports/inherits-from/calls relationships
- [x] Neo: update docs and MCP schema examples
- [x] Trin: verify relationships, docs/schema, and mixed-language regression
- [x] Smith: review UX/support-boundary wording
- [x] Morpheus: final architecture review

### Verification

- [x] Cycle 0 dependency gate passed before parser work.
- [x] Cycle 1 parser foundation passed focused and adjacent regression tests.
- [x] Cycle 2 implementation passed focused Dart/Flutter relationship and docs tests.
- [x] Existing Python, JS/TS, Markdown behavior remains green.
- [x] Full suite: 1324 passed, 1 skipped, 4 warnings.
