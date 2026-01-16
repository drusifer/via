# Match Command Architecture (Denormalized)

**Created**: 2026-01-13
**Architect**: @Morpheus
**Status**: Ready for Implementation
**Version**: 5.0 (Denormalized Schema)

---

## Design Principles

1. **Denormalized Match Table**: Single `symbols` table eliminates JOINs
2. **Trivial Queries**: Direct WHERE clauses, no templates needed
3. **Enums for Context**: SymbolType and MatchOp provide lookup values
4. **Complete Results**: Include byte_offset and byte_length
5. **References Table**: Separate table for relationship queries (future)

---

## Key Simplification

**Old Design (v4.0)**: Multiple normalized tables (functions, classes, imports, etc.) requiring complex JOINs and SQL templates for each symbol type.

**New Design (v5.0)**: Single denormalized `symbols` table. All queries use the same simple pattern:

```sql
SELECT * FROM symbols
WHERE symbol_type = ?
  AND symbol_name {match_op} ?
```

**Benefit**: Zero JOINs, zero templates, trivial query construction.

---

## Database Schema

### Symbols Table (Denormalized)

```sql
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_name TEXT NOT NULL,           -- The symbol name (e.g., "calculate_sum", "MyClass")
    symbol_type TEXT NOT NULL,           -- Type: method, class, function, filepath, filename, import, global
    file_path TEXT NOT NULL,             -- Full relative path to file
    line_number INTEGER NOT NULL,        -- Starting line number
    byte_offset INTEGER,                 -- Byte offset in file (NULL for files)
    byte_length INTEGER,                 -- Symbol byte length (NULL for files)
    qualified_name TEXT NOT NULL,        -- Fully qualified name (e.g., "models.user.User.save")
    parent_name TEXT,                    -- Parent class name for methods (NULL otherwise)

    -- Indexes for fast queries
    INDEX idx_symbols_name ON symbols(symbol_name),
    INDEX idx_symbols_type ON symbols(symbol_type),
    INDEX idx_symbols_type_name ON symbols(symbol_type, symbol_name),
    INDEX idx_symbols_file ON symbols(file_path)
);
```

### References Table (For Future Relationship Queries)

```sql
CREATE TABLE references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol_id INTEGER NOT NULL,     -- Symbol that makes the reference
    to_symbol_id INTEGER NOT NULL,       -- Symbol being referenced
    reference_type TEXT NOT NULL,        -- Type: calls, imports, inherits, instantiates
    line_number INTEGER,        -- Where the reference occurs

    FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    FOREIGN KEY (to_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,

    INDEX idx_references_from ON references(from_symbol_id),
    INDEX idx_references_to ON references(to_symbol_id),
    INDEX idx_references_type ON references(reference_type)
);
```

**Note**: The `references` table is for future complex queries like "find all callers of function X" or "show inheritance tree." The `match` command only uses the `symbols` table.

### Files Table (Kept for Metadata)

The existing `files` table is retained for tracking file metadata (mtime, size, parsed status, etc.) but is NOT used by the match command:

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    language TEXT,
    size_bytes INTEGER,
    mtime REAL,
    indexed_at REAL,
    parsed BOOLEAN DEFAULT 0,
    oversized BOOLEAN DEFAULT 0
);
```

---

## Example Data

| symbol_name | symbol_type | file_path | line_number | byte_offset | byte_length | qualified_name | parent_name |
|-------------|-------------|-----------|-------------|-------------|-------------|----------------|-------------|
| calculate_sum | function | src/utils.py | 42 | 1250 | 85 | utils.calculate_sum | NULL |
| User | class | src/models/user.py | 15 | 450 | 320 | models.user.User | NULL |
| save | method | src/models/user.py | 45 | 1234 | 56 | models.user.User.save | User |
| utils.py | filename | src/utils.py | 0 | NULL | NULL | src/utils.py | NULL |
| src/utils.py | filepath | src/utils.py | 0 | NULL | NULL | src/utils.py | NULL |
| json | import | src/utils.py | 1 | 0 | 11 | json | NULL |
| MAX_LIMIT | global | src/config.py | 5 | 120 | 15 | config.MAX_LIMIT | NULL |

---

## Streamlined Architecture

```
┌─────────────┐
│   CLI       │  via match -t method -g '*save()'
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Parse Args         │  Convert to SymbolType + MatchOp enums
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  DatabaseStore      │  db.match(symbol_type, match_op, pattern)
│  .match()           │  → Simple WHERE clause
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  SQLite             │  SELECT * FROM symbols WHERE ...
└─────────────────────┘
```

**Key**: Zero JOINs, zero templates, zero complexity.

---

## Core Types

### SymbolType Enum

**File**: `via/core/types.py`

```python
from enum import Enum


class SymbolType(Enum):
    """Entity types that can be matched.

    Each enum value corresponds to a symbol_type in the database.
    """

    METHOD = 'method'
    CLASS = 'class'
    FUNCTION = 'function'
    FILEPATH = 'filepath'
    FILENAME = 'filename'
    IMPORT = 'import'
    GLOBAL = 'global'
```

**Simplified!** No more table/column/has_byte_offset attributes. Just the type name.

### MatchOp Enum

**File**: `via/core/types.py`

```python
class MatchOp(Enum):
    """Match operators that map to SQL operators.

    Each enum provides:
    - sql_op: The SQL operator to use
    - needs_escaping: Whether pattern needs SQL escaping
    """

    # (value, sql_operator, needs_escaping)
    EXACT = ('exact', '=', True)
    GLOB = ('glob', 'GLOB', True)
    LIKE = ('like', 'LIKE', True)
    REGEXP = ('regexp', 'REGEXP', True)

    def __init__(self, op_name, sql_op, needs_escaping):
        self.op_name = op_name
        self.sql_op = sql_op
        self.needs_escaping = needs_escaping
```

### MatchResult Dataclass

**File**: `via/core/types.py`

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class MatchResult:
    """Single match result with complete position information."""
    symbol_type: str               # Entity type (method, class, function, etc.)
    symbol_name: str               # Simple name
    qualified_name: str            # Fully qualified name
    file_path: str                 # Relative file path
    line_number: Optional[int]               # Starting line number
    byte_offset: Optional[int]     # File byte offset (None for files)
    byte_length: Optional[int]     # Entity byte length (None for files)
    parent_name: Optional[str]     # Parent class name (None for non-methods)
```

---

## DatabaseStore.match() Method

**File**: `via/db/store.py`

The database layer is now TRIVIALLY simple - no templates, just direct queries:

```python
from typing import Iterator, Optional
from via.core.types import SymbolType, MatchOp, MatchResult


class DatabaseStore:
    """Database store with denormalized symbols table."""

    def match(
        self,
        symbol_type: SymbolType,
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool = True,
        limit: Optional[int] = None
    ) -> Iterator[MatchResult]:
        """Match symbols using denormalized table.

        Args:
            symbol_type: SymbolType enum value
            match_op: MatchOp enum value
            pattern: Pattern to match (user provides wildcards/regex)
            case_sensitive: Whether matching is case-sensitive
            limit: Optional result limit

        Yields:
            MatchResult objects with complete position data

        Example:
            for result in db.match(SymbolType.METHOD, MatchOp.GLOB, '*save()'):
                print(f"{result.qualified_name} at byte {result.byte_offset}")
        """
        # Build WHERE clause
        where_parts = ["symbol_type = ?"]
        params = [symbol_type.value]

        # Add name match clause
        column = "symbol_name"
        if not case_sensitive:
            column = "LOWER(symbol_name)"
            pattern = pattern.lower()

        # Escape pattern if needed
        if match_op.needs_escaping:
            pattern = pattern.replace("'", "''")

        where_parts.append(f"{column} {match_op.sql_op} ?")
        params.append(pattern)

        # Build query
        query = f"""
            SELECT
                symbol_name,
                symbol_type,
                file_path,
                line_number,
                byte_offset,
                byte_length,
                qualified_name,
                parent_name
            FROM symbols
            WHERE {' AND '.join(where_parts)}
            ORDER BY file_path, line_number
        """

        # Add limit if specified
        if limit:
            query += f"\nLIMIT {limit}"

        # Execute and yield results
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

**That's it!** No templates, no type-specific logic, just a simple WHERE clause.

---

## CLI Integration

**File**: `via/__main__.py`

```python
from via.core.types import SymbolType, MatchOp


def handle_match_command(args):
    """Handle via match command.

    Example:
        via m -t method -g '*save()'
    """
    # Determine match operator from flags
    if args.regex:
        match_op = MatchOp.REGEXP
    elif args.sql:
        match_op = MatchOp.LIKE
    else:
        match_op = MatchOp.GLOB  # default

    # Parse symbol type
    symbol_type = SymbolType[args.type.upper()]
    pattern = args.pattern

    # Open database
    with DatabaseStore(args.db_path) as db:
        for result in db.match(
            symbol_type,
            match_op,
            pattern,
            case_sensitive=not args.case_insensitive,
            limit=args.limit
        ):
            print_result(result)


def print_result(result: MatchResult):
    """Print result with byte position if available."""
    output = f"{result.symbol_type}:{result.file_path}:{result.line_number}:{result.qualified_name}"

    # Include byte position if available
    if result.byte_offset is not None:
        output += f":@{result.byte_offset}+{result.byte_length}"

    print(output)


# Example output formats:
# method:src/models/user.py:45:models.user.User.save:@1234+56
# class:src/models/user.py:10:models.user.User:@234+1000
# file:src/models/user.py:0:src/models/user.py
```

---

## Indexer Changes

The indexer must now populate the `symbols` table instead of separate tables. For each entity discovered during AST parsing:

```python
def index_function(file_id, file_path, func_node, class_name=None):
    """Index a function or method into symbols table."""
    symbol_type = 'method' if class_name else 'function'

    # Calculate qualified name
    module = file_path_to_module(file_path)
    if class_name:
        qualified_name = f"{module}.{class_name}.{func_node.name}"
    else:
        qualified_name = f"{module}.{func_node.name}"

    # Insert into symbols table
    cursor.execute("""
        INSERT INTO symbols (
            symbol_name, symbol_type, file_path, line_number,
            byte_offset, byte_length, qualified_name, parent_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        func_node.name,
        symbol_type,
        file_path,
        func_node.lineno,
        func_node.col_offset,  # byte offset from AST
        len(ast.unparse(func_node)),  # approximate byte length
        qualified_name,
        class_name  # NULL for functions, class name for methods
    ))
```

Similar logic for classes, imports, globals, and file entries.

---

## Adding New Symbol Types

To add a new symbol type (e.g., `DECORATOR`):

1. **Add to SymbolType enum**: `via/core/types.py`
```python
class SymbolType(Enum):
    # ... existing types ...
    DECORATOR = 'decorator'
```

2. **Update indexer** to populate `symbols` table with `symbol_type='decorator'`

**That's it!** No database schema changes, no query changes - just add the enum value and populate the table.

---

## Adding New Match Operators

To add a new operator (e.g., `STARTS_WITH`):

1. **Add to MatchOp enum**: `via/core/types.py`
```python
class MatchOp(Enum):
    # ... existing operators ...
    STARTS_WITH = ('startswith', 'LIKE', True)
```

2. **Optionally handle pattern transformation** in `match()` method:
```python
if match_op == MatchOp.STARTS_WITH:
    pattern = f"{pattern}%"
```

**That's it!** The SQL operator mapping handles the rest.

---

## File Structure

```
via/
├── core/
│   └── types.py                 # SymbolType enum, MatchOp enum, MatchResult
│
├── db/
│   ├── schema.py                # CREATE TABLE statements for symbols/references/files
│   └── store.py                 # DatabaseStore.match() with simple WHERE clause
│
└── __main__.py                  # CLI integration
```

**Minimal!** Just 3 files for entire match system, and the logic is trivial.

---

## Output Format

### Basic Format

```
type:file_path:line_number:qualified_name
```

### With Byte Position (when available)

```
type:file_path:line_number:qualified_name:@byte_offset+byte_length
```

### Examples

```bash
$ via m -t method -g '*save()'

method:src/models/user.py:45:models.user.User.save:@1234+56
method:src/models/post.py:78:models.post.Post.save:@3456+62
```

```bash
$ via m -t class -g 'User*'

class:src/models/user.py:10:models.user.User:@234+1000
class:src/models/user.py:89:models.user.UserProfile:@2340+450
```

```bash
$ via m -t filepath -g '**/utils/*.py'

file:src/utils/helpers.py:0:src/utils/helpers.py
file:src/utils/matcher.py:0:src/utils/matcher.py
file:tests/utils/test_helpers.py:0:tests/utils/test_helpers.py
```

---

## Query Examples

### Single Filter

```python
# Find all methods named like "*save()"
db.match(SymbolType.METHOD, MatchOp.GLOB, '*save()')
```

Generated SQL:
```sql
SELECT * FROM symbols
WHERE symbol_type = 'method'
  AND symbol_name GLOB '*save()'
ORDER BY file_path, line_number
```

### Case-Insensitive

```python
# Find all classes starting with "user" (case-insensitive)
db.match(SymbolType.CLASS, MatchOp.GLOB, 'user*', case_sensitive=False)
```

Generated SQL:
```sql
SELECT * FROM symbols
WHERE symbol_type = 'class'
  AND LOWER(symbol_name) GLOB 'user*'
ORDER BY file_path, line_number
```

### With Limit

```python
# Find first 10 functions
db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*', limit=10)
```

Generated SQL:
```sql
SELECT * FROM symbols
WHERE symbol_type = 'function'
  AND symbol_name GLOB '*'
ORDER BY file_path, line_number
LIMIT 10
```

---

## Byte Position Usage

The byte offset and length allow for:

1. **Direct file seeking** - Jump to exact location in file
2. **Extraction** - Read exact bytes for entity source code
3. **Rendering** - Display entity without parsing

**Example usage**:
```python
# Read entity source directly
with open(result.file_path, 'rb') as f:
    f.seek(result.byte_offset)
    source = f.read(result.byte_length).decode('utf-8')
    print(source)
```

---

## Testing Strategy

### Unit Tests (10 tests)

**SymbolType enum** (1 test):
- Test enum values

**MatchOp enum** (2 tests):
- Test enum values and attributes
- Test SQL operator mappings

**DatabaseStore.match()** (7 tests):
- Test each SymbolType (7 tests)
- Test each MatchOp (4 tests)
- Test case sensitivity (1 test)
- Test limit (1 test)
- Test byte_offset/byte_length in results (1 test)

### Integration Tests (10 tests)

**CLI Integration** (10 tests):
- Single filter with each syntax (3 tests)
- Each symbol type (7 tests)
- Output format with byte positions (1 test)
- Case-insensitive flag (1 test)
- Limit flag (1 test)
- Error handling (2 tests)

**Total**: 20 tests

---

## Design Decisions

### 1. Denormalized Symbols Table

**Decision**: Single `symbols` table instead of separate tables per entity type.

**Rationale**:
- **Eliminates JOINs**: All data in one place
- **Trivial queries**: Same pattern for all types
- **Faster**: No JOIN overhead
- **Simpler code**: One query path
- **Easy indexing**: Composite index on (symbol_type, symbol_name)

**Trade-off**: Some data duplication (file_path repeated), but disk is cheap and query performance is critical.

### 2. Separate References Table

**Decision**: Keep relationship data in separate `references` table.

**Rationale**:
- **Match command doesn't need it**: Only symbol lookups, not relationships
- **Future queries need it**: "Find all callers" requires relationships
- **Keeps symbols table simple**: No complex join logic for basic queries
- **Different access patterns**: Match = name lookups, References = graph traversal

### 3. No SQL Templates

**Decision**: Direct WHERE clause construction instead of templates.

**Rationale**:
- **All queries identical**: Only symbol_type and match operator vary
- **Simple dynamic SQL**: Just string concatenation
- **Clear intent**: Query is obvious
- **Easy debugging**: Can log exact SQL

### 4. Enums Still Valuable

**Decision**: Keep SymbolType and MatchOp enums despite simplification.

**Rationale**:
- **Type safety**: Prevent typos like "methd" vs "method"
- **Discoverability**: IDE autocomplete shows all types
- **Validation**: Invalid types caught at enum creation
- **SQL operator mapping**: MatchOp provides SQL_op attribute

---

## Migration from v4.0 to v5.0

### Schema Changes

**Remove**:
- Separate `functions` table
- Separate `classes` table
- Separate `imports` table
- Separate `globals` table
- Complex foreign key relationships

**Add**:
- New `symbols` table (denormalized)
- New `references` table (for future use)

**Keep**:
- `files` table (for metadata only)
- `metadata` table
- `schema_migrations` table

### Code Changes

**DatabaseStore.match()**:
- Remove `_QUERY_TEMPLATES` dictionary
- Remove complex JOIN logic
- Add simple WHERE clause builder
- Remove `_row_to_result()` complexity

**SymbolType enum**:
- Remove table/column/has_byte_offset attributes
- Simplify to just string value

**Indexer**:
- Change INSERT statements to target `symbols` table
- Add qualified_name calculation
- Remove parent_entity_id logic
- Populate parent_name for methods

---

## Summary

**Ultra-Simplified Design**:
- ✅ Single `symbols` table (denormalized)
- ✅ Simple WHERE clause queries (no templates)
- ✅ Zero JOINs, zero complexity
- ✅ Trivial to add new types (just enum value)
- ✅ Complete results with byte_offset and byte_length
- ✅ Separate `references` table for future relationship queries

**Key Simplifications from v4.0**:
- ❌ No SQL template dictionary
- ❌ No complex JOIN logic
- ❌ No type-specific query handling
- ❌ No table/column mapping in enums
- ✅ One query pattern for all types
- ✅ Database does all the work

**Pure Simplicity**:
```python
# The entire query logic:
query = f"SELECT * FROM symbols WHERE symbol_type = ? AND symbol_name {op} ?"
```

---

**Created by**: @Morpheus (Architect)
**Status**: ✅ Ready for Implementation (Denormalized)
**Next**: @Neo implement schema changes, @Neo update indexer, @Neo implement match command
