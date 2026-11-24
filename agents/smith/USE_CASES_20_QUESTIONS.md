# 20 Questions I Wish I Could Answer with `via`

_Author: Smith | Date: 2026-03-23_

These are the questions a developer reaches for constantly when navigating a real codebase.
Each entry shows the exact `via` command that answers it — or notes where a gap exists.

---

## Orientation — New to a Codebase

### 1. What are the top-level classes in this project? Give me a map of the domain.

```bash
via -mg "*" -tc
via -mg "*" -tc -oT          # table format — easier to scan
via -mg "*" -tc -oD          # Mermaid diagram — shows inheritance
```

---

### 2. Which file is the entry point? What does it call first?

```bash
# Find the entry-point file
via -mg "__main__*" -tN

# See all functions defined in it
via -mg "*" -tf --via has -mg "__main__*" -tN

# See what calls main()
via -mg "main" -tf --via calls -mg "*"
```

---

### 3. What does this module export — what's its public surface?

```bash
# All symbols whose qualified name starts with the module
via -mg "via.web.api.*" -Q
via -mg "via.web.api.*" -Q -tc -tf -tm    # filter to callable symbols only
```

---

### 4. Are there any god classes — classes with an unusually high number of methods?

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

## Change Impact

### 5. If I rename `DatabaseStore`, what else breaks — what calls it, imports it, or inherits from it?

```bash
# Who inherits from DatabaseStore?
via -mg "DatabaseStore" -tc --via inherits-from -mg "*" -tc

# What imports it?
via -mg "DatabaseStore" --via imports -mg "*"

# What references it?
via -mg "DatabaseStore" --via references -mg "*"
```

---

### 6. Which functions have changed in the last 2 days?

```bash
via -mg "*" -tf --newerthan 2d
via -mg "*" -tf --newerthan 2d -oT    # table: easier to compare
```

---

### 7. What symbols are stale — defined but not updated since their source changed?

```bash
# Stale tests: test functions that haven't been updated since their source class changed
via -mg "*" -tc --via inherits-from -mg "test_*" -tf --stale

# Stale references: symbols referencing something that was recently updated
via -mg "*" --via references -mg "*" --newerthan 1d --stale
```

> **Note**: `--stale` in `via` means "the result is older than its relationship anchor". It's best suited for stale test detection and stale-reference detection, not raw unused-symbol detection.

---

### 8. I'm about to delete this utility function. Is anything still calling it?

```bash
via -mg "my_util_function" -tf --via calls -mg "*"
via -mg "my_util_function" -tf --via calls -mg "*" -oT   # table: shows file paths clearly
```

---

## Architecture & Dependencies

### 9. What inherits from `BaseHandler`? Show me the full class hierarchy.

```bash
# Direct subclasses
via -mg "BaseHandler" -tc --via inherits-from -mg "*" -tc

# Diagram: the full inheritance tree
via -mg "BaseHandler" -tc --via inherits-from -mg "*" -tc -oD
```

---

### 10. Which modules import from `via.db`? I need to know the blast radius of a schema change.

```bash
via -mg "via.db*" --via imports -mg "*" -Q
via -mg "via.db*" --via imports -mg "*" -Q -oT    # table shows file paths
```

---

### 11. Does anything import from both `via.web` and `via.mcp`? (Layering violation check)

```bash
# Run both queries — intersect manually or via JSON
via -mg "via.web*" -ti -Q -oJ > /tmp/web_imports.json
via -mg "via.mcp*" -ti -Q -oJ > /tmp/mcp_imports.json
# Then: compare file_path fields for overlap
```

> **Gap**: `via` doesn't yet support compound AND queries in a single command. Two queries + external comparison is the workaround. A `--intersect` flag would close this gap.

---

### 12. What are all the external imports in this codebase — where are my third-party dependencies?

```bash
# All imports — scan for non-project prefixes
via -mg "*" -ti -oT

# Use regex to find imports that don't start with your package name
via -mr "^(?!via)" -ti -I
```

---

## Code Review / PR Prep

### 13. What new functions were added in the last 24 hours?

```bash
via -mg "*" -tf --newerthan 24h
via -mg "*" -tf --newerthan 1d -oT
```

---

### 14. Are there any functions named `test_` outside the `tests/` directory?

```bash
# Positive: find test_ functions INSIDE tests/ directory
via -mg "*/tests/*" -tF --via has -mg "test_*" -tf

# Exclusion: find test_ functions NOT in tests/ — use --sans has
via -mg "*/tests/*" -tF --sans has -mg "test_*" -tf
```

> **Note**: `--via has` finds files that contain the target symbol. `--sans has` finds files that contain NO matching symbol.

---

### 15. Do any method names shadow Python built-ins?

```bash
# Targeted queries for common built-ins
via -mr "^(list|type|id|dict|set|str|int|float|len|open|print|next|iter|map|filter|zip)$" -tm
```

---

## Debugging

### 16. Something is calling `get_counts()` — but where? Show me every call site.

```bash
via -mg "get_counts" --via calls -mg "*"
via -mg "get_counts" --via calls -mg "*" -oT    # table: file + line number
```

---

### 17. There's a `MAX_VALUE` global — how many are there, and are they consistent?

```bash
via -mg "MAX_VALUE" -tg
via -mg "MAX_VALUE" -tg -oR    # raw source — see the actual value at each definition
```

---

### 18. I'm seeing an import error for `via.web.api`. What does that module actually export?

```bash
via -mg "via.web.api*" -Q                          # everything in the module
via -mg "via.web.api.*" -Q -tc -tf -tm             # classes, functions, methods only
via -mg "via.web.api.*" -Q -oR -A 2 -B 2           # with source context
```

---

## Refactoring

### 19. I want to split this file. Which symbols are referenced externally vs. only internally?

```bash
# Who outside via.web references via.web symbols?
via -mg "via.web.*" -Q --via references -mg "*" -oT

# Narrow to a specific module
via -mg "via.web.handler.*" -Q --via references -mg "*" -oT
```

> **Tip**: Results whose referencing file path is outside `via/web/` are external callers — those symbols must stay in the public interface when splitting.

---

### 20. Are there any functions with duplicate names across different files? Could they be consolidated?

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

## Summary: Gaps Worth Closing

| # | Question | Gap |
|---|----------|-----|
| 4 | God class detection | No built-in group-by-class count |
| 11 | Cross-module layering check | No compound AND query |
| 14 | Out-of-directory test functions | Now solvable with `--sans has` (Sprint 13) |
| 7 | Unused symbol detection | `--stale` is relational, not standalone |

These four gaps represent the highest-value next features from a power-user perspective.
