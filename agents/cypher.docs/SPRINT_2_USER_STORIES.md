# Sprint 2 User Stories - Query Command (Match-Style Filtering)

**Created**: 2026-01-12 (Revised)
**Product Manager**: @Cypher
**Sprint Goal**: Implement `via query` command with match-style filtering for searching indexed code

---

## Sprint 2 Overview

**Goal**: Enable users to search indexed code using flexible pattern matching.

**Scope**:
- `via query` command with match mode (`-M`)
- 3 match syntaxes: glob, regex, SQL LIKE
- 5 entity type filters: method, class, function, import, global
- Simple text output (no rendering)

**Out of Scope** (Sprint 3+):
- `via render` command (syntax highlighting, context lines)
- `via list` command
- `via stats` command
- Multiple output formats (JSON, CSV, etc.)

---

## User Stories

### Story 1: Pattern Matcher Foundation (3 pts)
**As a** developer
**I want** pluggable pattern matching strategies
**So that** I can search using glob, regex, or SQL LIKE patterns

**Acceptance Criteria**:
- [ ] Create `PatternMatcher` abstract base class in `via/core/pattern_matcher.py`
- [ ] Implement `GlobMatcher` with SQLite GLOB support
- [ ] Implement `SqlLikeMatcher` with SQLite LIKE support
- [ ] Create `MatcherRegistry` for pattern matcher lookup
- [ ] Support case-sensitive and case-insensitive matching
- [ ] Each matcher generates correct SQL WHERE clauses
- [ ] Unit tests with 100% coverage (15 tests total)

**Tasks**:
- [S1.1] Design `PatternMatcher` ABC interface (0.5h)
- [S1.2] Implement `GlobMatcher` class (1.5h)
- [S1.3] Implement `SqlLikeMatcher` class (1h)
- [S1.4] Create `MatcherRegistry` class (0.5h)
- [S1.5] Unit tests for GlobMatcher (1h)
- [S1.6] Unit tests for SqlLikeMatcher (1h)
- [S1.7] Unit tests for MatcherRegistry (0.5h)

**Estimated**: 6h

**Example Code**:
```python
# Usage
matcher = GlobMatcher()
sql = matcher.to_sql_clause('*ToString()', 'name', case_sensitive=False)
# Output: "LOWER(name) GLOB '*tostring()'"
```

---

### Story 2: Query Service Layer (5 pts)
**As a** developer
**I want** a query service that searches the database using pattern matching
**So that** I can find code entities by pattern, type, and file path

**Acceptance Criteria**:
- [ ] Create `QueryService` class in `via/services/query_service.py`
- [ ] Support entity type filtering (method, class, function, import, global, all)
- [ ] Support multiple entity types with OR logic
- [ ] Support file path filtering (glob patterns)
- [ ] Support result limiting (`--limit N`)
- [ ] Build dynamic SQL queries using pattern matchers
- [ ] Construct fully qualified names (e.g., `module.Class.method`)
- [ ] Yield results as generator (streaming for pipes)
- [ ] Return structured results (type, file_path, line_number, qualified_name)
- [ ] Unit tests with 90%+ coverage (20 tests total)

**Tasks**:
- [S2.1] Design QueryService interface and result dataclass (1h)
- [S2.2] Implement single entity type queries (2h)
- [S2.3] Implement multiple entity type queries (UNION ALL) (2h)
- [S2.4] Implement file path filtering (1h)
- [S2.5] Implement result limiting (0.5h)
- [S2.6] Implement qualified name construction (1.5h)
- [S2.7] Unit tests for QueryService (2h)

**Estimated**: 10h

**Example Code**:
```python
# Usage
service = QueryService(db_store)
results = service.query(
    pattern='*ToString()',
    matcher='glob',
    entity_types=['method'],
    file_filter='src/**/*.py',
    case_sensitive=False,
    limit=10
)

for result in results:
    print(f"{result.type}:{result.file_path}:{result.line_number}:{result.qualified_name}")
```

---

### Story 3: CLI Query Command (3 pts)
**As a** developer
**I want** a `via query` command with ultra-short syntax
**So that** I can quickly search my codebase from the command line

**Acceptance Criteria**:
- [ ] Implement `via query` subcommand in `via/__main__.py`
- [ ] Support match mode flag (`-M` / `--match`)
- [ ] Support syntax flags: `-g` (glob), `-r` (regex), `-s` (sql)
- [ ] Support type flags: `-m` (method), `-c` (class), `-f` (function), `-i` (import), `-G` (global)
- [ ] Support qualifier flags: `-I` (case-insensitive), `-n N` (limit), `-F PATTERN` (file filter)
- [ ] Support ultra-short combined syntax (e.g., `-qMmg`)
- [ ] Wire QueryService to CLI
- [ ] Format output as: `type:file_path:line_number:qualified_name`
- [ ] Stream output for piping (no header/footer)
- [ ] Handle errors gracefully (no results, invalid pattern, etc.)
- [ ] Integration tests (12 tests total)

**Command Syntax**:
```bash
# Long form
via query --match <PATTERN> --glob --method --case-insensitive

# Short form
via -qMmg '<PATTERN>'

# Examples
via -qMmg '*ToString()'                      # Find methods ending with ToString()
via -qMcrI '^user$'                          # Find classes named "user" (case-insensitive, regex)
via -qMfg 'test_*' -F 'tests/**/*.py'        # Find test functions in tests/
via -qMmfg 'calculate*' -n 10                # Find methods or functions, limit to 10
```

**Tasks**:
- [S3.1] Add `query` subcommand to argparse (1h)
- [S3.2] Add all flags (match mode, syntax, types, qualifiers) (1.5h)
- [S3.3] Wire QueryService to CLI (1h)
- [S3.4] Implement result formatting (0.5h)
- [S3.5] Add error handling (0.5h)
- [S3.6] Integration tests for CLI (1.5h)

**Estimated**: 6h

**Output Format**:
```
method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

---

### Story 4: Regex Matcher (Optional - 3 pts)
**As a** developer
**I want** full regex pattern matching
**So that** I can use advanced patterns for complex searches

**Acceptance Criteria**:
- [ ] Implement `RegexMatcher` class
- [ ] Support full Python regex syntax
- [ ] Research SQLite regex extension options
- [ ] Implement Python-side filtering if SQLite regex unavailable
- [ ] Support case-sensitive and case-insensitive modes
- [ ] Performance acceptable (< 1s for 10k entities)
- [ ] Unit tests with 100% coverage (5 tests)

**Tasks**:
- [S4.1] Research SQLite regex extension (0.5h)
- [S4.2] Implement RegexMatcher (3h)
- [S4.3] Add performance optimization (1h)
- [S4.4] Unit tests (1.5h)

**Estimated**: 6h

**Note**: This story is optional if time permits. Regex support can be deferred to Sprint 3.

---

## Story Point Summary

| Story | Priority | Points | Est Hours |
|-------|----------|--------|-----------|
| S1: Pattern Matcher | **P0** | 3 | 6h |
| S2: Query Service | **P0** | 5 | 10h |
| S3: CLI Query | **P0** | 3 | 6h |
| S4: Regex Matcher | **P1** (optional) | 3 | 6h |
| **TOTAL (P0)** | | **11** | **22h** |
| **TOTAL (P0+P1)** | | **14** | **28h** |

---

## Sprint 2 Dependencies

### From Sprint 1 (Complete)
- ✅ Database schema with all entity tables (files, functions, classes, imports, globals)
- ✅ DatabaseStore with CRUD operations
- ✅ CLI framework with argparse
- ✅ Test infrastructure (pytest)

### New Dependencies
- None required for P0 stories
- SQLite regex extension (optional, for Story 4)

---

## Implementation Order

### Phase 1: Pattern Matcher Foundation (Day 1)
1. **Story 1: Pattern Matcher** (6h)
   - Build pluggable matcher architecture
   - Implement glob and SQL LIKE matchers
   - Full test coverage

**Deliverable**: Pattern matcher infrastructure ready

### Phase 2: Query Service (Day 2)
2. **Story 2: Query Service** (10h)
   - Build query engine with dynamic SQL generation
   - Support all entity type filters
   - Streaming results with generators

**Deliverable**: QueryService with full test coverage

### Phase 3: CLI Integration (Day 3)
3. **Story 3: CLI Query** (6h)
   - Wire everything to CLI
   - Support ultra-short syntax
   - Integration tests

**Deliverable**: Working `via query` command

### Phase 4: Regex Support (Optional - Day 4)
4. **Story 4: Regex Matcher** (6h)
   - Add regex pattern support
   - Optimize performance

**Deliverable**: Regex pattern matching

---

## Acceptance Criteria for Sprint 2

Sprint 2 is **DONE** when:

1. ✅ Users can search by glob patterns (`via -qMmg '*pattern'`)
2. ✅ Users can search by SQL LIKE patterns (`via -qMms '%pattern%'`)
3. ✅ Users can filter by entity type (method, class, function, import, global)
4. ✅ Users can filter by multiple types with OR logic (`via -qMmfg 'pattern'`)
5. ✅ Users can filter by file path (`via -qMmg 'pattern' -F 'src/**/*.py'`)
6. ✅ Users can limit results (`via -qMmg 'pattern' -n 10`)
7. ✅ Users can toggle case sensitivity (`via -qMmgI 'pattern'`)
8. ✅ Output shows: type, file_path, line_number, qualified_name
9. ✅ Results stream for piping to `less`, `grep`, etc.
10. ✅ All P0 stories have tests (47 total: 15 matcher + 20 service + 12 CLI)
11. ✅ Test coverage > 80%
12. ✅ Documentation updated

**Optional** (if Story 4 completed):
- ✅ Users can search by regex patterns (`via -qMmr '.*pattern$'`)

---

## Example Usage

```bash
# Find all methods ending with ToString()
via -qMmg '*ToString()'

# Find classes named "User" (case-insensitive)
via -qMcgI 'user'

# Find functions starting with "test_" in test files
via -qMfg 'test_*' -F 'tests/**/*.py'

# Find first 10 imports containing "os"
via -qMis '%os%' -n 10

# Find methods OR functions matching "calculate" pattern
via -qMmfg 'calculate*'

# Case-insensitive search for classes containing "model"
via -qMcgI '*model*'

# Regex search for magic methods (if Story 4 complete)
via -qMmr '__(init|str|repr)__'

# Pipe results to less for browsing
via -qMfg 'test_*' | less

# Count matching results
via -qMcg 'User*' | wc -l

# Search and filter with grep
via -qMmg '*' | grep 'src/models'
```

---

## Output Format (Sprint 2 - Simple Text)

**Format**: `type:file_path:line_number:qualified_name`

**Example Output**:
```
method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

**Future Formats** (Sprint 3+):
- JSON: `--format json`
- CSV: `--format csv`
- Table: `--format table`

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex performance on large databases | Medium | Use Python-side filtering with generator pattern |
| SQLite GLOB/LIKE case-sensitivity platform differences | Low | Explicit UPPER()/LOWER() conversion |
| Complex query patterns causing SQL errors | Medium | Validate patterns before query, catch SQL exceptions |
| Qualified name construction edge cases | Low | Comprehensive unit tests for all entity types |

---

## Technical Notes

### Entity Type to Database Mapping

| Entity Type | Database Query |
|-------------|----------------|
| **method** | `SELECT FROM functions WHERE parent_entity_id IS NOT NULL` |
| **function** | `SELECT FROM functions WHERE parent_entity_id IS NULL` |
| **class** | `SELECT FROM classes` |
| **import** | `SELECT FROM imports` |
| **global** | `SELECT FROM globals` |
| **all** | UNION ALL of above queries |

### Qualified Name Construction

- **Function**: `module.function_name`
  - Example: `utils.helpers.calculate_total`
- **Method**: `module.ClassName.method_name`
  - Example: `models.user.User.__init__`
- **Class**: `module.ClassName`
  - Example: `models.user.User`
- **Import**: `module_name`
  - Example: `os.path`
- **Global**: `module.GLOBAL_NAME`
  - Example: `config.settings.DEBUG`

### Module Path Derivation

```python
def get_module_path(file_path: str) -> str:
    """Convert file path to module path.

    Example: 'src/models/user.py' -> 'models.user'
    """
    # Remove .py extension and convert / to .
    path = file_path.replace('.py', '').replace('/', '.')

    # Remove 'src.' prefix if present
    if path.startswith('src.'):
        path = path[4:]

    return path
```

---

## Deferred to Sprint 3+

The following features are **explicitly out of scope** for Sprint 2:

### Rendering Features (Sprint 3)
- `via render` command
- Syntax highlighting with Pygments
- Context lines (`-A`, `-B`, `-C` flags)
- Color scheme configuration

### Listing Features (Sprint 3)
- `via list` command
- Browse all entities by type

### Statistics Features (Sprint 3)
- `via stats` command
- Database statistics

### Output Formats (Sprint 3+)
- JSON output (`--format json`)
- CSV output (`--format csv`)
- JSON Lines output (`--format json_lines`)
- ASCII table output (`--format table`)

### Advanced Query Features (Sprint 4+)
- Boolean operators (AND, OR, NOT)
- Field-specific queries (docstring search)
- Cross-project queries
- Query history

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Ready for Sprint Planning (@Mouse)
**Next**: @Mouse create detailed task breakdown
