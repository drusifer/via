# Sprint 2 Test Plan - Match Command

**Created**: 2026-01-13
**QA Engineer**: @Trin
**Feature**: `via match` command with denormalized symbols table
**Architecture**: v5.0 (Denormalized)

---

## Test Strategy

**Approach**: Bottom-up testing from unit tests to integration tests

**Test Pyramid**:
1. **Unit Tests** (70%): Test individual components in isolation
2. **Integration Tests** (25%): Test CLI → Database → Output flow
3. **End-to-End Tests** (5%): Test complete user workflows

**Coverage Goal**: 95%+ for new code

---

## Test Suite 1: Core Types Unit Tests

**File**: `tests/unit/test_core_types.py`

### Test 1.1: SymbolType Enum
**Purpose**: Verify SymbolType enum has all required values

```python
def test_symbol_type_enum_values():
    """Test that SymbolType has all required enum values."""
    assert SymbolType.METHOD.value == 'method'
    assert SymbolType.CLASS.value == 'class'
    assert SymbolType.FUNCTION.value == 'function'
    assert SymbolType.FILEPATH.value == 'filepath'
    assert SymbolType.FILENAME.value == 'filename'
    assert SymbolType.IMPORT.value == 'import'
    assert SymbolType.GLOBAL.value == 'global'

def test_symbol_type_count():
    """Test that we have exactly 7 symbol types."""
    assert len(SymbolType) == 7
```

### Test 1.2: MatchOp Enum
**Purpose**: Verify MatchOp enum has correct SQL operator mappings

```python
def test_match_op_exact():
    """Test EXACT match operator."""
    assert MatchOp.EXACT.op_name == 'exact'
    assert MatchOp.EXACT.sql_op == '='
    assert MatchOp.EXACT.needs_escaping is True

def test_match_op_glob():
    """Test GLOB match operator."""
    assert MatchOp.GLOB.op_name == 'glob'
    assert MatchOp.GLOB.sql_op == 'GLOB'
    assert MatchOp.GLOB.needs_escaping is True

def test_match_op_like():
    """Test LIKE match operator."""
    assert MatchOp.LIKE.op_name == 'like'
    assert MatchOp.LIKE.sql_op == 'LIKE'
    assert MatchOp.LIKE.needs_escaping is True

def test_match_op_regexp():
    """Test REGEXP match operator."""
    assert MatchOp.REGEXP.op_name == 'regexp'
    assert MatchOp.REGEXP.sql_op == 'REGEXP'
    assert MatchOp.REGEXP.needs_escaping is True
```

### Test 1.3: MatchResult Dataclass
**Purpose**: Verify MatchResult dataclass and string formatting

```python
def test_match_result_creation():
    """Test creating a MatchResult."""
    result = MatchResult(
        symbol_type='method',
        symbol_name='save',
        qualified_name='models.user.User.save',
        file_path='src/models/user.py',
        line_number=45,
        byte_offset=1234,
        byte_length=56,
        parent_name='User'
    )
    assert result.symbol_type == 'method'
    assert result.symbol_name == 'save'
    assert result.qualified_name == 'models.user.User.save'

def test_match_result_str_with_byte_position():
    """Test MatchResult string formatting with byte position."""
    result = MatchResult(
        symbol_type='method',
        symbol_name='save',
        qualified_name='models.user.User.save',
        file_path='src/models/user.py',
        line_number=45,
        byte_offset=1234,
        byte_length=56,
        parent_name='User'
    )
    expected = 'method:src/models/user.py:45:models.user.User.save:@1234+56'
    assert str(result) == expected

def test_match_result_str_without_byte_position():
    """Test MatchResult string formatting without byte position."""
    result = MatchResult(
        symbol_type='filepath',
        symbol_name='user.py',
        qualified_name='src/models/user.py',
        file_path='src/models/user.py',
        line_number=0,
        byte_offset=None,
        byte_length=None,
        parent_name=None
    )
    expected = 'filepath:src/models/user.py:0:src/models/user.py'
    assert str(result) == expected
```

**Total Test 1**: 10 tests

---

## Test Suite 2: DatabaseStore.match() Unit Tests

**File**: `tests/unit/test_database_match.py`

### Setup Fixture
```python
@pytest.fixture
def test_db():
    """Create a test database with sample symbols."""
    db = DatabaseStore(':memory:', '/test/root')
    db.connect()
    db.initialize_schema()

    # Insert test symbols
    db.insert_symbol('save', 'method', 'src/user.py', 10, 'user.User.save', 100, 50, 'User')
    db.insert_symbol('load', 'method', 'src/user.py', 20, 'user.User.load', 200, 40, 'User')
    db.insert_symbol('User', 'class', 'src/user.py', 5, 'user.User', 50, 200, None)
    db.insert_symbol('calculate', 'function', 'src/utils.py', 15, 'utils.calculate', 300, 80, None)
    db.insert_symbol('user.py', 'filename', 'src/user.py', 0, 'src/user.py', None, None, None)
    db.insert_symbol('json', 'import', 'src/user.py', 1, 'json', 0, 11, None)
    db.insert_symbol('MAX_SIZE', 'global', 'src/config.py', 3, 'config.MAX_SIZE', 30, 15, None)

    yield db
    db.close()
```

### Test 2.1: Match by Symbol Type
**Purpose**: Verify matching works for each symbol type

```python
def test_match_methods(test_db):
    """Test matching methods."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True))
    assert len(results) == 2
    assert all(r.symbol_type == 'method' for r in results)

def test_match_classes(test_db):
    """Test matching classes."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'User'

def test_match_functions(test_db):
    """Test matching functions."""
    results = list(test_db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'calculate'

def test_match_filenames(test_db):
    """Test matching filenames."""
    results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'user.py'

def test_match_imports(test_db):
    """Test matching imports."""
    results = list(test_db.match(SymbolType.IMPORT, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'json'

def test_match_globals(test_db):
    """Test matching globals."""
    results = list(test_db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'MAX_SIZE'
```

### Test 2.2: Match by Operator
**Purpose**: Verify each match operator works correctly

```python
def test_match_with_glob_wildcard(test_db):
    """Test GLOB pattern matching with wildcard."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sa*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_glob_question(test_db):
    """Test GLOB pattern matching with ? wildcard."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sav?', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_exact(test_db):
    """Test EXACT pattern matching."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, 'save', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_like(test_db):
    """Test LIKE pattern matching."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.LIKE, 's%', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'
```

### Test 2.3: Case Sensitivity
**Purpose**: Verify case-sensitive and case-insensitive matching

```python
def test_match_case_sensitive(test_db):
    """Test case-sensitive matching."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', True))
    assert len(results) == 0  # 'User' != 'user'

def test_match_case_insensitive(test_db):
    """Test case-insensitive matching."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', False))
    assert len(results) == 1
    assert results[0].symbol_name == 'User'

def test_match_case_insensitive_pattern(test_db):
    """Test case-insensitive with wildcard pattern."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'SA*', False))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'
```

### Test 2.4: Result Limiting
**Purpose**: Verify limit parameter works correctly

```python
def test_match_with_limit(test_db):
    """Test limiting results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=1))
    assert len(results) == 1

def test_match_with_limit_zero(test_db):
    """Test limit=0 returns no results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=0))
    assert len(results) == 0

def test_match_with_limit_greater_than_total(test_db):
    """Test limit greater than total results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=100))
    assert len(results) == 2  # Only 2 methods exist
```

### Test 2.5: Empty Results
**Purpose**: Verify behavior with no matches

```python
def test_match_no_results(test_db):
    """Test matching with no results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'nonexistent', True))
    assert len(results) == 0

def test_match_empty_pattern(test_db):
    """Test matching with empty pattern."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, '', True))
    assert len(results) == 0
```

### Test 2.6: Byte Position Data
**Purpose**: Verify byte position data is included correctly

```python
def test_match_result_has_byte_position(test_db):
    """Test that methods have byte position data."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
    assert len(results) == 1
    assert results[0].byte_offset == 100
    assert results[0].byte_length == 50

def test_match_result_no_byte_position_for_files(test_db):
    """Test that filenames don't have byte position data."""
    results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].byte_offset is None
    assert results[0].byte_length is None
```

### Test 2.7: SQL Injection Protection
**Purpose**: Verify pattern escaping works correctly

```python
def test_match_escapes_single_quotes(test_db):
    """Test that single quotes in patterns are escaped."""
    # Insert a symbol with single quote
    test_db.insert_symbol("O'Connor", 'class', 'src/test.py', 10, "test.O'Connor", 100, 50, None)

    results = list(test_db.match(SymbolType.CLASS, MatchOp.EXACT, "O'Connor", True))
    assert len(results) == 1
    assert results[0].symbol_name == "O'Connor"
```

**Total Test 2**: 20 tests

---

## Test Suite 3: CLI Integration Tests

**File**: `tests/integration/test_cli_match.py`

### Setup Fixture
```python
@pytest.fixture
def indexed_db(tmp_path):
    """Create a temporary indexed database for testing."""
    # Create test Python files
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()

    # Create test file with various entities
    (test_dir / "module.py").write_text('''
class TestClass:
    def test_method(self):
        pass

def test_function():
    pass

TEST_GLOBAL = 42
''')

    # Index the directory
    db_path = test_dir / ".via" / "index.db"
    db_path.parent.mkdir()

    with DatabaseStore(str(db_path), str(test_dir)) as db:
        db.initialize_schema()
        # ... populate with test data ...

    yield test_dir, db_path
```

### Test 3.1: CLI Command Parsing
**Purpose**: Verify CLI correctly parses arguments

```python
def test_match_command_with_required_args(indexed_db):
    """Test match command with required arguments."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', 'test_*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'test_function' in result.stdout

def test_match_command_alias(indexed_db):
    """Test match command with 'm' alias."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'm', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_command_missing_type(indexed_db):
    """Test match command fails without --type."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', 'pattern', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'required' in result.stderr.lower()
```

### Test 3.2: Match Syntax Flags
**Purpose**: Verify syntax flags work correctly

```python
def test_match_with_glob_flag(indexed_db):
    """Test -g/--glob flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', 'test_*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_with_regex_flag(indexed_db):
    """Test -r/--regex flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-r', '^test_.*$', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_with_sql_flag(indexed_db):
    """Test -s/--sql flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-s', 'test_%', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
```

### Test 3.3: Symbol Type Filters
**Purpose**: Verify all symbol type filters work

```python
def test_match_methods(indexed_db):
    """Test matching methods."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'method', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'method:' in result.stdout

def test_match_classes(indexed_db):
    """Test matching classes."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'class', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'class:' in result.stdout

def test_match_functions(indexed_db):
    """Test matching functions."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'function:' in result.stdout
```

### Test 3.4: Qualifier Flags
**Purpose**: Verify qualifier flags work correctly

```python
def test_match_case_insensitive_flag(indexed_db):
    """Test -I/--case-insensitive flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'class', '-g', 'testclass', '-I', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'TestClass' in result.stdout

def test_match_limit_flag(indexed_db):
    """Test -n/--limit flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-n', '1', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert len(lines) == 1
```

### Test 3.5: Output Format
**Purpose**: Verify output format is correct

```python
def test_match_output_format_with_byte_position(indexed_db):
    """Test output includes byte position."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'method', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # Format: type:file:line:qualified:@offset+length
    assert '@' in result.stdout
    assert '+' in result.stdout

def test_match_output_format_without_byte_position(indexed_db):
    """Test output for files doesn't include byte position."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'filename', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert '@' not in result.stdout  # No byte position for files
```

### Test 3.6: Error Handling
**Purpose**: Verify error cases are handled gracefully

```python
def test_match_database_not_found(tmp_path):
    """Test error when database doesn't exist."""
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(tmp_path)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'Database not found' in result.stderr
    assert 'via index' in result.stderr  # Suggests running index first

def test_match_invalid_symbol_type(indexed_db):
    """Test error with invalid symbol type."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'invalid', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_match_directory_not_found():
    """Test error when directory doesn't exist."""
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', '/nonexistent'],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'does not exist' in result.stderr.lower()
```

### Test 3.7: Streaming Output
**Purpose**: Verify results stream correctly (for piping)

```python
def test_match_streams_results(indexed_db):
    """Test that results are streamed (not buffered)."""
    test_dir, db_path = indexed_db
    # This test would verify generator-based streaming
    # In practice, verify no "Indexing complete" type headers
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # Should only have result lines, no headers/footers
    assert '====' not in result.stdout
    assert 'COMPLETE' not in result.stdout
```

**Total Test 3**: 18 tests

---

## Test Suite 4: Indexer Symbol Population Tests

**File**: `tests/unit/test_indexer_symbols.py`

### Test 4.1: Symbol Insertion
**Purpose**: Verify indexer populates symbols table correctly

```python
def test_indexer_creates_function_symbols(test_db):
    """Test that indexer creates symbol entries for functions."""
    # Index a file with a function
    # Verify symbol table has function entry

def test_indexer_creates_class_symbols(test_db):
    """Test that indexer creates symbol entries for classes."""
    # Index a file with a class
    # Verify symbol table has class entry

def test_indexer_creates_method_symbols(test_db):
    """Test that indexer creates symbol entries for methods."""
    # Index a file with a method
    # Verify symbol table has method entry with parent_name

def test_indexer_creates_import_symbols(test_db):
    """Test that indexer creates symbol entries for imports."""
    # Index a file with imports
    # Verify symbol table has import entries

def test_indexer_creates_global_symbols(test_db):
    """Test that indexer creates symbol entries for globals."""
    # Index a file with global variables
    # Verify symbol table has global entries

def test_indexer_creates_file_symbols(test_db):
    """Test that indexer creates filename and filepath symbols."""
    # Index a file
    # Verify symbol table has both filename and filepath entries
```

### Test 4.2: Qualified Name Calculation
**Purpose**: Verify qualified names are calculated correctly

```python
def test_qualified_name_for_function():
    """Test qualified name calculation for functions."""
    qname = _calculate_qualified_name('src/utils.py', 'calculate', None)
    assert qname == 'utils.calculate'

def test_qualified_name_for_method():
    """Test qualified name calculation for methods."""
    qname = _calculate_qualified_name('src/models/user.py', 'save', 'User')
    assert qname == 'models.user.User.save'

def test_qualified_name_removes_src_prefix():
    """Test that src/ prefix is removed from module path."""
    qname = _calculate_qualified_name('src/models/user.py', 'User', None)
    assert qname == 'models.user.User'
    assert 'src' not in qname
```

### Test 4.3: Symbol Deletion on Re-index
**Purpose**: Verify symbols are deleted when file is re-indexed

```python
def test_reindex_deletes_old_symbols(test_db):
    """Test that re-indexing a file deletes old symbols."""
    # Index a file
    # Verify symbols exist
    # Modify file
    # Re-index
    # Verify old symbols deleted and new symbols inserted
```

**Total Test 4**: 10 tests

---

## Test Summary

| Test Suite | Tests | Type | File |
|------------|-------|------|------|
| Suite 1: Core Types | 10 | Unit | `tests/unit/test_core_types.py` |
| Suite 2: DatabaseStore.match() | 20 | Unit | `tests/unit/test_database_match.py` |
| Suite 3: CLI Integration | 18 | Integration | `tests/integration/test_cli_match.py` |
| Suite 4: Indexer Symbols | 10 | Unit | `tests/unit/test_indexer_symbols.py` |
| **TOTAL** | **58** | | |

---

## Edge Cases to Test

1. **Special Characters in Patterns**:
   - Patterns with SQL wildcards (%, _)
   - Patterns with glob wildcards (*, ?)
   - Patterns with regex metacharacters
   - Patterns with single quotes (SQL injection)

2. **Unicode Support**:
   - Symbol names with unicode characters
   - File paths with unicode
   - Patterns with unicode

3. **Large Result Sets**:
   - Matching pattern that returns 1000+ results
   - Verify streaming works efficiently
   - Verify limit works with large result sets

4. **Empty Database**:
   - Match command on empty symbols table
   - Should return 0 results gracefully

5. **Concurrent Access**:
   - Multiple match queries simultaneously
   - SQLite handles this via locking

---

## Performance Tests

**File**: `tests/performance/test_match_performance.py`

### Test P.1: Query Performance
```python
def test_match_performance_with_10k_symbols():
    """Test match query completes in < 100ms with 10k symbols."""
    # Create database with 10,000 symbols
    # Time a match query
    # Assert time < 100ms

def test_match_performance_with_complex_pattern():
    """Test regex match completes in reasonable time."""
    # Test regex pattern matching performance
```

### Test P.2: Index Creation Performance
```python
def test_index_lookup_uses_composite_index():
    """Test that queries use the composite (type, name) index."""
    # Use EXPLAIN QUERY PLAN to verify index usage
```

**Total Performance Tests**: 3

---

## Coverage Goals

**Target Coverage**: 95%+

**Critical Paths to Cover**:
- ✅ All SymbolType enum values
- ✅ All MatchOp operators (EXACT, GLOB, LIKE, REGEXP)
- ✅ Case-sensitive and case-insensitive matching
- ✅ Result limiting
- ✅ Empty results
- ✅ Byte position inclusion
- ✅ SQL escaping
- ✅ CLI argument parsing
- ✅ Error handling (database not found, invalid type, etc.)
- ✅ Output formatting

---

## Test Execution Order

1. **Unit Tests First**: Run all unit tests (Suites 1, 2, 4)
2. **Integration Tests**: Run CLI integration tests (Suite 3)
3. **Performance Tests**: Run performance tests (Suite P)

**Continuous Integration**:
- Run all unit tests on every commit
- Run integration tests on pull requests
- Run performance tests nightly

---

## Test Data Requirements

**Minimal Test Database**:
- 1-2 Python files with:
  - At least 1 class with methods
  - At least 2 top-level functions
  - At least 3 imports
  - At least 2 global variables
  - Various naming patterns (CamelCase, snake_case, etc.)

**Test Files Location**: `tests/fixtures/test_project/`

---

## Acceptance Criteria

Sprint 2 testing is complete when:
- ✅ All 58 core tests pass
- ✅ All 3 performance tests pass
- ✅ Code coverage ≥ 95% for new code
- ✅ Zero critical bugs found
- ✅ All edge cases handled gracefully
- ✅ Performance benchmarks met (< 100ms for 10k symbols)

---

**Created by**: @Trin (QA Engineer)
**Status**: ✅ Ready for Test Implementation
**Next**: Implement tests in test files
