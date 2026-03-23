# JavaScript & TypeScript Support — Requirements

**Author**: Cypher (PM)
**Date**: 2026-03-22
**Status**: DRAFT — pending Smith review + Morpheus arch
**Theme**: Extend via to index and query JavaScript and TypeScript codebases
**Estimated Points**: ~18pts (recommend splitting across Sprint 11 + Sprint 12)

---

## Background

Via currently indexes Python (`.py`, `.pyx`, `.pyi`) and Markdown (`.md`) files. JavaScript and TypeScript are the dominant languages in frontend and full-stack projects. Adding JS/TS support extends via's value to those codebases without changing the core query pipeline — the `ParserABC` plugin architecture (S1-4) was designed for exactly this.

**Architecture fit**: `FileDiscovery.parseable_extensions` already accepts any extension set. `ParserRegistry` maps extension → parser. A new `JavaScriptParser(ParserABC)` is the only required seam — no changes to the query layer, CLI stages, or renderers.

---

## Scope

### In Scope
- File types: `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.tsx`
- Symbol extraction: functions, classes, methods, imports, module-level `const`/`let`/`var`
- Relationship extraction: `imports`, `inherits-from`, `calls` (within-file), `declares`
- TypeScript-specific: interfaces, type aliases, enums (as `class`-type records with appropriate subtype)
- All existing query, filter, and output stages work unchanged on JS/TS results

### Out of Scope
- Full cross-file call graph resolution (same limitation as Python today)
- `.vue`, `.svelte`, `.astro` single-file components (future sprint)
- `require()` CommonJS resolution (tracked as future story)
- JSDoc comment extraction (tracked as future story)

---

## User Stories

### S11-1: JS/TS File Discovery (1pt) — P0

**As a** developer with a JS/TS project,
**I want** `via index` to discover and index `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.tsx` files,
**so that** my project files appear in via's index alongside any Python files.

#### Acceptance Criteria

1. **Extensions registered**: `JavaScriptParser.get_supported_extensions()` returns `{'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'}`. The parser registry adds these to `parseable_extensions` automatically on registration.

2. **Discovery unchanged**: `FileDiscovery` needs no changes — it already supports arbitrary `parseable_extensions`.

3. **`via index` output**: After `via index`, JS/TS files appear in `via -mf '*.js'` and `via -mf '*.ts'` results.

4. **`--lang` filter (optional)**: `via -mf '*' -tF --lang js` filters to JS/TS files. If `--lang` is not implemented in this sprint, this AC is deferred.

5. **Tests**: Integration test confirming `.ts` and `.jsx` files are indexed after `via index`.

---

### S11-2: JavaScript/TypeScript AST Parser (8pts) — P0

**As a** developer using via on a JS/TS codebase,
**I want** via to extract functions, classes, imports, and module-level variables from JS/TS files,
**so that** I can search and query JS/TS symbols the same way I search Python symbols.

#### Background

**Recommended library**: [`tree-sitter`](https://github.com/tree-sitter/tree-sitter) with `tree-sitter-javascript` and `tree-sitter-typescript` grammars. This is the most robust option:
- Handles syntax errors gracefully (partial parse)
- Supports JSX natively
- TypeScript grammar is a superset of the JavaScript grammar
- Python bindings: `pip install tree-sitter tree-sitter-javascript tree-sitter-typescript`

Alternative if tree-sitter is too heavy: [`esprima-python`](https://github.com/Kronuz/esprima-python) (JS only, no TS).

**Decision for Morpheus**: Confirm tree-sitter vs alternative. See Open Questions.

#### Symbols Extracted

| JS/TS Construct | via Symbol Type | Notes |
|-----------------|-----------------|-------|
| `function foo() {}` | `function` | Named function declarations |
| `const foo = () => {}` | `function` | Arrow function assigned to const |
| `async function foo() {}` | `function` | Async functions |
| `class Foo {}` | `class` | Class declarations |
| `class Foo extends Bar {}` | `class` | `bases` field = `'Bar'` |
| `foo() {}` (method) | `function` | Method inside class, `class_id` set |
| `import X from 'y'` | `import` | `module='y'`, `name='X'` |
| `import { X, Y } from 'y'` | `import` | One `ImportEntity` per named import |
| `import * as X from 'y'` | `import` | `module='y'`, `alias='X'` |
| `const x = ...` (module-level) | `global` | Top-level const/let/var |
| `interface Foo {}` (TS) | `class` | `symbol_subtype='interface'` |
| `type Foo = ...` (TS) | `global` | Type alias as module-level global |
| `enum Foo {}` (TS) | `class` | `symbol_subtype='enum'` |
| `export default function` | `function` | Extracted same as non-export |
| `export const foo = () => {}` | `function` | Export wrapper stripped |

#### Acceptance Criteria

1. **Parser class**: `JavaScriptParser` in `via/parsers/javascript_parser.py` implements `ParserABC`.

2. **`get_supported_extensions()`**: Returns `{'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'}`.

3. **`language_name()`**: Returns `'javascript'` for `.js`/`.jsx`/`.mjs`/`.cjs`, `'typescript'` for `.ts`/`.tsx`.

4. **`can_parse(path)`**: Returns `True` iff the file extension is in the supported set.

5. **`parse(file_path, content)`**: Returns a `ParseResult` with correct `functions`, `classes`, `imports`, `globals`. No crash on syntax-error files — returns `ParseResult` with `parse_error` set.

6. **Line numbers**: `line_start` / `line_end` are 1-indexed (consistent with Python parser).

7. **Byte offsets**: `byte_offset` and `byte_length` match the UTF-8 byte range of the construct in the file.

8. **Class methods**: Methods inside a class are stored as `FunctionEntity` with `class_id` linked after store phase (consistent with Python parser behavior).

9. **Inheritance**: `ClassEntity.bases` is a comma-separated string of base class names (e.g. `'React.Component'`, `'Bar, Baz'`).

10. **TS interfaces as classes**: TypeScript `interface` declarations are stored as `ClassEntity` with a `symbol_subtype` of `'interface'` (requires schema or metadata field — Morpheus to decide mechanism).

11. **Partial parse**: If tree-sitter encounters a syntax error, continue parsing the rest of the file. Set `ParseResult.parse_error` to a short description but return all successfully parsed symbols.

12. **Size limit**: Respects the existing 10MB parse limit (skip file, log warning).

13. **Auto-registered**: `JavaScriptParser` is registered in the global parser registry at import time (same pattern as `PythonParser`).

14. **Tests**:
    - Unit tests for each symbol type (function, class, import, global) — `.js` and `.ts` variants
    - Unit test for `class Foo extends Bar` → `bases='Bar'`
    - Unit test for named imports → multiple `ImportEntity` records
    - Unit test for syntax error file → `parse_error` set, other symbols returned
    - Integration test: `via index` on a JS project dir → symbols queryable

---

### S11-3: JS/TS Relationship Extraction (3pts) — P1

**As a** developer querying a JS/TS codebase,
**I want** `via -mg 'MyClass' -tc -Vinh -mg '*' -tc` to show JS class inheritance,
**so that** I can navigate class hierarchies in JS/TS projects the same way I do in Python.

#### Acceptance Criteria

1. **`inherits-from` relationships**: `class Foo extends Bar` → `symbol_references` row with `ref_type='inherits-from'` from `Foo` → `Bar`. Works with `-Vinh` and `--ref-type inherits-from`.

2. **`imports` relationships**: Each `ImportEntity` produces an `imports` reference from the file's module to the imported module name. Works with `-Vimp`.

3. **`declares` relationships**: Each top-level function and class produces a `declares` reference from the file → symbol. Works with `--ref-type declares`.

4. **`calls` relationships**: Within-file function call detection (best-effort, not cross-file). `CallEntity` records extracted by the parser where tree-sitter can identify call sites. Works with `-Vca`.

5. **Existing Python relationships unaffected**: No regressions on Python relationship tests.

6. **Tests**: Unit test for each relationship type on a JS fixture file.

---

### S11-4: `--lang` Filter Flag (2pts) — P1

**As a** developer with a mixed Python+JS codebase,
**I want** to filter results to a specific language (`--lang py`, `--lang js`, `--lang ts`),
**so that** I can narrow searches to one language at a time.

#### Acceptance Criteria

1. **Flag**: `--lang <language>` is valid after any match stage (`-mg`, `-mf`, `-mr`).
   ```
   via -mg 'use*' --lang js -tf        # JS hooks only
   via -mg 'BaseModel' --lang py -tc   # Python classes only
   ```

2. **Values**: `py` (Python), `js` (JavaScript), `ts` (TypeScript), `md` (Markdown). Case-insensitive.

3. **Language stored in index**: `symbols.language` column populated from `ParseResult.language` (already exists as `language` in `ParseResult`). Morpheus to confirm schema — may already be stored.

4. **Filter applied in DB query**: `--lang` adds a `WHERE language = ?` clause, not a post-query filter.

5. **`via -mf '*' --lang js`**: Lists all indexed JS files.

6. **Tests**: Unit + integration tests for `--lang` filtering across Python and JS fixtures.

---

### S11-5: `node_modules` / `.gitignore` Exclusion (1pt) — P0

**As a** developer indexing a JS project,
**I want** `via index` to exclude `node_modules/`, `dist/`, `build/`, and `.next/` by default,
**so that** vendor dependencies don't pollute my index.

#### Acceptance Criteria

1. **Default excludes expanded**: `FileDiscovery.DEFAULT_EXCLUDES` adds: `node_modules`, `dist`, `.next`, `.nuxt`, `.svelte-kit`, `coverage`, `.turbo`.

2. **`.gitignore` respected**: Existing `.gitignore` support already handles most of these — this story adds the hard-coded defaults as a safety net.

3. **`--exclude` override**: User can still use `--exclude` to add more patterns; default excludes are always active.

4. **Tests**: Unit test confirming `node_modules/` files are not returned by `FileDiscovery.discover()`.

---

## Story Summary

| Story | Title | Points | Priority | Sprint |
|-------|-------|--------|----------|--------|
| S11-1 | JS/TS File Discovery | 1 | P0 | 11 |
| S11-5 | `node_modules` Exclusion | 1 | P0 | 11 |
| S11-2 | JavaScript/TypeScript AST Parser | 8 | P0 | 11 |
| S11-3 | JS/TS Relationship Extraction | 3 | P1 | 11 |
| S11-4 | `--lang` Filter Flag | 2 | P1 | 11 |
| **Total** | | **15pts** | | |

> **Recommendation**: S11-1, S11-5, S11-2 in Cycle 1 (~10pts). S11-3 + S11-4 in Cycle 2 (~5pts). This is a large sprint — Morpheus may recommend splitting into Sprint 11 (parser foundation) and Sprint 12 (relationships + lang filter).

---

## Open Questions for Morpheus

1. **OQ-1 — AST library**: tree-sitter vs esprima-python vs other? tree-sitter is recommended (handles TS, JSX, syntax errors gracefully). Confirm and add to `pyproject.toml` deps.

2. **OQ-2 — `symbol_subtype` for TS interfaces/enums**: Is there a `symbol_subtype` column in the schema, or should TS-specific types be encoded differently? Options: (a) add `symbol_subtype` column, (b) use a `metadata` JSON blob, (c) treat interface as class with a naming convention.

3. **OQ-3 — `language` column in `symbols` table**: Is `language` already stored per-symbol? If not, does it need to be added for `--lang` to work efficiently? (The `files` table has `language` — can join on `file_id`.)

4. **OQ-4 — Sprint split**: Is 15pts too large for one sprint given tree-sitter learning curve? Morpheus recommendation: split at 10pts (parser) / 5pts (relationships + lang)?

5. **OQ-5 — Arrow functions as globals vs functions**: `const foo = () => {}` at module level — store as `function` (richer) or `global` (simpler)? Recommendation: `function` with `is_arrow=True` metadata, but this depends on OQ-2.

---

## Arch Handoff

@Morpheus: JavaScript support requirements ready for arch review. Key decisions needed:
1. OQ-1: AST library selection (tree-sitter recommended)
2. OQ-2: `symbol_subtype` mechanism for TS interfaces/enums
3. OQ-3: `language` column strategy for `--lang` filter
4. OQ-4: Sprint split recommendation (15pts may be too large)
5. OQ-5: Arrow function storage strategy

Please write `agents/morpheus.docs/JAVASCRIPT_SUPPORT_ARCHITECTURE.md` before Neo begins implementation.

@Smith: These stories are ready for user review. Please assess:
- Is the JS/TS symbol extraction scope right (too narrow, too broad)?
- Is `--lang` the right UX for language filtering?
- Are the excluded directories (`node_modules`, `dist`, etc.) the right defaults?
