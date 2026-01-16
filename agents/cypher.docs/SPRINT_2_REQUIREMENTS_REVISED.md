# Sprint 2 Requirements - Query Command (Match-Style Filtering)

**Version**: 2.0 (Revised Scope)
**Date**: 2026-01-12
**Product Manager**: @Cypher
**Status**: Ready for Technical Review (@Morpheus)

---

## Executive Summary

Sprint 2 is now **narrowly focused** on implementing the `via query` command with match-style filtering only. All rendering, listing, and stats functionality is **deferred to future sprints**.

**Core Goal**: Enable users to search indexed entities using pattern matching with flexible syntax options.

**Out of Scope for Sprint 2**:
- ❌ `via render` command (deferred to Sprint 3)
- ❌ `via list` command (deferred to Sprint 3)
- ❌ `via stats` command (deferred to Sprint 3)
- ❌ Syntax highlighting (deferred to Sprint 3)
- ❌ Context lines (-A/-B/-C flags) (deferred to Sprint 3)
- ❌ Multiple output formats (json, csv, etc.) (deferred to Sprint 3)

---

## 1. Query Command Overview

### Purpose

Search indexed code entities using pattern matching with:
1. **Match Syntax Selection**: Choose between glob, regex, or SQL LIKE patterns
2. **Object Type Filtering**: Filter by specific entity types (method, class, function, import, global)
3. **Standard Qualifiers**: Case sensitivity, limit, file path filters

### Command Syntax

```bash
# Long form with explicit flags
via query --match <PATTERN> --glob --method --case-insensitive

# Short form (preferred)
via -qMmg '<PATTERN>'
```

**Key Design Principle**: The `-M` (match mode) flag is the primary mode for Sprint 2.

---

## 2. Match Syntax Types

### Three Supported Syntaxes

| Syntax | Long Flag | Short Flag | Description | Example |
|--------|-----------|------------|-------------|---------|
| **Glob** | `--glob` | `-g` | Shell-style wildcards | `*ToString()` |
| **Regex** | `--regex` | `-r` | Regular expressions | `.*ToString\(\)$` |
| **SQL** | `--sql` | `-s` | SQL LIKE patterns | `%ToString()` |

**Default**: If no syntax flag provided, use `--glob` (most user-friendly)

**Mutual Exclusivity**: Only ONE syntax type can be specified per query

### Glob Syntax (Default)

**Implementation**: Python `fnmatch` module

**Supported Wildcards**:
- `*` - Match zero or more characters
- `?` - Match exactly one character
- `[abc]` - Match any character in set
- `[!abc]` - Match any character NOT in set

**Examples**:
```bash
via -qMmg '*ToString()'       # Any method ending with ToString()
via -qMmg 'get*'              # Any entity starting with "get"
via -qMmg 'calculate_???'     # calculate_ followed by exactly 3 chars
via -qMmg '[A-Z]*'            # Starts with uppercase letter
```

### Regex Syntax

**Implementation**: Python `re` module

**Supported Patterns**: Full Python regex syntax

**Examples**:
```bash
via -qMmr '.*ToString\(\)$'           # Methods ending with ToString()
via -qMmr '^get[A-Z][a-z]+'           # getXxx pattern (camelCase)
via -qMmr '__(init|str|repr)__'       # Magic methods
via -qMmr '^test_.*'                  # Test functions
```

### SQL LIKE Syntax

**Implementation**: SQLite LIKE operator (database-native)

**Supported Wildcards**:
- `%` - Match zero or more characters (equivalent to `*` in glob)
- `_` - Match exactly one character (equivalent to `?` in glob)

**Examples**:
```bash
via -qMms '%ToString()'       # Methods ending with ToString()
via -qMms 'get%'              # Starts with "get"
via -qMms 'calculate___'      # calculate followed by exactly 3 chars
```

**Note**: SQL LIKE is the most efficient (database-native) but least expressive.

---

## 3. Object Type Filters

### Supported Entity Types

| Type | Long Flag | Short Flag | Database Mapping | Description |
|------|-----------|------------|------------------|-------------|
| **Method** | `--method` | `-m` | `functions` table where `parent_entity_id IS NOT NULL` | Class methods |
| **Class** | `--class` | `-c` | `classes` table | Class definitions |
| **Function** | `--function` | `-f` | `functions` table where `parent_entity_id IS NULL` | Top-level functions |
| **Import** | `--import` | `-i` | `imports` table | Import statements |
| **Global** | `--global` | `-G` | `globals` table | Global variables |
| **All** | (default) | (none) | All tables | All entity types |

**Default Behavior**: If no type flags specified, search ALL entity types.

**Multiple Types Allowed**: Users can specify multiple type filters.

**Examples**:
```bash
# Search only methods
via -qMm -g '*ToString()'

# Search methods AND functions
via -qMmf -g 'calculate*'

# Search classes AND imports
via -qMci -g '*User*'

# Search all types (default - no type flags)
via -qM -g 'get*'
```

### Query Logic for Multiple Types

When multiple type flags are specified, use **OR logic**:

```sql
SELECT * FROM (
    SELECT ... FROM functions WHERE parent_entity_id IS NOT NULL  -- methods
    UNION ALL
    SELECT ... FROM functions WHERE parent_entity_id IS NULL      -- functions
) WHERE name LIKE '%pattern%'
```

---

## 4. Standard Qualifiers

### Case Sensitivity

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--case-insensitive` | `-I` | Case-insensitive matching | `false` (case-sensitive) |

**Implementation**:
- **Glob/Regex**: Convert both pattern and text to lowercase before matching
- **SQL LIKE**: Use `LIKE` (case-insensitive) instead of `GLOB` (case-sensitive)

**Examples**:
```bash
# Case-sensitive (default)
via -qMmg 'ToString'      # Matches: ToString, but NOT tostring

# Case-insensitive
via -qMmgI 'ToString'     # Matches: ToString, tostring, TOSTRING, etc.
```

### Result Limit

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--limit N` | `-n N` | Limit results to N items | `unlimited` |

**Implementation**: SQL `LIMIT` clause

**Examples**:
```bash
# Get first 10 matches
via -qMmg '*ToString()' -n 10

# Get first 100 matches
via -qMmg 'get*' --limit 100
```

### File Path Filter

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--file PATTERN` | `-F PATTERN` | Filter by file path (glob pattern) | `*` (all files) |

**Implementation**: Apply glob pattern to `file_path` column

**Examples**:
```bash
# Search only in src/ directory
via -qMmg '*ToString()' -F 'src/**/*.py'

# Search in models.py files
via -qMmg 'User' -F '**/models.py'

# Search in test files
via -qMmg 'test_*' -F 'tests/**/*.py'
```

---

## 5. Command-Line Interface

### Primary Mode: Match Mode (`-M`)

The `-M` flag activates "match mode" for the query command.

### Full Syntax Breakdown

```bash
via [GLOBAL_FLAGS] query [QUERY_FLAGS] --match <PATTERN> [MATCH_SYNTAX] [TYPE_FILTERS] [QUALIFIERS]
```

**Simplified with short flags**:
```bash
via -q -M [TYPE_FLAGS] [SYNTAX_FLAG] [QUALIFIERS] '<PATTERN>'
```

**Ultra-short form** (combining short flags):
```bash
via -qMmg '<PATTERN>'
```

### Flag Categories

#### Global Flags (apply to all commands)
- `-v` / `--verbose` - Increase verbosity
- `-q` / `--quiet` - Suppress output
- `--db PATH` - Custom database path

#### Query Mode Flags
- `-M` / `--match` - Enable match mode (required for Sprint 2)

#### Match Syntax Flags (mutually exclusive)
- `-g` / `--glob` - Glob pattern (default)
- `-r` / `--regex` - Regex pattern
- `-s` / `--sql` - SQL LIKE pattern

#### Type Filter Flags (combinable with OR logic)
- `-m` / `--method` - Search methods only
- `-c` / `--class` - Search classes only
- `-f` / `--function` - Search functions only
- `-i` / `--import` - Search imports only
- `-G` / `--global` - Search globals only
- (none) - Search all types (default)

#### Qualifier Flags
- `-I` / `--case-insensitive` - Case-insensitive matching
- `-n N` / `--limit N` - Limit results to N items
- `-F PATTERN` / `--file PATTERN` - Filter by file path

### Examples

```bash
# Find all methods ending with ToString()
via -qMmg '*ToString()'

# Find classes named User (case-insensitive) with regex
via -qMcrI '^user$'

# Find functions starting with "test_" in test files
via -qMfg 'test_*' -F 'tests/**/*.py'

# Find first 10 imports containing "os" (SQL LIKE)
via -qMis '%os%' -n 10

# Find methods OR functions matching "calculate" pattern
via -qMmfg 'calculate*'

# Case-insensitive search for classes containing "model"
via -qMcgI '*model*'
```

---

## 6. Output Format (Sprint 2 - Text Only)

### Simple Text Output

For Sprint 2, output will be **simple, plain text** with one result per line.

### Output Schema

Each result line contains:
```
<type>:<file_path>:<line_number>:<qualified_name>
```

**Fields**:
- `type` - Entity type (method, class, function, import, global)
- `file_path` - Relative path from project root
- `line_number` - Starting line number
- `qualified_name` - Fully qualified name (see section 7)

### Example Output

```bash
$ via -qMmg '*ToString()'

method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

```bash
$ via -qMcg 'User*'

class:src/models/user.py:10:models.user.User
class:src/models/user.py:89:models.user.UserProfile
class:tests/test_user.py:5:tests.test_user.UserTestCase
```

### No Header/Footer (Sprint 2)

To support piping, Sprint 2 output has:
- ❌ No header (e.g., "Found 3 results")
- ❌ No footer (e.g., "Total: 3 matches")
- ✅ Only result lines (grep-style)

**Future**: Add `--no-header` / `--no-footer` flags for fine control.

---

## 7. Fully Qualified Names

### Purpose

Disambiguate entities with the same name across different modules/classes.

### Qualification Rules

| Entity Type | Qualification Format | Example |
|-------------|---------------------|---------|
| **Module-level Function** | `module.function_name` | `utils.helpers.calculate_total` |
| **Class** | `module.ClassName` | `models.user.User` |
| **Method** | `module.ClassName.method_name` | `models.user.User.__init__` |
| **Import** | `imported_module` | `os.path` |
| **Global** | `module.GLOBAL_NAME` | `config.settings.DEBUG` |

### Implementation

Qualified names are constructed by:
1. Getting the module path from the file path (e.g., `src/models/user.py` → `models.user`)
2. Appending the class name (if applicable)
3. Appending the entity name

**Note**: The `files` table already stores `file_path` (relative path). We can derive the module path by:
```python
def get_module_path(file_path: str) -> str:
    """Convert file path to module path."""
    # Remove .py extension and convert / to .
    return file_path.replace('/', '.').replace('.py', '')
```

**Database Consideration**: May want to add a `qualified_name` column to entity tables for efficiency.

---

## 8. Query Service Architecture

### Service Layer

Create a new `QueryService` class in `via/services/query_service.py`.

**Responsibilities**:
1. Accept query parameters (pattern, syntax, types, qualifiers)
2. Validate parameters
3. Build SQL query dynamically based on filters
4. Execute query against database
5. Yield results one at a time (generator pattern)

### Pattern Matcher Interface

Create pluggable pattern matchers for extensibility:

```python
from abc import ABC, abstractmethod

class PatternMatcher(ABC):
    """Abstract base class for pattern matchers."""

    @abstractmethod
    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        """Convert pattern to SQL WHERE clause."""
        pass

    @abstractmethod
    def matches(self, pattern: str, text: str, case_sensitive: bool) -> bool:
        """Test if text matches pattern (for validation)."""
        pass

class GlobMatcher(PatternMatcher):
    """Glob-style pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        if case_sensitive:
            return f"{column} GLOB '{pattern}'"
        else:
            return f"LOWER({column}) GLOB '{pattern.lower()}'"

class RegexMatcher(PatternMatcher):
    """Regex pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        # SQLite has limited regex support - may need to fetch all and filter in Python
        # For now, use LIKE as fallback or enable regex extension
        raise NotImplementedError("Regex requires SQLite regex extension or Python filtering")

class SqlLikeMatcher(PatternMatcher):
    """SQL LIKE pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        if case_sensitive:
            # SQLite LIKE is case-insensitive by default, use GLOB for case-sensitive
            return f"{column} GLOB '{pattern.replace('%', '*').replace('_', '?')}'"
        else:
            return f"{column} LIKE '{pattern}'"
```

### Query Builder

The `QueryService` dynamically builds SQL queries based on:
1. **Entity types selected**: UNION queries across tables
2. **Pattern matcher**: WHERE clause from matcher
3. **File filter**: Additional WHERE clause on `file_path`
4. **Limit**: SQL LIMIT clause

**Example Generated SQL** (for `via -qMmg '*ToString()' -n 10`):

```sql
-- Query methods only
SELECT
    'method' as type,
    f.file_path,
    fn.line_number,
    fn.name,
    fn.parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NOT NULL
  AND fn.name GLOB '*ToString()'
ORDER BY f.file_path, fn.line_number
LIMIT 10
```

**Example for Multiple Types** (`via -qMmfg 'calculate*'`):

```sql
-- Union of methods and functions
SELECT 'method' as type, f.file_path, fn.line_number, fn.name, fn.parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NOT NULL AND fn.name GLOB 'calculate*'

UNION ALL

SELECT 'function' as type, f.file_path, fn.line_number, fn.name, NULL as parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NULL AND fn.name GLOB 'calculate*'

ORDER BY file_path, line_number
LIMIT <limit_value>
```

---

## 9. Implementation Tasks

### Story 1: Pattern Matcher Foundation (3 pts, 6h)

**Tasks**:
1. Create `PatternMatcher` ABC in `via/core/pattern_matcher.py`
2. Implement `GlobMatcher` class
3. Implement `SqlLikeMatcher` class
4. Create `MatcherRegistry` for pattern matcher lookup
5. Write 15 unit tests (5 per matcher)

**Acceptance Criteria**:
- ✅ All matchers generate correct SQL clauses
- ✅ Case-sensitive and case-insensitive variants work
- ✅ Unit tests pass with 100% coverage

### Story 2: Query Service Layer (5 pts, 10h)

**Tasks**:
1. Create `QueryService` class in `via/services/query_service.py`
2. Implement `query()` method with generator pattern
3. Add support for entity type filters (method, class, function, import, global)
4. Add support for file path filters
5. Add support for result limits
6. Build dynamic SQL queries using pattern matchers
7. Handle qualified name construction
8. Write 20 unit tests

**Acceptance Criteria**:
- ✅ Can query by single entity type
- ✅ Can query by multiple entity types (OR logic)
- ✅ File path filtering works
- ✅ Result limiting works
- ✅ Qualified names constructed correctly
- ✅ Yields results one at a time (streaming)

### Story 3: CLI Query Command (3 pts, 6h)

**Tasks**:
1. Add `query` subcommand to `via/__main__.py`
2. Implement match mode (`-M` / `--match`)
3. Add syntax flags (`-g`, `-r`, `-s`)
4. Add type filter flags (`-m`, `-c`, `-f`, `-i`, `-G`)
5. Add qualifier flags (`-I`, `-n`, `-F`)
6. Wire `QueryService` to CLI
7. Format and print results
8. Write 12 integration tests

**Acceptance Criteria**:
- ✅ All flag combinations work correctly
- ✅ Short flags combine properly (e.g., `-qMmg`)
- ✅ Output format matches specification
- ✅ Error messages are clear and helpful
- ✅ Integration tests pass

### Story 4: Regex Matcher (Optional - 3 pts, 6h)

**Tasks**:
1. Research SQLite regex extension options
2. Implement `RegexMatcher` (possibly with Python fallback)
3. Add unit tests for regex patterns
4. Update CLI to support `-r` flag

**Acceptance Criteria**:
- ✅ Regex patterns work correctly
- ✅ Performance is acceptable (< 1s for 10k entities)

---

## 10. Success Criteria

Sprint 2 is **DONE** when:

1. ✅ Users can search for entities using glob patterns (`-g`)
2. ✅ Users can search for entities using SQL LIKE patterns (`-s`)
3. ✅ Users can filter by entity type (method, class, function, import, global)
4. ✅ Users can filter by file path
5. ✅ Users can limit results with `-n` flag
6. ✅ Users can toggle case sensitivity with `-I` flag
7. ✅ Output shows: type, file path, line number, qualified name
8. ✅ All short flags work (`-qMmg`, `-qMcr`, etc.)
9. ✅ Results stream (generator pattern) for piping
10. ✅ 47 unit tests pass (15 matcher + 20 service + 12 CLI)
11. ✅ Test coverage > 80%
12. ✅ Documentation updated

**Nice to Have** (Optional):
- ✅ Regex matcher implemented (`-r` flag)

---

## 11. Out of Scope (Deferred to Sprint 3+)

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
- JSON output (`-F json`)
- CSV output (`-F csv`)
- JSON Lines output (`-F json_lines`)
- ASCII table output (`-F ascii_table`)

### Advanced Query Features (Sprint 4+)
- Boolean query operators (AND, OR, NOT)
- Field-specific queries (e.g., search by docstring)
- Cross-project queries
- Query history

---

## 12. Database Schema Notes

### Current Schema (From Sprint 1)

The existing schema supports all required queries:

**Files Table**:
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL
);
```

**Functions Table** (includes both functions AND methods):
```sql
CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    end_line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    parent_entity_id INTEGER,  -- NULL for functions, set for methods
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Classes Table**:
```sql
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    end_line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Imports Table**:
```sql
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    imported_names TEXT,  -- JSON array
    line_number INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Globals Table**:
```sql
CREATE TABLE globals (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

### Potential Optimization: Add Qualified Name Column

**Consideration**: For performance, we could add a `qualified_name` column to each entity table. This would avoid runtime computation.

**Recommendation**: Start without it. Add it if profiling shows it's a bottleneck.

**Migration Query** (if needed later):
```sql
-- Add qualified_name column to functions table
ALTER TABLE functions ADD COLUMN qualified_name TEXT;

-- Populate it (pseudo-code)
UPDATE functions
SET qualified_name = (
    SELECT replace(replace(file_path, '/', '.'), '.py', '') || '.' ||
           CASE
               WHEN parent_entity_id IS NOT NULL THEN (SELECT name FROM classes WHERE id = parent_entity_id) || '.' || name
               ELSE name
           END
    FROM files WHERE id = functions.file_id
);
```

---

## 13. Testing Strategy

### Unit Tests (35 tests)

**Pattern Matchers** (15 tests):
- 5 tests for GlobMatcher (pattern conversion, case sensitivity, edge cases)
- 5 tests for SqlLikeMatcher
- 5 tests for RegexMatcher (if implemented)

**Query Service** (20 tests):
- 5 tests for single entity type queries
- 5 tests for multiple entity type queries
- 3 tests for file path filtering
- 3 tests for result limiting
- 4 tests for qualified name construction

### Integration Tests (12 tests)

**CLI Tests** (12 tests):
- Test glob pattern matching
- Test SQL LIKE pattern matching
- Test entity type filtering (each type individually)
- Test multiple entity types (OR logic)
- Test file path filtering
- Test result limiting
- Test case-insensitive flag
- Test combined short flags (`-qMmg`)
- Test error handling (invalid pattern, no results)
- Test output format (verify each field)

### Test Coverage Target

**Goal**: > 80% coverage for new code

**Critical Areas**:
- QueryService: 100% coverage
- Pattern matchers: 100% coverage
- CLI query subcommand: > 90% coverage

---

## 14. Documentation Requirements

### User-Facing Documentation

1. **README.md**: Update with `via query` examples
2. **USAGE.md**: Create detailed usage guide with all flag combinations

### Developer Documentation

1. **ARCHITECTURE.md**: Document QueryService and pattern matcher architecture
2. **API.md**: Document QueryService public API for future integrations

### Inline Documentation

1. **Docstrings**: All public methods must have docstrings
2. **TLDR sections**: Follow Oracle's template for all new files

---

## 15. Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Simple query (< 100 results) | < 100ms | `via -qMmg 'User' -n 100` |
| Complex query (< 1000 results) | < 500ms | `via -qMmfg 'test_*'` |
| Large query (< 10k results) | < 2s | `via -qMg '*'` (all entities) |

**Optimization Strategy**:
1. Use database indexes on `name` columns
2. Use SQL GLOB/LIKE natively (avoid Python filtering)
3. Stream results (generator pattern) to avoid memory overhead

---

## Next Steps

1. **@Morpheus**: Review architecture, suggest optimizations, validate SQL query generation strategy
2. **@Mouse**: Create detailed task breakdown from 4 stories
3. **@Neo**: Implement stories in priority order (1 → 2 → 3 → 4)
4. **@Trin**: Create test plan and acceptance criteria checklist

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Ready for Technical Review
**Review Date**: 2026-01-12
