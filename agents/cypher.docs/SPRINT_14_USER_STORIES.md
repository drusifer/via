# Sprint 14 — Query Extensions + Usability Fixes

**Author**: Cypher (PM)
**Date**: 2026-04-05
**Theme**: Complete JS/TS query capabilities (S11-3 + S11-4), add `--subtype` filtering, fix web UI relationship UX, and repair remaining USER_GUIDE.md bugs.
**Points**: ~11pts
**Baseline**: ~1121 tests (end of Sprint 13)

---

## Sprint Goal

Fill in the gaps left by Sprints 11–13: JS/TS relationship extraction was deferred, `--lang` and `--subtype` filters were never built despite the DB storing both fields, the web UI's relationship card still uses the old `invert` model from before Sprint 13, and four USER_GUIDE.md bugs from Smith's review remain unfixed. This sprint makes what's partially-there fully usable.

---

## Stories

---

### S14-1: JS/TS Relationship Extraction (P0, 3pt)

**As a** developer querying a JavaScript or TypeScript codebase,
**I want** `via -mg 'MyClass' -tc --via inherits-from -mg '*' -tc` to show JS/TS class inheritance,
**so that** I can navigate JS/TS class hierarchies the same way I do in Python.

#### Background

`JavaScriptParser` (`via/parsers/javascript_parser.py:40`) was shipped in Sprint 11. It extracts functions, classes, imports, and globals with correct `bases` and `ImportEntity` records. However, it does **not** write to `symbol_references` — so no relationship queries work on JS/TS symbols. The indexing service must call relationship-extraction logic for JS/TS files just as it does for Python.

#### Acceptance Criteria

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

### S14-2: `--lang` Filter Flag (P0, 2pt)

**As a** developer with a mixed Python+JS/TS codebase,
**I want** `via -mg '*service*' -tc --lang js` to return only JavaScript classes,
**so that** I can narrow searches to one language without using full-path regex hacks.

#### Background

`symbols.language` is populated from `ParseResult.language` for all indexed files (confirmed in Sprint 11). The DB has the data; there is no CLI flag to filter by it. The `via/core/flag_groups.py` defines `MATCH_FLAGS`, `TYPE_FLAGS`, etc — `--lang` would be a new option-stage flag (applies after match, like `--newerthan`).

#### Acceptance Criteria

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

### S14-3: `--subtype` Filter Flag (P1, 2pt)

**As a** developer using via on a TypeScript codebase,
**I want** `via -mg '*' -tc --subtype interface` to return only TypeScript interfaces,
**so that** I can distinguish interfaces from classes without grepping file content.

#### Background

`symbols.symbol_subtype` is in the schema (`via/db/schema.py:66`) and populated by `JavaScriptParser` for:
- `symbol_subtype='interface'` — TypeScript `interface` declarations
- `symbol_subtype='enum'` — TypeScript `enum` declarations
- `symbol_subtype='arrow_function'` — Arrow functions assigned to `const`

No CLI flag exposes this field. Adding `--subtype` makes these queryable.

#### Acceptance Criteria

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

### S14-4: Web UI Relationship Card — `--via`/`--sans` UX (P1, 2pt)

**As a** web UI user,
**I want** the relationship card to show a clear "Positive (--via)" / "Negative (--sans)" mode selector,
**so that** the UI matches the Sprint 13 CLI redesign and the `--invert` mental model is gone.

#### Background

The Sprint 13 CLI redesign replaced `--invert` with `--via` (positive) and `--sans` (negative) as distinct operators with symmetric semantics. The web UI (`via/web/template.py:508-509`) still shows an "Invert direction (--sans)" toggle checkbox. The API body (`via/web/api/query.py:147`) still accepts `invert: bool`. This creates a mismatch: CLI users learn `--via`/`--sans`, then find the web UI calling the same thing "invert".

#### Acceptance Criteria

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

### S14-5: Fix USER_GUIDE.md — Remaining Smith Bugs (P0, 1pt)

**As a** new user reading the USER_GUIDE,
**I want** the documentation to accurately describe current `via` behavior,
**so that** I can follow examples without hitting errors or confusion.

#### Background

Smith's review (`agents/smith.docs/USER_GUIDE_REVIEW_2026_03_25.md`) found 7 bugs. The `--sans has`/`--sans declares` crashes (Bugs 4, 6, 7) and crash examples were removed in commit `c131619`. Four bugs remain unfixed.

#### Acceptance Criteria — Fix all four remaining bugs

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

## Sprint Summary

| Story | Points | Priority | Owner |
|-------|--------|----------|-------|
| S14-1: JS/TS relationship extraction | 3 | P0 | Neo |
| S14-2: `--lang` filter flag | 2 | P0 | Neo |
| S14-5: Fix USER_GUIDE.md bugs | 1 | P0 | Neo |
| S14-3: `--subtype` filter flag | 2 | P1 | Neo |
| S14-4: Web UI `--via`/`--sans` UX | 2 | P1 | Neo |
| **Total** | **10** | | |

---

## Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S14-1 + S14-5 | JS/TS relationships + doc fixes |
| 2 | S14-2 + S14-3 | `--lang` + `--subtype` flags (both touch flag_groups + executor) |
| 3 | S14-4 | Web UI relationship card redesign |

---

## Key Files

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

## Open Questions for Morpheus

1. **S14-1 — Relationship extraction placement**: Should JS relationship extraction happen inside `JavaScriptParser.parse()` (returns a `relationships` field in `ParseResult`) or in `IndexingService` post-parse? Recommend: extend `ParseResult` with a `relationships` list, mirror Python approach.

2. **S14-2 — `--lang` join strategy**: `symbols.language` is stored via `files.language` — is there a `language` column on `symbols` directly, or does the query need a JOIN to `files`? Confirm the current schema and recommend the cheapest query path.

3. **S14-3 — `--subtype` + `--lang` ordering**: Should `--lang` and `--subtype` be parsed as part of the match stage args (alongside `-tc`, `-tf`, etc.) or as inter-stage options (alongside `--newerthan`)? Recommend: same stage as type flags (they refine the match, not the relationship).

@Smith: Please review these stories before Morpheus begins arch. Key UX questions:
- S14-2: Are `py`/`js`/`ts`/`md` the right `--lang` shorthands? Should `javascript` and `typescript` also be accepted?
- S14-3: Should invalid `--subtype` values silently return empty results or raise an error?
- S14-4: Segmented control vs radio buttons for `--via`/`--sans` — which is clearer in the card context?
