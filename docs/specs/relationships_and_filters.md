# VIA Relationship Queries and Container Filters

TL;DR: Guide to building advanced queries that trace inheritance, calls, imports, references, and container declarations, plus programmatic Python API usage.

## Table of Contents

- [Relationship Queries](#relationship-queries)
- [Container Filters](#container-filters-via-declares)
- [Python API](#python-api)

---

## Relationship Queries

VIA can trace relationships between symbols: inheritance, function calls, imports, references, and container membership. This lets you navigate code structure, not just search for names.

### Syntax

```
via <result-stage> --via <rel> <filter-stage>
via <result-stage> --sans <rel> <filter-stage>
```

- **result stage** (before `--via`/`--sans`): What VIA returns.
- **filter stage** (after `--via`/`--sans`): The related symbols/files that constrain the result stage.
- **`--via <rel>`**: Keep result-stage records that **have** the relationship to the filter stage.
- **`--sans <rel>`**: Keep result-stage records with **no** such relationship to the filter stage (NOT EXISTS).
- **`--not`**: Negate the immediately following pattern flag (`-mg`/`-mr`/`-ms`)
- **`-V <rel>`** / **`-S <rel>`**: Short forms of `--via` / `--sans`

Use only one match flag (`-mg`, `-mr`, or `-ms`) per stage. Type flags may be combined, so `-tf -tm -tc` remains a valid multi-type query.

### Relationship Types

| Relationship | `--via` / `-V` value | Description |
|---|---|---|
| Inheritance | `inherits-from` | Result classes filtered by the base classes they inherit from |
| Calls | `calls` | Result functions/methods filtered by what they call |
| Imports | `imports` | Result files/modules filtered by what they import |
| References | `references` | Result symbols filtered by what they reference in their body |
| Container membership | `declares` | Result containers filtered by the symbols they declare |

### `--sans`: Negative Relationship (NOT EXISTS)

`--sans <rel>` keeps result-stage records that have **no** relationship edge to anything matching the filter stage. Uses a SQL NOT EXISTS subquery.

```bash
# Root classes — no parent class at all
via -mg '*' -tc --sans inherits-from -mg '*' -tc

# Functions that call nothing
via -mg '*' -tf --sans calls -mg '*' -tf

# Functions that reference nothing (leaf implementations)
via -mg '*' -tf --sans references -mg '*' -tf
```

### `--not`: Negate a Pattern Flag

`--not` negates the match pattern immediately following it. Useful for exclusion patterns.

```bash
# All methods NOT starting with underscore
via -mg '*' -tm --not -mg '_*' -tm
```

### `--stale`: Cross-Stage Temporal Filter

`--stale` filters relationship results to those where the **result-stage symbol's file is older than the filter-stage symbol's file**. Use it to find stale dependencies — code that was last touched *before* the thing it depends on.

```bash
# Find test files that haven't been updated since the classes they test changed
via -mg 'test_*' -tf --via inherits-from -mg '*' -tc --stale

# Find subclasses older than their base class
via -mg '*' -tc --via inherits-from -mg 'Base*' -tc --stale

# Find callers that pre-date the function they call
via -mg '*' -tf --via calls -mg 'my_func' -tf --stale
```

> **Note**: `--stale` only applies to relationship queries. On a plain match query it is a no-op. If mtime data is missing, rebuild the index with `via index --force`.

### Inheritance Examples

```bash
# Find all classes that inherit from BaseClass
via -mg '*' -tc --via inherits-from -mg 'BaseClass' -tc

# Find children of any class matching *Base*
via -mg '*' -tc --via inherits-from -mg '*Base*' -tc

# Filter: only show children matching "Child*"
via -mg 'Child*' -tc --via inherits-from -mg 'BaseClass' -tc

# Root classes (no parent)
via -mg '*' -tc --sans inherits-from -mg '*' -tc
```

### Import Examples

```bash
# Find all files that import typing
via -mg '*' -tF --via imports -mg 'typing'

# Find all files importing dataclasses, show as table
via -mg '*' -tF --via imports -mg 'dataclasses' -oT
```

### Call Examples

```bash
# Find all functions that call helper_func
via -mg '*' -tf --via calls -mg 'helper_func' -tf

# Find all callers of a method
via -mg '*' -tm --via calls -mg 'save' -tm

# Functions that call nothing
via -mg '*' -tf --sans calls -mg '*' -tf
```

### Reference Examples

```bash
# Find all functions that reference a constant
via -mg '*' -tf --via references -mg 'MAX_RETRIES' -tg

# Find all referencers of a symbol
via -mg '*' --via references -mg 'process_data' -tf

# Functions that reference nothing (leaf implementations — no external dependencies)
via -mg '*' -tf --sans references -mg '*' -tf
```

### Combining with Output Formats

```bash
# Inheritance tree as table
via -mg '*' -tc --via inherits-from -mg 'BaseClass' -tc -oT

# Show source of all callers
via -mg '*' -tf --via calls -mg 'validate' -tf -oR
```

---

---

## Container Filters (`--via declares`)

`--via declares` filters containers by what they declare. The result stage still determines what VIA returns.

For example, a file result stage returns files. Adding `--via declares -mg 'DatabaseStore' -tc` filters those files to ones that declare a matching class; it does not invert the query and return every symbol inside the file.

### Syntax

```
via -m<X> CONTAINER_PATTERN -t<container> --via declares -m<Y> MEMBER_PATTERN -t<member>
```

Valid container types: `-tF` (filepath), `-tN` (filename), `-tc` (class), `-tf` (function)

### Examples

```bash
# Files named store.py that declare any class
via -mg 'store.py' -tN --via declares -mg '*' -tc

# DatabaseStore classes that declare any method
via -mg 'DatabaseStore' -tc --via declares -mg '*' -tm

# Service files that declare any function
via -mg '*service*' -tF --via declares -mg '*' -tf -n 0

# executor.py files that declare any method, as table
via -mg 'executor.py' -tN --via declares -mg '*' -tm -oT -n 0

# Test files that declare test functions
via -mg 'test_*.py' -tN --via declares -mg 'test_*' -tf -n 0
```

> **Note**: All patterns are case-sensitive. Use `-I` for case-insensitive matching.

---

---

## Python API

Use `ViaQueryBuilder` plus `ViaRunner` when you want to run via queries from Python code. This API keeps the same semantics as the CLI; it is a construction helper, not a new query language.

### Plain Query Example

```python
from via import ViaQueryBuilder, ViaRunner

query = (
    ViaQueryBuilder()
    .glob("*Service")
    .classes()
    .limit(10)
    .build()
)

records = list(ViaRunner(db_store).run(query))
```

### Relationship Query Example

```python
from via import ViaQueryBuilder, ViaRunner

query = (
    ViaQueryBuilder()
    .glob("*")
    .classes()
    .via("inherits-from")
        .glob("Base")
        .classes()
    .done()
    .build()
)

records = list(ViaRunner(db_store).run(query))
```

---
