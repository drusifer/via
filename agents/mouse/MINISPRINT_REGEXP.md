# Mini-Sprint: REGEXP Support

**Version**: 1.0
**Date**: 2026-01-23
**Task Owner**: @Mouse
**Assignee**: @Neo
**Status**: Ready for Implementation

---

## Problem Statement

SQLite does not have native REGEXP support. The `-r`/`--regex` flag currently fails with:
```
no such function: REGEXP
```

**Current Behavior**: Regex patterns cause SQLite error
**Desired Behavior**: Regex patterns work via Python-side filtering

---

## Solution Design

### Approach: Python-side Filtering

Instead of using SQLite's REGEXP function, we:
1. Query ALL symbols matching the type filter (no pattern filter in SQL)
2. Apply regex filtering in Python using `re.search()`
3. Stream filtered results to maintain O(1) memory

### Why This Works

- SQLite is fast at type filtering (indexed)
- Python regex is fast for string matching
- Memory stays O(1) because we filter during iteration
- No SQLite extension required

---

## Implementation Plan

### Task 1: Update DatabaseStore.match() (2h)

**File**: `via/db/store.py`

**Changes**:
1. Add `use_python_regex: bool = False` parameter
2. When `match_op == MatchOp.REGEXP`:
   - Set `use_python_regex = True`
   - Query without pattern filter (get all of type)
   - Return iterator that filters with `re.search()`

**Code Sketch**:
```python
def match(self, symbol_type, match_op, pattern, ...):
    if match_op == MatchOp.REGEXP:
        # Query all symbols of type, filter in Python
        return self._match_with_regex(symbol_type, pattern, ...)
    else:
        # Existing GLOB/LIKE behavior
        return self._match_with_sql(symbol_type, match_op, pattern, ...)

def _match_with_regex(self, symbol_type, pattern, case_sensitive, limit, match_qualified):
    """Match using Python regex instead of SQL."""
    import re
    flags = 0 if case_sensitive else re.IGNORECASE
    regex = re.compile(pattern, flags)

    # Query all symbols of type
    base_column = "qualified_name" if match_qualified else "symbol_name"
    query = f"SELECT * FROM symbols WHERE symbol_type = ?"
    params = [symbol_type]

    count = 0
    for row in self.conn.execute(query, params):
        value = row[base_column]
        if regex.search(value):
            yield self._row_to_record(row)
            count += 1
            if limit and count >= limit:
                break
```

**Acceptance Criteria**:
- AC1: `-r` flag queries all symbols of type
- AC2: Python regex filters results during iteration
- AC3: Case-insensitive flag works with regex
- AC4: Limit parameter respected
- AC5: match_qualified (-Q) works with regex

---

### Task 2: Update Tests (1h)

**File**: `tests/unit/test_database_store.py` (or new file)

**Test Cases**:
```python
def test_match_regex_basic():
    """Test basic regex matching."""
    results = list(db.match('function', MatchOp.REGEXP, r'test_\w+'))
    assert all(re.search(r'test_\w+', r.symbol_name) for r in results)

def test_match_regex_case_insensitive():
    """Test case-insensitive regex."""
    results = list(db.match('class', MatchOp.REGEXP, r'TEST', case_sensitive=False))
    # Should match 'Test', 'test', 'TEST'

def test_match_regex_with_limit():
    """Test regex with limit."""
    results = list(db.match('method', MatchOp.REGEXP, r'.*', limit=5))
    assert len(results) <= 5

def test_match_regex_qualified():
    """Test regex on qualified_name."""
    results = list(db.match('method', MatchOp.REGEXP, r'MyClass\.test_.*', match_qualified=True))
    assert all('MyClass.' in r.qualified_name for r in results)

def test_match_regex_invalid_pattern():
    """Test invalid regex pattern raises error."""
    with pytest.raises(re.error):
        list(db.match('function', MatchOp.REGEXP, r'[invalid'))
```

---

### Task 3: Update Integration Tests (0.5h)

**File**: `tests/integration/test_cli_pipeline.py`

**Changes**:
1. Unskip `test_chained_match_with_regex`
2. Add additional regex integration tests

---

### Task 4: Update Documentation (0.5h)

**Files**:
- `docs/USER_GUIDE.md`
- `via/__main__.py` (help text)

**Changes**:
1. Document regex syntax support
2. Add examples with regex patterns
3. Note: regex is slower than glob for large result sets

---

## Estimated Effort

| Task | Hours | Priority |
|------|-------|----------|
| 1. Update DatabaseStore.match() | 2h | P0 |
| 2. Unit Tests | 1h | P0 |
| 3. Integration Tests | 0.5h | P1 |
| 4. Documentation | 0.5h | P2 |
| **Total** | **4h** | |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance on large codebases | Medium | Medium | Add warning for expensive regex |
| Invalid regex patterns | Low | Low | Catch re.error, show helpful message |
| Memory with limit=0 | Low | Low | Already streaming, no change needed |

---

## Success Criteria

- [ ] `via -r 'test_\w+' -f` works (no SQL error)
- [ ] `via -r '.*Parser' -c` finds classes ending in Parser
- [ ] Case-insensitive regex works with `-I`
- [ ] Qualified name regex works with `-Q`
- [ ] All existing tests still pass
- [ ] New regex tests pass
- [ ] Integration test unskipped and passing

---

## Implementation Notes

### Why Not SQLite Extension?

1. **Portability**: Users would need to install extension
2. **Complexity**: Build/distribute native code
3. **Performance**: Python regex is fast enough for typical use
4. **Simplicity**: No external dependencies

### Performance Considerations

For a query like `via -r '.*' -f`:
- Queries all functions (fast, uses index)
- Regex `.*` matches everything (fast)
- Net result: similar to `via -g '*' -f`

For selective regex like `via -r 'test_\w+' -f`:
- Queries all functions
- Filters to ~10% matches
- Slightly slower than glob, but acceptable

---

**Status**: Ready for @Neo to implement
**Estimated Completion**: 4 hours
