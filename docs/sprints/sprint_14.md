# Sprint 14 Consolidated Documentation

This document consolidates all documentation for Sprint 14.

## Table of Contents

- [SPRINT_14_USER_STORIES.md](#sprint-14-user-storiesmd) (originally `agents/cypher.docs/SPRINT_14_USER_STORIES.md`)

- [SPRINT_14_ARCHITECTURE.md](#sprint-14-architecturemd) (originally `agents/morpheus.docs/SPRINT_14_ARCHITECTURE.md`)

- [SPRINT_14_REVIEW.md](#sprint-14-reviewmd) (originally `agents/smith.docs/SPRINT_14_REVIEW.md`)


---


## SPRINT_14_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_14_USER_STORIES.md`


## Sprint 14 — Query Extensions + Usability Fixes

**Author**: Cypher (PM)
**Date**: 2026-04-05
**Theme**: Complete JS/TS query capabilities (S11-3 + S11-4), add `--subtype` filtering, fix web UI relationship UX, and repair remaining USER_GUIDE.md bugs.
**Points**: ~11pts
**Baseline**: ~1121 tests (end of Sprint 13)

---

### Sprint Goal

Fill in the gaps left by Sprints 11–13: JS/TS relationship extraction was deferred, `--lang` and `--subtype` filters were never built despite the DB storing both fields, the web UI's relationship card still uses the old `invert` model from before Sprint 13, and four USER_GUIDE.md bugs from Smith's review remain unfixed. This sprint makes what's partially-there fully usable.

---

### Stories

---

#### S14-1: JS/TS Relationship Extraction (P0, 3pt)

**As a** developer querying a JavaScript or TypeScript codebase,
**I want** `via -mg 'MyClass' -tc --via inherits-from -mg '*' -tc` to show JS/TS class inheritance,
**so that** I can navigate JS/TS class hierarchies the same way I do in Python.

##### Background

`JavaScriptParser` (`via/parsers/javascript_parser.py:40`) was shipped in Sprint 11. It extracts functions, classes, imports, and globals with correct `bases` and `ImportEntity` records. However, it does **not** write to `symbol_references` — so no relationship queries work on JS/TS symbols. The indexing service must call relationship-extraction logic for JS/TS files just as it does for Python.

##### Acceptance Criteria

1. **`inherits-from`**: `class Foo extends Bar {}` → `symbol_references` row `Foo → Bar` with `ref_type='inherits-from'`. Works with `--via inherits-from`.

2. **`imports`**: Each `ImportEntity` from the JS parser → `symbol_references` row from the containing file to the imported module name with `ref_type='imports'`. Works with `--via imports` and `--sans imports`.

3. **`declares`**: Each top-level function and class → `symbol_references` row from the containing file to the symbol with `ref_type='declares'`. Works with `--via declares` and `--sans declares`.

4. **`calls`**: Within-file function call sites (best-effort, where tree-sitter resolves the name). Works with `--via calls`. No cross-file resolution required.

5. **No Python regressions**: All existing Python relationship tests pass unchanged.

6. **Tests**:
   - Unit test: `class Foo extends Bar` in a `.js` fixture → `inherits-from` row in DB
   - Unit test: `import { X } from 'mod'` → `imports` row
   - Unit test: `export function foo() {}` at top level → `declares` row
   - Integration test: `via index` on a JS fixture dir + relationship query returns correct results

**Files expected to change:**
- `via/services/indexing.py` — add relationship extraction call after JS/TS parse
- `via/parsers/javascript_parser.py` — add `_extract_relationships()` or similar
- `via/db/store.py` — confirm `store_references()` handles JS file references correctly

---

#### S14-2: `--lang` Filter Flag (P0, 2pt)

**As a** developer with a mixed Python+JS/TS codebase,
**I want** `via -mg '*service*' -tc --lang js` to return only JavaScript classes,
**so that** I can narrow searches to one language without using full-path regex hacks.

##### Background

`symbols.language` is populated from `ParseResult.language` for all indexed files (confirmed in Sprint 11). The DB has the data; there is no CLI flag to filter by it. The `via/core/flag_groups.py` defines `MATCH_FLAGS`, `TYPE_FLAGS`, etc — `--lang` would be a new option-stage flag (applies after match, like `--newerthan`).

##### Acceptance Criteria

1. **Flag**: `--lang <language>` is valid after any match stage (`-mg`, `-mr`, `-ms`).
   ```
   via -mg '*hook*' -tf --lang js          # JS functions only
   via -mg 'BaseModel' -tc --lang py       # Python classes only
   via -mg '*' -tH --lang md               # All markdown headers
   ```

2. **Values** (case-insensitive): `py` / `python`, `js` / `javascript`, `ts` / `typescript`, `md` / `markdown`. Invalid value produces:
   ```
   Error: Unknown --lang 'go'. Valid: py/python, js/javascript, ts/typescript, md/markdown.
   ```

3. **DB filter**: `--lang` adds a `WHERE files.language = ?` JOIN clause — not a post-query Python filter.

4. **Works on all symbol types**: `--lang js -tF`, `--lang py -tc`, `--lang md -tH` all work.

5. **Tests**: Unit tests for `--lang` parsing and error; integration tests filtering by each language on a multi-language fixture.

**Files expected to change:**
- `via/core/flag_groups.py` — add `--lang` flag definition
- `via/__main__.py` — parse `--lang` and pass to pipeline
- `via/db/store.py` or `via/pipeline/executor.py` — apply language filter in query

---

#### S14-3: `--subtype` Filter Flag (P1, 2pt)

**As a** developer using via on a TypeScript codebase,
**I want** `via -mg '*' -tc --subtype interface` to return only TypeScript interfaces,
**so that** I can distinguish interfaces from classes without grepping file content.

##### Background

`symbols.symbol_subtype` is in the schema (`via/db/schema.py:66`) and populated by `JavaScriptParser` for:
- `symbol_subtype='interface'` — TypeScript `interface` declarations
- `symbol_subtype='enum'` — TypeScript `enum` declarations
- `symbol_subtype='arrow_function'` — Arrow functions assigned to `const`

No CLI flag exposes this field. Adding `--subtype` makes these queryable.

##### Acceptance Criteria

1. **Flag**: `--subtype <subtype>` is valid after any match stage, parallel to `--lang`.
   ```
   via -mg '*' -tc --subtype interface       # TS interfaces only
   via -mg '*' -tc --subtype enum            # TS enums only
   via -mg '*' -tf --subtype arrow_function  # Arrow functions only
   ```

2. **Valid values**: Any non-empty string is accepted (stored values are open-ended). Unknown values silently return no results (the DB WHERE clause handles it naturally). The `--help` text must include: *"`--subtype` is case-sensitive; unknown values return no results."*

3. **DB filter**: `WHERE symbols.symbol_subtype = ?` — not a post-query filter.

4. **Combinable with `--lang`**: `--lang ts --subtype interface` works correctly.

5. **Tests**: Unit test for `--subtype` flag parsing; integration test filtering TS interfaces vs classes in a fixture.

**Files expected to change:**
- `via/core/flag_groups.py` — add `--subtype` flag
- `via/__main__.py` — parse and pass to pipeline
- `via/db/store.py` or executor — apply in query

---

#### S14-4: Web UI Relationship Card — `--via`/`--sans` UX (P1, 2pt)

**As a** web UI user,
**I want** the relationship card to show a clear "Positive (--via)" / "Negative (--sans)" mode selector,
**so that** the UI matches the Sprint 13 CLI redesign and the `--invert` mental model is gone.

##### Background

The Sprint 13 CLI redesign replaced `--invert` with `--via` (positive) and `--sans` (negative) as distinct operators with symmetric semantics. The web UI (`via/web/template.py:508-509`) still shows an "Invert direction (--sans)" toggle checkbox. The API body (`via/web/api/query.py:147`) still accepts `invert: bool`. This creates a mismatch: CLI users learn `--via`/`--sans`, then find the web UI calling the same thing "invert".

##### Acceptance Criteria

1. **Replace invert checkbox**: Remove the "Negative relationship (--sans)" toggle from the relationship card.

2. **Add mode selector**: Add a segmented control or radio group with two options:
   - **"With (--via)"** — positive relationship (default)
   - **"Without (--sans)"** — negative relationship

3. **API body updated**: Replace `"invert": bool` with `"mode": "via" | "sans"` in the JSON body sent to `POST /api/query`. `"via"` maps to `is_negative=False`, `"sans"` maps to `is_negative=True` in `_build_relationship_filter()`.

4. **Conditional visibility**: Mode selector is only shown when the relationship type dropdown has a non-empty selection. Clearing the relationship dropdown hides the mode selector and resets mode to "With".

5. **Reset clears to "With"**: Clicking Reset sets mode back to "With (--via)".

5. **No functional regression**: All existing relationship queries (positive and negative) continue to work.

6. **Tests**: Update API unit tests that assert `"invert"` in body → assert `"mode"` instead.

**Files expected to change:**
- `via/web/template.py` — replace invert toggle with mode selector
- `via/web/static/app.js` — send `mode` instead of `invert`, update reset
- `via/web/api/query.py` — read `body.get("mode")` instead of `body.get("invert")`

---

#### S14-5: Fix USER_GUIDE.md — Remaining Smith Bugs (P0, 1pt)

**As a** new user reading the USER_GUIDE,
**I want** the documentation to accurately describe current `via` behavior,
**so that** I can follow examples without hitting errors or confusion.

##### Background

Smith's review (`agents/smith.docs/USER_GUIDE_REVIEW_2026_03_25.md`) found 7 bugs. The `--sans has`/`--sans declares` crashes (Bugs 4, 6, 7) and crash examples were removed in commit `c131619`. Four bugs remain unfixed.

##### Acceptance Criteria — Fix all four remaining bugs

**Bug 1 (P1)**: Notes inside code fence at lines ~143–146.
- Close the code fence after the syntax line.
- Move `**Note on filtering**` and `**Note on multiple types**` outside as regular paragraphs.

**Bug 2 (P1)**: `--via` misdescribed as a "filter chaining operator" (line ~143).
- Remove the "Note on filtering" paragraph entirely (it documents an implementation detail and gives the wrong mental model).
- If pipeline chaining deserves a note: *"Use `--via <rel>` to add a relationship stage — see [Relationship Queries](#relationship-queries)."*

**Bug 3 (P1)**: "Add `--via` followed by output flags to change format" (line ~219).
- Replace with: *"Output flags control how results are rendered:"*

**Bug 5 (P0)**: `cut -d: -tf2` → `cut -d: -f2` (line ~732).
- Fix the flag typo.

**Structural Issue 1 (P2)**: Output Formats section order — `-f<X>` (format modifiers) appears before `-o<X>` (primary output flags).
- Reorder: `-o<X>` table first, then `-f<X>` table with a note that these are secondary format modifiers.

---

### Sprint Summary

| Story | Points | Priority | Owner |
|-------|--------|----------|-------|
| S14-1: JS/TS relationship extraction | 3 | P0 | Neo |
| S14-2: `--lang` filter flag | 2 | P0 | Neo |
| S14-5: Fix USER_GUIDE.md bugs | 1 | P0 | Neo |
| S14-3: `--subtype` filter flag | 2 | P1 | Neo |
| S14-4: Web UI `--via`/`--sans` UX | 2 | P1 | Neo |
| **Total** | **10** | | |

---

### Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S14-1 + S14-5 | JS/TS relationships + doc fixes |
| 2 | S14-2 + S14-3 | `--lang` + `--subtype` flags (both touch flag_groups + executor) |
| 3 | S14-4 | Web UI relationship card redesign |

---

### Key Files

| File | Relevance |
|------|-----------|
| `via/parsers/javascript_parser.py:40` | `JavaScriptParser` — add relationship extraction |
| `via/core/flag_groups.py` | Add `--lang` and `--subtype` flag definitions |
| `via/__main__.py` | Parse new flags, pass to pipeline |
| `via/db/store.py` | Apply language/subtype filters in queries |
| `via/web/template.py:508` | Replace invert toggle with mode selector |
| `via/web/static/app.js:94` | Send `mode` instead of `invert` |
| `via/web/api/query.py:147` | Read `mode` instead of `invert` |
| `docs/USER_GUIDE.md:143,219,732` | Fix remaining Smith bugs |

---

### Open Questions for Morpheus

1. **S14-1 — Relationship extraction placement**: Should JS relationship extraction happen inside `JavaScriptParser.parse()` (returns a `relationships` field in `ParseResult`) or in `IndexingService` post-parse? Recommend: extend `ParseResult` with a `relationships` list, mirror Python approach.

2. **S14-2 — `--lang` join strategy**: `symbols.language` is stored via `files.language` — is there a `language` column on `symbols` directly, or does the query need a JOIN to `files`? Confirm the current schema and recommend the cheapest query path.

3. **S14-3 — `--subtype` + `--lang` ordering**: Should `--lang` and `--subtype` be parsed as part of the match stage args (alongside `-tc`, `-tf`, etc.) or as inter-stage options (alongside `--newerthan`)? Recommend: same stage as type flags (they refine the match, not the relationship).

@Smith: Please review these stories before Morpheus begins arch. Key UX questions:
- S14-2: Are `py`/`js`/`ts`/`md` the right `--lang` shorthands? Should `javascript` and `typescript` also be accepted?
- S14-3: Should invalid `--subtype` values silently return empty results or raise an error?
- S14-4: Segmented control vs radio buttons for `--via`/`--sans` — which is clearer in the card context?


---


## SPRINT_14_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_14_ARCHITECTURE.md`


## Sprint 14 Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-05
**Reference**: `agents/cypher.docs/SPRINT_14_USER_STORIES.md`, Smith review `agents/smith.docs/SPRINT_14_REVIEW.md`

---

### Summary

Sprint 14 adds three new match-stage filters (`--lang`, `--subtype`, JS `calls`), fixes the web UI relationship card, and repairs doc bugs. All changes are narrow, low-risk additions to existing extension points.

---

### S14-1: JS/TS Relationship Extraction — RESCOPED

#### Finding (from live testing)
**Three of four JS/TS relationship types already work:**

| Relationship | Status | How |
|---|---|---|
| `declares` | ✅ Works | `_store_declares_relationships()` is language-agnostic |
| `imports` | ✅ Works | `_store_import_symbols()` processes `parse_result.imports` for all languages |
| `inherits-from` | ✅ Works | `_store_class_symbols()` reads `cls.bases` for all languages |
| `calls` | ❌ Missing | `JavaScriptParser.parse()` does not populate `ParseResult.calls` |

**Rescoped**: S14-1 = add `calls` extraction to `JavaScriptParser` + add JS relationship tests. **Downsize from 3pt → 2pt**.

#### Design Decision

**Where**: Add `_extract_calls()` to `JavaScriptParser`, called from `parse()`.

**Pattern**: Mirror `PythonParser._extract_calls()`. Populate `ParseResult.calls` with `CallEntity` objects.

**Scope**: Within-file call sites only (same limitation as Python). Use tree-sitter to walk `call_expression` nodes.

```python
## In JavaScriptParser.parse():
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

#### Tests Required
- Unit test: JS file with `foo()` call → `CallEntity` in `ParseResult.calls`
- Integration test: `via -mg 'callee' --via calls -mg '*' -tf` returns JS caller file
- Integration test: `via -mg 'React.Component' --via inherits-from -mg '*' -tc` — add a JS fixture with `class Foo extends Bar {}`

---

### S14-2: `--lang` Filter Flag

#### Design Decision (OQ-2 resolved)

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

### S14-3: `--subtype` Filter Flag

Same pattern as `--lang`. The `symbols.symbol_subtype` column exists with index `idx_symbols_subtype`.

**Implementation path** (same 4 files as S14-2, implement in the same pass):

1. **`flag_groups.py`**: Add `Flag(FlagGroup.MATCH, None, 'subtype', 'symbol_subtype_filter', None, '--subtype TYPE: case-sensitive; unknown values return no results')`.

2. **`__main__.py`**: Add `--subtype` to match stage parser. No validation (open-ended values are fine — document in help text).

3. **`executor.py`**: Read `getattr(args, 'symbol_subtype_filter', None)`, pass to `db.match()`.

4. **`store.py`**: Add `subtype: Optional[str] = None` to `match()`. When set: `where_parts.append("s.symbol_subtype = ?"); params.append(subtype)`.

**Combine S14-2 and S14-3 into one implementation pass** — both touch the same 4 files with the same pattern. Neo should implement both in a single cycle.

---

### S14-4: Web UI Relationship Card UX

#### Design Decision (OQ-3 resolved)

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

### S14-5: USER_GUIDE.md Fixes

No architecture needed. Direct edits to `docs/USER_GUIDE.md` at lines ~143, ~219, ~732. Neo implements directly.

---

### Implementation Order (Cycle Plan)

| Cycle | Stories | Notes |
|---|---|---|
| 1 | S14-1 | JS `calls` extraction + JS relationship tests (2pt) |
| 2 | S14-2 + S14-3 + S14-5 | `--lang` + `--subtype` + doc fixes (5pt in one pass) |
| 3 | S14-4 | Web UI relationship card (2pt) |

---

### Revised Point Estimate

| Story | Original | Revised | Reason |
|---|---|---|---|
| S14-1 | 3pt | 2pt | `declares`/`imports`/`inherits-from` already work; only `calls` missing |
| S14-2 | 2pt | 2pt | unchanged |
| S14-3 | 2pt | 1pt | identical pattern to S14-2, implement in same pass |
| S14-4 | 2pt | 2pt | unchanged |
| S14-5 | 1pt | 1pt | unchanged |
| **Total** | **10pt** | **8pt** | |

---

### Open Questions — Resolved

**OQ-1 (S14-1 relationship placement)**: Add `_extract_calls()` to `JavaScriptParser.parse()`. `ParseResult.references` not needed for this sprint — `calls` uses `ParseResult.calls` which already goes through `_store_relationships`. ✅

**OQ-2 (S14-2 `--lang` join strategy)**: `symbols.language` is a direct column on `symbols`, not a join to `files`. `WHERE s.language = ?` with indexed column. ✅

**OQ-3 (S14-3 placement)**: `--lang` and `--subtype` are match-stage modifiers (same tier as `--newerthan`). They belong in the `match_parser` args, read by `executor.py`, passed to `db.match()`. ✅

---

@Neo: Ready to implement. Start with Cycle 1 (S14-1 — JS `calls` extraction). Key files: `via/parsers/javascript_parser.py`, `via/db/store.py`. Revised total: 8pts across 3 cycles.


---


## SPRINT_14_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_14_REVIEW.md`


## Sprint 14 Stories — Smith User Review
**Date**: 2026-04-05
**Reviewer**: Smith (HCI Expert)
**Verdict**: APPROVED with 3 notes

---

### Testing Performed

- Confirmed `--lang` and `--subtype` do not exist: `Error: Invalid match stage arguments`
- Confirmed JS/TS files ARE indexed (7 `.js` files, 5+ `.ts` files in index)
- Confirmed JS/TS files have ZERO relationship records (`--via declares`, `--via imports` return nothing for JS files)
- Confirmed USER_GUIDE.md bugs at lines 143, 219, 732 are present

---

### Story Verdicts

#### S14-1: JS/TS Relationship Extraction — PASS
- **Heuristic #4 (Consistency)**: Python has relationships, JS/TS doesn't. Users will query `app.js --via imports` and get silence — confusing gap. Filling this is essential for consistency.
- ACs are specific, testable, and correctly scoped to within-file calls only.

#### S14-2: `--lang` Filter Flag — PASS with Note
- Flag position (after match stage, like `--newerthan`) is correct UX.
- ACs accept both `py`/`python`, `js`/`javascript`, etc. — good for learnability.
- **Note**: The error message example in the ACs says `"Valid: py, js, ts, md"` but the ACs also accept full names (`python`, `javascript`, `typescript`, `markdown`). Error message should list all accepted forms to prevent confusion:
  ```
  Error: Unknown --lang 'go'. Valid: py/python, js/javascript, ts/typescript, md/markdown.
  ```

#### S14-3: `--subtype` Filter Flag — PASS with Note
- **Heuristic #9 (Error Recovery)**: The AC says "unknown values silently return no results." This is an anti-pattern — users who typo `--subtype interfaze` will see 0 results with no feedback.
- **Recommendation**: Keep the open-ended acceptance (no hardcoded list), but add a `--help` note: *"--subtype is case-sensitive; unknown values return no results."* This sets user expectations without requiring us to enumerate all possible subtypes.
- Combinability with `--lang` (AC #4) is the right call — `--lang ts --subtype interface` is a natural query.

#### S14-4: Web UI Relationship Card UX — PASS with Clarification
- Segmented control is the right choice over radio buttons for this context. Compact, shows both options simultaneously (recognition over recall, Nielsen #6).
- **Gap in ACs**: Story doesn't specify that the mode selector should only be visible when a relationship type is selected. If the relationship dropdown is "(none)", showing "With / Without" makes no sense.
- **Add AC**: *"Mode selector is only displayed when the relationship type dropdown has a non-empty selection. Clearing the relationship type hides the mode selector and resets mode to 'With'."*

#### S14-5: USER_GUIDE.md Fixes — PASS
- All 4 bugs confirmed present. ACs are precise with line numbers and exact fix instructions.

---

### Cypher's Open Questions — Answered

**Q1 (S14-2)**: Are `py`/`js`/`ts`/`md` the right shorthands?
→ **Yes, with full-name aliases.** Accept `py`/`python`, `js`/`javascript`, `ts`/`typescript`, `md`/`markdown`. Show both in error messages.

**Q2 (S14-3)**: Should invalid `--subtype` values error or return empty?
→ **Silent empty is acceptable, but document it.** Add to `--help` text: "case-sensitive; unknown values return no results." Hardcoding a valid-values list is brittle since subtypes are open-ended.

**Q3 (S14-4)**: Segmented control vs radio buttons?
→ **Segmented control.** Two-option mode toggle is cleaner in a card. Plus: make it conditionally visible (only when relationship type is selected).

---

### Summary

All 5 stories are approved. The 3 notes above should be folded into the ACs before Morpheus begins arch:
1. S14-2: Error message should list `py/python, js/javascript, ts/typescript, md/markdown`
2. S14-3: Document in `--help` that `--subtype` is case-sensitive and unknown values return empty
3. S14-4: Add conditional visibility AC for mode selector


---
