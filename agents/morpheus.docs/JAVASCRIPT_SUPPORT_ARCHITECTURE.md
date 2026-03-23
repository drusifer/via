# JavaScript & TypeScript Support — Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-22
**Resolves**: `cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md` OQ-1 to OQ-5
**Also resolves**: Smith Gate 1 Notes 1-4 (`smith.docs/SPRINT_11_GATE1_REVIEW.md`)

---

## Executive Summary

JavaScript/TypeScript support slots cleanly into the existing parser plugin architecture. Two schema migrations are required (add `symbol_subtype` and `language` columns to `symbols`). Sprint is split: **Sprint 11** ships the parser foundation (S11-1, S11-5, S11-2); **Sprint 12** ships relationships and `--lang` filter (S11-3, S11-4).

---

## Schema Changes (Migration Required)

Both columns are added to `symbols` via a new versioned migration in `initialize_schema()`.

### New Column 1: `symbol_subtype TEXT`

```sql
ALTER TABLE symbols ADD COLUMN symbol_subtype TEXT;
```

- **Nullable**: existing Python/Markdown symbols leave it `NULL`.
- **JS/TS values**: `'interface'`, `'enum'`, `'arrow_function'` — these are the only subtypes for now; more can be added later.
- **Python future use**: `'dataclass'`, `'abstract'` — the column is general-purpose.
- **Index**: Add `idx_symbols_subtype ON symbols(symbol_subtype)` for future filter performance.

### New Column 2: `language TEXT`

```sql
ALTER TABLE symbols ADD COLUMN language TEXT;
```

- **Denormalized** — consistent with the existing "denormalized symbols table for fast matching" philosophy. Avoids JOIN at query time.
- **Populated from**: `ParseResult.language` field (already set by both existing parsers).
- **Values**: `'python'`, `'markdown'`, `'javascript'`, `'typescript'`.
- **Index**: Add `idx_symbols_language ON symbols(language)`.
- **Backfill**: On migration, existing rows get `language` set via a JOIN on `files.language` (one-time migration step in `initialize_schema()`).

**Why not JOIN on `files.language`?** The `symbols` table is already denormalized (`file_path TEXT NOT NULL` instead of a `file_id` FK). Adding `language` follows the same pattern. JOIN would require `file_path = files.path` at query time — slower than a direct column.

---

## OQ-1: AST Library — tree-sitter ✅ CONFIRMED

**Decision**: Use `tree-sitter` with `tree-sitter-javascript` and `tree-sitter-typescript` grammars.

**Rationale**:
- Handles syntax errors gracefully (partial parse, no crash) — same guarantee as Python's `ast.parse`
- Supports JSX natively (`tree-sitter-javascript`)
- TypeScript grammar is a strict superset of the JavaScript grammar
- Well-maintained, used in Neovim, GitHub Linguist, and many editors

**Dependencies added to `pyproject.toml`**:
```toml
[project.dependencies]
tree-sitter = ">=0.23"
tree-sitter-javascript = ">=0.23"
tree-sitter-typescript = ">=0.23"
```

**Multiprocessing safety**: The `ParserABC.parse()` is called in worker processes. tree-sitter `Parser` objects are NOT picklable — do NOT share a single `Parser` instance across processes. `JavaScriptParser` must construct its tree-sitter `Language` and `Parser` objects lazily on first use per-process (thread-local or module-level initialized once per process via `__init__`). Pattern:

```python
class JavaScriptParser(ParserABC):
    _js_parser: Optional[ts.Parser] = None  # per-process singleton
    _ts_parser: Optional[ts.Parser] = None

    def _get_parser(self, language: str) -> ts.Parser:
        # Initialize once per process (worker forks reset this to None)
        if language == 'typescript' and self._ts_parser is None:
            ...
        ...
```

---

## OQ-2: `symbol_subtype` Mechanism — New Column ✅ DECIDED

**Decision**: Add `symbol_subtype TEXT` nullable column to `symbols` table (see Schema Changes above).

**JS/TS subtype values**:
| Construct | `symbol_type` | `symbol_subtype` |
|-----------|---------------|------------------|
| `class Foo {}` | `class` | `NULL` |
| `interface Foo {}` (TS) | `class` | `'interface'` |
| `enum Foo {}` (TS) | `class` | `'enum'` |
| `function foo()` | `function` | `NULL` |
| `const foo = () => {}` | `function` | `'arrow_function'` |

**Display**: The table renderer's `TYPE` column shows `symbol_type` for `NULL` subtype and `symbol_subtype` when set. So `-tc` results show `class`, `interface`, or `enum` in the type column — users can visually distinguish without a separate filter flag. (Resolves Smith Note 1.)

**`--help` update**: `-tc` help text updated to: `Classes (includes TypeScript interfaces and enums)`.

---

## OQ-3: `language` Column Strategy — Denormalized on `symbols` ✅ DECIDED

See Schema Changes above. `--lang` implementation:

```sql
-- via -mg 'pattern' -tf --lang js
SELECT ... FROM symbols WHERE symbol_name GLOB ? AND language IN ('javascript') ...
```

**`--lang` value → `language` column mapping** (resolves Smith Note 3):

| `--lang` | DB `language` values matched |
|----------|------------------------------|
| `py` | `'python'` |
| `js` | `'javascript'` |
| `ts` | `'typescript'` |
| `md` | `'markdown'` |

**Extension → `language` field** (set in `JavaScriptParser.parse()`):
| Extension | `ParseResult.language` |
|-----------|----------------------|
| `.js`, `.mjs`, `.cjs`, `.jsx` | `'javascript'` |
| `.ts`, `.tsx` | `'typescript'` |

This resolves Smith Note 3: `--lang js` covers `.jsx`; `--lang ts` covers `.tsx`. The mapping is set at parse time, not at filter time.

---

## OQ-4: Sprint Split — 11 (parser) + 12 (relationships + lang) ✅ DECIDED

**Decision**: Split into two sprints.

| Sprint | Stories | Points | Theme |
|--------|---------|--------|-------|
| **Sprint 11** | S11-1, S11-5, S11-2 | ~10pts | JS/TS parser foundation |
| **Sprint 12** | S11-3, S11-4 | ~5pts | Relationships + `--lang` filter |

**Rationale**: S11-2 (8pts, tree-sitter parser) is the highest-complexity story and needs its own sprint to do well. Rushing relationships into the same sprint risks a half-baked implementation. Sprint 12 is short (~5pts) — Mouse may pair it with other small stories.

---

## OQ-5: Arrow Functions — `FunctionEntity` (No Special Subtype) ✅ DECIDED

**Decision**: `const foo = () => {}` at module level → stored as `FunctionEntity` with `symbol_subtype='arrow_function'`.

**Rationale**: From the user's perspective, `foo` is a function — they search for it with `-tf`. But preserving the subtype is useful for users who care about the distinction (e.g., linting integration, future analysis tools). The `symbol_subtype` column exists for free after OQ-2, so use it.

**Not stored**: Inline arrow functions not assigned to a named const (e.g., `arr.map(x => x + 1)`) — these are anonymous and not useful as symbols.

---

## Smith Notes Resolution

| Note | Decision |
|------|----------|
| Note 1 — `interface` in `-tc` results | `symbol_subtype` column + type column shows `interface`/`enum`; `--help` updated |
| Note 2 — `imports` target is string-based | Confirmed: unresolved imports use `pending_relationships`; external targets (e.g., `react`) are dropped at resolution — same as Python behavior. Document in `--help` for `-Vimp`. |
| Note 3 — `--lang js` must cover `.jsx` | Resolved via `language='javascript'` for all `.jsx` files at parse time. See OQ-3 table. |
| Note 4 — `dist/` vs `dist` | S11-5 uses `dist/` (trailing slash = directory-only) in `DEFAULT_EXCLUDES`. |

---

## `JavaScriptParser` Implementation Sketch

```
via/parsers/
  javascript_parser.py     ← new
  __init__.py              ← register JavaScriptParser here

via/db/
  schema.py                ← add symbol_subtype + language columns + migration
  store.py                 ← populate language on INSERT, add WHERE language clause for --lang

via/core/
  discovery.py             ← S11-5: expand DEFAULT_EXCLUDES

pyproject.toml             ← add tree-sitter deps
```

### `JavaScriptParser` API (ParserABC contract)

```python
class JavaScriptParser(ParserABC):
    def get_supported_extensions(self) -> Set[str]:
        return {'.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'}

    def language_name(self, file_path: str) -> str:
        return 'typescript' if Path(file_path).suffix in {'.ts', '.tsx'} else 'javascript'

    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.get_supported_extensions()

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        # Use tree-sitter JS or TS grammar based on extension
        # Walk AST, emit FunctionEntity, ClassEntity, ImportEntity, GlobalEntity
        # On ERROR node: set parse_error, continue walking
        ...
```

### Tree-sitter Node Types to Extract

| tree-sitter node type | Action |
|----------------------|--------|
| `function_declaration` | → `FunctionEntity` |
| `arrow_function` (parent = `variable_declarator` at module scope) | → `FunctionEntity`, subtype `arrow_function` |
| `class_declaration` | → `ClassEntity`; `bases` from `class_heritage` |
| `method_definition` | → `FunctionEntity` with `class_id` |
| `import_statement` | → `ImportEntity` per specifier |
| `lexical_declaration` / `variable_declaration` at module scope | → `GlobalEntity` (unless arrow function — then `FunctionEntity`) |
| `interface_declaration` (TS) | → `ClassEntity`, subtype `interface` |
| `enum_declaration` (TS) | → `ClassEntity`, subtype `enum` |
| `type_alias_declaration` (TS) | → `GlobalEntity` |
| `ERROR` node | Set `parse_error`, continue |

---

## Sprint 11 Cycle Plan

| Cycle | Stories | Assigned |
|-------|---------|----------|
| 1 | S11-5 (node_modules excludes) + S11-1 (file discovery) | Neo → Trin |
| 2 | S11-2 (JavaScriptParser, tree-sitter, schema migrations) | Neo → Trin |

**Total**: ~10pts, 2 cycles.

---

## Arch Handoff

@Mouse: Sprint 11 architecture ready. 2 cycles:
- Cycle 1: S11-5 + S11-1 (~2pts, quick wins, prove the extension flow)
- Cycle 2: S11-2 + schema migrations (~8pts, the parser itself)

@Neo: Key implementation notes:
1. tree-sitter `Parser` objects are per-process — initialize lazily in `_get_parser()`, not at module import
2. Add `symbol_subtype` + `language` columns via new schema migration version
3. Populate `language` on every symbol INSERT (not just JS/TS — backfill Python/Markdown too)
4. S11-5: use `dist/` with trailing slash in `DEFAULT_EXCLUDES`
5. Arrow functions at module scope → `FunctionEntity` with `symbol_subtype='arrow_function'`
