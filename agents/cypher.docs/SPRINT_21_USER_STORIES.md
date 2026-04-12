# Sprint 21 — JS Body Analyzer Extraction + MCP Builder Adoption

**Author**: Cypher (PM)
**Date**: 2026-04-12
**Theme**: Internal quality — complete the JS parser refactor backlog and close the last pipeline bypass
**Points**: ~6pts

---

## Context

Sprint 18 extracted JS top-level dispatch into polymorphic handler objects but explicitly deferred
`FunctionBodyAnalyzer` extraction. Three near-identical recursive tree-walkers still live as free
functions in `javascript_parser.py`:

- `_collect_calls_in_body` (line 531)
- `_collect_http_calls_in_body` (line 596)
- `_collect_string_constants_in_body` (line 805)

Sprint 19–20 shipped `ViaRunner` as the shared pipeline seam. The web API adopted it (Sprint 20),
but the MCP server still bypasses it in favour of raw `PipelineParser` + `PipelineExecutor`. That
means the MCP server doesn't benefit from any future pipeline-level improvements made in the runner.

Sprint 21 closes both gaps.

---

## Sprint Goal

Complete the Sprint 18 refactor backlog (body analyzer extraction) and migrate the MCP server to
`ViaRunner`, making the query path consistent across all three callers (CLI, web API, MCP).

**Non-scope**: executor redesign, full CLI parser replacement, new user-visible features.

---

## Story 1: Extract `_FunctionBodyAnalyzer` from JS Parser (P0, 3pts)

**As a developer maintaining `via`'s JS parser**, I want body-analysis logic encapsulated in a
dedicated class, so that adding a new body scan (e.g. import-call tracking, decorator analysis)
requires writing one method, not copy-pasting a tree-walker.

### Background

`_collect_calls_in_body`, `_collect_http_calls_in_body`, and `_collect_string_constants_in_body`
share an identical recursive structure:

1. Check current node type
2. Collect entity if match
3. Recurse into child nodes
4. Stop at `_FUNCTION_BOUNDARIES`

The only difference per walker is (a) the node type tested and (b) the entity appended to `out`.
A class with a single `_walk(node, ...)` skeleton and per-subclass `_visit(node)` hooks eliminates
this duplication.

### Acceptance Criteria

- [ ] New private class `_FunctionBodyAnalyzer` in `via/parsers/javascript_parser.py` (or extracted
  to a sibling `via/parsers/_js_body.py` — Morpheus to decide placement)
- [ ] Three concrete subclasses (or strategy objects):
  - `_CallAnalyzer` — replaces `_collect_calls_in_body`
  - `_HttpCallAnalyzer` — replaces `_collect_http_calls_in_body`
  - `_StringConstantAnalyzer` — replaces `_collect_string_constants_in_body`
- [ ] `_FunctionBodyAnalyzer.collect(root_node, content, ...) -> list` as the public entry point
  for each analyzer
- [ ] `_FUNCTION_BOUNDARIES` stop condition encapsulated inside the base class (not repeated)
- [ ] All existing call/http/string-constant tests pass without modification
- [ ] No user-visible behaviour change; no new CLI flags; no schema changes

### Implementation Notes

- `_extract_all_calls` (line 650), `_extract_all_http_calls`, `_extract_all_string_constants` are
  the top-level walkers that invoke the body functions — they should delegate to the new analyzer
  classes
- Morpheus to decide: single base class with abstract `_visit()` or a composition strategy; confirm
  before Neo starts

---

## Story 2: Migrate MCP Server to `ViaRunner` (P0, 3pts)

**As an operator running `via` in MCP mode**, I want the MCP server to execute queries through the
same `ViaRunner` path as the web API, so that pipeline improvements and validation are applied
consistently regardless of caller.

### Background

`via/mcp/server.py` currently builds stages like this:

```python
stages = PipelineParser().parse(clean_args)
executor = PipelineExecutor(mcp_store)
```

The web API (`via/web/api/query.py`) uses:

```python
runner = ViaRunner(db_store)
```

`ViaRunner` wraps `PipelineParser` + `PipelineExecutor` and centralises error handling, output
rendering, and any future runner-level improvements (e.g. query tracing, rate limits). The MCP
server bypasses all of this.

### Acceptance Criteria

- [ ] `via/mcp/server.py` imports and uses `ViaRunner` (from `via.api`) instead of calling
  `PipelineParser` + `PipelineExecutor` directly
- [ ] `ViaRunner` interface is sufficient for MCP usage (text/diagram output, error propagation) —
  if gaps exist, extend `ViaRunner` rather than keeping direct executor calls in the MCP server
- [ ] All existing MCP server behaviour is preserved: `via_query` tool, diagram detection,
  output-type detection, error dict returns
- [ ] Existing MCP integration tests pass without modification
- [ ] No user-visible behaviour change

### Implementation Notes

- `via/mcp/server.py:153,161` — two `PipelineParser().parse(...)` call sites
- `ViaRunner.run_raw(args: list[str]) -> str` may need to be added if it doesn't yet expose a
  list-of-strings entry point (the builder path takes a builder object; MCP currently passes raw
  string args)
- Morpheus to confirm: extend `ViaRunner` with a `run_raw(args)` method, or have the MCP server
  construct a `ViaQueryBuilder` from its arg list?

---

## Sprint Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| S21-1 | 3 | P0 | Extract `_FunctionBodyAnalyzer` from JS parser |
| S21-2 | 3 | P0 | Migrate MCP server to `ViaRunner` |
| **Total** | **6** | | |

## Cycle Plan

| Cycle | Phase | Stories |
|-------|-------|---------|
| 1 | S21-1 body analyzer extraction | S21-1 |
| 2 | S21-2 MCP runner migration | S21-2 |

---

## Out of Scope

- Executor redesign / full CLI parser replacement
- New user-visible query features
- Python parser body analyzer (separate backlog item if desired)
- Broader builder adoption beyond MCP server

---

## Arch Handoff

@Morpheus: Sprint 21 user stories ready. Two design decisions needed before Neo starts:

1. **S21-1 placement**: `_FunctionBodyAnalyzer` in `javascript_parser.py` or extracted to
   `via/parsers/_js_body.py`? Recommend separate file given the module is already 926 lines.
2. **S21-1 pattern**: Single abstract base class with `_visit()` hook, or composition (strategy
   objects passed to a shared walker)? Recommend base class — consistent with Sprint 18 handler
   pattern.
3. **S21-2 ViaRunner gap**: Does `ViaRunner` need a new `run_raw(args: list[str])` method, or
   should the MCP server construct a `ViaQueryBuilder` from its string args? Recommend `run_raw`
   as the minimal seam — cleaner than parsing CLI args into builder calls.
