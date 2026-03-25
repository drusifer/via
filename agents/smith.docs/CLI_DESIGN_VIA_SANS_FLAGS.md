# CLI Design: `--via` and `--sans` Relationship Flags

_Author: Smith | Date: 2026-03-23_

## Decision

Replace the current `-V<rel>` / `--invert` pattern with two explicit, symmetric flags:

| Short | Long | Meaning |
|-------|------|---------|
| `-V <rel>` | `--via <rel>` | Symbol has this relationship (positive filter) |
| `-S <rel>` | `--sans <rel>` | Symbol does NOT have this relationship (negative filter) |

Relationship type is a **named argument** to the flag, not encoded in the flag suffix.

---

## Rationale

### Problems with the current design

- `-Vinh`, `-Vca`, `-Vimp` etc. encode the relationship type in the flag name — adding a new relationship type requires a new flag
- `--invert` is ambiguous: it means "flip relationship direction" in most cases but "logical negation" with `-Vhas` — two different operations, one flag
- `--invert` has a positional ambiguity: does it apply to the preceding or following `-V` flag?

### Why `--via` / `--sans`

- **`via`** (Latin/English): "by way of", "through" — already the tool name; fits naturally as a preposition
- **`sans`** (Latin/French, English borrowed): "without" — exact counterpart to `via`, same register, same brevity
- The pair is self-documenting: `--via calls` / `--sans calls` reads as plain English
- Relationship type becomes a discrete value: tab-completable, cleanly validated, no new flags needed for new relationship types

---

## Syntax

```
ANCHOR-PATTERN  --via|--sans  REL-TYPE  [RESULT-PATTERN]
```

```bash
# Positive — find symbols WITH this relationship
via --match-glob "Base*" --type-class --via inherits-from --match-glob "*" --type-class

# Negative — find symbols WITHOUT this relationship
via --match-glob "*" --type-class --sans inherits-from --match-glob "Base*" --type-class
```

---

## Match Negation

Separately, `--not` negates the match pattern (not the relationship):

```bash
via --not --match-glob "_*" --type-method      # methods not starting with underscore
via --not --match-glob "test_*" --type-function # functions not named test_*
```

`--not` and `--sans` are orthogonal — one filters the symbol name, the other filters relationship existence.

---

## Relationship Types

Standard values for the `<rel>` argument:

| Value | Meaning |
|-------|---------|
| `inherits-from` | Class inheritance |
| `calls` | Function/method call |
| `imports` | Import dependency |
| `references` | Symbol reference |
| `has` | Container membership (file/class has member) |
| `declares` | Alias for `has` |

Short aliases (TBD): `inh`, `calls`, `imp`, `ref`, `has`

---

## Direction Convention (replaces `--invert`)

`--invert` is removed. Direction is encoded by argument order:

- **Anchor** (left, before `--via`/`--sans`): the known/fixed side of the relationship
- **Results** (right, after `--via`/`--sans`): what gets returned

```bash
# "What inherits from BaseHandler?" — BaseHandler is the anchor
via --match-glob "BaseHandler" --type-class --via inherits-from --match-glob "*" --type-class

# "What does MyClass inherit from?" — MyClass is the anchor, results are parents
via --match-glob "*" --type-class --via inherits-from --match-glob "MyClass" --type-class
```

No flag needed — just put whichever side you know on the left.

---

## Before / After Examples

| Question | Before | After |
|----------|--------|-------|
| Subclasses of BaseHandler | `via -mg "BaseHandler" -Vinh -mg "*"` | `via --match-glob "BaseHandler" --via inherits-from --match-glob "*"` |
| Parents of MyClass | `via -mg "MyClass" -Vinh -mg "*" --invert` | `via --match-glob "*" --via inherits-from --match-glob "MyClass"` |
| Callers of get_counts | `via -mg "*" -Vca -mg "get_counts"` | `via --match-glob "*" --via calls --match-glob "get_counts"` |
| Uncalled functions | _(not supported)_ | `via --match-glob "*" --type-function --sans calls --match-glob "*"` |
| Classes without a parent | _(not supported)_ | `via --match-glob "*" --type-class --sans inherits-from --match-glob "*"` |
| test_ functions outside tests/ | `--invert with -Vhas` (errored) | `via --match-glob "test_*" --type-function --sans has --match-glob "*/tests/*" --type-filepath` |

---

## Migration

- `-V<rel>` short flags (`-Vinh`, `-Vca`, etc.) retained as **deprecated aliases** for one release
- `--invert` removed — no alias, direction is now handled by argument order
- `--without` (earlier proposal) superseded by `--sans` / `-S`

---

## 20 Real Use Cases: Old vs New

Questions with no relationship flags are marked **unchanged** — only the match syntax applies.

---

### 1. What are the top-level classes in this project?

_Unchanged — no relationship flag_
```bash
via --match-glob "*" --type-class
via --match-glob "*" --type-class --output-table
via --match-glob "*" --type-class --output-diagram
```

---

### 2. Which file is the entry point? What does it call first?

```bash
# OLD
via -mg "*" -tf -Vhas -mg "__main__*" -tN
via -mg "main" -tf -Vca -mg "*"

# NEW
via --match-glob "*" --type-function --via has --match-glob "__main__*" --type-filename
via --match-glob "main" --type-function --via calls --match-glob "*"
```

---

### 3. What does this module export?

_Unchanged — qualified name match, no relationship flag_
```bash
via --match-glob "via.web.api.*" --qualified --type-class --type-function --type-method
```

---

### 4. Are there any god classes?

_Unchanged — no relationship flag_
```bash
via --match-glob "*" --type-method --output-table
via --match-glob "*" --type-method --output-json | python3 -c "..."   # group + count by class
```

---

### 5. If I rename `DatabaseStore`, what breaks?

```bash
# OLD
via -mg "*" -tc -Vinh -mg "DatabaseStore" -tc
via -mg "*" -ti -Vimp -mg "DatabaseStore"
via -mg "*" -Vr  -mg "DatabaseStore"

# NEW
via --match-glob "*" --type-class  --via inherits-from --match-glob "DatabaseStore" --type-class
via --match-glob "*" --type-import --via imports       --match-glob "DatabaseStore"
via --match-glob "*"               --via references    --match-glob "DatabaseStore"
```

---

### 6. Which functions changed in the last 2 days?

_Unchanged — temporal filter, no relationship flag_
```bash
via --match-glob "*" --type-function --newerthan 2d --output-table
```

---

### 7. What symbols are stale / never called?

```bash
# OLD — stale relational detection only (--stale)
via -mg "*" -tc -Vinh -mg "test_*" -tf --stale
via -mg "*" -Vr -mg "*" --newerthan 1d --stale

# NEW — same stale queries
via --match-glob "*" --type-class    --via inherits-from --match-glob "test_*" --type-function --stale
via --match-glob "*"                 --via references    --match-glob "*" --newerthan 1d --stale

# NEW — standalone "never called" (was not supported before)
via --match-glob "*" --type-function --sans calls --match-glob "*"
via --match-glob "*" --type-class    --sans inherits-from --match-glob "*"
```

---

### 8. Is anything still calling this utility function?

```bash
# OLD
via -mg "*" -Vca -mg "my_util_function" -tf

# NEW
via --match-glob "*" --via calls --match-glob "my_util_function" --type-function
```

---

### 9. What inherits from `BaseHandler`?

```bash
# OLD
via -mg "*" -tc -Vinh -mg "BaseHandler" -tc
via -mg "*" -tc -Vinh -mg "BaseHandler" -tc -oD

# NEW
via --match-glob "*" --type-class --via inherits-from --match-glob "BaseHandler" --type-class
via --match-glob "*" --type-class --via inherits-from --match-glob "BaseHandler" --type-class --output-diagram
```

---

### 10. Which modules import from `via.db`?

```bash
# OLD
via -mg "*" -ti -Vimp -mg "via.db*" -Q -oT

# NEW
via --match-glob "*" --type-import --via imports --match-glob "via.db*" --qualified --output-table
```

---

### 11. Does anything import from both `via.web` and `via.mcp`?

```bash
# OLD — two queries, intersect manually
via -mg "via.web*" -ti -Q -oJ > /tmp/web.json
via -mg "via.mcp*" -ti -Q -oJ > /tmp/mcp.json

# NEW — same (compound AND still a gap; --intersect not yet implemented)
via --match-glob "via.web*" --type-import --qualified --output-json > /tmp/web.json
via --match-glob "via.mcp*" --type-import --qualified --output-json > /tmp/mcp.json
```

---

### 12. What are all the external imports?

_Unchanged — regex match, no relationship flag_
```bash
via --match-regex "^(?!via)" --type-import --case-insensitive --output-table
```

---

### 13. What new functions were added in the last 24 hours?

_Unchanged — temporal filter, no relationship flag_
```bash
via --match-glob "*" --type-function --newerthan 1d --output-table
```

---

### 14. Are there `test_` functions outside the `tests/` directory?

```bash
# OLD — positive case only (exclusion errored with --invert)
via -mg "*/tests/*" -tF -Vhas -mg "test_*" -tf          # inside tests/ (worked)
via -mg "*/tests/*" -tF -Vhas -mg "test_*" -tf --invert  # outside tests/ (errored)

# NEW — both cases clean
via --match-glob "test_*" --type-function --via  has --match-glob "*/tests/*" --type-filepath
via --match-glob "test_*" --type-function --sans has --match-glob "*/tests/*" --type-filepath
```

---

### 15. Do any methods shadow Python built-ins?

_Unchanged — regex match, no relationship flag_
```bash
via --match-regex "^(list|type|id|dict|set|str|int|float|len|open|print|next|iter|map|filter|zip)$" --type-method
```

---

### 16. Something is calling `get_counts()` — show every call site.

```bash
# OLD
via -mg "*" -Vca -mg "get_counts" -oT

# NEW
via --match-glob "*" --via calls --match-glob "get_counts" --output-table
```

---

### 17. There's a `MAX_VALUE` global — how many are there?

_Unchanged — no relationship flag_
```bash
via --match-glob "MAX_VALUE" --type-global
via --match-glob "MAX_VALUE" --type-global --output-raw
```

---

### 18. What does `via.web.api` actually export?

_Unchanged — qualified name match, no relationship flag_
```bash
via --match-glob "via.web.api.*" --qualified --type-class --type-function --type-method
via --match-glob "via.web.api.*" --qualified --output-raw -A 2 -B 2
```

---

### 19. Which symbols are referenced externally vs. internally?

```bash
# OLD
via -mg "via.web.*" -Q -Vr -mg "*" -oT

# NEW
via --match-glob "via.web.*" --qualified --via references --match-glob "*" --output-table
```

---

### 20. Are there functions with duplicate names across files?

_Unchanged — no relationship flag_
```bash
via --match-glob "*" --type-function --output-table
via --match-glob "*" --type-function --output-json | python3 -c "..."   # group by name, show duplicates
```

---

## Summary: Which Queries Change

| # | Question | Change |
|---|----------|--------|
| 1 | Domain map | unchanged |
| 2 | Entry point + calls | `-Vhas` → `--via has`, `-Vca` → `--via calls` |
| 3 | Module exports | unchanged |
| 4 | God classes | unchanged |
| 5 | Rename impact | `-Vinh`/`-Vimp`/`-Vr` → `--via inherits-from`/`--via imports`/`--via references` |
| 6 | Recently changed | unchanged |
| 7 | Stale/uncalled | `-Vinh`/`-Vr` → `--via`; **`--sans calls` is new capability** |
| 8 | Safe to delete? | `-Vca` → `--via calls` |
| 9 | Inheritance tree | `-Vinh` → `--via inherits-from` |
| 10 | Import blast radius | `-Vimp` → `--via imports` |
| 11 | Layering violation | unchanged (still two queries) |
| 12 | External imports | unchanged |
| 13 | New additions | unchanged |
| 14 | Misplaced tests | **`--sans has` replaces erroring `--invert`** |
| 15 | Built-in shadows | unchanged |
| 16 | Call sites | `-Vca` → `--via calls` |
| 17 | Duplicate globals | unchanged |
| 18 | Module surface | unchanged |
| 19 | External refs | `-Vr` → `--via references` |
| 20 | Duplicate names | unchanged |

---

## Queries Unlocked by the New Syntax

These queries were **impossible or errored** with the old design. `--sans` makes them first-class.

### Uncalled functions — dead code detection

```bash
via --match-glob "*" --type-function --sans calls --match-glob "*"
```
_Functions that nothing calls. Previously required external tooling (coverage reports, linters)._

### Classes with no subclasses — leaf classes

```bash
via --match-glob "*" --type-class --sans inherits-from --match-glob "*"
```
_Classes that nothing inherits from. Useful for identifying safe-to-refactor leaf nodes._

### Classes with no parent — root classes

```bash
via --match-glob "*" --type-class --sans inherits-from --match-glob "*"
```
_Root classes in the hierarchy — useful for mapping domain entry points._

### Modules with no imports — isolated files

```bash
via --match-glob "*" --type-filepath --sans imports --match-glob "*"
```
_Files that import nothing. May indicate standalone utilities or forgotten dead files._

### Test functions outside the test directory

```bash
via --match-glob "test_*" --type-function --sans has --match-glob "*/tests/*" --type-filepath
```
_Previously errored with `--invert`. Now a clean single command._

### Public methods never referenced

```bash
via --not --match-glob "_*" --type-method --sans references --match-glob "*"
```
_Non-private methods that are never referenced anywhere — prime refactor candidates._

### Classes that import from a module but don't inherit from it

```bash
via --match-glob "*" --type-class --via imports --match-glob "via.db*" --qualified --sans inherits-from --match-glob "*Base*" --type-class
```
_Detects direct DB usage outside the intended inheritance pattern — an architecture enforcement query._

### Recently changed functions with no test coverage

```bash
via --match-glob "*" --type-function --newerthan 1d --sans has --match-glob "*/tests/*" --type-filepath
```
_Functions modified recently that don't live in a test file — flag for test coverage review._

### Symbols with stale references

```bash
via --match-glob "*" --via references --match-glob "*" --stale
```
_References that point to symbols older than the referencing file — potential stale/broken links._
