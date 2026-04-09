# Sprint 16 — Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-08
**Stories**: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_16_GATE1_REVIEW.md`)

---

## S16-1: Fix `--slice` For OR'd Multi-Type Queries (1pt)

### Root Cause

Sprint 15 added `LIMIT/OFFSET` support to the main match flow, but the OR-path for multiple requested symbol types does not consistently propagate slice offset/limit into `_match_multiple_types`. The total count is still computed, but the returned page can behave like `offset=0`.

### Fix

- Thread `slice_start` / `slice_end` through the multi-type query path.
- Apply the same SQL `LIMIT/OFFSET` semantics used by the single-type path.
- Preserve `COUNT(*) OVER()` based `total_matches`.

### Files Changed

| File | Change |
|------|--------|
| `via/db/store.py` and/or `via/pipeline/executor.py` | Pass and apply slice arguments for OR'd type queries |
| tests | Add regression coverage for second-page windows |

---

## S16-2: String Constants As `-ts` Symbol Type (3pt)

### Architecture

#### 1. New Symbol Type

Add a new symbol type: `string_constant`.

- CLI flag: `-ts`
- Internal enum/type support alongside existing symbol kinds
- Renderers treat it as a leaf symbol with file/line/value metadata

#### 2. Conservative Extraction Rule

Sprint 16 should not attempt to index every raw string literal in every file. Keep extraction conservative and high-signal:

- Python:
  - assigned literal values
  - return-string literals
  - string literals used in logging/error/message call arguments
- JavaScript/TypeScript:
  - assigned literal values
  - returned string literals
  - string literals passed to common call sites where the enclosing symbol is known

**Explicit non-goal:** generic "source contains X" search.

#### 3. Ownership Model

Each `string_constant` symbol is stored as a normal symbol row with:

- `symbol_name`: normalized literal value (possibly truncated for display)
- `qualified_name`: stable value including file path and enclosing symbol context
- file path + line number
- `parent_name`: enclosing symbol when known

#### 4. Relationship Model

To support Smith's desired workflow:

```bash
via -mg '/api/query' -ts --via references -mg '*' -tf
```

store a `references` relationship from the `string_constant` symbol to its enclosing code symbol when that enclosure exists. This reuses an existing relationship verb instead of inventing a new one. For module-level literals with no narrower owner, relate to the file path symbol.

#### 5. Rendering

- JSON/list/table must show enough of the literal value to identify it.
- Raw/formatted output should still point back to source location.
- Very long literals should be truncated for display only, not for matching identity.

### Design Constraints

- No full-text index.
- No cross-file deduplication in Sprint 16.
- No attempt to infer semantic meaning of URLs, SQL, or templates yet.

### Files Changed

| File | Change |
|------|--------|
| `via/core/types.py` / enum definitions | Add `string_constant` |
| `via/core/flag_groups.py` | Add `-ts` flag |
| `via/parsers/python_parser.py` | Extract conservative Python string constants |
| `via/parsers/javascript_parser.py` | Extract conservative JS/TS string constants |
| indexing/store pipeline | Persist symbols and `references` rows |
| renderers/tests | Display + regression coverage |

---

## S16-3: Coverage Import As `covered-by` Relationship (2pt)

### Architecture

Sprint 16 should support exactly one import format: `coverage.xml`.

This keeps the feature implementation-oriented and avoids tight coupling to `.coverage` internals or coverage.py APIs. If later demand exists, other formats can be translated into the same internal relationship model.

#### 1. CLI Surface

Add a focused import path:

```bash
via coverage import coverage.xml
```

This should be separate from normal indexing/query execution.

#### 2. Relationship Model

Import `covered-by` relationships linking:

- covered function/method/class symbols
- to the best-resolved test file or test symbol anchor available from the report/filename mapping

If symbol-level test attribution is not reliably available from the XML, Sprint 16 may link to test files first. The key is that `--sans covered-by` becomes useful immediately.

#### 3. Resolution Strategy

- Resolve coverage entries by file path and line ranges against existing indexed symbols.
- Prefer the narrowest enclosing symbol for a covered line span.
- Report unresolved coverage paths clearly, without crashing the import.

### Files Changed

| File | Change |
|------|--------|
| new coverage import command/module | Parse `coverage.xml` and map rows to symbols |
| relationship storage/query layer | Add `covered-by` support if missing |
| CLI wiring | Add `coverage import` entrypoint |
| tests | Fixture coverage import + query verification |

---

## S16-4: Canned Queries (`via --canned`) (2pt)

### Architecture

#### 1. Expansion Model

`--canned` is not a second query engine. It is a template expander that produces a normal via argv list and then hands it to the existing parser/executor path.

#### 2. Storage

Merge two sources:

- built-ins shipped with via
- user-defined `.via/canned/*.json`

JSON is sufficient for Sprint 16 and keeps the loader simple.

#### 3. Arguments

Support:

```bash
via --canned "callers" --args symbol=Foo,type=class
```

Expansion substitutes named placeholders into the canned argv template before normal validation.

#### 4. Transparency

On error, surface the expanded query or the missing placeholder so users can diagnose mistakes. Avoid "magic" behavior.

### Built-ins

- `unused`
- `callers`
- `inheritors`
- `dead-docs`

### Files Changed

| File | Change |
|------|--------|
| new canned-query module | Load built-ins and user JSON |
| CLI parser / main entry | Expand `--canned` before normal pipeline parse |
| tests/docs | Built-in and custom canned-query coverage |

---

## Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S16-1 | Small correctness fix; closes Sprint 15 carry-over |
| 2 | S16-2 | Main architecture-heavy feature |
| 3 | S16-3 + S16-4 | Workflow features once `-ts` semantics are stable |

---

## Risks

1. `-ts` scope creep into generic text search. Keep extraction conservative.
2. Coverage import path resolution may be noisy on repos with stale coverage files. Make errors explicit and non-fatal.
3. Canned-query placeholders can become opaque if expansion is hidden. Error messages must expose the expanded or failed template state.

---

## Smith Gate 2 Notes

- Sprint 16 remains a structured-query sprint, not a full-text-search sprint.
- `coverage.xml` only is a deliberate usability choice: one reliable path beats two partial ones.
- `--canned` remains transparent by expanding into standard via queries.
