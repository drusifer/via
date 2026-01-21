# Sprint 3 Test Plan - Internal Pipeline & Render System

**Created**: 2026-01-21
**QA Engineer**: @Trin
**Feature**: Internal pipeline architecture with polymorphic rendering
**Sprint Status**: MVP Complete (386 tests, 81% coverage)

---

## Executive Summary

Sprint 3 implements the internal pipeline architecture with polymorphic MatchRecord system and multiple renderers. This test plan covers both **existing tests validation** and **gap analysis** for additional test coverage.

**Current State**:
- 386 tests passing
- 81% coverage
- 19 ruff lint issues identified
- 3+ bandit security warnings

**Goal**: 95%+ coverage, zero critical bugs, all edge cases handled

---

## Test Strategy

**Approach**: Bottom-up testing with focus on streaming and polymorphism

**Test Pyramid**:
1. **Unit Tests** (70%): Test individual components in isolation
2. **Integration Tests** (25%): Test pipeline → renderer → output flow
3. **End-to-End Tests** (5%): Test complete user workflows

**Test Categories**:
- Functional correctness
- Streaming behavior (O(1) memory)
- Error handling
- Edge cases
- Performance
- Security
- Code quality (static analysis)

---

## Test Suite 1: Pipeline Parser (Phase 1)

**File**: `tests/unit/test_pipeline_parser.py`
**Status**: ✅ Implemented (26+ tests)

### Test 1.1: Stage Splitting
```python
def test_split_on_via_single_stage():
    """Test splitting argv with no --via flags."""
    parser = PipelineParser()
    result = parser._split_on_via(['-g', '*', '-c'])
    assert len(result) == 1

def test_split_on_via_multiple_stages():
    """Test splitting argv on --via flags."""
    parser = PipelineParser()
    result = parser._split_on_via(['-g', '*', '-c', '--via', '-rT'])
    assert len(result) == 2

def test_split_on_via_empty():
    """Test empty argv."""
    parser = PipelineParser()
    result = parser._split_on_via([])
    assert len(result) == 0
```

### Test 1.2: Match Stage Parsing
```python
def test_parse_match_stage_glob():
    """Test parsing match stage with glob pattern."""
def test_parse_match_stage_regex():
    """Test parsing match stage with regex pattern."""
def test_parse_match_stage_sql():
    """Test parsing match stage with SQL pattern."""
def test_parse_match_stage_type_flags():
    """Test all symbol type shorthand flags (-c, -m, -f, etc.)."""
```

### Test 1.3: Render Stage Parsing
```python
def test_parse_render_stage_list():
    """Test parsing render stage for list output."""
def test_parse_render_stage_table():
    """Test parsing render stage for table output."""
def test_parse_render_stage_raw():
    """Test parsing render stage for raw output."""
def test_parse_render_stage_formatted():
    """Test parsing render stage for formatted output."""
```

### Test 1.4: Error Handling
```python
def test_invalid_flags_raises_error():
    """Test that invalid flags raise PipelineParseError."""
def test_mutually_exclusive_syntax_flags():
    """Test that -g and -r can't be used together."""
```

**Gap Analysis**: ✅ Complete

---

## Test Suite 2: Pipeline Executor (Phase 1)

**File**: `tests/unit/test_pipeline_executor.py`
**Status**: ✅ Implemented

### Test 2.1: Match Stage Execution
```python
def test_execute_single_match_stage():
    """Test executing a single match stage against database."""
def test_execute_match_stage_returns_iterator():
    """Test that match stage returns iterator (not list)."""
def test_execute_match_with_limit():
    """Test limit parameter is passed correctly."""
```

### Test 2.2: Filter Stage (Chained Matches)
```python
def test_execute_filter_stage():
    """Test filtering previous results with second match stage."""
def test_filter_by_type():
    """Test filtering by symbol type."""
def test_filter_by_pattern():
    """Test filtering by pattern matching."""
```

### Test 2.3: Render Stage Execution
```python
def test_execute_render_stage_consumes_iterator():
    """Test that render stage fully consumes iterator."""
def test_execute_render_stage_prints_output():
    """Test that render stage prints to stdout."""
def test_render_is_terminal_stage():
    """Test that render returns None (terminal)."""
```

### ⚠️ GAP: Type Hint Mismatch
```python
# MISSING: Test that executor uses MatchRecord (not MatchResult)
def test_executor_uses_matchrecord_types():
    """Verify executor methods use MatchRecord type, not MatchResult."""
    # Check parameter types in _execute_filter_stage
    # Check return types in _execute_match_stage
```

**Gap Analysis**: 1 critical gap (type hints)

---

## Test Suite 3: MatchRecord System (Phase 2)

**File**: `tests/unit/test_match_record.py`
**Status**: ✅ Implemented (48 tests)

### Test 3.1: Base MatchRecord
```python
def test_matchrecord_is_abstract():
    """Test that MatchRecord cannot be instantiated."""
def test_matchrecord_str_format():
    """Test __str__() produces correct format."""
def test_matchrecord_with_byte_position():
    """Test format includes @offset+length."""
def test_matchrecord_without_byte_position():
    """Test format without byte position (files)."""
```

### Test 3.2: Derived Record Types
```python
def test_class_match_record_supports_diagram():
    """Test ClassMatchRecord supports RenderType.DIAGRAM."""
def test_method_match_record_no_diagram():
    """Test MethodMatchRecord doesn't support DIAGRAM."""
def test_function_match_record_supports_raw():
    """Test FunctionMatchRecord supports RAW."""
def test_file_match_record_no_formatted():
    """Test FileMatchRecord doesn't support FORMATTED."""
def test_import_match_record_supports_usage():
    """Test ImportMatchRecord supports USAGE."""
def test_global_match_record_supports_formatted():
    """Test GlobalMatchRecord supports FORMATTED."""
```

### Test 3.3: MatchRecordFactory
```python
def test_factory_creates_correct_type():
    """Test factory creates right MatchRecord subclass."""
def test_factory_with_metadata():
    """Test factory attaches metadata to records."""
def test_factory_unknown_type_raises():
    """Test factory raises ValueError for unknown types."""
```

**Gap Analysis**: ✅ Complete

---

## Test Suite 4: Streaming & Metadata (Phase 3)

**File**: `tests/unit/test_database_streaming.py`
**Status**: ✅ Implemented (17 tests)

### Test 4.1: Metadata Computation
```python
def test_metadata_computed_before_streaming():
    """Test metadata query runs before result streaming."""
def test_metadata_contains_total_matches():
    """Test metadata includes total_matches count."""
def test_metadata_contains_column_widths():
    """Test metadata includes max column widths."""
def test_column_widths_reflect_all_matches():
    """Test widths are from ALL matches, not just limited."""
```

### Test 4.2: Limit Behavior
```python
def test_default_limit_is_10():
    """Test default limit returns 10 results."""
def test_custom_limit():
    """Test custom limit (e.g., -n 20)."""
def test_limit_zero_is_unlimited():
    """Test -n 0 returns all results."""
```

### ⚠️ GAP: Streaming Memory Test
```python
# MISSING: Verify O(1) memory usage
def test_streaming_memory_constant():
    """Test that streaming uses O(1) memory for large result sets."""
    # Generate 10000 records
    # Stream through renderer
    # Verify memory doesn't grow linearly
```

**Gap Analysis**: 1 medium gap (memory verification)

---

## Test Suite 5: List & Table Renderers (Phase 4)

**File**: `tests/unit/test_renderers.py`
**Status**: ✅ Implemented (24 tests)

### Test 5.1: ListRenderer
```python
def test_list_renderer_basic_output():
    """Test ListRenderer produces one line per record."""
def test_list_renderer_uses_str():
    """Test ListRenderer uses MatchRecord.__str__()."""
def test_list_renderer_more_indicator():
    """Test '... (N more)' indicator when limited."""
def test_list_renderer_streams():
    """Test ListRenderer processes records lazily."""
```

### Test 5.2: TableRenderer
```python
def test_table_renderer_uses_metadata_widths():
    """Test TableRenderer uses pre-computed column widths."""
def test_table_renderer_streams():
    """Test TableRenderer doesn't materialize records."""
def test_table_renderer_ascii_format():
    """Test ASCII table format output."""
def test_table_renderer_markdown_format():
    """Test Markdown table format output."""
def test_table_renderer_html_format():
    """Test HTML table format output."""
```

### Test 5.3: RendererFactory
```python
def test_factory_creates_list_renderer():
    """Test factory creates ListRenderer for RenderType.LIST."""
def test_factory_creates_table_renderer():
    """Test factory creates TableRenderer for RenderType.TABLE."""
def test_factory_invalid_type_raises():
    """Test factory raises for unsupported types."""
```

**Gap Analysis**: ✅ Complete

---

## Test Suite 6: Raw Renderer (Phase 5)

**File**: `tests/unit/test_raw_renderer.py`
**Status**: ✅ Implemented (16 tests)

### Test 6.1: Source Extraction
```python
def test_raw_renderer_extracts_source():
    """Test source code extraction using byte offsets."""
def test_raw_renderer_file_record():
    """Test FileMatchRecord reads entire file."""
def test_raw_renderer_missing_file():
    """Test graceful handling of missing files."""
```

### Test 6.2: Context Lines
```python
def test_raw_renderer_context_before():
    """Test -B flag includes lines before match."""
def test_raw_renderer_context_after():
    """Test -A flag includes lines after match."""
def test_raw_renderer_context_both():
    """Test -C flag includes lines before and after."""
def test_context_at_file_start():
    """Test context lines at beginning of file."""
def test_context_at_file_end():
    """Test context lines at end of file."""
```

### ⚠️ GAP: Edge Cases
```python
# MISSING: Binary file handling
def test_raw_renderer_binary_file():
    """Test handling of binary (non-UTF8) files."""
    # Should use errors='replace' or skip gracefully

# MISSING: Empty file
def test_raw_renderer_empty_file():
    """Test extraction from empty file."""

# MISSING: Very long lines
def test_raw_renderer_long_lines():
    """Test extraction with lines >10KB."""
```

**Gap Analysis**: 3 medium gaps (edge cases)

---

## Test Suite 7: Formatted Renderer (Phase 6)

**File**: `tests/unit/test_formatted_renderer.py`
**Status**: ✅ Implemented (31 tests)

### Test 7.1: Syntax Highlighting
```python
def test_formatted_renderer_uses_pygments():
    """Test output includes ANSI color codes."""
def test_formatted_renderer_python_highlighting():
    """Test Python syntax is highlighted correctly."""
def test_formatted_renderer_language_detection():
    """Test correct language detected from file extension."""
```

### Test 7.2: Header Formatting
```python
def test_formatted_renderer_header():
    """Test header includes qualified name and location."""
def test_header_format():
    """Test header format: # {qualified_name} ({file}:{line})."""
```

### Test 7.3: Type Filtering
```python
def test_formatted_skips_file_records():
    """Test FileMatchRecord is skipped (not supported)."""
def test_formatted_skips_import_records():
    """Test ImportMatchRecord is skipped (not supported)."""
def test_formatted_accepts_code_symbols():
    """Test class/method/function/global are accepted."""
```

### Test 7.4: Theme Support
```python
def test_theme_auto_detection():
    """Test terminal theme auto-detection."""
def test_theme_explicit_override():
    """Test --theme flag overrides auto-detection."""
def test_theme_dark_terminal():
    """Test dark theme for dark terminals."""
def test_theme_light_terminal():
    """Test light theme for light terminals."""
```

### ⚠️ GAP: Use supported_render_types
```python
# MISSING: Should use MatchRecord.supported_render_types
def test_formatted_uses_supported_render_types():
    """Test that FormattedRenderer uses record.supported_render_types."""
    # Instead of hardcoded SUPPORTED_TYPES set
```

**Gap Analysis**: 1 high gap (validation method)

---

## Test Suite 8: Integration Tests

**File**: `tests/integration/test_cli_pipeline.py`
**Status**: ✅ Implemented (12 tests)

### Test 8.1: Full Pipeline Flows
```python
def test_match_and_list():
    """Test: via -g '*' -c --via -rL"""
def test_match_and_table():
    """Test: via -g '*' -c --via -rT"""
def test_match_and_raw():
    """Test: via -g '*' -f --via -rR"""
def test_match_and_formatted():
    """Test: via -g '*' -f --via -rF"""
def test_chained_matches():
    """Test: via -g '*Test*' -c --via -g '*' -m"""
```

### Test 8.2: Context Lines Integration
```python
def test_context_lines_raw():
    """Test -C flag with raw renderer."""
def test_context_lines_formatted():
    """Test -C flag with formatted renderer."""
```

### Test 8.3: Limit Integration
```python
def test_limit_with_render():
    """Test -n flag works with renderers."""
def test_unlimited_results():
    """Test -n 0 for unlimited results."""
```

### ⚠️ GAP: End-to-End Tests
```python
# MISSING: Real file system tests
def test_e2e_index_and_match_and_render(tmp_path):
    """Test complete flow: index → match → render."""
    # Create test Python files
    # Run via index
    # Run via -g '*' -c --via -rF
    # Verify output contains syntax highlighting
```

**Gap Analysis**: 1 medium gap (E2E tests)

---

## Test Suite 9: Code Quality (Static Analysis)

**Run**: `make lint-fast` (Ruff)
**Status**: ⚠️ 19 issues found

### 9.1: Complexity Violations (C901)
| File | Function | Complexity | Max |
|------|----------|------------|-----|
| `__main__.py:307` | `_run_match_command` | 11 | 10 |
| `python_parser.py:75` | `_extract_entities` | 15 | 10 |
| `indexing.py:262` | `_store_parsed_file` | 12 | 10 |
| `factory.py:40` | `create` | 13 | 10 |

**Action**: Refactor to reduce complexity below 10

### 9.2: Unused Imports (F401)
| File | Import |
|------|--------|
| `__main__.py:18` | `os` |
| `__main__.py:21` | `Optional` |
| `store.py:20` | `Path` |
| `store.py:28` | `MatchResult` |
| `types.py:5` | `Any` |
| `table_formatters.py:17` | `List` |
| `indexing.py:18` | `os` |
| `indexing.py:21` | `List` |

**Action**: Remove unused imports

### 9.3: Unused Variables (F841)
| File | Variable |
|------|----------|
| `parser.py:122` | `e` (exception) |
| `parser.py:147` | `e` (exception) |
| `parser.py:169` | `e` (exception) |
| `code_formatters.py:268` | `width` |

**Action**: Remove or use underscore prefix (`_e`)

### 9.4: Commented-Out Code (ERA)
| File | Line |
|------|------|
| `types.py:46` | Legacy code |

**Action**: Remove commented-out code

---

## Test Suite 10: Security Analysis

**Run**: `make security` (Bandit)
**Status**: ⚠️ 3+ warnings

### 10.1: SQL Injection Warnings (B608)
| File | Line | Issue |
|------|------|-------|
| `store.py:235` | `f"UPDATE files SET {updates}"` | Dynamic SQL |
| `store.py:774` | `f"WHERE {where_clause}"` | Dynamic SQL |

**Risk Assessment**: LOW - Internal use only, parameterized values
**Action**: Document as acceptable risk OR use query builder

### 10.2: Hardcoded SQL Expressions
```python
# Current (flagged by Bandit):
query = f"SELECT ... WHERE {where_clause}"

# Alternative (safer):
query = "SELECT ... WHERE " + where_clause  # Still flagged
# OR
query_builder.where(where_clause)  # Requires new dependency
```

**Recommendation**: Add `# nosec B608` comment with justification

---

## Test Suite 11: Duplicate Code Analysis

**Run**: `make duplicates` (Pylint)
**Status**: ⚠️ ~140 lines duplicated

### 11.1: Source Extraction Duplication
| File A | File B | Lines | Functions |
|--------|--------|-------|-----------|
| `raw.py:68-165` | `formatted.py:106-179` | ~70 each | `_extract_source`, `_find_context_start`, `_find_context_end` |

**Action**: Extract to `via/renderers/utils/source_extraction.py`

```python
# Proposed shared utility
def extract_source(
    file_path: str,
    byte_offset: Optional[int],
    byte_length: Optional[int],
    before_context: int = 0,
    after_context: int = 0,
    read_full_file: bool = False
) -> str:
    """Shared source extraction logic."""
    ...
```

---

## Test Matrix: Render Type × Symbol Type

| Symbol Type | LIST | TABLE | RAW | FORMATTED | DIAGRAM | USAGE |
|-------------|------|-------|-----|-----------|---------|-------|
| class | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| method | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| function | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| file | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| import | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| global | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

**Legend**: ✅ Supported | ❌ Not Supported

**Tests Required**: 42 combinations (7 types × 6 renders)

---

## Edge Cases Checklist

### File System Edge Cases
- [ ] Empty files
- [ ] Binary files (non-UTF8)
- [ ] Files with only whitespace
- [ ] Very long lines (>10KB)
- [ ] Missing files (deleted after index)
- [ ] Files with Unicode characters
- [ ] Files with Windows line endings (CRLF)

### Pattern Edge Cases
- [ ] Empty pattern
- [ ] Pattern with special regex chars
- [ ] Pattern with SQL injection attempt
- [ ] Unicode in patterns
- [ ] Extremely long patterns

### Rendering Edge Cases
- [ ] Zero results
- [ ] Exactly limit results (no "more" indicator)
- [ ] Results at file start (no before context)
- [ ] Results at file end (no after context)
- [ ] Very large output (>1MB)

### Metadata Edge Cases
- [ ] Symbol name longer than any existing
- [ ] All symbols same length
- [ ] Null parent_name handling

---

## Performance Tests

**File**: `tests/performance/test_sprint3_performance.py`

### P.1: Metadata Query Performance
```python
def test_metadata_query_performance():
    """Metadata query completes in < 20ms with 10k symbols."""
    # Create database with 10,000 symbols
    # Time metadata query
    # Assert time < 20ms
```

### P.2: Streaming Performance
```python
def test_streaming_throughput():
    """Renderer processes 1000 records/second minimum."""
    # Generate 1000 records
    # Time render() call
    # Assert throughput >= 1000/s
```

### P.3: Memory Efficiency
```python
def test_memory_constant_with_large_results():
    """Memory usage stays constant regardless of result count."""
    # Measure baseline memory
    # Render 100 records
    # Measure memory
    # Render 10000 records
    # Measure memory
    # Assert memory increase < 10%
```

---

## Test Summary

| Test Suite | Tests | Type | Status |
|------------|-------|------|--------|
| 1. Pipeline Parser | 26 | Unit | ✅ Complete |
| 2. Pipeline Executor | 15 | Unit | ⚠️ 1 gap |
| 3. MatchRecord System | 48 | Unit | ✅ Complete |
| 4. Streaming & Metadata | 17 | Unit | ⚠️ 1 gap |
| 5. List & Table Renderers | 24 | Unit | ✅ Complete |
| 6. Raw Renderer | 16 | Unit | ⚠️ 3 gaps |
| 7. Formatted Renderer | 31 | Unit | ⚠️ 1 gap |
| 8. Integration (Pipeline) | 12 | Integration | ⚠️ 1 gap |
| 9. Code Quality (Ruff) | - | Static | ⚠️ 19 issues |
| 10. Security (Bandit) | - | Static | ⚠️ 3 issues |
| 11. Duplicate Code | - | Static | ⚠️ 140 lines |
| **Current Total** | **386** | | |
| **Proposed Additions** | ~25 | | |
| **Target Total** | ~411 | | |

---

## Action Items

### Critical (Must Fix)
1. [ ] Fix MatchResult → MatchRecord type mismatch in executor.py
2. [ ] Extract duplicated source extraction code (140 lines)

### High Priority
3. [ ] Add logging for file read errors (silent failures)
4. [ ] Use MatchRecord.supported_render_types for validation
5. [ ] Remove 13 unused imports (F401)

### Medium Priority
6. [ ] Refactor 4 complex functions (C901 > 10)
7. [ ] Add edge case tests (empty files, binary files, etc.)
8. [ ] Add E2E integration test
9. [ ] Add memory efficiency test

### Low Priority
10. [ ] Remove commented-out code (ERA)
11. [ ] Fix unused variables with underscore prefix
12. [ ] Add inline security comments for Bandit warnings

---

## Acceptance Criteria

Sprint 3 testing is complete when:
- ✅ All 386+ tests pass
- ✅ Code coverage ≥ 90% for new code
- ✅ Zero ruff errors (after fixes)
- ✅ Zero critical security issues
- ✅ Zero duplicate code blocks > 6 lines
- ✅ All edge cases handled gracefully
- ✅ Performance benchmarks met
- ✅ Type hints consistent (MatchRecord, not MatchResult)

---

## Test Execution Commands

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=via --cov-report=html

# Run specific suite
pytest tests/unit/test_renderers.py -v

# Run static analysis (fast)
make lint-fast

# Run full analysis (slow)
make lint-slow

# Run security scan
make security

# Run duplicate detection
make duplicates
```

---

**Created by**: @Trin (QA Engineer)
**Status**: ✅ QA Plan Complete
**Next Steps**:
1. Address critical gaps
2. Run `make lint-slow` and fix all issues
3. Add missing edge case tests
4. Verify 95%+ coverage
