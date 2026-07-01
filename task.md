# Current Sprint Task Board

## Sprint 26 - CLI/Executor Refactoring & Query Performance (Tech Debt)

**Status**: In Progress  
**Stories**: `agents/cypher.docs/SPRINT_26_USER_STORIES.md`  
**Architecture**: `agents/morpheus.docs/SPRINT_26_ARCHITECTURE.md`  
**Task Plan**: `agents/mouse.docs/SPRINT_26_TASKS.md`  

### Cycle 1 - Baseline Stabilization & Unit Testing

- [x] Neo: resolve `test_invalid_container_type_raises_error` baseline test failure
- [x] Neo: resolve `test_query_filepath_imports_filepath` baseline test failure
- [x] Neo: resolve `test_sans_declares_returns_empty_markdown` baseline test failure
- [x] Neo: create dedicated unit tests for `FunctionBodyAnalyzer` in `tests/unit/test_js_body_analyzer.py`
- [x] Trin: verify baseline and new unit tests are green
- [x] Morpheus: review Cycle 1 implementation quality

### Cycle 2 - Unified Parser and Executor

- [x] Neo: refactor argparse and CLI routing in `via/__main__.py` to use command handler registry
- [x] Neo: refactor stage execution in `via/pipeline/executor.py` to use pipeline stage handler registry
- [x] Neo: unify CLI and programmatic `ViaRunner` execution paths
- [ ] Trin: verify CLI routing and runner regressions
- [ ] Smith: review UX/CLI flag consistency
- [ ] Morpheus: review Cycle 2 architecture alignment

### Cycle 3 - Performance Optimization

- [x] Neo: implement nested CTE SQLite compiling for chained relationship pipeline stages in `DatabaseStore`
- [x] Neo: optimize Python-side relationship query batching for non-CTE stages
- [ ] Trin: verify relationship queries and performance benchmarks
- [ ] Morpheus: final architecture review

### Verification

- [x] Cycle 1 baseline stabilization and body analyzer tests pass.
- [x] Cycle 2 unified parser and executor routing passes.
- [ ] Cycle 3 chained query performance optimization passes.
- [x] Full suite baseline is completely green (1339+ passed tests).
