# CLI Test Plan - Story 7
**Created**: 2026-01-11 12:11:30
**Persona**: @Trin (QA)
**Target**: CLI Implementation by @Neo
**Status**: DRAFT - Awaiting Oracle Review

---

## Test Scope

Testing the `via` CLI tool with focus on the `index` subcommand implementation.

**Components Under Test**:
- `via/__main__.py` - Main entry point and argument parsing
- `via index` command integration with IndexingService
- Progress reporting and error handling
- Exit codes and user-facing messages

---

## 1. Unit Tests for CLI Functions

### 1.1 Argument Parser Tests
**File**: `tests/unit/test_cli_parser.py`

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_create_parser_structure` | Verify parser has correct subcommands | Parser has 'index' subcommand |
| `test_version_flag` | Test `via --version` | Prints version string and exits |
| `test_verbosity_levels` | Test `-v`, `-vv`, `-vvv`, `-vvvv` | Correctly mapped to VERBOSITY constants |
| `test_index_default_args` | Test `via index` with no args | Directory defaults to `.` |
| `test_index_with_directory` | Test `via index /path/to/dir` | Directory set correctly |
| `test_force_flag` | Test `--force` flag | force=True in args |
| `test_watch_flag` | Test `-w`/`--watch` flag | watch=True in args |
| `test_exclude_patterns_single` | Test `--exclude "*.pyc"` | Pattern added to exclusion list |
| `test_exclude_patterns_multiple` | Test multiple `--exclude` flags | All patterns collected |
| `test_custom_db_path` | Test `--db /custom/path.db` | Custom db path set |
| `test_no_command` | Test `via` with no subcommand | Shows help and exits 0 |
| `test_unknown_command` | Test `via unknown` | Error message, exits with EXIT_ERROR |

### 1.2 Progress Callback Tests
**File**: `tests/unit/test_cli_progress.py`

| Test Case | Description | Expected Result |
|-----------|-------------|-----------------|
| `test_progress_callback_with_total` | Call with total > 0 | Prints percentage format |
| `test_progress_callback_no_total` | Call with total = 0 | Prints simple counter format |
| `test_progress_callback_output_format` | Verify output format | Contains message, current, total, % |

---

## 2. Integration Tests for CLI Commands

### 2.1 Index Command - Happy Path
**File**: `tests/integration/test_cli_index.py`

| Test Case | Description | Prerequisites | Expected Result |
|-----------|-------------|---------------|-----------------|
| `test_index_current_directory` | `via index` in test project | Test project with .py files | Success exit code, database created |
| `test_index_specific_directory` | `via index /tmp/test_proj` | Test project exists | Success exit code, correct db path |
| `test_index_with_force` | `via index --force` | Existing index | All files re-indexed |
| `test_index_with_custom_db` | `via index --db /tmp/test.db` | Test project | Database created at custom path |
| `test_index_with_verbosity` | `via index -vvv` | Test project | Verbose logging output visible |
| `test_index_output_format` | Verify summary output | Test project | Stats printed in correct format |
| `test_index_creates_via_directory` | Index creates .via/ dir | Test project without .via/ | .via/ directory created |

### 2.2 Index Command - Error Handling
**File**: `tests/integration/test_cli_index_errors.py`

| Test Case | Description | Input | Expected Result |
|-----------|-------------|-------|-----------------|
| `test_index_nonexistent_directory` | Index non-existent path | `/nonexistent/path` | Error message, EXIT_ERROR code |
| `test_index_file_not_directory` | Index a file path | `/path/to/file.txt` | Error message, EXIT_ERROR code |
| `test_index_watch_not_implemented` | Use `-w` flag | `via index -w` | Error message about not implemented |
| `test_index_keyboard_interrupt` | Simulate Ctrl+C during indexing | Mock KeyboardInterrupt | Graceful exit with EXIT_KEYBOARD_INTERRUPT |
| `test_index_database_error` | Database connection failure | Mock db error | Error message, EXIT_ERROR code |
| `test_index_parser_failure` | Parser raises exception | Project with bad syntax | Files marked as failed, overall success |

### 2.3 Database Connection Issue (FOUND BY NEO)
**File**: `tests/integration/test_cli_database.py`

| Test Case | Description | Root Cause | Expected Fix |
|-----------|-------------|------------|--------------|
| `test_database_store_connected` | Verify db is connected before use | Missing `.connect()` call | DatabaseStore should auto-connect or CLI should call `.connect()` |
| `test_database_initialized` | Verify schema initialized | Missing `.initialize_schema()` | Schema created before indexing |
| `test_database_cleanup` | Verify db closes properly | Resource leak | Connection closed on exit |

**BLOCKER**: Neo found that `DatabaseStore` requires manual `.connect()` and `.initialize_schema()` calls. The CLI must handle this.

**Suggested Fix**:
```python
# In _run_index_command():
with DatabaseStore(str(db_path), str(target_dir)) as db_store:
    db_store.initialize_schema()
    parser_registry = ParserRegistry()
    indexing_service = IndexingService(db_store, parser_registry)
    stats = indexing_service.index(...)
```

---

## 3. End-to-End Acceptance Tests

### 3.1 Real Project Indexing
**File**: `tests/e2e/test_real_indexing.py`

| Test Case | Description | Test Data | Acceptance Criteria |
|-----------|-------------|-----------|---------------------|
| `test_index_via_project_itself` | Index the VIA project | VIA codebase | All .py files indexed, entities extracted |
| `test_incremental_reindex` | Modify file, re-index | Touch a file | Only modified file re-indexed |
| `test_force_reindex` | Force full re-index | Existing index | All files re-indexed regardless of mtime |
| `test_large_project` | Index large codebase | Mock 1000+ files | Completes without crash, progress visible |
| `test_gitignore_respected` | Index with .gitignore | Project with .gitignore | Ignored files not indexed |

### 3.2 Edge Cases
**File**: `tests/e2e/test_edge_cases.py`

| Test Case | Description | Scenario | Expected Behavior |
|-----------|-------------|----------|-------------------|
| `test_empty_directory` | Index empty directory | No .py files | 0 files indexed, success |
| `test_no_python_files` | Index dir with no Python | Only .js, .txt files | 0 files indexed, success |
| `test_nested_gitignore` | Multiple .gitignore files | Nested .gitignore rules | All rules respected |
| `test_oversized_files` | Files > 10MB | Large .py file | File skipped, logged as oversized |
| `test_syntax_error_file` | File with syntax errors | Invalid Python | File marked as failed, continues |
| `test_unicode_filenames` | Unicode in file paths | 文件.py | Handled correctly |
| `test_symlinks` | Symbolic links | Symlinked .py files | Follow or skip (check spec) |
| `test_permission_denied` | No read permission | chmod 000 file | Graceful error, continue |

---

## 4. Test Implementation Checklist

### Phase 1: Unit Tests (Priority: HIGH)
- [ ] `test_cli_parser.py` - 12 test cases
- [ ] `test_cli_progress.py` - 3 test cases
- [ ] Fix DatabaseStore connection issue FIRST

### Phase 2: Integration Tests (Priority: HIGH)
- [ ] `test_cli_index.py` - 7 test cases (happy path)
- [ ] `test_cli_index_errors.py` - 6 test cases (error handling)
- [ ] `test_cli_database.py` - 3 test cases (db connection fix)

### Phase 3: E2E Tests (Priority: MEDIUM)
- [ ] `test_real_indexing.py` - 5 acceptance tests
- [ ] `test_edge_cases.py` - 8 edge case tests

**Total Test Cases**: 44 tests

---

## 5. Test Fixtures Required

### 5.1 Common Fixtures
```python
@pytest.fixture
def temp_test_project(tmp_path):
    """Create a temporary test project with sample Python files."""
    # Create structure with .py files, .gitignore, etc.
    pass

@pytest.fixture
def cli_runner():
    """Provide a CLI test runner using Click's CliRunner or subprocess."""
    pass

@pytest.fixture
def mock_progress_callback():
    """Mock progress callback to verify it's called correctly."""
    pass
```

### 5.2 Test Data
- Sample Python files with various entities (funcs, classes, imports, globals)
- .gitignore files with various exclusion patterns
- Files with syntax errors
- Oversized files (> 10MB)
- Unicode filenames

---

## 6. Coverage Goals

| Module | Target Coverage | Current | Priority |
|--------|----------------|---------|----------|
| `via/__main__.py` | 90%+ | 0% | HIGH |
| `via.services.indexing` | 95%+ | 92% | MEDIUM |
| `via.db.store` | 95%+ | 88% | MEDIUM |

---

## 7. Blockers & Risks

### BLOCKER 1: DatabaseStore Connection
**Severity**: HIGH
**Description**: CLI doesn't call `.connect()` and `.initialize_schema()` on DatabaseStore
**Impact**: `via index` command crashes with "Database not connected"
**Owner**: @Neo
**Fix Required**: Use context manager or add manual connect/init calls

### RISK 1: --exclude Flag Not Implemented
**Severity**: MEDIUM
**Description**: `--exclude` patterns not passed to FileDiscovery
**Impact**: Users can't exclude custom patterns
**Mitigation**: Show warning message (already done), implement in Phase 2

### RISK 2: Watch Mode Not Implemented
**Severity**: LOW
**Description**: `-w` flag errors out
**Impact**: Feature not available yet
**Mitigation**: Clear error message (already done), defer to Phase 2

---

## 8. Acceptance Criteria (Oracle Review Needed)

### Story 7 is DONE when:
1. ✅ `via --version` prints version
2. ✅ `via --help` shows usage
3. ✅ `via index --help` shows index command help
4. ❌ `via index` successfully indexes current directory
5. ❌ `via index <dir>` indexes specified directory
6. ✅ `--force` flag is parsed and passed to IndexingService
7. ✅ `-v/-vv/-vvv/-vvvv` flags control verbosity
8. ❌ Progress is shown during indexing
9. ❌ Summary stats are printed on completion
10. ❌ Error messages are user-friendly
11. ❌ Exit codes are correct (0, 1, 130)
12. ❌ All 44 test cases pass
13. ❌ Coverage > 90% for __main__.py

**Current Status**: 3/13 criteria met (23%)

**BLOCKER**: Must fix DatabaseStore connection issue before further testing

---

## 9. Next Steps for @Neo

1. **IMMEDIATE**: Fix DatabaseStore connection issue
   - Use context manager pattern: `with DatabaseStore(...) as db_store:`
   - Call `db_store.initialize_schema()` after connection
   - Ensure proper cleanup on exit

2. **TEST**: Run basic smoke test
   ```bash
   via index /tmp/via_test
   ```

3. **REQUEST REVIEW**: @Trin *qa test cli - Run full CLI test suite

---

## 10. Test Execution Commands

```bash
# Run unit tests
pytest tests/unit/test_cli_*.py -v

# Run integration tests
pytest tests/integration/test_cli_*.py -v

# Run E2E tests
pytest tests/e2e/test_*.py -v

# Run all CLI tests
pytest tests/ -k cli -v

# Coverage report
pytest tests/ -k cli --cov=via.__main__ --cov-report=term-missing
```

---

**Test Plan Created By**: @Trin (QA Guardian)
**Status**: DRAFT - Awaiting @Neo to fix blocker
**Next Review**: After DatabaseStore fix implemented
