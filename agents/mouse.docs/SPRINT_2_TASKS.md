# Sprint 2 Task Breakdown - Match Command (v5.0 Denormalized)

**Created**: 2026-01-13
**Task Manager**: @Mouse
**Architecture**: v5.0 Denormalized (single `symbols` table)
**Sprint Goal**: Implement `via match` command with simple pattern matching

---

## Overview

**Architecture Change**: v5.0 uses a denormalized `symbols` table, eliminating JOINs and SQL templates. This drastically simplifies implementation.

**Key Simplifications**:
- No PatternMatcher classes needed (just enum values)
- No QueryService layer (DatabaseStore.match() is sufficient)
- Trivial SQL: `SELECT * FROM symbols WHERE symbol_type = ? AND symbol_name {op} ?`

---

## Phase 1: Schema Migration (CRITICAL - Must Complete First)

### Task 1.1: Create New Schema (2h)
**Owner**: @Neo
**Priority**: P0 - BLOCKER
**File**: `via/db/schema.py`

**Subtasks**:
- [x] Review current schema (functions, classes, imports, globals, files tables)
- [ ] Create `symbols` table schema with indexes
- [ ] Create `references` table schema (for future use)
- [ ] Update `SCHEMA_VERSION` to 2
- [ ] Keep `files` table for metadata
- [ ] Add schema migration logic for v1 → v2

**Schema Details**:
```sql
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_name TEXT NOT NULL,
    symbol_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    byte_offset INTEGER,
    byte_length INTEGER,
    qualified_name TEXT NOT NULL,
    parent_name TEXT
);

CREATE INDEX idx_symbols_name ON symbols(symbol_name);
CREATE INDEX idx_symbols_type ON symbols(symbol_type);
CREATE INDEX idx_symbols_type_name ON symbols(symbol_type, symbol_name);
CREATE INDEX idx_symbols_file ON symbols(file_path);

CREATE TABLE references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol_id INTEGER NOT NULL,
    to_symbol_id INTEGER NOT NULL,
    reference_type TEXT NOT NULL,
    line_number INTEGER,
    FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    FOREIGN KEY (to_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
);

CREATE INDEX idx_references_from ON references(from_symbol_id);
CREATE INDEX idx_references_to ON references(to_symbol_id);
CREATE INDEX idx_references_type ON references(reference_type);
```

**Acceptance Criteria**:
- [ ] Schema v2 defined in schema.py
- [ ] Migration logic handles v1 databases
- [ ] New databases create v2 schema
- [ ] `files` table retained for metadata
- [ ] All indexes created

**Estimated**: 2h

---

### Task 1.2: Migrate Indexer to Symbols Table (4h)
**Owner**: @Neo
**Priority**: P0 - BLOCKER
**Files**: `via/indexer/*.py`

**Subtasks**:
- [ ] Update function indexing to insert into `symbols` table
- [ ] Update class indexing to insert into `symbols` table
- [ ] Update import indexing to insert into `symbols` table
- [ ] Update global indexing to insert into `symbols` table
- [ ] Add file path indexing (filename + filepath types)
- [ ] Calculate qualified names during indexing
- [ ] Track parent_name for methods
- [ ] Remove old table inserts (functions, classes, imports, globals)

**Qualified Name Logic**:
```python
def calculate_qualified_name(file_path, entity_name, parent_class=None):
    """Calculate fully qualified name for entity."""
    # Convert file path to module: src/models/user.py -> models.user
    module = file_path.replace('.py', '').replace('/', '.')
    if module.startswith('src.'):
        module = module[4:]

    # Build qualified name
    if parent_class:
        return f"{module}.{parent_class}.{entity_name}"
    else:
        return f"{module}.{entity_name}"
```

**Acceptance Criteria**:
- [ ] All entity types insert into `symbols` table
- [ ] Qualified names calculated correctly
- [ ] Parent class names tracked for methods
- [ ] Byte offset and length captured
- [ ] File entries created for filename/filepath matching
- [ ] Old table inserts removed
- [ ] Existing tests updated

**Estimated**: 4h

---

### Task 1.3: Test Schema Migration (1h)
**Owner**: @Trin
**Priority**: P0
**Files**: `tests/db/test_schema_migration.py`

**Subtasks**:
- [ ] Test v1 → v2 migration on existing database
- [ ] Test fresh v2 schema creation
- [ ] Verify all indexes created
- [ ] Verify data integrity after migration
- [ ] Test rollback if migration fails

**Acceptance Criteria**:
- [ ] Migration tests pass
- [ ] No data loss during migration
- [ ] Indexes functioning
- [ ] Can query migrated data

**Estimated**: 1h

---

## Phase 2: Core Types (Simple)

### Task 2.1: Create Core Types (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/core/types.py`

**Subtasks**:
- [ ] Create `SymbolType` enum (method, class, function, filepath, filename, import, global)
- [ ] Create `MatchOp` enum (EXACT, GLOB, LIKE, REGEXP)
- [ ] Create `MatchResult` dataclass

**Code**:
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class SymbolType(Enum):
    """Symbol types for matching."""
    METHOD = 'method'
    CLASS = 'class'
    FUNCTION = 'function'
    FILEPATH = 'filepath'
    FILENAME = 'filename'
    IMPORT = 'import'
    GLOBAL = 'global'


class MatchOp(Enum):
    """Match operators mapping to SQL operators."""
    # (name, sql_op, needs_escaping)
    EXACT = ('exact', '=', True)
    GLOB = ('glob', 'GLOB', True)
    LIKE = ('like', 'LIKE', True)
    REGEXP = ('regexp', 'REGEXP', True)

    def __init__(self, op_name, sql_op, needs_escaping):
        self.op_name = op_name
        self.sql_op = sql_op
        self.needs_escaping = needs_escaping


@dataclass
class MatchResult:
    """Match result with position information."""
    symbol_type: str
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: Optional[int]
    byte_offset: Optional[int]
    byte_length: Optional[int]
    parent_name: Optional[str]
```

**Acceptance Criteria**:
- [ ] All enums defined
- [ ] MatchResult dataclass complete
- [ ] Type hints correct

**Estimated**: 1h

---

## Phase 3: Database Match Method (Simple)

### Task 3.1: Implement DatabaseStore.match() (2h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/db/store.py`

**Subtasks**:
- [ ] Add `match()` method to DatabaseStore
- [ ] Build simple WHERE clause dynamically
- [ ] Support case-sensitive/insensitive matching
- [ ] Support result limit
- [ ] Yield MatchResult objects
- [ ] Handle SQL escaping

**Code**:
```python
def match(
    self,
    symbol_type: SymbolType,
    match_op: MatchOp,
    pattern: str,
    case_sensitive: bool = True,
    limit: Optional[int] = None
) -> Iterator[MatchResult]:
    """Match symbols using denormalized table."""
    # Build WHERE clause
    where_parts = ["symbol_type = ?"]
    params = [symbol_type.value]

    # Add name match
    column = "symbol_name"
    if not case_sensitive:
        column = "LOWER(symbol_name)"
        pattern = pattern.lower()

    # Escape if needed
    if match_op.needs_escaping:
        pattern = pattern.replace("'", "''")

    where_parts.append(f"{column} {match_op.sql_op} ?")
    params.append(pattern)

    # Build query
    query = f"""
        SELECT symbol_name, symbol_type, file_path, line_number,
               byte_offset, byte_length, qualified_name, parent_name
        FROM symbols
        WHERE {' AND '.join(where_parts)}
        ORDER BY file_path, line_number
    """

    if limit:
        query += f"\nLIMIT {limit}"

    # Execute and yield
    cursor = self.conn.execute(query, params)
    for row in cursor:
        yield MatchResult(
            symbol_name=row[0],
            symbol_type=row[1],
            file_path=row[2],
            line_number=row[3],
            byte_offset=row[4],
            byte_length=row[5],
            qualified_name=row[6],
            parent_name=row[7]
        )
```

**Acceptance Criteria**:
- [ ] match() method implemented
- [ ] WHERE clause construction works
- [ ] All MatchOp operators supported
- [ ] Case sensitivity works
- [ ] Limit works
- [ ] Returns MatchResult generator

**Estimated**: 2h

---

### Task 3.2: Unit Test DatabaseStore.match() (2h)
**Owner**: @Trin
**Priority**: P0
**File**: `tests/db/test_store_match.py`

**Test Cases**:
- [ ] Test each SymbolType (7 tests)
- [ ] Test each MatchOp (4 tests)
- [ ] Test case-insensitive matching (1 test)
- [ ] Test limit (1 test)
- [ ] Test empty results (1 test)
- [ ] Test byte_offset/byte_length in results (1 test)

**Total Tests**: 15

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 100% coverage of match() method

**Estimated**: 2h

---

## Phase 4: CLI Integration

### Task 4.1: Add Match Subcommand (2h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Add `match` subcommand (alias `m`) to argparse
- [ ] Add `-t/--type` flag (choices: method, class, function, etc.)
- [ ] Add pattern positional argument
- [ ] Add `-g/--glob` flag (default)
- [ ] Add `-r/--regex` flag
- [ ] Add `-s/--sql` flag (SQL LIKE)
- [ ] Add `-I/--case-insensitive` flag
- [ ] Add `-n/--limit` flag
- [ ] Wire to DatabaseStore.match()

**Command Examples**:
```bash
via match -t method -g '*save()'
via m -t class -r '^User'
via m -t function -s 'test_%' -I
via m -t method '*ToString()' -n 10
```

**Acceptance Criteria**:
- [ ] match subcommand works
- [ ] All flags implemented
- [ ] Short alias `m` works
- [ ] Calls DatabaseStore.match() correctly

**Estimated**: 2h

---

### Task 4.2: Implement Output Formatting (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Format as `type:file_path:line_number:qualified_name`
- [ ] Add byte position if available: `:@byte_offset+byte_length`
- [ ] Stream output (no header/footer)
- [ ] Handle empty results gracefully

**Output Format**:
```
method:src/models/user.py:45:models.user.User.save:@1234+56
class:src/models/user.py:10:models.user.User:@234+1000
function:src/utils.py:15:utils.calculate_sum:@567+48
file:src/utils.py:0:src/utils.py
```

**Acceptance Criteria**:
- [ ] Output format correct
- [ ] Byte position included when available
- [ ] Streams for piping
- [ ] No errors on empty results

**Estimated**: 1h

---

### Task 4.3: Add Error Handling (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Handle invalid symbol type
- [ ] Handle invalid pattern (malformed regex/glob)
- [ ] Handle database not found
- [ ] Handle database corruption
- [ ] Provide helpful error messages

**Acceptance Criteria**:
- [ ] Graceful error handling
- [ ] User-friendly messages
- [ ] Non-zero exit codes on error

**Estimated**: 1h

---

## Phase 5: Integration Testing

### Task 5.1: CLI Integration Tests (3h)
**Owner**: @Trin
**Priority**: P0
**File**: `tests/cli/test_match_command.py`

**Test Cases**:
- [ ] Test match with each SymbolType (7 tests)
- [ ] Test GLOB matching (1 test)
- [ ] Test REGEXP matching (1 test)
- [ ] Test SQL LIKE matching (1 test)
- [ ] Test case-insensitive flag (1 test)
- [ ] Test limit flag (1 test)
- [ ] Test output format (1 test)
- [ ] Test byte position in output (1 test)
- [ ] Test empty results (1 test)
- [ ] Test error cases (3 tests)

**Total Tests**: 18

**Acceptance Criteria**:
- [ ] All integration tests pass
- [ ] Tests use real indexed database
- [ ] Output format validated
- [ ] Error handling tested

**Estimated**: 3h

---

### Task 5.2: End-to-End Testing (2h)
**Owner**: @Trin
**Priority**: P1
**File**: `tests/e2e/test_match_workflow.py`

**Test Scenarios**:
- [ ] Index codebase → match methods → verify results
- [ ] Index codebase → match classes → verify qualified names
- [ ] Index codebase → match files → verify file paths
- [ ] Complex patterns (wildcards, regex)
- [ ] Case-insensitive searches
- [ ] Large result sets with limit

**Acceptance Criteria**:
- [ ] E2E workflow works
- [ ] Realistic test data
- [ ] Performance acceptable

**Estimated**: 2h

---

## Phase 6: Documentation

### Task 6.1: Update README (1h)
**Owner**: @Neo
**Priority**: P1
**File**: `README.md`

**Subtasks**:
- [ ] Add `via match` command documentation
- [ ] Add usage examples
- [ ] Add pattern syntax guide
- [ ] Update feature list

**Estimated**: 1h

---

### Task 6.2: Add Command Help (0.5h)
**Owner**: @Neo
**Priority**: P1
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Add detailed help text for match command
- [ ] Add examples in help
- [ ] Document all flags

**Estimated**: 0.5h

---

## Task Summary

### By Phase

| Phase | Tasks | Est Hours | Priority |
|-------|-------|-----------|----------|
| 1. Schema Migration | 3 | 7h | P0 |
| 2. Core Types | 1 | 1h | P0 |
| 3. Database Match | 2 | 4h | P0 |
| 4. CLI Integration | 3 | 4h | P0 |
| 5. Integration Testing | 2 | 5h | P0 |
| 6. Documentation | 2 | 1.5h | P1 |
| **TOTAL P0** | **11** | **21h** | |
| **TOTAL P0+P1** | **13** | **22.5h** | |

### By Owner

| Owner | Tasks | Est Hours |
|-------|-------|-----------|
| @Neo | 8 | 13.5h |
| @Trin | 4 | 8h |
| @Mouse | 1 | 1h (this doc) |
| **TOTAL** | **13** | **22.5h** |

---

## Critical Path

**BLOCKERS** (must complete in order):
1. Task 1.1: Create New Schema (2h)
2. Task 1.2: Migrate Indexer (4h)
3. Task 1.3: Test Schema Migration (1h)

**PARALLEL** (can work simultaneously after blockers):
- Task 2.1: Core Types (1h)
- Task 3.1: DatabaseStore.match() (2h)
- Task 4.1: CLI Integration (2h)

**PARALLEL TESTING** (after implementation):
- Task 3.2: Unit Tests (2h)
- Task 5.1: Integration Tests (3h)
- Task 5.2: E2E Tests (2h)

**FINAL**:
- Task 6.1: Documentation (1h)
- Task 6.2: Help Text (0.5h)

**Total Critical Path**: ~7h (if perfectly parallel) to ~22.5h (if sequential)

---

## Risk Assessment

### High Risk
- **Schema Migration**: Breaking change to database schema
  - **Mitigation**: Thorough migration testing, backup before migration
  - **Fallback**: Keep migration reversible

### Medium Risk
- **Indexer Changes**: Must update all entity indexing logic
  - **Mitigation**: Update tests first, then implementation
  - **Fallback**: Can revert to v1 schema if needed

### Low Risk
- **CLI Integration**: Straightforward wiring
- **Match Logic**: Simple SQL, well-defined

---

## Definition of Done

Sprint 2 is complete when:
- ✅ Schema v2 created and tested
- ✅ Indexer populates `symbols` table correctly
- ✅ `via match` command works with all flags
- ✅ All unit tests pass (15+ tests)
- ✅ All integration tests pass (18+ tests)
- ✅ E2E tests pass
- ✅ Documentation updated
- ✅ Help text complete
- ✅ Zero regressions in `via index` command

---

## Notes

**Architecture Benefits**:
- Much simpler than original user stories (no PatternMatcher classes, no QueryService)
- Denormalized schema eliminates all complexity
- Single query pattern for all symbol types
- Easy to test and maintain

**Deferred to Sprint 3**:
- Multiple match clauses with AND logic
- File path filtering (`-F` flag)
- `via render` command
- Multiple output formats (JSON, CSV)

**Comparison to Original Estimate**:
- Original user stories: 22-28h
- New v5.0 tasks: 22.5h
- Similar time but MUCH simpler implementation!

---

**Created by**: @Mouse (Task Manager)
**Reviewed by**: @Morpheus (Architecture alignment)
**Status**: ✅ Ready for Sprint Planning
**Next**: @Neo start Phase 1 (Schema Migration)
