# Sprint 16 — String Intelligence + Reusable Query Workflows

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Turn Sprint 15's MCP ergonomics gains into higher-value analysis workflows by indexing string constants, importing real coverage data, and making common query patterns reusable.
**Sources**: `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`, `agents/cypher.docs/SPRINT_15_CLOSEOUT_2026-04-08T18:24.md`, Oracle recorded decisions in `agents/oracle.docs/context.md`
**Points**: ~8pt
**Baseline**: 1235 passed, 1 skipped, 4 warnings (end of Sprint 15)

---

## Sprint Goal

Sprint 15 fixed the most painful MCP correctness and discoverability gaps. Sprint 16 should raise via's ceiling for expert users: let them search for meaningful string constants, reason about real test coverage with the existing relationship model, and reuse common query patterns without rebuilding them each time. The sprint also closes the one known correctness gap left behind by Sprint 15 (`--slice` on OR'd type queries).

This is intentionally narrower than "index everything interesting." We are prioritizing the smallest set of changes that create a new, composable workflow:

1. find a string constant (`-ts`)
2. navigate to producers/consumers with `--via` / `--sans`
3. save the query as a canned pattern
4. optionally combine with `covered-by` to find untested or potentially unused code

---

## Stories

### S16-1: Fix `--slice` for OR'd Multi-Type Queries (P0, 1pt)

**As a** power user querying multiple symbol types at once,  
**I want** `--slice` to behave correctly for OR'd type queries,  
**so that** pagination remains correct regardless of how broad my query is.

#### Background

Sprint 15 delivered `--slice`, but Morpheus noted one known gap during Cycle 2 review: OR'd type queries ignore the slice offset. This is a correctness issue and should be closed before new higher-level query workflows build on top of pagination.

#### Acceptance Criteria

1. `--slice start:end` applies correctly when the query includes OR'd type filters.
2. `total` and `shown` remain correct for these queries.
3. Existing non-OR query behavior is unchanged.
4. `-n` and `--slice` remain mutually exclusive.
5. **Tests**: regression coverage for OR'd type queries with `--slice`, including offset windows beyond the first page.

**Files expected to change:**
- `via/db/store.py` and/or `via/pipeline/executor.py`
- tests covering query pagination

---

### S16-2: String Constants as First-Class Symbols (`-ts`) (P0, 3pt)

**As an** expert user,  
**I want** string constants indexed as a symbol type,  
**so that** I can search for log/error/API-route strings semantically and then traverse relationships from them.

#### Background

Smith explicitly separated "full-text contains" from the more tractable, high-value feature of indexing string constants as symbols. This is the Sprint 16 centerpiece because it unlocks concrete workflows like:

```bash
via -mg 'User not found' -ts
via -mg '/api/query' -ts --via references -mg '*' -tf
```

This is not generic text search. It is a structured symbol type for literal string values that matter to developers.

#### Acceptance Criteria

1. Add a new symbol type flag: `-ts` / `--type string_constant`.
2. Python string constants that are assigned, returned directly, passed as call arguments, or used in logging/error messages can be indexed as `string_constant` symbols.
3. JavaScript/TypeScript string literals in comparable positions are also indexed when supported by the existing parser.
4. Each indexed string constant stores enough metadata to:
   - match by displayed value
   - report its file/line
   - participate in `references`-style navigation back to the enclosing code symbol when applicable
5. Matching is exact/glob/regex through the existing matcher pipeline; no new full-text engine is introduced.
6. `-ts` results render sensibly in list/table/json output.
7. The feature documents its scope clearly: not every raw string in a file must be indexed, and this is not a replacement for grep.
8. **Tests**: unit + integration coverage for Python and JS/TS fixtures, renderer output, and relationship traversal from `-ts` results.

**Files expected to change:**
- `via/core/types.py` or enum/flag definitions for symbol type support
- relevant parser(s): `via/parsers/python_parser.py`, `via/parsers/javascript_parser.py`
- indexing/storage pipeline
- renderers/tests/docs as needed

---

### S16-3: Coverage Import as `covered-by` Relationship (P1, 2pt)

**As a** developer,  
**I want** coverage data imported into via as relationships,  
**so that** I can query for untested functions and navigate test-to-code connections using the existing `--via` / `--sans` model.

#### Background

Smith called coverage import a strong sprint story because it fits via's relationship system directly. To keep scope controlled, Sprint 16 should prefer one stable interchange format over multiple coverage backends if needed.

#### Acceptance Criteria

1. via can import coverage data from a documented coverage artifact format.
   Preferred default: `coverage.xml` if that is materially simpler than `.coverage`.
2. Imported data creates a `covered-by` relationship between code symbols and test files/functions when resolvable.
3. Users can query:
   ```bash
   via -mg '*' -tf --sans covered-by -mg '*'
   ```
   to find functions with no imported coverage relationship.
4. Importing coverage is additive and non-destructive to regular indexing.
5. Error messages clearly explain unsupported or malformed coverage input.
6. **Tests**: import fixture coverage data, assert `covered-by` relationships exist, assert untested-function query works.

**Files expected to change:**
- new or existing import command/path in CLI
- coverage parsing/import code
- relationship storage/query layer
- tests/docs

---

### S16-4: Canned Queries (`via --canned`) (P1, 2pt)

**As a** power user or MCP client,  
**I want** named reusable query templates,  
**so that** I can run common workflows without reconstructing long argument lists every time.

#### Background

Smith's recommendation is a local, customizable canned-query system with built-ins. This compounds the value of Sprint 15 and Sprint 16 features because it makes relationship-heavy workflows easy to repeat.

#### Acceptance Criteria

1. Add `via --canned "<name>"` to execute a named query template.
2. Add `--args key=value[,key=value...]` or equivalent templating input for parameterized canned queries.
3. Built-in canned queries ship for at least:
   - `unused` / `potentially-unused`
   - `callers`
   - `inheritors`
   - `dead-docs`
4. User-defined canned queries can be stored locally in a documented location under `.via/`.
5. Canned queries expand into normal via queries; they do not bypass validation or create a second query engine.
6. Error messages cover missing canned names and missing required args.
7. **Tests**: built-in canned query execution, custom canned query loading, arg substitution, invalid query handling.

**Files expected to change:**
- CLI parsing/execution
- canned-query storage/loader module
- docs/tests

---

## Deferred Beyond Sprint 16

These remain valuable, but they should not be pulled into Sprint 16 unless scope is explicitly expanded:

| Item | Reason Deferred |
|------|-----------------|
| URL/link indexing (`link` symbol type) | Pairs well with `-ts`, but should wait until string-constant storage/query semantics are stable |
| HTTP bridge / cross-language tracing | Depends on string constants and likely framework-specific design |
| Generic `--contains` source-text search | Separate problem from structured symbols; needs different architecture |

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S16-1 | Fix `--slice` for OR'd multi-type queries | 1 | P0 |
| S16-2 | String constants as `-ts` symbol type | 3 | P0 |
| S16-3 | Coverage import as `covered-by` relationship | 2 | P1 |
| S16-4 | Canned queries (`via --canned`) | 2 | P1 |
| **Total** | | **8pt** | |

---

## Recommended Planning Flow

1. Smith Gate 1 review of these stories
2. Morpheus architecture for Sprint 16
3. Mouse task board split into short cycles:
   - Cycle 1: S16-1
   - Cycle 2: S16-2
   - Cycle 3: S16-3 + S16-4

