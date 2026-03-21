# Via Query Documentation Review — 2026-03-21

**Author:** Trin (QA Guardian)
**Scope:** All documented query examples in `via/mcp/schema.py` and agent SKILL.md files
**Test file:** `tests/uat/test_documented_queries_uat.py`
**Suite result:** 47 pass, 5 xfail (known doc issues below), 0 fail

---

## Summary

All 12 schema examples and skill-unique patterns were tested end-to-end against
a synthetic indexed project. Five inconsistencies were found between the
documented descriptions and actual implementation behavior.

Each finding below includes: **what is documented**, **what actually happens**,
and **options** for resolution. Please mark each with your decision.

---

## Finding 1 — Path-glob filtering not supported

**Severity:** Medium — misleading to users building queries
**Source:** `via/mcp/schema.py` examples 2 and 5

### Documented
```
Ex02: ["-mg", "via/core/*", "-tf"]   → "Find all functions in a specific file pattern"
Ex05: ["-mg", "via/services/*", "-tF"] → "Find all files matching a path pattern"
```

### Actual behavior
`-mg` matches against `symbol_name` in the database. Function symbol names are
plain identifiers (`parse_config`, `connect`) — never paths. The glob `via/core/*`
never matches any function name. Both examples return **empty results**.

For `-tF` (filepath type), `symbol_name` is the **basename only** (e.g. `utils.py`),
not the full path. `via/services/*` never matches a bare filename.


### Drew feeback
Desired behavior: the match should always apply to the '-t' type of object so -tf will always apply the match to function symbols and -tF will always apply to file symbols (file name). 


Ex02:
Finding  all function in a specific file pattern requires a relationship query so it work in two stages.  First query files mattching pattern then query functions contained within matching files using a relationship. We'll need -Vhas for this (SPRINT 9)


Ex05: 
The -Q param matches 'fully qualified' symbols or files. For fies: without -Q we match only the base name but with -Q it should match the full path 


### Working alternative (confirmed by tests)
```
# Match files by basename glob:
["-mg", "*service*", "-tF"]   → returns filepath symbols whose name contains "service"
```

### Options
- [ ] **A — Fix the docs:** Correct Ex02 and Ex05 to show basename matching. Document
      that path-based filtering isn't directly supported by `-mg`.
- [ ] **B — Fix the implementation:** Add a path-match mode (e.g. `-mp` or
      `--match-path`) that matches against `file_path` column instead of `symbol_name`.
- [ ] **C — Match against qualified_name:** `-mg` already has a `match_qualified`
      mode. For filepath symbols, `qualified_name = full_path`. Adding a flag to
      enable this would make Ex05 work.

Yes to C
But - wath for sprint 9 re all functions in files

---

## Finding 2 — Class-level call query returns empty

**Severity:** Medium — documented pattern silently returns nothing
**Source:** `via/mcp/schema.py` example 9; `neo.docs/SKILL.md`; `morpheus.docs/SKILL.md`

### Documented
```
["-mg", "MyClass", "-tc", "-Vca", "-iv", "-mg", "*", "-tf"]
→ "Find what a class's methods call (-iv returns the callees)"
```

### Actual behavior
Call relationships are stored from **method** symbols (`symbol_type = 'method'`)
to their callees. No call relationship has a **class** as the source
(`symbol_type = 'class'`). Anchoring with `-tc` (class type) on the left side
finds no call sources → **empty results**.

### Working alternative (confirmed by tests)
```
# Anchor on the specific method instead:
["-mg", "run", "-tm", "-Vca", "-iv", "-mg", "*"]
→ returns what the method 'run' calls
```

### Options
- [ ] **A — Fix the docs:** Update all three SKILL.md files and schema.py to anchor
      on `-tm` (method) instead of `-tc` (class).
- [ ] **B — Fix the implementation:** When the anchor is a class with `-tc`, expand
      the relationship query to include all methods where `parent_name = class_name`.
      This would make the documented form work as described.


### Drew feeback
We are supposed to be indexing both method calls and function calls.  This is a bug.


---

## Finding 3 — Morpheus SKILL.md uses `-th` (invalid flag)

**Severity:** Low — typo, easy fix
**Source:** `agents/morpheus.docs/SKILL.md` line 133

### Documented
```
["-mg", "*SectionName*", "-th"]   → "Find a section in an arch doc"
```

### Actual behavior
The valid type filter for Markdown headers is **`-tH`** (uppercase H), as defined
in `via/core/flag_groups.py` and correctly used in `schema.py` example 11.
`-th` (lowercase) is not a recognized flag. It is silently ignored, returning
all symbols matching the pattern regardless of type.

### Resolution
- [ ] **Fix the docs:** Change `-th` → `-tH` in `morpheus.docs/SKILL.md`. One-line fix.

### Drew feeback
agreed

---

## Finding 4 — Trin SKILL.md subclass query has anchor/result reversed

**Severity:** Medium — returns wrong results, not an error
**Source:** `agents/trin.docs/SKILL.md` relationship query table

### Documented
```
["-mg", "*", "-tc", "-Vinh", "-mg", "Base", "-tc"]
→ "All subclasses of Base"
```

### Actual behavior
The pipeline executor maps the **LEFT** stage as the anchor (the known/fixed thing).
With `*` on the LEFT and `Base` on the RIGHT:
- The query looks for **class symbols named `Base`** that have an inherits-from
  relationship to any class (`*`).
- This returns `Base` itself (if it inherits from something) — **not** its subclasses.

The correct form, consistent with `schema.py` Ex06, `neo.docs`, and `morpheus.docs`:
```
["-mg", "Base", "-tc", "-Vinh", "-mg", "*", "-tc"]   ← Base on LEFT (anchor)
→ returns all subclasses of Base
```

### Resolution
- [ ] **Fix the docs:** Correct the subclass entry in `trin.docs/SKILL.md` to put
      the known anchor on the LEFT. Applies to the relationship query table row.

### Drew feeback

This might be a test setup issue

via -mg MatchRecord -tc -Vinh -mg "*" -tc
class:/home/drusifer/Projects/via/via/core/match_record.py:101:.home.drusifer.Projects.via.via.core.match_record.ClassMatchRecord:@3077+745
class:/home/drusifer/Projects/via/via/core/match_record.py:125:.home.drusifer.Projects.via.via.core.match_record.MethodMatchRecord:@3836+567
class:/home/drusifer/Projects/via/via/core/match_record.py:145:.home.drusifer.Projects.via.via.core.match_record.FunctionMatchRecord:@4417+521
class:/home/drusifer/Projects/via/via/core/match_record.py:164:.home.drusifer.Projects.via.via.core.match_record.FileMatchRecord:@4952+516
class:/home/drusifer/Projects/via/via/core/match_record.py:182:.home.drusifer.Projects.via.via.core.match_record.ImportMatchRecord:@5482+520
class:/home/drusifer/Projects/via/via/core/match_record.py:201:.home.drusifer.Projects.via.via.core.match_record.GlobalMatchRecord:@6016+547
class:/home/drusifer/Projects/via/via/core/match_record.py:220:.home.drusifer.Projects.via.via.core.match_record.HeaderMatchRecord:@6577+688

perhaps there is no class name Base in your test or it is not indexed for some reason

---

## Finding 5 — `-Vr` (references) only tracks names inside function bodies

**Severity:** Low — behavior is reasonable but underdocumented
**Source:** All SKILL.md files; `morpheus.docs/SKILL.md` documents `-Vr`

### Documented
```
["-mg", "SymbolName", "-Vr", "-mg", "*"]   → "Who references Symbol?"
```

### Actual behavior
The Python parser collects references by walking `ast.Name` nodes with `Load`
context **inside function and method bodies only**. The following usages are
**not** tracked as references:
- Using a class as a base class: `class Child(Base):`
- Import statements: `from module import Symbol`
- Module-level expressions

Only explicit name usage inside a function/method body is captured. For example,
`connect(host)` inside `run_connection()` IS tracked; `class ChildModel(BaseClass):`
is NOT.

### Options
- [ ] **A — Accept and document:** Add a note to SKILL.md files clarifying that
      `-Vr` finds references within function/method bodies only.
- [ ] **B — Expand the parser:** Extend reference tracking to include class
      bases, decorators, and module-level usages. More complete but changes semantics.


### Drew feeback
Agreed - we will tackle this in sprint 9

---

## Tests Added

`tests/uat/test_documented_queries_uat.py` — 52 tests total:
- 47 passing (verify correct behavior for all working documented patterns)
- 5 xfail (document each finding above with a concrete failing assertion)

The xfail tests will automatically become failures if the implementation is fixed
to match the documentation (options B in Findings 1, 2) — serving as regression
guards for future work.

---

## Decisions Requested

| # | Finding | Decision |
|---|---------|----------|
| 1 | Path-glob: fix docs or add path-match mode? | |
| 2 | Class call query: fix docs or expand implementation? | |
| 3 | Morpheus `-th` typo | Fix docs |
| 4 | Trin subclass query reversed | Fix docs |
| 5 | `-Vr` scope: document limitation or expand parser? | |




### Drew feeback

See above, let's fix documentation that is in accurate and remove examples that are not yet impemented
