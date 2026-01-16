**Task**: Sprint 3 Phase 1 - Core Pipeline Implementation
**Status**: In Progress (75%)
**Started**: 2026-01-16

**Completed Tasks**:
- ✅ Task 1.1: Pipeline Parser with argparse (26/26 tests, 95% coverage)
- ✅ Task 1.2: Pipeline Executor (7/7 tests, 80% coverage)

**Current Task**: Task 1.3 - Wire Pipeline into CLI Entry Point

**Progress**:
- Parser handles shorthand flags: -mg (match glob), -mr (match regex), -rT (render table), etc.
- Parser splits argv on --via flags for pipeline stages
- Executor handles match, filter, render stages
- Iterator-based streaming between stages (zero-copy)

**Files Created**:
- via/pipeline/__init__.py
- via/pipeline/types.py (StageType, PipelineStage)
- via/pipeline/parser.py (PipelineParser, PipelineParseError)
- via/pipeline/executor.py (PipelineExecutor)
- tests/unit/test_pipeline_parser.py (26 tests)
- tests/unit/test_pipeline_executor.py (7 tests)

**Next Steps**:
1. Wire pipeline into via/__main__.py
2. Add backward compatibility for Sprint 2 syntax
3. Write integration tests for full pipeline
4. Test with real database
