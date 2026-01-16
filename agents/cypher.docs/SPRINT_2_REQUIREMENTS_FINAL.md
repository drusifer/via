# Sprint 2 Requirements - Match Command

**Version**: 4.0 Final
**Date**: 2026-01-12
**Product Manager**: @Cypher
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 2 delivers the `via match` command for searching indexed entities. Users can specify **what to match against** (`--type`) and **the pattern to match** (using glob, regex, or SQL syntax).

**Core Concept**:
- `--type` = The field/entity type to match against (filename, filepath, method, class, function, import, global)
- Pattern syntax: `--glob`, `--regex`, or `--sql` (default: glob)
- Multiple type/pattern pairs combine with **AND** logic for precise filtering

**Out of Scope**:
- ❌ `via render` command (backlogged to Sprint 3)
- ❌ `via list` command (backlogged to Sprint 3)
- ❌ `via stats` command (backlogged to Sprint 3)
- ❌ Pipeline operators (backlogged to future sprint)

---

## 1. Core Design Principles

### Match Semantics

**`--type TYPE`**: Specifies what field to match against
- `filename` - Match against file name only (e.g., `matcher.py`)
- `filepath` - Match against full file path (e.g., `via/utils/matcher.py`)
- `method` - Match against method names
- `class` - Match against class names
- `function` - Match against function names (top-level, non-method)
- `import` - Match against import module names
- `global` - Match against global variable names

**Pattern SYNTAX**: Specifies the test value and syntax
- Pattern: The string pattern to match (positional argument)
- Syntax: `--glob` / `-g`, `--regex` / `-r`, or `--sql` / `-s` (default: glob)

**Multiple Filters**: When multiple `--type` and pattern pairs are provided, they combine with **AND** logic.

---

## 2. Command Syntax

### Basic Syntax

```bash
via match --type TYPE --SYNTAX 'PATTERN'
```

### Short Form

```bash
via match -t TYPE -SYNTAX 'PATTERN'
# Even shorter
via m -t TYPE -SYNTAX 'PATTERN'
```

### Multiple Type/Pattern Pairs (AND Logic)

```bash
via match --type TYPE1 --SYNTAX1 'PATTERN1' --type TYPE2 --SYNTAX2 'PATTERN2'
```

**Short form**:
```bash
via m -t TYPE1 -SYNTAX1 'PATTERN1' -t TYPE2 -SYNTAX2 'PATTERN2'
```

**Examples**:
```bash
# Single filter: find files in utils/
via m -t filepath -g '**/utils/*.py'

# Two filters (AND): find functions in utils/ files
via m -t filepath -g '**/utils/*.py' -t function -r '^calculate_.*'
```

---

## 3. Object Types

### Supported Types for `--type` Flag

| Type | Short | Matches Against | Database Source |
|------|-------|-----------------|-----------------|
| `filename` | `-t filename` | File name only | `files` table (basename of `file_path`) |
| `filepath` | `-t filepath` | Full file path | `files` table (`file_path` column) |
| `method` | `-t method` | Method names | `functions` table where `parent_entity_id IS NOT NULL` |
| `class` | `-t class` | Class names | `classes` table |
| `function` | `-t function` | Function names | `functions` table where `parent_entity_id IS NULL` |
| `import` | `-t import` | Import module names | `imports` table (`module_name` column) |
| `global` | `-t global` | Global variable names | `globals` table |

**Default**: If no `--type` specified, match against **all** entity name fields (method, class, function, import, global names - NOT files).

---

## 4. Match Syntax Types

### Three Supported Syntaxes

| Syntax | Long Flag | Short Flag | Description | Example Pattern |
|--------|-----------|------------|-------------|-----------------|
| **Glob** | `--glob` | `-g` | Shell-style wildcards (default) | `*ToString()` |
| **Regex** | `--regex` | `-r` | Regular expressions | `__.*__\(` |
| **SQL** | `--sql` | `-s` | SQL LIKE patterns | `%ToString()` |

**Default**: If no syntax flag provided, use `--glob`.

**Mutual Exclusivity**: Each `--match` clause can only have ONE syntax type.

### Glob Syntax (Default)

**Implementation**: Python `fnmatch` module + SQLite GLOB

**Wildcards**:
- `*` - Match zero or more characters
- `?` - Match exactly one character
- `[abc]` - Match any character in set
- `[!abc]` - Match any character NOT in set

**Examples**:
```bash
via m -t method -g '*ToString()'       # Methods ending with ToString()
via m -t filepath -g '**/utils/*.py'   # Files in any utils/ directory
via m -t class -g '[A-Z]*Model'        # Classes starting with capital + ending in Model
```

### Regex Syntax

**Implementation**: Python `re` module (with SQLite fallback or Python-side filtering)

**Examples**:
```bash
via m -t method -r '__.*__\('          # Magic methods
via m -t function -r '^test_.*'        # Test functions
via m -t class -r '^[A-Z][a-z]+$'      # Pascal case single-word classes
```

### SQL LIKE Syntax

**Implementation**: SQLite LIKE operator

**Wildcards**:
- `%` - Match zero or more characters
- `_` - Match exactly one character

**Examples**:
```bash
via m -t import -s '%os%'              # Imports containing "os"
via m -t global -s 'DEBUG%'            # Globals starting with DEBUG
```

---

## 5. Multiple Match Clauses (AND Logic)

### Syntax

**Long Form**:
```bash
via match --match --type TYPE1 --SYNTAX1 'PATTERN1' \
          --match --type TYPE2 --SYNTAX2 'PATTERN2'
```

**Short Form**:
```bash
via m -t TYPE1 -SYNTAX1 'PATTERN1' -t TYPE2 -SYNTAX2 'PATTERN2'
```

### How AND Logic Works

When multiple `--match` clauses are provided:
1. Each match clause filters independently
2. Results must satisfy **ALL** match clauses (intersection)
3. If match types differ (e.g., filename + method), we filter files first, then entities within those files

### Examples

**Example 1**: Match files in utils/ AND functions matching regex pattern
```bash
via m -t filepath -g '**/utils/*.py' -t function -r '^calculate_.*'
```

**SQL Logic**:
```sql
SELECT 'function' as type, f.file_path, fn.line_number, fn.name
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NULL                -- functions only
  AND f.file_path GLOB '**/utils/*.py'           -- first match clause
  AND fn.name REGEXP '^calculate_.*'             -- second match clause
```

**Example 2**: Match classes in models.py files
```bash
via m -t filename -g 'models.py' -t class -g '*User*'
```

**SQL Logic**:
```sql
SELECT 'class' as type, f.file_path, c.line_number, c.name
FROM classes c
JOIN files f ON c.file_id = f.id
WHERE f.file_path LIKE '%models.py'              -- first match (filename)
  AND c.name GLOB '*User*'                       -- second match (class name)
```

**Example 3**: Match test functions in test files
```bash
via m -t filepath -g 'tests/**/*.py' -t function -g 'test_*'
```

---

## 6. Additional Qualifiers

### Case Sensitivity

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--case-insensitive` | `-I` | Case-insensitive matching | `false` |

**Applies to**: All `--match` clauses in the query.

**Implementation**:
- **Glob/Regex**: Convert pattern and text to lowercase
- **SQL LIKE**: Use SQLite `LIKE` (case-insensitive) instead of `GLOB`

**Example**:
```bash
via m -t class -g 'user' -I          # Matches: User, USER, user, UsEr
```

### Result Limit

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--limit N` | `-n N` | Limit results to N items | `unlimited` |

**Example**:
```bash
via m -t method -g '*' -n 10         # First 10 methods
```

---

## 7. Output Format

### Simple Text Output (Sprint 2)

**Format**: `type:file_path:line_number:qualified_name`

**Fields**:
- `type` - Entity type (file, method, class, function, import, global)
- `file_path` - Relative path from project root
- `line_number` - Starting line number (0 for files)
- `qualified_name` - Fully qualified name

### Qualified Name Format

| Entity Type | Format | Example |
|-------------|--------|---------|
| **File** | `file_path` | `via/utils/matcher.py` |
| **Function** | `module.function_name` | `utils.matcher.calculate_total` |
| **Method** | `module.ClassName.method_name` | `utils.matcher.Helper.ToString` |
| **Class** | `module.ClassName` | `models.user.User` |
| **Import** | `module_name` | `os.path` |
| **Global** | `module.GLOBAL_NAME` | `config.settings.DEBUG` |

### Example Output

```bash
$ via m -t filepath -g '**/utils/matcher*.py' -t function -r '__.*__'

file:via/utils/matcher.py:0:via/utils/matcher.py
function:via/utils/matcher.py:45:utils.matcher.__init__
function:via/utils/matcher.py:67:utils.matcher.__str__
```

```bash
$ via m -t method -g '*ToString()'

method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

### No Header/Footer

Output is **streaming** (grep-style) for piping:
- ✅ One result per line
- ❌ No header (e.g., "Found 3 results")
- ❌ No footer (e.g., "Total: 3")

---

## 8. Command-Line Flag Summary

### Primary Flags

| Long Flag | Short | Description | Example |
|-----------|-------|-------------|---------|
| `--type TYPE` | `-t TYPE` | What to match against | `-t method`, `-t filepath` |

### Syntax Flags (mutually exclusive per match clause)

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--glob` | `-g` | Glob pattern (default) |
| `--regex` | `-r` | Regex pattern |
| `--sql` | `-s` | SQL LIKE pattern |

### Qualifier Flags

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--case-insensitive` | `-I` | Case-insensitive matching |
| `--limit N` | `-n N` | Limit results to N items |

### Global Flags (inherited from CLI)

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--verbose` | `-v` | Increase verbosity |
| `--quiet` | `-q` | Suppress output |
| `--db PATH` | (none) | Custom database path |

---

## 9. Implementation Architecture

### Pattern Matcher Interface

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
```

### Query Service Architecture

```python
from dataclasses import dataclass
from typing import Iterator, List

@dataclass
class MatchClause:
    """Represents a single match clause."""
    type: str           # filename, filepath, method, class, function, import, global
    pattern: str        # The pattern to match
    syntax: str         # glob, regex, sql

@dataclass
class QueryResult:
    """Represents a single query result."""
    type: str           # Entity type
    file_path: str      # Relative file path
    line_number: int    # Starting line number
    qualified_name: str # Fully qualified name

class QueryService:
    """Service for querying indexed entities."""

    def query(
        self,
        match_clauses: List[MatchClause],
        case_sensitive: bool = True,
        limit: int = None
    ) -> Iterator[QueryResult]:
        """Execute query with multiple match clauses (AND logic).

        Yields results one at a time (streaming).
        """
        # Build dynamic SQL query based on match clauses
        sql = self._build_query(match_clauses, case_sensitive, limit)

        # Execute and yield results
        for row in self.db.execute(sql):
            yield self._row_to_result(row)

    def _build_query(self, match_clauses: List[MatchClause], case_sensitive: bool, limit: int) -> str:
        """Build SQL query from match clauses."""
        # Complex logic to combine multiple match types with AND
        pass
```

### CLI Argument Parsing

```python
# Match command parser
match_parser = subparsers.add_parser('match', aliases=['m'], help='Search indexed entities')

# Type and pattern are paired - use action='append' for multiple filters
match_parser.add_argument('-t', '--type', action='append',
                          choices=['filename', 'filepath', 'method', 'class', 'function', 'import', 'global'],
                          help='Type to match against')

# Syntax flags (mutually exclusive per type/pattern pair in implementation)
match_parser.add_argument('-g', '--glob', action='store_true', help='Use glob pattern (default)')
match_parser.add_argument('-r', '--regex', action='store_true', help='Use regex pattern')
match_parser.add_argument('-s', '--sql', action='store_true', help='Use SQL LIKE pattern')

# Qualifiers
match_parser.add_argument('-I', '--case-insensitive', action='store_true', help='Case-insensitive matching')
match_parser.add_argument('-n', '--limit', type=int, help='Limit results to N items')

# Pattern (positional, multiple allowed)
match_parser.add_argument('pattern', nargs='*', help='Pattern to match')
```

---

## 10. User Stories (Revised)

### Story 1: Pattern Matcher Foundation (3 pts, 6h)

**Acceptance Criteria**:
- [ ] Create `PatternMatcher` ABC
- [ ] Implement `GlobMatcher`
- [ ] Implement `SqlLikeMatcher`
- [ ] Create `MatcherRegistry`
- [ ] Support case-sensitive/insensitive modes
- [ ] 15 unit tests (100% coverage)

### Story 2: Query Service Layer (5 pts, 10h)

**Acceptance Criteria**:
- [ ] Create `QueryService` class
- [ ] Support all object types (filename, filepath, method, class, function, import, global)
- [ ] Support multiple match clauses with AND logic
- [ ] Build dynamic SQL queries
- [ ] Construct qualified names
- [ ] Yield results as generator (streaming)
- [ ] 20 unit tests (90% coverage)

### Story 3: CLI Match Command (3 pts, 6h)

**Acceptance Criteria**:
- [ ] Implement `via match` subcommand (with `m` alias)
- [ ] Support multiple `-t` flags for type/pattern pairs
- [ ] Support all type options (`-t filename`, `-t method`, etc.)
- [ ] Support all syntax flags (`-g`, `-r`, `-s`)
- [ ] Support qualifiers (`-I`, `-n`)
- [ ] Format output as `type:file_path:line_number:qualified_name`
- [ ] Stream output (no header/footer)
- [ ] 12 integration tests

### Story 4: Regex Matcher (Optional - 3 pts, 6h)

**Acceptance Criteria**:
- [ ] Implement `RegexMatcher`
- [ ] Support full Python regex syntax
- [ ] Performance < 1s for 10k entities
- [ ] 5 unit tests

**Total**: 11 P0 points (22h), 14 total points (28h)

---

## 11. Example Usage

### Single Match Clause

```bash
# Find methods ending with ToString()
via m -t method -g '*ToString()'

# Find files in utils/ directory
via m -t filepath -g '**/utils/*.py'

# Find classes starting with "User" (case-insensitive)
via m -t class -g 'User*' -I

# Find imports containing "os" (SQL LIKE)
via m -t import -s '%os%'

# Find magic methods (regex)
via m -t method -r '__.*__\('
```

### Multiple Match Clauses (AND Logic)

```bash
# Find functions in utils/ files
via m -t filepath -g '**/utils/*.py' -t function -g '*'

# Find test functions in test files
via m -t filepath -g 'tests/**/*.py' -t function -g 'test_*'

# Find User classes in models.py files
via m -t filename -g 'models.py' -t class -g '*User*'

# Find magic methods in utils/ (complex)
via m -t filepath -g '**/utils/*.py' -t method -r '__.*__\('
```

### With Qualifiers

```bash
# Case-insensitive search for classes
via m -t class -g 'user' -I

# Limit to first 10 results
via m -t method -g 'calculate*' -n 10

# Case-insensitive, limited, multiple matches
via m -t filepath -g '**/models/*.py' -t class -g '*user*' -I -n 5
```

### Piping Results

```bash
# Pipe to less for browsing
via m -t function -g 'test_*' | less

# Count results
via m -t method -g '*' | wc -l

# Filter with grep
via m -t class -g '*' | grep 'Model'
```

---

## 12. Success Criteria

Sprint 2 is **DONE** when:

1. ✅ Users can match against any object type (filename, filepath, method, class, function, import, global)
2. ✅ Users can specify patterns with glob, regex, or SQL LIKE syntax
3. ✅ Users can combine multiple match clauses with AND logic
4. ✅ Files are treated as object types (no separate file filter)
5. ✅ Output format: `type:file_path:line_number:qualified_name`
6. ✅ Results stream for piping
7. ✅ Case-insensitive mode works (`-I`)
8. ✅ Result limiting works (`-n`)
9. ✅ All tests pass (47 total: 15 matcher + 20 service + 12 CLI)
10. ✅ Test coverage > 80%
11. ✅ Documentation updated

---

## 13. Backlog (Future Sprints)

### Sprint 3 Backlog
- `via render` command with syntax highlighting
- `via list` command for browsing entities
- `via stats` command for database statistics
- Context lines (`-A`, `-B`, `-C` flags)
- Color scheme configuration
- Multiple output formats (JSON, CSV, table)

### Sprint 4+ Backlog
- Pipeline operators (OR, NOT)
- Field-specific queries (docstring search)
- Boolean query syntax
- Cross-project queries
- Query history

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Final - Ready for Implementation
**Next**: @Morpheus technical review, @Mouse sprint planning
