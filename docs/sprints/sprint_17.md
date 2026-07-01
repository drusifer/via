# Sprint 17 Consolidated Documentation

This document consolidates all documentation for Sprint 17.

## Table of Contents

- [SPRINT_17_CLOSEOUT_2026-04-08T20-45.md](#sprint-17-closeout-2026-04-08t20-45md) (originally `agents/cypher.docs/SPRINT_17_CLOSEOUT_2026-04-08T20-45.md`)

- [SPRINT_17_USER_STORIES.md](#sprint-17-user-storiesmd) (originally `agents/cypher.docs/SPRINT_17_USER_STORIES.md`)

- [SPRINT_17_ARCHITECTURE.md](#sprint-17-architecturemd) (originally `agents/morpheus.docs/SPRINT_17_ARCHITECTURE.md`)

- [SPRINT_17_REVIEW_2026-04-08T20-45.md](#sprint-17-review-2026-04-08t20-45md) (originally `agents/morpheus.docs/SPRINT_17_REVIEW_2026-04-08T20-45.md`)

- [SPRINT_17_GATE1_REVIEW.md](#sprint-17-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_17_GATE1_REVIEW.md`)

- [SPRINT_17_GATE2_REVIEW.md](#sprint-17-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_17_GATE2_REVIEW.md`)

- [SPRINT_17_SCRUM_CLOSEOUT_Summary_2026-04-08T20-45.md](#sprint-17-scrum-closeout-summary-2026-04-08t20-45md) (originally `agents/mouse.docs/SPRINT_17_SCRUM_CLOSEOUT_Summary_2026-04-08T20-45.md`)

- [SPRINT_17_TASKS.md](#sprint-17-tasksmd) (originally `agents/mouse.docs/SPRINT_17_TASKS.md`)

- [SPRINT_17_Summary_2026-04-08T20-45.md](#sprint-17-summary-2026-04-08t20-45md) (originally `agents/neo.docs/SPRINT_17_Summary_2026-04-08T20-45.md`)

- [SPRINT_17_UAT_Summary_2026-04-08T20-45.md](#sprint-17-uat-summary-2026-04-08t20-45md) (originally `agents/trin.docs/SPRINT_17_UAT_Summary_2026-04-08T20-45.md`)


---


## SPRINT_17_CLOSEOUT_2026-04-08T20-45.md

**Original Location**: `agents/cypher.docs/SPRINT_17_CLOSEOUT_2026-04-08T20-45.md`


## Sprint 17 Closeout

**Author**: Cypher  
**Date**: 2026-04-08T20:45

### Outcome

Sprint 17 is SHIPPED.

#### Delivered
- S17-1: `link` symbols with markdown-first URL extraction
- S17-2: `http-calls` primitive for JS/TS outbound HTTP call sites
- S17-3: `--contains` as symbol-body filtering

#### Verification
- 138 targeted tests passed locally
- Sprint 15/16 touched regressions stayed green in the consolidated run

#### Product Notes
- The sprint delivered the intended structured workflow extension without collapsing via into generic grep
- Automatic backend route resolution remains out of scope
- Broader non-markdown link extraction remains backlog material


---


## SPRINT_17_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`


## Sprint 17 — Link Intelligence + HTTP Bridge Primitives

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Build on Sprint 16's string-symbol foundation with link-aware indexing and a pragmatic cross-language HTTP bridge, while scoping any raw source-text search work as a bounded MVP rather than an unbounded grep replacement.
**Sources**: `agents/cypher.docs/SPRINT_16_CLOSEOUT_2026-04-08T19-00.md`, `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`, Oracle recorded decisions in `agents/oracle.docs/context.md`
**Points**: ~7pt
**Baseline**: 176 targeted tests passed locally (end of Sprint 16)

---

### Sprint Goal

Sprint 16 made string constants queryable and reusable. Sprint 17 should capitalize on that by indexing URLs as first-class symbols, exposing the HTTP call sites that use them, and deciding whether via should support any bounded source-text search without collapsing the product back into generic grep.

The product goal is not "automatic full-stack tracing." It is a more pragmatic workflow:

1. find a URL or route string
2. see where docs or code declare or reference it
3. see which frontend call sites issue that HTTP request
4. keep any broader text-search story explicitly separate from structured symbol search

---

### Stories

#### S17-1: URL/Link Indexing as `link` Symbols (P0, 2pt)

**As a** developer navigating docs and config-heavy code,  
**I want** URLs and hyperlinks indexed as `link` symbols,  
**so that** I can query for where a URL is declared or referenced without treating it as an arbitrary text blob.

##### Background

Sprint 16 proved the value of structured string-like symbols. The next logical step is to treat URLs and hyperlinks as a distinct symbol type, especially for markdown and other documentation where links are navigational structure, not just text.

##### Acceptance Criteria

1. Add a new symbol type flag: `-tl` / `--type-link` or equivalent naming consistent with existing CLI conventions.
2. Markdown links are indexed as `link` symbols with:
   - displayed URL target
   - file/line metadata
   - optional label/title metadata when available
3. Bare URLs in supported sources may be indexed when extraction is low-risk, but markdown link syntax is the minimum required scope.
4. `link` symbols participate in normal matcher behavior (`-mg`, regex, JSON output, slicing).
5. The feature is documented as structured URL indexing, not generic raw-text URL search.
6. **Tests**: markdown link extraction, matching, rendering, and regression coverage for non-link markdown structure.

**Files expected to change:**
- parser and symbol-type definitions
- markdown parsing/indexing path
- renderer/tests/docs

---

#### S17-2: Pragmatic HTTP Bridge via JS HTTP Call Sites (P0, 3pt)

**As an** expert user working across frontend and backend code,  
**I want** via to index common JavaScript HTTP call sites,  
**so that** I can manually bridge frontend requests to backend routes using Sprint 16's string-symbol model.

##### Background

Smith's review was explicit: full cross-language tracing is too framework-dependent to do cleanly right now. The pragmatic bridge is to index common JS HTTP calls and let users match on URL/path strings rather than pretending via understands every web framework.

##### Acceptance Criteria

1. JavaScript/TypeScript indexing recognizes common outbound HTTP call forms:
   - `fetch(...)`
   - `axios(...)` and `axios.get/post/...`
   - `XMLHttpRequest` open/send patterns when reasonably detectable
2. Detected call sites are queryable through a dedicated relationship or symbol model that Morpheus can finalize in architecture.
3. URL/path strings used by those HTTP calls remain discoverable through existing `-ts` support where possible.
4. The documented workflow supports queries of the form:
   ```bash
   via -mg '/api/*' -ts --via references -mg '*' -tf --lang js
   ```
   and/or a dedicated HTTP-call traversal if architecture supports it.
5. The feature does not claim automatic resolution to Python route handlers.
6. Docs clearly frame this as an "HTTP bridge" primitive, not full cross-language tracing.
7. **Tests**: JS/TS fixtures covering fetch/axios patterns and at least one end-to-end bridge query example.

**Files expected to change:**
- `via/parsers/javascript_parser.py`
- relationship/symbol model definitions
- indexing/query plumbing
- tests/docs

---
#### S17-3: `--contains` as Symbol-Body Filtering (P1, 2pt)


**As a** power user who sometimes needs raw source-text lookup,  
**I want** `--contains` to filter the symbols I already matched by whether their source body contains a string,  
**so that** I can ask questions like "which matching classes/functions contain `foo`?" without turning via into a generic repo-wide grep tool.

##### Background

Sprint 16 correctly refused to blur `-ts` into generic text search. The more useful follow-on is not repo-wide grep semantics; it is a post-match filter over structured symbols. That means the user still starts with via's symbol/query model, then narrows the results by searching the body/source span of each matched symbol.

Example target workflow:

```bash
via -mg '*Controller' -tc --contains 'rate_limit'
```

This should mean "find class symbols matching `*Controller` whose source body contains `rate_limit`," not "show me every line in the repo containing that text."

##### Acceptance Criteria

1. `--contains <pattern>` is defined as a filter over the already-matched symbol set, using each symbol's source/body text where available.
2. The command continues to return symbol results, not grep-style line snippets.
3. Scope is explicitly limited to symbol types that have retrievable source spans/bodies.
4. If current output/render support is insufficient, Sprint 17 may extend existing raw/body-oriented output so users can inspect the full matched symbol body that `--contains` evaluated.
5. Docs clearly distinguish:
   - `-ts` = structured string-constant symbols
   - `--contains` = body-text filter over matched symbols
   - external grep/ripgrep = repo-wide text search
6. The implementation must not pretend this is SQL-backed symbol lookup; body inspection may happen after initial symbol matching.
7. **Tests**: at least one function/class/body filter example, one unsupported-symbol-type behavior case, and one regression showing results remain symbols rather than raw grep lines.

**Files expected to change:**
- architecture/docs minimum
- query/executor path for post-match body filtering
- renderer/output path only if body inspection needs an exposed/raw-symbol-body mode

---

### Deferred Beyond Sprint 17

These remain explicitly out of this sprint unless scope is expanded:

| Item | Reason Deferred |
|------|-----------------|
| Automatic backend route resolution from frontend HTTP calls | Too framework-specific for the current architecture |
| Generic full-repo text indexing engine | Separate product/problem space from via's structured symbol model |
| Broad non-markdown link extraction across every parser | Start with high-value/low-risk sources first |

---

### Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S17-1 | URL/link indexing as `link` symbols | 2 | P0 |
| S17-2 | Pragmatic HTTP bridge via JS HTTP call sites | 3 | P0 |
| S17-3 | `--contains` as symbol-body filtering | 2 | P1 |
| **Total** | | **7pt** | |

---

### Recommended Planning Flow

1. Smith Gate 1 review of these stories
2. Morpheus architecture for Sprint 17, especially S17-2 and S17-3 boundaries
3. Mouse task board split into short cycles:
   - Cycle 1: S17-1
   - Cycle 2: S17-2
   - Cycle 3: S17-3 symbol-body filtering


---


## SPRINT_17_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_17_ARCHITECTURE.md`


## Sprint 17 — Architecture

**Author**: Morpheus (Tech Lead)  
**Date**: 2026-04-08  
**Stories**: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`  
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_17_GATE1_REVIEW.md`)  
**Oracle Basis**: `agents/oracle.docs/context.md` reviewed for carry-forward CLI and relationship decisions

---

### Architectural Summary

Sprint 17 should extend Sprint 16's structured-symbol model, not sidestep it.

The governing decisions are:

1. `link` is a new structured symbol type, parallel to `string_constant`, not a text-search mode.
2. The HTTP bridge is a primitive visibility feature for outbound JS/TS HTTP call sites, not automatic frontend-to-backend resolution.
3. `--contains` is a post-match symbol-body filter that uses existing file spans (`byte_offset`, `byte_length`) to inspect source bodies after symbol matching.
4. Sprint 17 should prefer additive parser/index/executor changes over new storage engines or new query subsystems.

---

### S17-1: URL/Link Indexing As `link` Symbols (2pt)

#### Architecture

##### 1. New Symbol Type

Add a new symbol type: `link`.

- CLI flag: `-tl`
- Internal enum/type support alongside `string_constant`
- Match/render path remains identical to other leaf symbols

##### 2. Extraction Scope

Sprint 17 should start with markdown links only:

- `[label](target)`
- reference-style link targets only if trivially recoverable
- bare URLs are optional and should not delay the sprint

This keeps the parser risk low and matches the highest-value source called out in backlog discussions.

##### 3. Parser Contract

Extend the markdown parser contract to emit structured link entities in `ParseResult`, similar to how Sprint 16 added `string_constants`.

Each link entity should carry:

- target URL
- line number
- byte offset / byte length
- optional label text

##### 4. Storage Model

Persist each extracted link as a normal symbol row:

- `symbol_type = link`
- `symbol_name = target URL`
- `qualified_name` should include file path and a stable per-link discriminator
- `parent_name` may point to the enclosing markdown header path when resolvable, but that is optional for Sprint 17

No new relationship type is required for Story 1.

#### Files Changed

| File | Change |
|------|--------|
| `via/core/types.py` / flag definitions | Add `link` symbol type and `-tl` flag |
| `via/parsers/base.py` | Add `LinkEntity` + `ParseResult.links` |
| `via/parsers/markdown_parser.py` | Extract markdown links |
| `via/services/indexing.py` | Persist link symbols |
| renderers/tests/docs | Display and coverage |

---

### S17-2: Pragmatic HTTP Bridge Via JS HTTP Call Sites (3pt)

#### Architecture

##### 1. Relationship Model

Use a new relationship type: `http-calls`.

This is cleaner than inventing an HTTP-call symbol family because the user's mental model is relational:

- "what JS symbols issue HTTP requests?"
- "what calls reference `/api/foo`?"

The anchor remains the callable/function/method symbol, and the outbound HTTP target remains discoverable via Sprint 16 `string_constant` symbols.

##### 2. Extraction Scope

Recognize high-signal JS/TS forms only:

- `fetch(url, ...)`
- `axios(url, ...)`
- `axios.get/post/put/delete(url, ...)`
- `XMLHttpRequest.open(method, url, ...)` when statically identifiable

Skip dynamic or framework-specific abstractions in Sprint 17.

##### 3. Ownership Model

When a JS/TS HTTP call is found:

- attach the call site to the enclosing function/method/arrow-function symbol when known
- store a `string_constant` symbol for the URL/path if Sprint 16 extraction already captures it
- add `http-calls` from the enclosing symbol to the URL/path-backed symbol when resolvable

If direct symbol-to-symbol linking to the string constant proves awkward, Morpheus authorizes a fallback:

- store `http-calls` from enclosing code symbol to a synthetic `link` or `string_constant`-like target symbol representing the URL literal

The key is that users can traverse HTTP call sites semantically; exact internal target ownership can be finalized during implementation if the query surface remains stable.

##### 4. User Query Model

Sprint 17 should document one or both of these workflows:

```bash
via -mg '/api/*' -ts --via references -mg '*' -tf --lang js
via -mg '*' -tf --lang js --via http-calls -mg '/api/*' -tl
```

The second form is preferable if `http-calls` ships cleanly because it makes the new capability visible and learnable.

##### 5. Explicit Non-Goal

Do not claim:

- automatic resolution to Python route handlers
- framework-aware route normalization
- end-to-end "trace request from button to backend method"

Sprint 17 ships the primitives only.

#### Files Changed

| File | Change |
|------|--------|
| `via/core/relationship_types.py` | Add `http-calls` |
| `via/parsers/javascript_parser.py` | Extract supported HTTP call patterns |
| `via/services/indexing.py` | Persist `http-calls` relationships |
| relationship query/docs/tests | Add traversal/query coverage |

---

### S17-3: `--contains` As Symbol-Body Filtering (2pt)

#### Architecture

##### 1. Execution Model

`--contains` is not a database match operator.

Execution should be:

1. run the normal symbol query first
2. for each matched symbol with a valid file span, read the symbol body from disk using `file_path`, `byte_offset`, and `byte_length`
3. keep only symbols whose extracted body matches the requested pattern

This preserves via's existing matcher pipeline and keeps the feature honest about where the work happens.

##### 2. Supported Symbol Scope

Only symbol types with meaningful source spans should participate:

- class
- function
- method
- header
- possibly global / string_constant / link if their byte spans are already trustworthy

File/filepath-style results with no body span should be rejected or skipped with a clear message. Silent degradation is not acceptable.

##### 3. Match Semantics

`--contains` should reuse the existing pattern family where possible:

- default glob semantics if consistent with `-mg`
- future extension to regex/sql-like variants can wait

For Sprint 17, one flag is enough:

```bash
via -mg '*Controller' -tc --contains 'rate_limit'
```

##### 4. Output Model

The command still returns symbol records, not line snippets.

If the existing raw/formatted output is insufficient for inspection, implementation may add a body-oriented render mode or extend raw output to emit the full symbol body. That is secondary. The primary feature is filtering, not rendering.

##### 5. Performance Constraint

Body reads are allowed to be per-result in Sprint 17 because this is a post-match narrowing step over an already limited symbol set.

Do not add:

- a full-text index
- repo-wide scan mode
- a second query engine

#### Files Changed

| File | Change |
|------|--------|
| CLI/parser flags | Add `--contains` |
| `via/pipeline/executor.py` | Post-match body filtering stage |
| utility layer | Read symbol body by byte span safely |
| tests/docs | Feature semantics and unsupported cases |

---

### Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S17-1 | Low-risk extension of markdown parser + indexing |
| 2 | S17-2 | Main architecture-heavy feature; relationship plumbing in JS parser/indexer |
| 3 | S17-3 | Executor-stage body filtering over existing symbol spans |

---

### Risks

1. `link` and `string_constant` semantics may blur if URLs are duplicated across both types. Docs/help must explain the distinction clearly.
2. JS HTTP call extraction can drift into framework-specific heuristics. Keep Sprint 17 to static, recognizable primitives.
3. `--contains` can become misleading if unsupported symbol types are silently ignored. Errors or skips must be explicit.
4. Per-result body reads could become expensive on large result sets. Keep the feature explicitly post-match and bounded by the existing result pipeline.

---

### Smith Gate 2 Notes

- `-tl`, `-ts`, and `--contains` are intentionally different surfaces with different mental models.
- `http-calls` is approved only as a primitive visibility relationship, not a claim of automatic cross-language tracing.
- `--contains` remains a symbol filter that returns symbols; it must not degrade into grep-style line output.


---


## SPRINT_17_REVIEW_2026-04-08T20-45.md

**Original Location**: `agents/morpheus.docs/SPRINT_17_REVIEW_2026-04-08T20-45.md`


## Sprint 17 Review

**Author**: Morpheus  
**Date**: 2026-04-08T20:45

### Verdict

APPROVED

### Review Notes

- S17-1 delivered through the existing markdown parser/index seams with a new `link` symbol type
- S17-2 delivered as an additive `http-calls` relationship over JS/TS call-site analysis
- S17-3 delivered as executor-stage body filtering over existing byte spans, with no second query engine

### Architecture Match

Sprint 17 shipped as designed. No redesign was required during implementation.


---


## SPRINT_17_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_17_GATE1_REVIEW.md`


## Sprint 17 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 17 — Link Intelligence + HTTP Bridge Primitives  
**Source Reviewed**: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`

### Verdict

**APPROVED**

### Summary

Sprint 17 is pointed at a real user workflow instead of abstract "cross-language tracing" claims. The revised S17-3 is the key improvement: `--contains` is now framed as a filter over already-matched symbols, which preserves via's mental model and avoids collapsing the product into repo-wide grep.

### Story Verdicts

#### S17-1: URL/Link Indexing as `link` Symbols
**Verdict**: APPROVED

Why:
- Matches user expectations for docs/config navigation.
- Keeps scope grounded in structured link targets rather than arbitrary text.
- Markdown-first scoping is a good risk boundary.

Notes for Morpheus:
- Keep the flag naming consistent with existing type aliases and long-form help text.
- Ensure rendered output exposes the URL target clearly; optional label metadata is useful but secondary.

#### S17-2: Pragmatic HTTP Bridge via JS HTTP Call Sites
**Verdict**: APPROVED WITH NOTES

Why:
- The story now avoids the misleading promise of automatic route resolution.
- It aligns with Smith's earlier recommendation: expose HTTP call primitives and let users bridge with `-ts` and relationships.

Notes for Morpheus:
- The user mental model should stay simple: "show me outbound HTTP call sites" is clearer than introducing a magical cross-language abstraction.
- If a new relationship type is introduced, the CLI/help text must explain it in plain language and show one example query.

#### S17-3: `--contains` as Symbol-Body Filtering
**Verdict**: APPROVED

Why:
- This matches the user's feedback and is materially different from grep.
- Returning symbols instead of line snippets preserves consistency with the rest of via.
- The explicit separation from `-ts` and external grep tools addresses the biggest Sprint 16 risk.

Notes for Morpheus:
- Unsupported symbol/body cases must fail clearly or skip clearly; silent partial behavior would be a UX defect.
- If body retrieval depends on existing raw output internals, keep the public model simple: `--contains` filters symbols, it does not change the result type by default.

### Gate Notes

1. `-ts`, `link`, and `--contains` must remain distinct concepts in docs/help:
   - `-ts`: structured string-constant symbols
   - `-tl`/`link`: structured URL/link symbols
   - `--contains`: body-text filter over matched symbols
2. Sprint 17 should ship at least one help/doc example for each new surface; this sprint is prone to semantic confusion if examples are missing.
3. The HTTP bridge story is acceptable only if the team keeps the claim at the primitive/workflow level and avoids overstating automatic linkage.

### Handoff

Sprint 17 Gate 1 is approved to proceed to architecture.


---


## SPRINT_17_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_17_GATE2_REVIEW.md`


## Sprint 17 Gate 2 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 17  
**Architecture Reviewed**: `agents/morpheus.docs/SPRINT_17_ARCHITECTURE.md`

### Verdict

APPROVED

### Summary

The architecture kept the user-facing boundaries intact through implementation:

- `link` remains a structured URL/link symbol, not a generic string alias
- `http-calls` ships as a primitive JS/TS call-site relationship, not fake automatic tracing
- `--contains` filters symbol bodies and still returns symbols instead of grep-like line output

### Notes

1. The distinction among `-tl`, `-ts`, and `--contains` is still the key UX risk, but the implemented surfaces are consistent with the approved stories.
2. The `http-calls` mental model is acceptable because it exposes exactly what users can rely on: outbound HTTP call sites.
3. `--contains` preserved via's symbol-query model, which was the critical Gate 1 requirement.


---


## SPRINT_17_SCRUM_CLOSEOUT_Summary_2026-04-08T20-45.md

**Original Location**: `agents/mouse.docs/SPRINT_17_SCRUM_CLOSEOUT_Summary_2026-04-08T20-45.md`


## Sprint 17 Scrum Closeout Summary

**Author**: Mouse  
**Date**: 2026-04-08T20:45

### Status

Sprint 17 is archived.

### Completed Flow

- Cypher planned Sprint 17
- Smith approved Gate 1
- Morpheus produced architecture
- Smith approved Gate 2
- Neo implemented all 3 stories
- Trin verified the sprint
- Morpheus and Cypher marked the sprint shipped
- Mouse archived the board

### Verification Reference

- Consolidated targeted suite: 138 passed


---


## SPRINT_17_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_17_TASKS.md`


## Sprint 17 Task Board

**Sprint**: 17  
**Theme**: Link Intelligence + HTTP Bridge Primitives  
**Status**: COMPLETE

### Cycles

| Cycle | Stories | Status |
|-------|---------|--------|
| 1 | S17-1 `link` symbols | ✅ Done |
| 2 | S17-2 `http-calls` primitive | ✅ Done |
| 3 | S17-3 `--contains` body filtering | ✅ Done |

### Notes

- Gate 1 approved by Smith
- Architecture completed by Morpheus
- Implementation completed by Neo
- Verification passed by Trin
- Final review approved by Smith and Morpheus


---


## SPRINT_17_Summary_2026-04-08T20-45.md

**Original Location**: `agents/neo.docs/SPRINT_17_Summary_2026-04-08T20-45.md`


## Sprint 17 Summary

**Author**: Neo  
**Date**: 2026-04-08T20:45

### Delivered

- S17-1: `link` symbol type with markdown link extraction and `-tl`
- S17-2: JS/TS `http-calls` primitive relationship for `fetch` / `axios` call sites
- S17-3: `--contains` as post-match symbol-body filtering over existing byte spans

### Files Changed

- `via/parsers/base.py`
- `via/parsers/markdown_parser.py`
- `via/parsers/javascript_parser.py`
- `via/services/indexing.py`
- `via/core/types.py`
- `via/core/flag_groups.py`
- `via/core/match_record.py`
- `via/core/relationship_types.py`
- `via/pipeline/parser.py`
- `via/pipeline/executor.py`
- `via/__main__.py`
- `tests/unit/test_sprint17_c1.py`
- `tests/unit/test_sprint17_c2.py`
- `tests/unit/test_sprint17_c3.py`

### Verification

- Consolidated targeted suite: 138 passed
- Notes: `make test` was not used for full-project verification because the repo bootstrap path previously failed under restricted network access


---


## SPRINT_17_UAT_Summary_2026-04-08T20-45.md

**Original Location**: `agents/trin.docs/SPRINT_17_UAT_Summary_2026-04-08T20-45.md`


## Sprint 17 UAT Summary

**Author**: Trin  
**Date**: 2026-04-08T20:45

### Verdict

PASS

### Verified

- S17-1: markdown link extraction/querying via `-tl`
- S17-2: JS HTTP call-site indexing/querying via `http-calls`
- S17-3: `--contains` filters symbol bodies and still returns symbol results

### Regression Coverage

- Markdown parser suite
- Pipeline parser suite
- Relationship executor suite
- Sprint 15 markdown declares
- Sprint 16 string constant path
- CLI match integration suite

### Verification Baseline

- Consolidated targeted suite: 138 passed, 19 warnings


---
