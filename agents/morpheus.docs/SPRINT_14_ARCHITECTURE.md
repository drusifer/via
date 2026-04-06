# Sprint 14 Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-05
**Reference**: `agents/cypher.docs/SPRINT_14_USER_STORIES.md`, Smith review `agents/smith.docs/SPRINT_14_REVIEW.md`

---

## Summary

Sprint 14 adds three new match-stage filters (`--lang`, `--subtype`, JS `calls`), fixes the web UI relationship card, and repairs doc bugs. All changes are narrow, low-risk additions to existing extension points.

---

## S14-1: JS/TS Relationship Extraction — RESCOPED

### Finding (from live testing)
**Three of four JS/TS relationship types already work:**

| Relationship | Status | How |
|---|---|---|
| `declares` | ✅ Works | `_store_declares_relationships()` is language-agnostic |
| `imports` | ✅ Works | `_store_import_symbols()` processes `parse_result.imports` for all languages |
| `inherits-from` | ✅ Works | `_store_class_symbols()` reads `cls.bases` for all languages |
| `calls` | ❌ Missing | `JavaScriptParser.parse()` does not populate `ParseResult.calls` |

**Rescoped**: S14-1 = add `calls` extraction to `JavaScriptParser` + add JS relationship tests. **Downsize from 3pt → 2pt**.

### Design Decision

**Where**: Add `_extract_calls()` to `JavaScriptParser`, called from `parse()`.

**Pattern**: Mirror `PythonParser._extract_calls()`. Populate `ParseResult.calls` with `CallEntity` objects.

**Scope**: Within-file call sites only (same limitation as Python). Use tree-sitter to walk `call_expression` nodes.

```python
# In JavaScriptParser.parse():
result.calls = self._extract_calls(tree, content)

def _extract_calls(self, tree, content: str) -> List[CallEntity]:
    """Extract within-file function call sites."""
    calls = []
    for node in tree.root_node.children:  # walk top-level + nested
        # find call_expression nodes, extract callee name
        ...
    return calls
```

**No `IndexingService` changes needed.** `_store_relationships(file_info, parse_result.calls, 'calls', ...)` already exists and is called for all languages.

### Tests Required
- Unit test: JS file with `foo()` call → `CallEntity` in `ParseResult.calls`
- Integration test: `via -mg 'callee' --via calls -mg '*' -tf` returns JS caller file
- Integration test: `via -mg 'React.Component' --via inherits-from -mg '*' -tc` — add a JS fixture with `class Foo extends Bar {}`

---

## S14-2: `--lang` Filter Flag

### Design Decision (OQ-2 resolved)

**`symbols.language` is stored directly on the `symbols` table** (confirmed in `via/db/schema.py:162-167` — Sprint 11 added the column with backfill and index `idx_symbols_language`). No JOIN to `files` needed.

**Filter placement**: Match-stage modifier, same tier as `--newerthan`. The `Executor._execute_match_stage()` reads `args.lang` and passes to `db.match()`.

**Implementation path** (4 files):

1. **`via/core/flag_groups.py`**: Add to `MATCH_FLAGS` group:
   ```python
   Flag(FlagGroup.MATCH, None, 'lang', 'language_filter', None, 'Filter by language: py/python, js/javascript, ts/typescript, md/markdown'),
   ```

2. **`via/__main__.py`**: Add `--lang` to the match stage `argparse.ArgumentParser`. Normalise to canonical form in `__main__`:
   ```python
   LANG_ALIASES = {
       'py': 'python', 'python': 'python',
       'js': 'javascript', 'javascript': 'javascript',
       'ts': 'typescript', 'typescript': 'typescript',
       'md': 'markdown', 'markdown': 'markdown',
   }
   ```
   Validate on parse; raise `argparse.ArgumentError` with `"Valid: py/python, js/javascript, ts/typescript, md/markdown"`.

3. **`via/pipeline/executor.py`**: Read `getattr(args, 'language_filter', None)` and pass to `db.match()`.

4. **`via/db/store.py`**: Add `language: Optional[str] = None` param to `match()` and `_match_with_regex()`. When set: `where_parts.append("s.language = ?"); params.append(language)`.

**No schema changes.** The column and index exist.

---

## S14-3: `--subtype` Filter Flag

Same pattern as `--lang`. The `symbols.symbol_subtype` column exists with index `idx_symbols_subtype`.

**Implementation path** (same 4 files as S14-2, implement in the same pass):

1. **`flag_groups.py`**: Add `Flag(FlagGroup.MATCH, None, 'subtype', 'symbol_subtype_filter', None, '--subtype TYPE: case-sensitive; unknown values return no results')`.

2. **`__main__.py`**: Add `--subtype` to match stage parser. No validation (open-ended values are fine — document in help text).

3. **`executor.py`**: Read `getattr(args, 'symbol_subtype_filter', None)`, pass to `db.match()`.

4. **`store.py`**: Add `subtype: Optional[str] = None` to `match()`. When set: `where_parts.append("s.symbol_subtype = ?"); params.append(subtype)`.

**Combine S14-2 and S14-3 into one implementation pass** — both touch the same 4 files with the same pattern. Neo should implement both in a single cycle.

---

## S14-4: Web UI Relationship Card UX

### Design Decision (OQ-3 resolved)

**Segmented control** (two-button toggle: `With --via | Without --sans`). Render as adjacent pill buttons — CSS only, no new dependencies.

**Conditional visibility**: The mode selector `<div>` gets `display: none` when the relationship dropdown value is `""`. Show on `change` event of the relationship dropdown.

**API change**: `"invert": bool` → `"mode": "via" | "sans"` in POST body.

**Files**:

| File | Change |
|---|---|
| `via/web/template.py:508-509` | Replace `<label>` invert toggle with `<div id="rel-mode">` segmented control |
| `via/web/static/app.js:94` | Send `mode: ($('invert').checked ? 'sans' : 'via')` → `mode: relMode()` where `relMode()` reads the segmented control |
| `via/web/api/query.py:147` | `invert = body.get("invert", False)` → `is_negative = body.get("mode") == "sans"` |

**Backward compat**: The API change is internal (browser → server, same process). No public API to preserve.

---

## S14-5: USER_GUIDE.md Fixes

No architecture needed. Direct edits to `docs/USER_GUIDE.md` at lines ~143, ~219, ~732. Neo implements directly.

---

## Implementation Order (Cycle Plan)

| Cycle | Stories | Notes |
|---|---|---|
| 1 | S14-1 | JS `calls` extraction + JS relationship tests (2pt) |
| 2 | S14-2 + S14-3 + S14-5 | `--lang` + `--subtype` + doc fixes (5pt in one pass) |
| 3 | S14-4 | Web UI relationship card (2pt) |

---

## Revised Point Estimate

| Story | Original | Revised | Reason |
|---|---|---|---|
| S14-1 | 3pt | 2pt | `declares`/`imports`/`inherits-from` already work; only `calls` missing |
| S14-2 | 2pt | 2pt | unchanged |
| S14-3 | 2pt | 1pt | identical pattern to S14-2, implement in same pass |
| S14-4 | 2pt | 2pt | unchanged |
| S14-5 | 1pt | 1pt | unchanged |
| **Total** | **10pt** | **8pt** | |

---

## Open Questions — Resolved

**OQ-1 (S14-1 relationship placement)**: Add `_extract_calls()` to `JavaScriptParser.parse()`. `ParseResult.references` not needed for this sprint — `calls` uses `ParseResult.calls` which already goes through `_store_relationships`. ✅

**OQ-2 (S14-2 `--lang` join strategy)**: `symbols.language` is a direct column on `symbols`, not a join to `files`. `WHERE s.language = ?` with indexed column. ✅

**OQ-3 (S14-3 placement)**: `--lang` and `--subtype` are match-stage modifiers (same tier as `--newerthan`). They belong in the `match_parser` args, read by `executor.py`, passed to `db.match()`. ✅

---

@Neo: Ready to implement. Start with Cycle 1 (S14-1 — JS `calls` extraction). Key files: `via/parsers/javascript_parser.py`, `via/db/store.py`. Revised total: 8pts across 3 cycles.
