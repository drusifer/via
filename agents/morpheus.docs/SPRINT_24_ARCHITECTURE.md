# Sprint 24 Architecture — Result-Stage-First Query Model

**Author**: Morpheus  
**Date**: 2026-04-12  
**Theme**: Formalize the result-stage-first query model so the first stage always determines what is returned and subsequent `--via`/`--sans` stages act as filters.

---

## Sprint Goal

Eliminate the inverted relationship semantics in the executor so that VIA queries read left-to-right:

```text
via <RESULT STAGE> [--via REL <FILTER STAGE>]... [--sans REL <EXCLUSION STAGE>]...
```

The first stage selects the symbol type and pattern for **returned results**. Every `--via`/`--sans` clause narrows those results by requiring (or excluding) a relationship to symbols matching the filter stage.

No backward compatibility is required. All existing relationship queries, canned expansions, tests, help text, and MCP schema examples will be rewritten to the new semantics.

---

## Non-Goals

- No new CLI flags beyond inverse relationship type names.
- No executor strategy refactor (polymorphic strategies deferred from Sprint 18).
- No changes to the DB schema or `symbol_references` table layout.
- No changes to parser/indexer relationship storage direction (`from_symbol_id` = source, `to_symbol_id` = target — this stays).

---

## The Problem: Inverted Executor Semantics

### Current Behavior (WRONG — anchor-first)

In `executor.py:_execute_relationship_query`, the pattern **before** `--via` is treated as the anchor/object (the known side), and the pattern **after** `--via` is what gets returned:

```python
# executor.py lines 219-233 (current)
# Pattern BEFORE --via: anchor/object filter (what we're relating through)
object_pattern = args.pattern
# Pattern AFTER --via: result/subject filter (what gets returned)
subject_pattern = rel.object_pattern
```

This means `via -mg "BaseClass" -tc --via inherits-from -mg "*" -tc` reads as "start from BaseClass, find things that inherit from it, return `*`". The user writes the anchor first and the wildcard result last.

### New Behavior (CORRECT — result-first)

The pattern **before** `--via` is what gets **returned**. The pattern **after** `--via` is the **filter anchor**:

```python
# executor.py (new)
# Pattern BEFORE --via: result — what gets returned
subject_pattern = args.pattern
# Pattern AFTER --via: filter anchor — what we require a relationship TO
object_pattern = rel.filter_pattern  # renamed from object_pattern
```

Now `via -mg "*" -tc --via inherits-from -mg "BaseClass" -tc` reads as "find all classes, filtered to those that inherit from BaseClass". The user writes what they want first.

---

## Command Model Reference

### Canonical Form

```text
via <RESULT STAGE> [--via|--sans REL <FILTER STAGE>]...
```

| Position | Role | What It Controls |
|----------|------|-----------------|
| First stage (before any `--via`/`--sans`) | **Result stage** | Symbol types and pattern of **returned results** |
| After `--via REL` | **Positive filter** | Requires returned symbols to have relationship REL to symbols matching this stage |
| After `--sans REL` | **Negative filter** | Excludes returned symbols that have relationship REL to symbols matching this stage |

### Forward vs Inverse Relationship Types

The DB stores relationships as `(from_symbol_id, to_symbol_id)`:
- `calls`: from=caller, to=callee
- `inherits-from`: from=child, to=parent
- `declares`: from=member, to=container
- `imports`: from=importer, to=imported
- `references`: from=referencing function, to=referenced symbol

**Forward** relationship names return the **source** (from) side. **Inverse** relationship names return the **target** (to) side. The DB storage is unchanged — an inverse is just the same row queried from the other direction.

| Forward | Inverse | Result returned from |
|---------|---------|---------------------|
| `calls` | `called-by` | from=caller / to=callee |
| `inherits-from` | `inherited-by` | from=child / to=parent |
| `imports` | `imported-by` | from=importer / to=imported |
| `references` | `referenced-by` | from=referencer / to=referenced |
| `declares` | `declared-in` | from=member / to=container |
| `covered-by` | `covers` | from=symbol / to=test |
| `http-calls` | `http-called-by` | from=caller / to=endpoint |

### Example Queries Under New Semantics

| Task | Command | Reading |
|------|---------|---------|
| Subclasses of BaseClass | `via -mg "*" -tc --via inherits-from -mg "BaseClass" -tc` | All classes → that inherit from BaseClass |
| What does ChildClass inherit from? | `via -mg "*" -tc --via inherited-by -mg "ChildClass" -tc` | All classes → that ChildClass inherits from (returns parents) |
| Functions calling connect | `via -mg "*" -tf --via calls -mg "connect" -tf` | All functions → that call connect |
| Unused functions (never called) | `via -mg "*" -tf --sans called-by -mg "*" -tf` | All functions → excluding those called by anything |
| Functions that call nothing | `via -mg "*" -tf --sans calls -mg "*" -tf` | All functions → excluding those that call anything |
| Files containing a class | `via -mg "*" -tF --via declared-in -mg "MyClass" -tc` | All files → that MyClass is declared in |
| Symbols declared in a file | `via -mg "*" --via declares -mg "utils.py" -tF` | All symbols → declared in utils.py |
| Functions calling connect (excluding test files) | `via -mg "*" -tf --via calls -mg "connect" -tf --sans declared-in -mg "*test*" -tF` | All functions → that call connect → excluding those in test files |

---

## Architecture Decisions

### Decision 1: Swap Subject/Object in Executor Relationship Dispatch

**File**: `via/pipeline/executor.py`

In `_execute_relationship_query`:

```python
# OLD (anchor-first):
object_pattern = args.pattern           # before --via = anchor
subject_pattern = rel.object_pattern    # after --via = returned

# NEW (result-first):
subject_pattern = args.pattern          # before --via = returned results
object_pattern = rel.filter_pattern     # after --via = filter anchor
```

The `db.query_relationships()` call arguments swap accordingly:
- `subject_pattern` (from side, returned) ← `args.pattern`
- `object_pattern` (to side, anchor) ← `rel.filter_pattern`
- `subject_type` ← `args.symbol_type`
- `object_type` ← first of `rel.filter_types`

For **forward** relationship types, `select_from` stays as `"s"` (source/from side).
For **inverse** relationship types, `select_from` flips to `"t"` (target/to side) — the executor passes `invert=True` to the DB method.

**Key insight**: The DB's `query_relationships` already has the right internal convention and `invert` support:
- `s` = source (`from_symbol_id`) — the entity performing the action (caller, child, importer)
- `t` = target (`to_symbol_id`) — the entity being acted upon (callee, parent, imported)
- `invert=True` → `select_from = "t"` — returns the target side

The swap is purely in how the executor maps CLI args to DB args. No DB changes needed.

### Decision 2: Add Inverse Relationship Types to ReferenceType

**File**: `via/core/relationship_types.py`

Add an inverse name mapping. Inverse names are **not** new enum values — they resolve to existing `ReferenceType` values plus an `inverted=True` flag.

```python
# New mapping in ReferenceType or a module-level dict
_INVERSE_MAP = {
    "called-by": ("calls", True),
    "inherited-by": ("inherits-from", True),
    "imported-by": ("imports", True),
    "referenced-by": ("references", True),
    "declared-in": ("declares", True),
    "covers": ("covered-by", True),
    "http-called-by": ("http-calls", True),
}
```

The parser resolves a relationship name to `(ReferenceType, inverted: bool)`. The `RelationshipFilter` gains an `inverted: bool = False` field.

The executor checks `rel.inverted` and passes `invert=True` to `db.query_relationships()` (for `--via`) or sets `invert_join=True` on `db.query_negative_relationships()` (for `--sans`).

**Consistency rule**: No hidden behavior. Canned queries are plain argv that any user can copy to the CLI and get the same result.

### Decision 3: Rename RelationshipFilter Fields

**File**: `via/pipeline/relationship_filter.py`

Rename fields to match new semantics and add the `inverted` flag:

| Old Name | New Name | Meaning |
|----------|----------|---------|
| `object_pattern` | `filter_pattern` | Pattern for the filter stage (after `--via`/`--sans`) |
| `object_match_syntax` | `filter_match_syntax` | Match syntax for the filter pattern |
| `object_types` | `filter_types` | Symbol types for the filter stage |
| *(new)* | `inverted` | If True, return from the target (to) side of the relationship |

This rename is non-functional (except `inverted`) but prevents confusion. Every reference to these fields across the codebase must be updated.

### Decision 4: Support Multiple `--via`/`--sans` Clauses (Parser Change)

**File**: `via/pipeline/parser.py`

Currently `_find_relationship_split` finds the **first** `--via`/`--sans` and splits args into two halves. For the new model, a single result stage can have multiple relationship filters chained:

```text
via -mg "*" -tf --via calls -mg "connect" --sans declared-in -mg "*test*" -tF
```

**Parser change**: After extracting the result stage (everything before the first `--via`/`--sans`), collect remaining `--via`/`--sans` clauses into a list of relationship filters.

**Data model change**: `PipelineStage.args.relationship` becomes `PipelineStage.args.relationships: list[RelationshipFilter]`.

**Executor change**: Apply the first relationship as the primary DB query. Apply subsequent relationships as post-filters on the result set.

**Sprint 24 scope**: Deliver multi-filter chaining. The parser collects all `--via`/`--sans` clauses. The executor applies the first as the primary query and subsequent ones sequentially. If only one clause exists, behavior is identical to current single-relationship support.

### Decision 5: Rewrite All Canned Query Expansions

**File**: `via/canned.py`

Every built-in canned query that uses `--via`/`--sans` must have its argument order corrected. With inverse relationship types, all canned queries are transparent argv — no hidden behavior.

| Query | Old Expansion | New Expansion |
|-------|--------------|---------------|
| `callers` | `["-mg", "{symbol}", "-tf", "--via", "calls", "-mg", "*", "-tf"]` | `["-mg", "*", "-tf", "--via", "calls", "-mg", "{symbol}", "-tf"]` |
| `methods-calling` | `["-mg", "{symbol}", "--via", "calls", "-mg", "*", "-tm"]` | `["-mg", "*", "-tm", "--via", "calls", "-mg", "{symbol}"]` |
| `inheritors` | `["-mg", "{symbol}", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"]` | `["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "{symbol}", "-tc"]` |
| `unused` | `["-mg", "*", "-tf", "--sans", "calls", "-mg", "*", "-tf"]` | `["-mg", "*", "-tf", "--sans", "called-by", "-mg", "*", "-tf"]` |
| `potentially-unused` | Same as unused | Same as unused |
| `dead-docs` | `["-mg", "*.md", "-tF", "--sans", "declares", "-mg", "*", "-tH"]` | `["-mg", "*.md", "-tF", "--sans", "declared-in", "-mg", "*", "-tH"]` |

**`callers` reading**: "Find all functions, filtered to those that call `{symbol}`" → returns callers of `{symbol}`.

**`unused` reading**: "Find all functions, excluding those called by anything" → returns functions nobody calls. Uses `called-by` (inverse of `calls`) so `--sans` checks the callee side.

**`dead-docs` reading**: "Find all markdown files, excluding those that have symbols declared in them" → returns .md files with no declared headers. Uses `declared-in` (inverse of `declares`) so `--sans` checks the container side.

### Decision 6: Update MCP Schema and CLI Help

**Files**: `via/mcp/schema.py`, `via/__main__.py`

All examples must be rewritten to result-first form. Add inverse relationship types to the valid REL list.

```python
# Old MCP schema example:
{"description": "Find all subclasses of Renderer",
 "args": ["-mg", "Renderer", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"]}

# New:
{"description": "Find all subclasses of Renderer",
 "args": ["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "Renderer", "-tc"]}
```

Valid REL types must list both forward and inverse:
```
inherits-from, inherited-by, calls, called-by, imports, imported-by,
references, referenced-by, declares, declared-in, covered-by, covers,
http-calls, http-called-by
```

### Decision 7: No DB Layer Changes

The DB's `query_relationships` and `query_negative_relationships` methods have the correct internal convention already:
- `subject_pattern` filters `s` (source/from_symbol_id)
- `object_pattern` filters `t` (target/to_symbol_id)
- `select_from="s"` returns source symbols
- `invert=True` returns target symbols
- `invert_join=True` (negative queries) flips the NOT EXISTS anchor

The only change is which CLI-side values get passed as `subject_pattern` vs `object_pattern`, and whether `invert`/`invert_join` is set based on the `inverted` flag. The DB methods themselves are unchanged.

---

## Affected Files — Complete Inventory

### Production Code

| File | Change | Risk |
|------|--------|------|
| `via/core/relationship_types.py` | Add inverse name map and resolution method | **Low** — additive |
| `via/pipeline/executor.py` | Swap subject/object mapping; pass `invert`/`invert_join` based on `rel.inverted` | **Medium** — core semantic change |
| `via/pipeline/relationship_filter.py` | Rename `object_*` → `filter_*`, add `inverted: bool` | **Low** — mechanical rename + one new field |
| `via/pipeline/parser.py` | Resolve inverse names; collect multiple `--via`/`--sans` into list; pass result-stage args as subject | **Medium** — parser restructuring |
| `via/pipeline/stage_builder.py` | Update `build_relationship_filter` field names, accept `inverted` | **Low** — follows rename |
| `via/canned.py` | Rewrite all relationship canned queries to result-first with inverse names | **Low** — data change only |
| `via/mcp/schema.py` | Rewrite description and all relationship examples | **Low** — text changes |
| `via/__main__.py` | Rewrite help text examples, `_build_pipeline_help` relationship section | **Low** — text changes |
| `via/api/query_builder.py` | Update `ViaQuery.to_cli_args()` and `build()` to use renamed fields | **Low** — follows rename |
| `via/web/api/query.py` | Update `_build_relationship_filter` to use renamed fields | **Low** — follows rename |

### Test Files (Direction Swap Required)

Every test that constructs a `RelationshipFilter` or a CLI argv with `--via`/`--sans` must have its arguments reordered and fields renamed. Tests that only test non-relationship queries are unaffected.

| Test File | Scope of Change |
|-----------|----------------|
| `tests/unit/test_relationship_executor.py` | **Heavy** — all `Namespace` constructions swap pattern/filter, rename fields, add `inverted` |
| `tests/unit/test_relationship_pipeline.py` | **Heavy** — all CLI argv strings reverse result/anchor order |
| `tests/unit/test_relationship_cli.py` | **Heavy** — all CLI argv strings and assertions reverse |
| `tests/unit/test_type_filter_relationships.py` | **Heavy** — all `Namespace` constructions swap |
| `tests/unit/test_pipeline_parser.py` | **Medium** — relationship-related tests swap, non-relationship tests unchanged |
| `tests/unit/test_web_query_relationship.py` | **Medium** — `_build_relationship_filter` field names change |
| `tests/integration/test_cli_relationships.py` | **Heavy** — all subprocess CLI invocations reverse |
| `tests/integration/test_cli_pipeline.py` | **Light** — only relationship examples if any |
| `tests/unit/test_sprint15_c1.py` | **Light** — help text assertions may need updating |
| `tests/unit/test_sprint22_c1.py` through `c3` | **Light** — error contract tests, some help text assertions |
| `tests/unit/test_sprint23_c1.py` through `c2` | **Light** — canned/help assertions |
| `tests/uat/test_sprint5_uat.py` | **Medium** — UAT relationship queries reverse |
| `tests/uat/test_documented_queries_uat.py` | **Medium** — documented query argv reverses |

---

## Behavioral Contract for Tests

This section defines the **expected behavior** under the new semantics. Tests should be rewritten to assert these behaviors.

### Simple Match (No Relationship) — UNCHANGED

```python
# via -mg "*" -tc → all classes
args = Namespace(pattern="*", symbol_type="class", relationship=None)
# Returns: all class symbols matching "*"
```

### Positive Relationship (`--via`) — Forward

```
via -mg "*" -tc --via inherits-from -mg "BaseClass" -tc
```

**Semantics**: Find all classes (result stage), filtered to those that inherit from BaseClass (filter stage).

**Namespace construction**:
```python
args = Namespace(
    pattern="*",               # RESULT: what gets returned
    symbol_type="class",
    symbol_types=["class"],
    relationship=RelationshipFilter(
        relationship_type=RelationshipType.INHERITS_FROM,
        filter_pattern="BaseClass",    # FILTER: the anchor
        filter_match_syntax="glob",
        filter_types=["class"],
        is_negative=False,
        inverted=False,           # Forward: return from (source) side
    ),
)
```

**DB call**: `query_relationships(relationship_type="inherits-from", subject_pattern="*", object_pattern="BaseClass", subject_type="class", object_type="class", invert=False)`

**Returns**: ChildA, ChildB (they inherit from BaseClass). Source/from side.

### Positive Relationship (`--via`) — Inverse

```
via -mg "*" -tc --via inherited-by -mg "ChildClass" -tc
```

**Semantics**: Find all classes that ChildClass inherits from (returns parents).

**Namespace construction**:
```python
args = Namespace(
    pattern="*",
    symbol_type="class",
    symbol_types=["class"],
    relationship=RelationshipFilter(
        relationship_type=RelationshipType.INHERITS_FROM,
        filter_pattern="ChildClass",
        filter_match_syntax="glob",
        filter_types=["class"],
        is_negative=False,
        inverted=True,            # Inverse: return to (target) side
    ),
)
```

**DB call**: `query_relationships(relationship_type="inherits-from", subject_pattern="*", object_pattern="ChildClass", subject_type="class", object_type="class", invert=True)`

**Returns**: BaseClass (what ChildClass inherits from). Target/to side.

### Positive Relationship — Calls (Forward)

```
via -mg "*" -tf --via calls -mg "helper_func" -tf
```

**Semantics**: Find all functions, filtered to those that call helper_func.

**DB call**: `query_relationships(relationship_type="calls", subject_pattern="*", object_pattern="helper_func", subject_type="function", object_type="function", invert=False)`

**Returns**: main_func (it calls helper_func). The caller (from side) is returned.

### Positive Relationship — Called-by (Inverse)

```
via -mg "*" -tf --via called-by -mg "main_func" -tf
```

**Semantics**: Find all functions that main_func calls (returns callees).

**DB call**: `query_relationships(relationship_type="calls", subject_pattern="*", object_pattern="main_func", ..., invert=True)`

**Returns**: helper_func (main_func calls it). The callee (to side) is returned.

### Positive Relationship — References (Forward)

```
via -mg "*" -tf -tm --via references -mg "MY_CONSTANT" -tg
```

**Semantics**: Find all functions and methods, filtered to those that reference MY_CONSTANT.

**DB call**: `query_relationships(relationship_type="references", subject_pattern="*", object_pattern="MY_CONSTANT", subject_type=None, object_type="global", invert=False)`

**Returns**: shared_logic (method), use_constant (function). The referencing symbols (from side).

### Positive Relationship — References with Result Type Filter

```
via -mg "*" -tm --via references -mg "MY_CONSTANT" -tg
```

**Semantics**: Find only **methods** that reference MY_CONSTANT.

**DB call**: `query_relationships(..., subject_type="method", ...)`

**Returns**: shared_logic only (it's a method). use_constant is a function and is excluded.

### Negative Relationship (`--sans`) — Forward

```
via -mg "*" -tc --sans inherits-from -mg "*" -tc
```

**Semantics**: Find all classes, excluding those that inherit from anything.

**DB call**: `query_negative_relationships(relationship_type="inherits-from", subject_pattern="*", object_pattern="*", subject_type="class", invert_join=False)`

**Returns**: BaseClass (it inherits from nothing). ChildA, ChildB excluded.

### Negative Relationship — Functions That Call Nothing

```
via -mg "*" -tf --sans calls -mg "*" -tf
```

**Semantics**: Find all functions, excluding those that call anything.

**DB call**: `query_negative_relationships(relationship_type="calls", ..., invert_join=False)`

**Returns**: helper_func (it calls nothing). main_func excluded (it calls helper_func).

### Negative Relationship — Unused Functions (`--sans called-by`)

```
via -mg "*" -tf --sans called-by -mg "*" -tf
```

**Semantics**: Find all functions, excluding those called by anything (nobody calls them).

**DB call**: `query_negative_relationships(relationship_type="calls", ..., invert_join=True)`

**Returns**: Functions that nobody calls. helper_func is called by main_func → excluded. main_func and any leaf functions with no callers → returned.

### Negative Relationship — Declared-in (Inverse)

```
via -mg "*.md" -tF --sans declared-in -mg "*" -tH
```

**Semantics**: Find .md files excluding those that have any headers declared in them.

**DB call**: `query_negative_relationships(relationship_type="declares", ..., invert_join=True)`

**Returns**: Markdown files with no header symbols.

### Wrong Type Filter Returns Empty

```
via -mg "*" -tc --via references -mg "MY_CONSTANT" -tc
```

**Semantics**: Find classes that reference MY_CONSTANT. But MY_CONSTANT is a global (-tg), and the filter stage says -tc (class). No class named MY_CONSTANT exists.

**Returns**: Empty. The filter anchor doesn't match.

### Canned Query: `callers`

```
via --canned callers --args symbol=parse_args
```

**Expands to**: `via -mg "*" -tf --via calls -mg "parse_args" -tf`

**Semantics**: Find all functions that call parse_args.

### Canned Query: `inheritors`

```
via --canned inheritors --args symbol=BaseClass
```

**Expands to**: `via -mg "*" -tc --via inherits-from -mg "BaseClass" -tc`

**Semantics**: Find all classes that inherit from BaseClass.

### Canned Query: `unused`

```
via --canned unused
```

**Expands to**: `via -mg "*" -tf --sans called-by -mg "*" -tf`

**Semantics**: Find functions that are never called by anything (nobody calls them). Uses `called-by` (inverse of `calls`) so `--sans` checks the callee side. No hidden behavior — the same argv works on the command line.

### Canned Query: `dead-docs`

```
via --canned dead-docs
```

**Expands to**: `via -mg "*.md" -tF --sans declared-in -mg "*" -tH`

**Semantics**: Find .md files that have no headers declared in them. Uses `declared-in` (inverse of `declares`).

### Limit Enforcement

Limits apply to the result stage. `via -mg "*" -tc -n 1 --via inherits-from -mg "BaseClass"` returns at most 1 class.

### Pattern Matching on Filter Stage

Glob patterns on the filter side narrow the anchor:

```
via -mg "*" -tc --via inherits-from -mg "*Base*" -tc
```

**Semantics**: Find classes that inherit from any class matching `*Base*`.

---

## Cycle Plan

### Cycle 1: Inverse Relationship Types + Executor Direction Swap + RelationshipFilter Rename

**Scope**:
1. Add inverse relationship name map to `via/core/relationship_types.py`
2. Rename `RelationshipFilter` fields: `object_pattern` → `filter_pattern`, `object_types` → `filter_types`, `object_match_syntax` → `filter_match_syntax`; add `inverted: bool = False`
3. Update `stage_builder.py` to use new field names and accept `inverted`
4. Update parser to resolve inverse names and set `inverted=True` on the filter
5. Swap subject/object mapping in `executor.py:_execute_relationship_query`; pass `invert=True` when `rel.inverted`
6. Swap subject/object mapping in `executor.py:_execute_negative_relationship_query`; pass `invert_join=True` when `rel.inverted`
7. Update `api/query_builder.py` to use new field names
8. Update `web/api/query.py` to use new field names
9. Rewrite all unit tests for executor, relationship filter, type filter, and pipeline parser
10. Run full test suite

**Exit criteria**: `make test` passes. All relationship queries use result-first semantics. Inverse relationship types work for both `--via` and `--sans`.

### Cycle 2: Canned Queries + MCP Schema + CLI Help

**Scope**:
1. Rewrite `canned.py` built-in query expansions to result-first with inverse names where needed
2. Rewrite `mcp/schema.py` examples and description text; add inverse types to valid REL list
3. Rewrite `__main__.py` help text examples and `_build_pipeline_help` relationship section
4. Update sprint-specific tests that assert help text or canned expansions
5. Run full test suite

**Exit criteria**: `make test` passes. `via --help`, MCP schema, and `--canned` all use result-first examples with inverse types documented.

### Cycle 3: Integration Tests + UAT + Documentation

**Scope**:
1. Rewrite `tests/integration/test_cli_relationships.py` subprocess invocations
2. Rewrite `tests/uat/test_sprint5_uat.py` and `test_documented_queries_uat.py`
3. Update `docs/USER_GUIDE.md` and `agents/PROJECT.md` examples
4. Smith HCI review of help text and MCP schema wording
5. Run full test suite including integration and UAT

**Exit criteria**: `make test` passes including integration and UAT. Smith approves wording.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DB query returns wrong results after swap | Medium | High | Behavioral contract above defines expected results per test case. Write tests first. |
| Inverse relationship invert flag not propagated correctly | Medium | Medium | Test both `--via called-by` and `--sans called-by` explicitly. |
| Help text / MCP schema has stale anchor-first examples | Low | Medium | Grep for old patterns (`-mg "BaseClass" -tc --via inherits-from -mg "*"`) after rewrite. |
| `declares` special-case container check breaks | Low | Medium | `declares` container check moves to filter stage validation — test explicitly. |
| Web UI relationship queries silently break | Low | Medium | `test_web_query_relationship.py` covers the web API path. |
| Multi-filter chain (`--via` + `--sans` on same query) edge cases | Medium | Medium | Test the combined case explicitly with the `calls` + `declared-in` example. |
