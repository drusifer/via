# Sprint 17 — Architecture

**Author**: Morpheus (Tech Lead)  
**Date**: 2026-04-08  
**Stories**: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`  
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_17_GATE1_REVIEW.md`)  
**Oracle Basis**: `agents/oracle.docs/context.md` reviewed for carry-forward CLI and relationship decisions

---

## Architectural Summary

Sprint 17 should extend Sprint 16's structured-symbol model, not sidestep it.

The governing decisions are:

1. `link` is a new structured symbol type, parallel to `string_constant`, not a text-search mode.
2. The HTTP bridge is a primitive visibility feature for outbound JS/TS HTTP call sites, not automatic frontend-to-backend resolution.
3. `--contains` is a post-match symbol-body filter that uses existing file spans (`byte_offset`, `byte_length`) to inspect source bodies after symbol matching.
4. Sprint 17 should prefer additive parser/index/executor changes over new storage engines or new query subsystems.

---

## S17-1: URL/Link Indexing As `link` Symbols (2pt)

### Architecture

#### 1. New Symbol Type

Add a new symbol type: `link`.

- CLI flag: `-tl`
- Internal enum/type support alongside `string_constant`
- Match/render path remains identical to other leaf symbols

#### 2. Extraction Scope

Sprint 17 should start with markdown links only:

- `[label](target)`
- reference-style link targets only if trivially recoverable
- bare URLs are optional and should not delay the sprint

This keeps the parser risk low and matches the highest-value source called out in backlog discussions.

#### 3. Parser Contract

Extend the markdown parser contract to emit structured link entities in `ParseResult`, similar to how Sprint 16 added `string_constants`.

Each link entity should carry:

- target URL
- line number
- byte offset / byte length
- optional label text

#### 4. Storage Model

Persist each extracted link as a normal symbol row:

- `symbol_type = link`
- `symbol_name = target URL`
- `qualified_name` should include file path and a stable per-link discriminator
- `parent_name` may point to the enclosing markdown header path when resolvable, but that is optional for Sprint 17

No new relationship type is required for Story 1.

### Files Changed

| File | Change |
|------|--------|
| `via/core/types.py` / flag definitions | Add `link` symbol type and `-tl` flag |
| `via/parsers/base.py` | Add `LinkEntity` + `ParseResult.links` |
| `via/parsers/markdown_parser.py` | Extract markdown links |
| `via/services/indexing.py` | Persist link symbols |
| renderers/tests/docs | Display and coverage |

---

## S17-2: Pragmatic HTTP Bridge Via JS HTTP Call Sites (3pt)

### Architecture

#### 1. Relationship Model

Use a new relationship type: `http-calls`.

This is cleaner than inventing an HTTP-call symbol family because the user's mental model is relational:

- "what JS symbols issue HTTP requests?"
- "what calls reference `/api/foo`?"

The anchor remains the callable/function/method symbol, and the outbound HTTP target remains discoverable via Sprint 16 `string_constant` symbols.

#### 2. Extraction Scope

Recognize high-signal JS/TS forms only:

- `fetch(url, ...)`
- `axios(url, ...)`
- `axios.get/post/put/delete(url, ...)`
- `XMLHttpRequest.open(method, url, ...)` when statically identifiable

Skip dynamic or framework-specific abstractions in Sprint 17.

#### 3. Ownership Model

When a JS/TS HTTP call is found:

- attach the call site to the enclosing function/method/arrow-function symbol when known
- store a `string_constant` symbol for the URL/path if Sprint 16 extraction already captures it
- add `http-calls` from the enclosing symbol to the URL/path-backed symbol when resolvable

If direct symbol-to-symbol linking to the string constant proves awkward, Morpheus authorizes a fallback:

- store `http-calls` from enclosing code symbol to a synthetic `link` or `string_constant`-like target symbol representing the URL literal

The key is that users can traverse HTTP call sites semantically; exact internal target ownership can be finalized during implementation if the query surface remains stable.

#### 4. User Query Model

Sprint 17 should document one or both of these workflows:

```bash
via -mg '/api/*' -ts --via references -mg '*' -tf --lang js
via -mg '*' -tf --lang js --via http-calls -mg '/api/*' -tl
```

The second form is preferable if `http-calls` ships cleanly because it makes the new capability visible and learnable.

#### 5. Explicit Non-Goal

Do not claim:

- automatic resolution to Python route handlers
- framework-aware route normalization
- end-to-end "trace request from button to backend method"

Sprint 17 ships the primitives only.

### Files Changed

| File | Change |
|------|--------|
| `via/core/relationship_types.py` | Add `http-calls` |
| `via/parsers/javascript_parser.py` | Extract supported HTTP call patterns |
| `via/services/indexing.py` | Persist `http-calls` relationships |
| relationship query/docs/tests | Add traversal/query coverage |

---

## S17-3: `--contains` As Symbol-Body Filtering (2pt)

### Architecture

#### 1. Execution Model

`--contains` is not a database match operator.

Execution should be:

1. run the normal symbol query first
2. for each matched symbol with a valid file span, read the symbol body from disk using `file_path`, `byte_offset`, and `byte_length`
3. keep only symbols whose extracted body matches the requested pattern

This preserves via's existing matcher pipeline and keeps the feature honest about where the work happens.

#### 2. Supported Symbol Scope

Only symbol types with meaningful source spans should participate:

- class
- function
- method
- header
- possibly global / string_constant / link if their byte spans are already trustworthy

File/filepath-style results with no body span should be rejected or skipped with a clear message. Silent degradation is not acceptable.

#### 3. Match Semantics

`--contains` should reuse the existing pattern family where possible:

- default glob semantics if consistent with `-mg`
- future extension to regex/sql-like variants can wait

For Sprint 17, one flag is enough:

```bash
via -mg '*Controller' -tc --contains 'rate_limit'
```

#### 4. Output Model

The command still returns symbol records, not line snippets.

If the existing raw/formatted output is insufficient for inspection, implementation may add a body-oriented render mode or extend raw output to emit the full symbol body. That is secondary. The primary feature is filtering, not rendering.

#### 5. Performance Constraint

Body reads are allowed to be per-result in Sprint 17 because this is a post-match narrowing step over an already limited symbol set.

Do not add:

- a full-text index
- repo-wide scan mode
- a second query engine

### Files Changed

| File | Change |
|------|--------|
| CLI/parser flags | Add `--contains` |
| `via/pipeline/executor.py` | Post-match body filtering stage |
| utility layer | Read symbol body by byte span safely |
| tests/docs | Feature semantics and unsupported cases |

---

## Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S17-1 | Low-risk extension of markdown parser + indexing |
| 2 | S17-2 | Main architecture-heavy feature; relationship plumbing in JS parser/indexer |
| 3 | S17-3 | Executor-stage body filtering over existing symbol spans |

---

## Risks

1. `link` and `string_constant` semantics may blur if URLs are duplicated across both types. Docs/help must explain the distinction clearly.
2. JS HTTP call extraction can drift into framework-specific heuristics. Keep Sprint 17 to static, recognizable primitives.
3. `--contains` can become misleading if unsupported symbol types are silently ignored. Errors or skips must be explicit.
4. Per-result body reads could become expensive on large result sets. Keep the feature explicitly post-match and bounded by the existing result pipeline.

---

## Smith Gate 2 Notes

- `-tl`, `-ts`, and `--contains` are intentionally different surfaces with different mental models.
- `http-calls` is approved only as a primitive visibility relationship, not a claim of automatic cross-language tracing.
- `--contains` remains a symbol filter that returns symbols; it must not degrade into grep-style line output.
