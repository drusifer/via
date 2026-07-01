# Sprint 16 Consolidated Documentation

This document consolidates all documentation for Sprint 16.

## Table of Contents

- [SPRINT_16_CLOSEOUT_2026-04-08T19-00.md](#sprint-16-closeout-2026-04-08t19-00md) (originally `agents/cypher.docs/SPRINT_16_CLOSEOUT_2026-04-08T19-00.md`)

- [SPRINT_16_USER_STORIES.md](#sprint-16-user-storiesmd) (originally `agents/cypher.docs/SPRINT_16_USER_STORIES.md`)

- [SPRINT_16_ARCHITECTURE.md](#sprint-16-architecturemd) (originally `agents/morpheus.docs/SPRINT_16_ARCHITECTURE.md`)

- [SPRINT_16_REVIEW_2026-04-08T19-00.md](#sprint-16-review-2026-04-08t19-00md) (originally `agents/morpheus.docs/SPRINT_16_REVIEW_2026-04-08T19-00.md`)

- [SPRINT_16_GATE1_REVIEW.md](#sprint-16-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_16_GATE1_REVIEW.md`)

- [SPRINT_16_GATE2_REVIEW.md](#sprint-16-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_16_GATE2_REVIEW.md`)

- [SPRINT_16_SCRUM_CLOSEOUT_Summary_2026-04-08T19-00.md](#sprint-16-scrum-closeout-summary-2026-04-08t19-00md) (originally `agents/mouse.docs/SPRINT_16_SCRUM_CLOSEOUT_Summary_2026-04-08T19-00.md`)

- [SPRINT_16_TASKS.md](#sprint-16-tasksmd) (originally `agents/mouse.docs/SPRINT_16_TASKS.md`)

- [SPRINT_16_C1_Summary_2026-04-08T18-52.md](#sprint-16-c1-summary-2026-04-08t18-52md) (originally `agents/neo.docs/SPRINT_16_C1_Summary_2026-04-08T18-52.md`)

- [SPRINT_16_Summary_2026-04-08T19-00.md](#sprint-16-summary-2026-04-08t19-00md) (originally `agents/neo.docs/SPRINT_16_Summary_2026-04-08T19-00.md`)

- [SPRINT_16_UAT_Summary_2026-04-08T19-00.md](#sprint-16-uat-summary-2026-04-08t19-00md) (originally `agents/trin.docs/SPRINT_16_UAT_Summary_2026-04-08T19-00.md`)


---


## SPRINT_16_CLOSEOUT_2026-04-08T19-00.md

**Original Location**: `agents/cypher.docs/SPRINT_16_CLOSEOUT_2026-04-08T19-00.md`


## Sprint 16 Closeout

**Author**: Cypher  
**Date**: 2026-04-08T19:00

### Outcome

Sprint 16 is SHIPPED.

#### Delivered
- S16-1: `--slice` fix for OR'd multi-type queries
- S16-2: `-ts` string constants as structured symbols
- S16-3: `coverage.xml` import as `covered-by`
- S16-4: `via --canned` with built-ins and `.via/canned/*.json`

#### Verification
- 176 targeted tests passed locally
- Sprint 15 slice regressions remained green

#### Deferred
- URL/link indexing
- HTTP bridge / cross-language tracing
- Generic source-text `--contains`


---


## SPRINT_16_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`


## Sprint 16 — String Intelligence + Reusable Query Workflows

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Turn Sprint 15's MCP ergonomics gains into higher-value analysis workflows by indexing string constants, importing real coverage data, and making common query patterns reusable.
**Sources**: `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`, `agents/cypher.docs/SPRINT_15_CLOSEOUT_2026-04-08T18-24.md`, Oracle recorded decisions in `agents/oracle.docs/context.md`
**Points**: ~8pt
**Baseline**: 1235 passed, 1 skipped, 4 warnings (end of Sprint 15)

---

### Sprint Goal

Sprint 15 fixed the most painful MCP correctness and discoverability gaps. Sprint 16 should raise via's ceiling for expert users: let them search for meaningful string constants, reason about real test coverage with the existing relationship model, and reuse common query patterns without rebuilding them each time. The sprint also closes the one known correctness gap left behind by Sprint 15 (`--slice` on OR'd type queries).

This is intentionally narrower than "index everything interesting." We are prioritizing the smallest set of changes that create a new, composable workflow:

1. find a string constant (`-ts`)
2. navigate to producers/consumers with `--via` / `--sans`
3. save the query as a canned pattern
4. optionally combine with `covered-by` to find untested or potentially unused code

---

### Stories

#### S16-1: Fix `--slice` for OR'd Multi-Type Queries (P0, 1pt)

**As a** power user querying multiple symbol types at once,  
**I want** `--slice` to behave correctly for OR'd type queries,  
**so that** pagination remains correct regardless of how broad my query is.

##### Background

Sprint 15 delivered `--slice`, but Morpheus noted one known gap during Cycle 2 review: OR'd type queries ignore the slice offset. This is a correctness issue and should be closed before new higher-level query workflows build on top of pagination.

##### Acceptance Criteria

1. `--slice start:end` applies correctly when the query includes OR'd type filters.
2. `total` and `shown` remain correct for these queries.
3. Existing non-OR query behavior is unchanged.
4. `-n` and `--slice` remain mutually exclusive.
5. **Tests**: regression coverage for OR'd type queries with `--slice`, including offset windows beyond the first page.

**Files expected to change:**
- `via/db/store.py` and/or `via/pipeline/executor.py`
- tests covering query pagination

---

#### S16-2: String Constants as First-Class Symbols (`-ts`) (P0, 3pt)

**As an** expert user,  
**I want** string constants indexed as a symbol type,  
**so that** I can search for log/error/API-route strings semantically and then traverse relationships from them.

##### Background

Smith explicitly separated "full-text contains" from the more tractable, high-value feature of indexing string constants as symbols. This is the Sprint 16 centerpiece because it unlocks concrete workflows like:

```bash
via -mg 'User not found' -ts
via -mg '/api/query' -ts --via references -mg '*' -tf
```

This is not generic text search. It is a structured symbol type for literal string values that matter to developers.

##### Acceptance Criteria

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

#### S16-3: Coverage Import as `covered-by` Relationship (P1, 2pt)

**As a** developer,  
**I want** coverage data imported into via as relationships,  
**so that** I can query for untested functions and navigate test-to-code connections using the existing `--via` / `--sans` model.

##### Background

Smith called coverage import a strong sprint story because it fits via's relationship system directly. To keep scope controlled, Sprint 16 should prefer one stable interchange format over multiple coverage backends if needed.

##### Acceptance Criteria

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

#### S16-4: Canned Queries (`via --canned`) (P1, 2pt)

**As a** power user or MCP client,  
**I want** named reusable query templates,  
**so that** I can run common workflows without reconstructing long argument lists every time.

##### Background

Smith's recommendation is a local, customizable canned-query system with built-ins. This compounds the value of Sprint 15 and Sprint 16 features because it makes relationship-heavy workflows easy to repeat.

##### Acceptance Criteria

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

### Deferred Beyond Sprint 16

These remain valuable, but they should not be pulled into Sprint 16 unless scope is explicitly expanded:

| Item | Reason Deferred |
|------|-----------------|
| URL/link indexing (`link` symbol type) | Pairs well with `-ts`, but should wait until string-constant storage/query semantics are stable |
| HTTP bridge / cross-language tracing | Depends on string constants and likely framework-specific design |
| Generic `--contains` source-text search | Separate problem from structured symbols; needs different architecture |

---

### Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S16-1 | Fix `--slice` for OR'd multi-type queries | 1 | P0 |
| S16-2 | String constants as `-ts` symbol type | 3 | P0 |
| S16-3 | Coverage import as `covered-by` relationship | 2 | P1 |
| S16-4 | Canned queries (`via --canned`) | 2 | P1 |
| **Total** | | **8pt** | |

---

### Recommended Planning Flow

1. Smith Gate 1 review of these stories
2. Morpheus architecture for Sprint 16
3. Mouse task board split into short cycles:
   - Cycle 1: S16-1
   - Cycle 2: S16-2
   - Cycle 3: S16-3 + S16-4



---


## SPRINT_16_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_16_ARCHITECTURE.md`


## Sprint 16 — Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-08
**Stories**: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_16_GATE1_REVIEW.md`)

---

### S16-1: Fix `--slice` For OR'd Multi-Type Queries (1pt)

#### Root Cause

Sprint 15 added `LIMIT/OFFSET` support to the main match flow, but the OR-path for multiple requested symbol types does not consistently propagate slice offset/limit into `_match_multiple_types`. The total count is still computed, but the returned page can behave like `offset=0`.

#### Fix

- Thread `slice_start` / `slice_end` through the multi-type query path.
- Apply the same SQL `LIMIT/OFFSET` semantics used by the single-type path.
- Preserve `COUNT(*) OVER()` based `total_matches`.

#### Files Changed

| File | Change |
|------|--------|
| `via/db/store.py` and/or `via/pipeline/executor.py` | Pass and apply slice arguments for OR'd type queries |
| tests | Add regression coverage for second-page windows |

---

### S16-2: String Constants As `-ts` Symbol Type (3pt)

#### Architecture

##### 1. New Symbol Type

Add a new symbol type: `string_constant`.

- CLI flag: `-ts`
- Internal enum/type support alongside existing symbol kinds
- Renderers treat it as a leaf symbol with file/line/value metadata

##### 2. Conservative Extraction Rule

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

##### 3. Ownership Model

Each `string_constant` symbol is stored as a normal symbol row with:

- `symbol_name`: normalized literal value (possibly truncated for display)
- `qualified_name`: stable value including file path and enclosing symbol context
- file path + line number
- `parent_name`: enclosing symbol when known

##### 4. Relationship Model

To support Smith's desired workflow:

```bash
via -mg '/api/query' -ts --via references -mg '*' -tf
```

store a `references` relationship from the `string_constant` symbol to its enclosing code symbol when that enclosure exists. This reuses an existing relationship verb instead of inventing a new one. For module-level literals with no narrower owner, relate to the file path symbol.

##### 5. Rendering

- JSON/list/table must show enough of the literal value to identify it.
- Raw/formatted output should still point back to source location.
- Very long literals should be truncated for display only, not for matching identity.

#### Design Constraints

- No full-text index.
- No cross-file deduplication in Sprint 16.
- No attempt to infer semantic meaning of URLs, SQL, or templates yet.

#### Files Changed

| File | Change |
|------|--------|
| `via/core/types.py` / enum definitions | Add `string_constant` |
| `via/core/flag_groups.py` | Add `-ts` flag |
| `via/parsers/python_parser.py` | Extract conservative Python string constants |
| `via/parsers/javascript_parser.py` | Extract conservative JS/TS string constants |
| indexing/store pipeline | Persist symbols and `references` rows |
| renderers/tests | Display + regression coverage |

---

### S16-3: Coverage Import As `covered-by` Relationship (2pt)

#### Architecture

Sprint 16 should support exactly one import format: `coverage.xml`.

This keeps the feature implementation-oriented and avoids tight coupling to `.coverage` internals or coverage.py APIs. If later demand exists, other formats can be translated into the same internal relationship model.

##### 1. CLI Surface

Add a focused import path:

```bash
via coverage import coverage.xml
```

This should be separate from normal indexing/query execution.

##### 2. Relationship Model

Import `covered-by` relationships linking:

- covered function/method/class symbols
- to the best-resolved test file or test symbol anchor available from the report/filename mapping

If symbol-level test attribution is not reliably available from the XML, Sprint 16 may link to test files first. The key is that `--sans covered-by` becomes useful immediately.

##### 3. Resolution Strategy

- Resolve coverage entries by file path and line ranges against existing indexed symbols.
- Prefer the narrowest enclosing symbol for a covered line span.
- Report unresolved coverage paths clearly, without crashing the import.

#### Files Changed

| File | Change |
|------|--------|
| new coverage import command/module | Parse `coverage.xml` and map rows to symbols |
| relationship storage/query layer | Add `covered-by` support if missing |
| CLI wiring | Add `coverage import` entrypoint |
| tests | Fixture coverage import + query verification |

---

### S16-4: Canned Queries (`via --canned`) (2pt)

#### Architecture

##### 1. Expansion Model

`--canned` is not a second query engine. It is a template expander that produces a normal via argv list and then hands it to the existing parser/executor path.

##### 2. Storage

Merge two sources:

- built-ins shipped with via
- user-defined `.via/canned/*.json`

JSON is sufficient for Sprint 16 and keeps the loader simple.

##### 3. Arguments

Support:

```bash
via --canned "callers" --args symbol=Foo,type=class
```

Expansion substitutes named placeholders into the canned argv template before normal validation.

##### 4. Transparency

On error, surface the expanded query or the missing placeholder so users can diagnose mistakes. Avoid "magic" behavior.

#### Built-ins

- `unused`
- `callers`
- `inheritors`
- `dead-docs`

#### Files Changed

| File | Change |
|------|--------|
| new canned-query module | Load built-ins and user JSON |
| CLI parser / main entry | Expand `--canned` before normal pipeline parse |
| tests/docs | Built-in and custom canned-query coverage |

---

### Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S16-1 | Small correctness fix; closes Sprint 15 carry-over |
| 2 | S16-2 | Main architecture-heavy feature |
| 3 | S16-3 + S16-4 | Workflow features once `-ts` semantics are stable |

---

### Risks

1. `-ts` scope creep into generic text search. Keep extraction conservative.
2. Coverage import path resolution may be noisy on repos with stale coverage files. Make errors explicit and non-fatal.
3. Canned-query placeholders can become opaque if expansion is hidden. Error messages must expose the expanded or failed template state.

---

### Smith Gate 2 Notes

- Sprint 16 remains a structured-query sprint, not a full-text-search sprint.
- `coverage.xml` only is a deliberate usability choice: one reliable path beats two partial ones.
- `--canned` remains transparent by expanding into standard via queries.


---


## SPRINT_16_REVIEW_2026-04-08T19-00.md

**Original Location**: `agents/morpheus.docs/SPRINT_16_REVIEW_2026-04-08T19-00.md`


## Sprint 16 Review

**Author**: Morpheus  
**Date**: 2026-04-08T19:00

### Verdict

Sprint 16 implementation APPROVED.

- S16-1 matches architecture: OR-query pagination is applied to the combined result set
- S16-2 keeps `-ts` scoped to structured string-symbol indexing
- S16-3 stays format-limited to `coverage.xml`
- S16-4 expands canned queries into ordinary via argv rather than adding a second execution model

### Verification Basis

- 176 targeted tests passed locally
- Existing parser/query/index regressions included in the run


---


## SPRINT_16_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_16_GATE1_REVIEW.md`


## Sprint 16 — Smith Gate 1 Review

**Date**: 2026-04-08
**Reviewer**: Smith (HCI Expert)
**Stories reviewed**: `agents/cypher.docs/SPRINT_16_USER_STORIES.md`
**Verdict**: **APPROVED**

---

### Story-by-Story Review

#### S16-1: `--slice` for OR'd multi-type queries — APPROVED

This is a straightforward correctness carry-over from Sprint 15. It is the right P0 opener because it protects the pagination mental model before additional workflow features build on top of it.

**HCI assessment:** Preserves trust in system status and result navigation.

#### S16-2: `-ts` string constants — APPROVED

This is the highest-value Sprint 16 feature. It gives users a way to search for meaningful developer-facing strings without pretending via is a full-text search engine.

**Notes:**
- Keep scope explicit: this is structured string-symbol indexing, not arbitrary `--contains` source search.
- The value is strongest when string constants can bridge to their enclosing symbol or file through existing relationship queries.

**HCI assessment:** Strong match to real user tasks such as locating error strings, route literals, and log messages.

#### S16-3: Coverage import as `covered-by` — APPROVED WITH NOTE

Very strong user value, but scope discipline matters.

**Note:**
- Prefer one documented interchange format for Sprint 16. `coverage.xml` is the safest initial target if it avoids coupling to coverage.py internals.

**HCI assessment:** Gives users a concrete and trustworthy way to ask "what is untested?" instead of inferring from call graphs alone.

#### S16-4: Canned queries — APPROVED

This is the right time to add reusable query workflows because Sprint 15 and Sprint 16 make the query model richer. Naming and argument handling will matter more than implementation cleverness.

**Notes:**
- Built-ins should use user-language names, not internal jargon.
- Expansion must stay transparent so users can understand what query actually ran.

**HCI assessment:** Improves efficiency for expert users without complicating the base query model.

---

### Sprint-Level Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Story quality | ★★★★★ | Focused, traceable to Smith review and Sprint 15 closeout |
| Scope | ★★★★☆ | Tight enough if coverage import stays format-limited |
| User value | ★★★★★ | All four stories compound each other well |
| Risk | ★★★★☆ | `-ts` needs architectural discipline to avoid accidental full-text creep |

**Overall:** APPROVED. Proceed to Morpheus architecture.

### One Guidance Note For Morpheus

Keep Sprint 16 framed as **structured analysis primitives**, not "search everything." The moment `-ts` or canned queries start acting like a second search engine, the user mental model will blur.


---


## SPRINT_16_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_16_GATE2_REVIEW.md`


## Sprint 16 — Smith Gate 2 Review

**Date**: 2026-04-08
**Reviewer**: Smith (HCI Expert)
**Architecture reviewed**: `agents/morpheus.docs/SPRINT_16_ARCHITECTURE.md`
**Verdict**: **APPROVED**

---

### Assessment

Morpheus kept Sprint 16 disciplined in the right way.

- S16-1 closes the known Sprint 15 pagination gap without widening scope.
- S16-2 clearly separates `string_constant` symbols from generic text search, which preserves the user's mental model.
- S16-3 choosing `coverage.xml` only is the correct first-step usability tradeoff.
- S16-4 keeps canned queries transparent by expanding into ordinary via queries rather than inventing a hidden execution mode.

### HCI Notes

1. `-ts` must be documented as "structured string symbols" and not "search any source text."
2. Coverage import errors must name the unresolved file/path so users can recover.
3. Canned-query failures must mention the missing canned name or placeholder directly.

**Overall:** APPROVED. Proceed to Mouse sprint planning.


---


## SPRINT_16_SCRUM_CLOSEOUT_Summary_2026-04-08T19-00.md

**Original Location**: `agents/mouse.docs/SPRINT_16_SCRUM_CLOSEOUT_Summary_2026-04-08T19-00.md`


## Sprint 16 Scrum Closeout

**Author**: Mouse  
**Date**: 2026-04-08T19:00

### Status

Sprint 16 is complete and archived from the Scrum side.

- Cycle 1 complete, UAT pass, lead review pass
- Cycle 2 complete, UAT pass, lead review pass
- Cycle 3 complete, UAT pass, lead review pass
- PM closeout recorded

### Final Verification

- 176 targeted tests passed locally
- `make test` unavailable in this session due network-restricted dependency bootstrap


---


## SPRINT_16_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_16_TASKS.md`


## Sprint 16 — Task Board

**Sprint**: String Intelligence + Reusable Query Workflows
**Points**: 8pt (4 stories)
**Baseline**: 1235 passed, 1 skipped, 4 warnings
**Arch**: `morpheus.docs/SPRINT_16_ARCHITECTURE.md`
**Stories**: `cypher.docs/SPRINT_16_USER_STORIES.md`

---

### Cycle 1: Carry-Over Correctness (1pt) — S16-1

#### S16-1: Fix `--slice` For OR'd Multi-Type Queries (1pt)
- [x] C1-1: Add regression test covering OR'd multi-type query with `--slice 10:20`
- [x] C1-2: Thread slice offset/limit through `_match_multiple_types` path
- [x] C1-3: Verify `total` / `shown` remain correct for paged OR queries
- [x] C1-4: Verify `--slice` + `-n` conflict behavior unchanged

**Exit criteria**: All relevant pagination tests pass. Hand to Trin UAT.

---

### Cycle 2: New Symbol Type (3pt) — S16-2

#### S16-2: String Constants As `-ts` (3pt)
- [x] C2-1: Add `string_constant` symbol type and `-ts` flag support
- [x] C2-2: Extract conservative Python string constants
- [x] C2-3: Extract conservative JS/TS string constants
- [x] C2-4: Persist `string_constant` symbols with file/line/enclosing-symbol metadata
- [x] C2-5: Store `references` relationship from string constants to enclosing symbol/file anchor
- [x] C2-6: Add renderer coverage for list/table/json output
- [x] C2-7: Add unit/integration tests for Python and JS/TS fixtures

**Exit criteria**: `-ts` queries work end-to-end with stable output. Hand to Trin UAT.

---

### Cycle 3: Workflow Features (4pt) — S16-3 + S16-4

#### S16-3: Coverage Import As `covered-by` (2pt)
- [x] C3-1: Add `via coverage import <coverage.xml>` CLI path
- [x] C3-2: Parse `coverage.xml` fixture and resolve covered symbols
- [x] C3-3: Store `covered-by` relationships
- [x] C3-4: Add query test for `--sans covered-by`
- [x] C3-5: Add clear error handling for malformed/unresolved coverage inputs

#### S16-4: Canned Queries (`via --canned`) (2pt)
- [x] C3-6: Add canned-query loader for built-ins + `.via/canned/*.json`
- [x] C3-7: Add `--canned` and `--args` expansion path
- [x] C3-8: Ship built-ins: `unused`, `callers`, `inheritors`, `dead-docs`
- [x] C3-9: Add tests for custom canned queries, arg substitution, and invalid inputs

**Exit criteria**: Coverage import and canned queries both pass tests. Hand to Trin UAT.

---

### Post-Implementation

- [x] Trin UAT (per cycle)
- [x] Morpheus review (per cycle)
- [ ] Oracle doc groom
- [ ] Smith end-to-end user test
- [x] Cypher closeout


---


## SPRINT_16_C1_Summary_2026-04-08T18-52.md

**Original Location**: `agents/neo.docs/SPRINT_16_C1_Summary_2026-04-08T18-52.md`


## Sprint 16 Cycle 1 Summary

**Author**: Neo  
**Date**: 2026-04-08T18:52  
**Scope**: S16-1 — Fix `--slice` for OR'd multi-type queries

### Changes Made

- Updated `via/pipeline/executor.py` so OR'd type queries paginate against the combined result set.
- `_match_multiple_types()` now:
  - fetches all matching records for each requested type
  - combines and orders them consistently
  - applies `offset`/`limit` after combination
  - rewrites `total_matches` to reflect the combined count
- `_execute_match_stage()` now passes the computed `offset` into `_match_multiple_types()`.

### Tests Added

- `tests/unit/test_sprint16_c1.py`
  - second slice window for OR queries advances correctly
  - `total`/`shown` reflect the combined OR-query result set
  - `-n 0` returns all OR-query matches

### Verification

- `python -m pytest tests/unit/test_sprint16_c1.py -q` → 3 passed
- `python -m pytest tests/unit/test_sprint15_c2.py -q` → 16 passed

### Notes

- `make test` could not be used for verification in this session because the target attempted dependency bootstrap and failed on restricted network access.


---


## SPRINT_16_Summary_2026-04-08T19-00.md

**Original Location**: `agents/neo.docs/SPRINT_16_Summary_2026-04-08T19-00.md`


## Sprint 16 Implementation Summary

**Author**: Neo  
**Date**: 2026-04-08T19:00

### Delivered

- S16-1: OR-query `--slice` fix in `via/pipeline/executor.py`
- S16-2: `-ts` string constants across parser/index/query stack
- S16-3: `coverage import` using `coverage.xml`
- S16-4: `--canned` query expansion with built-ins and local JSON configs

### Verification

- 176 targeted tests passed locally
- Key files exercised: parser, indexing, match/query, relationship parser, CLI integration


---


## SPRINT_16_UAT_Summary_2026-04-08T19-00.md

**Original Location**: `agents/trin.docs/SPRINT_16_UAT_Summary_2026-04-08T19-00.md`


## Sprint 16 UAT Summary

**Author**: Trin  
**Date**: 2026-04-08T19:00

### Verdict

Sprint 16 UAT PASSED on targeted verification.

- Cycle 1: OR-query `--slice` fix verified
- Cycle 2: `-ts` string constants verified across parser/index/query flow
- Cycle 3: `coverage import` and `--canned` verified through CLI tests

### Verification

- 176 targeted tests passed locally
- No Sprint 15 slice regressions found

### Limits

- `make test` could not be used in this session because dependency bootstrap hit restricted network access


---
