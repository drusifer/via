# Sprint 17 — Link Intelligence + HTTP Bridge Primitives

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Build on Sprint 16's string-symbol foundation with link-aware indexing and a pragmatic cross-language HTTP bridge, while scoping any raw source-text search work as a bounded MVP rather than an unbounded grep replacement.
**Sources**: `agents/cypher.docs/SPRINT_16_CLOSEOUT_2026-04-08T19:00.md`, `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md`, Oracle recorded decisions in `agents/oracle.docs/context.md`
**Points**: ~7pt
**Baseline**: 176 targeted tests passed locally (end of Sprint 16)

---

## Sprint Goal

Sprint 16 made string constants queryable and reusable. Sprint 17 should capitalize on that by indexing URLs as first-class symbols, exposing the HTTP call sites that use them, and deciding whether via should support any bounded source-text search without collapsing the product back into generic grep.

The product goal is not "automatic full-stack tracing." It is a more pragmatic workflow:

1. find a URL or route string
2. see where docs or code declare or reference it
3. see which frontend call sites issue that HTTP request
4. keep any broader text-search story explicitly separate from structured symbol search

---

## Stories

### S17-1: URL/Link Indexing as `link` Symbols (P0, 2pt)

**As a** developer navigating docs and config-heavy code,  
**I want** URLs and hyperlinks indexed as `link` symbols,  
**so that** I can query for where a URL is declared or referenced without treating it as an arbitrary text blob.

#### Background

Sprint 16 proved the value of structured string-like symbols. The next logical step is to treat URLs and hyperlinks as a distinct symbol type, especially for markdown and other documentation where links are navigational structure, not just text.

#### Acceptance Criteria

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

### S17-2: Pragmatic HTTP Bridge via JS HTTP Call Sites (P0, 3pt)

**As an** expert user working across frontend and backend code,  
**I want** via to index common JavaScript HTTP call sites,  
**so that** I can manually bridge frontend requests to backend routes using Sprint 16's string-symbol model.

#### Background

Smith's review was explicit: full cross-language tracing is too framework-dependent to do cleanly right now. The pragmatic bridge is to index common JS HTTP calls and let users match on URL/path strings rather than pretending via understands every web framework.

#### Acceptance Criteria

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
### S17-3: `--contains` as Symbol-Body Filtering (P1, 2pt)


**As a** power user who sometimes needs raw source-text lookup,  
**I want** `--contains` to filter the symbols I already matched by whether their source body contains a string,  
**so that** I can ask questions like "which matching classes/functions contain `foo`?" without turning via into a generic repo-wide grep tool.

#### Background

Sprint 16 correctly refused to blur `-ts` into generic text search. The more useful follow-on is not repo-wide grep semantics; it is a post-match filter over structured symbols. That means the user still starts with via's symbol/query model, then narrows the results by searching the body/source span of each matched symbol.

Example target workflow:

```bash
via -mg '*Controller' -tc --contains 'rate_limit'
```

This should mean "find class symbols matching `*Controller` whose source body contains `rate_limit`," not "show me every line in the repo containing that text."

#### Acceptance Criteria

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

## Deferred Beyond Sprint 17

These remain explicitly out of this sprint unless scope is expanded:

| Item | Reason Deferred |
|------|-----------------|
| Automatic backend route resolution from frontend HTTP calls | Too framework-specific for the current architecture |
| Generic full-repo text indexing engine | Separate product/problem space from via's structured symbol model |
| Broad non-markdown link extraction across every parser | Start with high-value/low-risk sources first |

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S17-1 | URL/link indexing as `link` symbols | 2 | P0 |
| S17-2 | Pragmatic HTTP bridge via JS HTTP call sites | 3 | P0 |
| S17-3 | `--contains` as symbol-body filtering | 2 | P1 |
| **Total** | | **7pt** | |

---

## Recommended Planning Flow

1. Smith Gate 1 review of these stories
2. Morpheus architecture for Sprint 17, especially S17-2 and S17-3 boundaries
3. Mouse task board split into short cycles:
   - Cycle 1: S17-1
   - Cycle 2: S17-2
   - Cycle 3: S17-3 symbol-body filtering
