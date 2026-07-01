# VIA Real-World Queries, Troubleshooting, and Quick Reference

TL;DR: Practical query handbook, legacy subcommand mapping, troubleshooting guide, and cheat sheet for daily developer workflows.

## Table of Contents

- [Legacy Subcommand Syntax](#legacy-subcommand-syntax)
- [Practical Examples](#practical-examples)
- [20 Real-World Queries](#20-real-world-queries)
- [Troubleshooting](#troubleshooting)
- [Quick Reference](#quick-reference)

---

## Legacy Subcommand Syntax

The older subcommand syntax still works:

```bash
# Index
via index .
via index /path/to/project --force

# Match
via match '*save*' -t method
via match 'test_*' -t function -g
via match '%User%' -t class -s -I
```

**Note:** Pipeline syntax is recommended for new usage.

---

## Practical Examples

### Find All Test Functions

```bash
via -mg 'test_*' -tf
```

### Find Classes in a Module Pattern

```bash
via -mg '*Handler' -tc -oT
```

### View a Specific Class Implementation

```bash
via -mg 'DatabaseStore' -tc -oF
```

### Find Methods and Show Context

```bash
via -mg '*save*' -tm -oR -C 5
```

### Count Symbols

```bash
# Count all classes
via -mg '*' -tc -n 0 | wc -l

# Count all methods
via -mg '*' -tm -n 0 | wc -l

# Count test functions
via -mg 'test_*' -tf -n 0 | wc -l
```

### Find Unique Files with Matches

```bash
via -mg '*save*' -tm -n 0 | cut -d: -f2 | sort -u
```

### Search Imports

```bash
# Find all typing imports
via -mg '*typing*' -ti

# Find json imports
via -mg 'json' -ti
```

### Find Global Constants

```bash
# Find all globals
via -mg '*' -tg

# Find uppercase constants
via -mg '*_*' -tg
```

### Find Files by Name or Path

```bash
# Find test files (by filename)
via -mg '*test*' -tN

# Find files in a directory (by full path — requires -Q)
via -mg 'via/core/*' -tF -Q

# Find all Python files under a subdirectory
via -mg '*/pipeline/*' -tF -Q -n 0
```

### Complex Pipeline: Search and Format

```bash
# Find all Renderer classes with syntax highlighting
via -mg '*Renderer' -tc -oF

# Find save methods, show as table
via -mg '*save*' -tm -oT

# Find functions, show raw source with 3 lines context
via -mg 'main' -tf -oR -C 3
```

---

## 20 Real-World Queries

These are the questions developers reach for constantly when navigating a real codebase.
Each entry shows the exact `via` command that answers it.

### Orientation — New to a Codebase

#### 1. What are the top-level classes in this project? Give me a map of the domain.

```bash
via -mg "*" -tc
via -mg "*" -tc -oT          # table format — easier to scan
via -mg "*" -tc -oD          # Mermaid diagram — shows inheritance
```

#### 2. Which file is the entry point? What does it call first?

```bash
# Find the entry-point file
via -mg "__main__*" -tN

# See all functions defined in it
via -mg "*" -tf --via declares -mg "__main__*" -tN

# See what calls main()
via -mg "*" -tf --via calls -mg "main" -tf
```

#### 3. What does this module export — what's its public surface?

```bash
# All symbols whose qualified name starts with the module
via -mg "via.web.api.*" -Q
via -mg "via.web.api.*" -Q -tc -tf -tm    # filter to callable symbols only
```

#### 4. Are there any god classes — classes with an unusually high number of methods?

```bash
# Get all methods in table format — scan for classes with many rows
via -mg "*" -tm -oT

# JSON output for scripted counting
via -mg "*" -tm -oJ | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
counts = Counter(r['qualified_name'].rsplit('.', 1)[0] for r in data)
for cls, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'{n:4d}  {cls}')
"
```

> **Gap**: `via` doesn't yet have a built-in "group and count by class" output mode. JSON + script is the current workaround.

---

### Change Impact

#### 5. If I rename `DatabaseStore`, what else breaks?

```bash
# Who inherits from DatabaseStore?
via -mg "*" -tc --via inherits-from -mg "DatabaseStore" -tc

# What imports it?
via -mg "*" --via imports -mg "DatabaseStore"

# What references it?
via -mg "*" --via references -mg "DatabaseStore"
```

#### 6. Which functions have changed in the last 2 days?

```bash
via -mg "*" -tf --newerthan 2d
via -mg "*" -tf --newerthan 2d -oT    # table: easier to compare
```

#### 7. What symbols are stale — not updated since their source changed?

```bash
# Stale tests: test functions that haven't been updated since their source class changed
via -mg "test_*" -tf --via inherits-from -mg "*" -tc --stale

# Stale references: symbols referencing something that was recently updated
via -mg "*" --via references -mg "*" --newerthan 1d --stale
```

> **Note**: `--stale` means "the result-stage record is older than the related filter-stage record". Best for stale test detection and stale-reference detection, not raw unused-symbol detection.

#### 8. I'm about to delete this utility function. Is anything still calling it?

```bash
via -mg "*" -tf --via calls -mg "my_util_function" -tf
via -mg "*" -tf --via calls -mg "my_util_function" -tf -oT   # table: shows file paths clearly
```

---

### Architecture & Dependencies

#### 9. What inherits from `BaseHandler`? Show me the full class hierarchy.

```bash
# Direct subclasses
via -mg "*" -tc --via inherits-from -mg "BaseHandler" -tc

# Diagram: the full inheritance tree
via -mg "*" -tc --via inherits-from -mg "BaseHandler" -tc -oD
```

#### 10. Which modules import from `via.db`? I need to know the blast radius of a schema change.

```bash
via -mg "*" --via imports -mg "via.db*" -Q
via -mg "*" --via imports -mg "via.db*" -Q -oT    # table shows file paths
```

#### 11. Does anything import from both `via.web` and `via.mcp`? (Layering violation check)

```bash
# Run both queries — intersect manually or via JSON
via -mg "via.web*" -ti -Q -oJ > /tmp/web_imports.json
via -mg "via.mcp*" -ti -Q -oJ > /tmp/mcp_imports.json
# Then: compare file_path fields for overlap
```

> **Gap**: `via` doesn't yet support compound AND queries in a single command. Two queries + external comparison is the workaround.

#### 12. What are all the external imports — where are my third-party dependencies?

```bash
# All imports — scan for non-project prefixes
via -mg "*" -ti -oT

# Use regex to find imports that don't start with your package name
via -mr "^(?!via)" -ti -I
```

---

### Code Review / PR Prep

#### 13. What new functions were added in the last 24 hours?

```bash
via -mg "*" -tf --newerthan 24h
via -mg "*" -tf --newerthan 1d -oT
```

#### 14. Are there any functions named `test_` outside the `tests/` directory?

```bash
# Positive: find test_ functions INSIDE tests/ directory
via -mg "*/tests/*" -tF --via declares -mg "test_*" -tf

# Exclusion: find files NOT in tests/ that have test_ functions
# Use --not to negate the path pattern
via --not -mg "*/tests/*" -tF --via declares -mg "test_*" -tf
```

> **Note**: `--via declares` finds files that contain the target symbol.

#### 15. Do any method names shadow Python built-ins?

```bash
via -mr "^(list|type|id|dict|set|str|int|float|len|open|print|next|iter|map|filter|zip)$" -tm
```

---

### Debugging

#### 16. Something is calling `get_counts()` — but where? Show me every call site.

```bash
via -mg "*" --via calls -mg "get_counts"
via -mg "*" --via calls -mg "get_counts" -oT    # table: file + line number
```

#### 17. There's a `MAX_VALUE` global — how many are there, and are they consistent?

```bash
via -mg "MAX_VALUE" -tg
via -mg "MAX_VALUE" -tg -oR    # raw source — see the actual value at each definition
```

#### 18. I'm seeing an import error for `via.web.api`. What does that module actually export?

```bash
via -mg "via.web.api*" -Q                          # everything in the module
via -mg "via.web.api.*" -Q -tc -tf -tm             # classes, functions, methods only
via -mg "via.web.api.*" -Q -oR -A 2 -B 2           # with source context
```

---

### Refactoring

#### 19. I want to split this file. Which symbols are referenced externally vs. only internally?

```bash
# Who outside via.web references via.web symbols?
via -mg "*" --via references -mg "via.web.*" -Q -oT

# Narrow to a specific module
via -mg "*" --via references -mg "via.web.handler.*" -Q -oT
```

> **Tip**: Results whose referencing file path is outside `via/web/` are external callers — those symbols must stay in the public interface when splitting.

#### 20. Are there any functions with duplicate names across different files?

```bash
# Table sorted by name — duplicate names appear in adjacent rows
via -mg "*" -tf -oT

# JSON for scripted duplicate detection
via -mg "*" -tf -oJ | python3 -c "
import json, sys
from collections import defaultdict
data = json.load(sys.stdin)
by_name = defaultdict(list)
for r in data:
    by_name[r['symbol_name']].append(r['file_path'])
for name, files in sorted(by_name.items()):
    if len(files) > 1:
        print(f'{name}:')
        for f in files:
            print(f'  {f}')
"
```

---

### Gaps Worth Closing

| # | Question | Gap |
|---|----------|-----|
| 4 | God class detection | No built-in group-by-class count — JSON + script workaround |
| 11 | Cross-module layering check | No compound AND query — two queries + external intersect |

---

## Troubleshooting

### "Database not found"

Run `via index .` first:

```bash
$ via -mg '*' -tc
Error: Database not found

$ via index .
$ via -mg '*' -tc
# Now works
```

### No Results

1. **Case sensitivity**: Patterns are case-sensitive by default. `*store*` won't match `DatabaseStore` — use `*Store*` or add `-I` for case-insensitive matching.
2. **Broaden pattern**: Try `via -mg '*' -tc` to see if anything matches
3. **Check type**: Try different type flags (`-tc`, `-tm`, `-tf`)
4. **File path matching**: Use `-Q` with `-tF` to match by full directory path: `via -mg 'via/core/*' -tF -Q`
5. **Re-index**: Run `via index . --force`

### REGEXP Not Available

SQLite REGEXP requires an extension that may not be installed:

```bash
$ via -mr '^test_.*' -tf
Error: no such function: REGEXP

# Use glob instead
$ via -mg 'test_*' -tf
```

### Slow Indexing

- Use incremental indexing (default)
- Add patterns to `.gitignore`
- Use `--exclude` for generated directories

---

## Quick Reference

### Index Commands

```bash
via index .                  # Index current directory
via index /path --force      # Force re-index
via index . -vvv             # Very verbose
```

### Search Commands

```bash
via -mg PATTERN               # Search all types
via -mg PATTERN -tc            # Search classes
via -mg PATTERN -tm            # Search methods
via -mg PATTERN -tf            # Search functions
via -mg PATTERN -ti            # Search imports
via -mg PATTERN -tg            # Search globals
via -mg PATTERN -tF            # Search filepaths
via -mg PATTERN -tN            # Search filenames
```

### Output Commands

```bash
via ... -oL            # List output
via ... -oT            # Table output
via ... -oR            # Raw source
via ... -oF            # Formatted source
via ... -oR -C 3       # With context lines
```

### Relationship Commands

```bash
via <result> --via inherits-from <filter>   # Result classes inheriting from filter classes
via <result> --via calls <filter>           # Result functions/methods calling filter symbols
via <result> --via imports <filter>         # Result files/modules importing filter modules
via <result> --via references <filter>      # Result symbols referencing filter symbols
via <result> --via declares <filter>        # Result containers declaring filter symbols
via <result> --sans <rel> <filter>          # NOT EXISTS — results with no relationship
via ... --not -mg 'pattern'                 # Negate a pattern flag
```

### Temporal Commands

```bash
via ... --newerthan 1d         # Symbols from files changed in last day
via ... --olderthan 1w         # Symbols from files not changed in last week
```

### Pattern Types

```bash
-mg 'pattern'                 # Glob: * ?  (case-sensitive; add -I to ignore case)
-ms 'pattern'                 # SQL LIKE: % _
-mr 'pattern'                 # Regex (if available)
-Q                            # Match qualified name (full path for -tF)
```

---
