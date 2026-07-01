# Sprint 21 Consolidated Documentation

This document consolidates all documentation for Sprint 21.

## Table of Contents

- [SPRINT_21_CLOSEOUT_2026-04-12.md](#sprint-21-closeout-2026-04-12md) (originally `agents/cypher.docs/SPRINT_21_CLOSEOUT_2026-04-12.md`)

- [SPRINT_21_USER_STORIES.md](#sprint-21-user-storiesmd) (originally `agents/cypher.docs/SPRINT_21_USER_STORIES.md`)

- [SPRINT_21_ARCHITECTURE.md](#sprint-21-architecturemd) (originally `agents/morpheus.docs/SPRINT_21_ARCHITECTURE.md`)

- [SPRINT_21_TASKS.md](#sprint-21-tasksmd) (originally `agents/mouse.docs/SPRINT_21_TASKS.md`)


---


## SPRINT_21_CLOSEOUT_2026-04-12.md

**Original Location**: `agents/cypher.docs/SPRINT_21_CLOSEOUT_2026-04-12.md`


## Sprint 21 Closeout

**Author**: Cypher
**Date**: 2026-04-12

### Outcome

Sprint 21 is SHIPPED.

#### Delivered

- S21-1: `_FunctionBodyAnalyzer` extracted — `_js_body.py` (244 lines) with `_BodyAnalyzer` ABC
  + `_CallBodyAnalyzer`, `_HttpCallBodyAnalyzer`, `_StringConstantBodyAnalyzer`. 
  `javascript_parser.py` reduced from 926 → 754 lines.
- S21-2: `ViaRunner.run_cli_args(args: list[str])` added. MCP server migrated from direct
  `PipelineParser+PipelineExecutor` to `ViaRunner`. No `PipelineParser` or `PipelineExecutor`
  imports remain in `mcp/server.py`.

#### Verification

- 1259 tests passed, 1 skipped — both phases

#### Backlog Items Added

- Add explicit `_js_body` unit tests if body analysis logic diverges further (Trin/Smith)
- Executor strategy / full CLI parser replacement (Morpheus — defer unless planned)


---


## SPRINT_21_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_21_USER_STORIES.md`


## Sprint 21 — JS Body Analyzer Extraction + MCP Builder Adoption

**Author**: Cypher (PM)
**Date**: 2026-04-12
**Theme**: Internal quality — complete the JS parser refactor backlog and close the last pipeline bypass
**Points**: ~6pts

---

### Context

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

### Sprint Goal

Complete the Sprint 18 refactor backlog (body analyzer extraction) and migrate the MCP server to
`ViaRunner`, making the query path consistent across all three callers (CLI, web API, MCP).

**Non-scope**: executor redesign, full CLI parser replacement, new user-visible features.

---

### Story 1: Extract `_FunctionBodyAnalyzer` from JS Parser (P0, 3pts)

**As a developer maintaining `via`'s JS parser**, I want body-analysis logic encapsulated in a
dedicated class, so that adding a new body scan (e.g. import-call tracking, decorator analysis)
requires writing one method, not copy-pasting a tree-walker.

#### Background

`_collect_calls_in_body`, `_collect_http_calls_in_body`, and `_collect_string_constants_in_body`
share an identical recursive structure:

1. Check current node type
2. Collect entity if match
3. Recurse into child nodes
4. Stop at `_FUNCTION_BOUNDARIES`

The only difference per walker is (a) the node type tested and (b) the entity appended to `out`.
A class with a single `_walk(node, ...)` skeleton and per-subclass `_visit(node)` hooks eliminates
this duplication.

#### Acceptance Criteria

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

#### Implementation Notes

- `_extract_all_calls` (line 650), `_extract_all_http_calls`, `_extract_all_string_constants` are
  the top-level walkers that invoke the body functions — they should delegate to the new analyzer
  classes
- Morpheus to decide: single base class with abstract `_visit()` or a composition strategy; confirm
  before Neo starts

---

### Story 2: Migrate MCP Server to `ViaRunner` (P0, 3pts)

**As an operator running `via` in MCP mode**, I want the MCP server to execute queries through the
same `ViaRunner` path as the web API, so that pipeline improvements and validation are applied
consistently regardless of caller.

#### Background

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

#### Acceptance Criteria

- [ ] `via/mcp/server.py` imports and uses `ViaRunner` (from `via.api`) instead of calling
  `PipelineParser` + `PipelineExecutor` directly
- [ ] `ViaRunner` interface is sufficient for MCP usage (text/diagram output, error propagation) —
  if gaps exist, extend `ViaRunner` rather than keeping direct executor calls in the MCP server
- [ ] All existing MCP server behaviour is preserved: `via_query` tool, diagram detection,
  output-type detection, error dict returns
- [ ] Existing MCP integration tests pass without modification
- [ ] No user-visible behaviour change

#### Implementation Notes

- `via/mcp/server.py:153,161` — two `PipelineParser().parse(...)` call sites
- `ViaRunner.run_raw(args: list[str]) -> str` may need to be added if it doesn't yet expose a
  list-of-strings entry point (the builder path takes a builder object; MCP currently passes raw
  string args)
- Morpheus to confirm: extend `ViaRunner` with a `run_raw(args)` method, or have the MCP server
  construct a `ViaQueryBuilder` from its arg list?

---

### Sprint Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| S21-1 | 3 | P0 | Extract `_FunctionBodyAnalyzer` from JS parser |
| S21-2 | 3 | P0 | Migrate MCP server to `ViaRunner` |
| **Total** | **6** | | |

### Cycle Plan

| Cycle | Phase | Stories |
|-------|-------|---------|
| 1 | S21-1 body analyzer extraction | S21-1 |
| 2 | S21-2 MCP runner migration | S21-2 |

---

### Out of Scope

- Executor redesign / full CLI parser replacement
- New user-visible query features
- Python parser body analyzer (separate backlog item if desired)
- Broader builder adoption beyond MCP server

---

### Arch Handoff

@Morpheus: Sprint 21 user stories ready. Two design decisions needed before Neo starts:

1. **S21-1 placement**: `_FunctionBodyAnalyzer` in `javascript_parser.py` or extracted to
   `via/parsers/_js_body.py`? Recommend separate file given the module is already 926 lines.
2. **S21-1 pattern**: Single abstract base class with `_visit()` hook, or composition (strategy
   objects passed to a shared walker)? Recommend base class — consistent with Sprint 18 handler
   pattern.
3. **S21-2 ViaRunner gap**: Does `ViaRunner` need a new `run_raw(args: list[str])` method, or
   should the MCP server construct a `ViaQueryBuilder` from its string args? Recommend `run_raw`
   as the minimal seam — cleaner than parsing CLI args into builder calls.


---


## SPRINT_21_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_21_ARCHITECTURE.md`


## Sprint 21 Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-12
**Sprint**: 21 — JS Body Analyzer Extraction + MCP Builder Adoption

---

### S21-1: `_FunctionBodyAnalyzer` Extraction

#### Problem

`javascript_parser.py` (926 lines) contains three near-identical recursive tree-walkers as free
functions:

| Function | Collects |
|----------|----------|
| `_collect_calls_in_body` (L531) | `CallEntity` — all JS function/method calls |
| `_collect_http_calls_in_body` (L596) | `CallEntity` — HTTP calls (fetch, axios, etc.) |
| `_collect_string_constants_in_body` (L805) | string constant entities |

All three share:
- `_FUNCTION_BOUNDARIES` stop condition (do not descend into nested function nodes)
- `out: list` accumulation pattern
- Same caller context parameters (`caller_name`, `caller_type`, `caller_parent`)

#### Decision: Placement

**Extract to `via/parsers/_js_body.py`** (private module, `_` prefix).

Rationale: `javascript_parser.py` at 926 lines is already large. The body analysis functions are
cohesive and self-contained. Extracting them is consistent with how Sprint 18 extracted top-level
handlers — those remain in `javascript_parser.py` because they're tightly coupled to the parse
result; body analyzers are not.

#### Decision: Pattern

**Abstract base class** — same pattern as Sprint 18's `_TopLevelSymbolHandler`.

The walks are similar but not identical:
- `_CallBodyAnalyzer` recurses into `call_expression.arguments` for chained calls
- `_HttpCallBodyAnalyzer` also checks `new_expression` (XMLHttpRequest)
- `_StringConstantBodyAnalyzer` walks to string-literal nodes

A shared `collect()` entry point and shared `_FUNCTION_BOUNDARIES` constant eliminate the
duplication that matters. Subclasses own their specific `_walk()` implementation.

#### Design

```python
## via/parsers/_js_body.py

from abc import ABC, abstractmethod
from typing import Optional

## Mirror the constant from javascript_parser — single source after extraction
_FUNCTION_BOUNDARIES = {
    'function_declaration', 'arrow_function', 'function_expression',
    'method_definition', 'generator_function_declaration',
}


class _BodyAnalyzer(ABC):
    """Walk a JS/TS AST function body, collecting entities without crossing
    nested function boundaries."""

    def collect(
        self,
        root_node,
        content: bytes,
        *,
        caller_name: str,
        caller_type: str,
        caller_parent: Optional[str],
    ) -> list:
        """Entry point: walk *root_node* and return collected entities."""
        out: list = []
        self._walk(root_node, content, caller_name, caller_type, caller_parent, out)
        return out

    @abstractmethod
    def _walk(self, node, content: bytes, caller_name: str, caller_type: str,
              caller_parent: Optional[str], out: list) -> None:
        """Subclass implements the specific node-matching and recursion logic."""


class _CallBodyAnalyzer(_BodyAnalyzer):
    """Collect all JS function/method call expressions."""
    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        # ... (extracted from _collect_calls_in_body)

class _HttpCallBodyAnalyzer(_BodyAnalyzer):
    """Collect HTTP call expressions (fetch, axios, XMLHttpRequest)."""
    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        # ... (extracted from _collect_http_calls_in_body)

class _StringConstantBodyAnalyzer(_BodyAnalyzer):
    """Collect string literal constants."""
    def _walk(self, node, content, caller_name, caller_type, caller_parent, out):
        # ... (extracted from _collect_string_constants_in_body)
```

#### Migration in `javascript_parser.py`

1. Remove `_collect_calls_in_body`, `_collect_http_calls_in_body`, `_collect_string_constants_in_body`
2. Remove the duplicated `_FUNCTION_BOUNDARIES` references within those functions (the constant stays
   in `javascript_parser.py` for top-level dispatch — or import from `_js_body.py` if preferred)
3. `_extract_all_calls`, `_extract_all_http_calls`, `_extract_all_string_constants` (the top-level
   walkers that call the body functions) delegate to `_CallBodyAnalyzer().collect(...)`, etc.
4. No changes to `ParseResult`, `IndexingService`, or any other module

#### Contracts

- `_FunctionBodyAnalyzer` classes are private to `via/parsers/` — not exported from `via/parsers/__init__.py`
- Behavior is byte-for-byte identical to the original functions (no logic changes)
- All existing tests pass without modification

---

### S21-2: MCP Server → `ViaRunner`

#### Problem

`via/mcp/server.py` creates `PipelineParser` and `PipelineExecutor` directly:

```python
stages = PipelineParser().parse(clean_args)
executor = PipelineExecutor(mcp_store)
results = list(executor.execute(stages) or [])
```

`ViaRunner` (Sprint 19–20) wraps these two objects as the canonical shared seam. The MCP server
bypasses it, meaning future improvements to `ViaRunner` don't apply to MCP.

#### Decision: Add `ViaRunner.run_cli_args()`

**Method signature** (per Smith naming note — `run_raw` avoided as it implies unvalidated):

```python
class ViaRunner:
    def run_cli_args(self, args: list[str]) -> Optional[Iterator[MatchRecord]]:
        """Parse a CLI argument list and execute through the shared pipeline seam."""
        stages = PipelineParser().parse(args)
        return self._executor.execute(stages)
```

This is the minimal extension. It parses the arg list and delegates to the existing executor,
returning the same `Optional[Iterator[MatchRecord]]` as `execute()`.

#### MCP Server Migration

The MCP server creates a `ViaRunner` at server startup (alongside `mcp_store`) and reuses it for
every `via_query` call:

```python
## at server init (near mcp_store creation)
runner = ViaRunner(mcp_store)

## JSON path (was: PipelineParser + PipelineExecutor)
results = list(runner.run_cli_args(clean_args) or [])

## Rendered path (stdout capture stays in MCP — ViaRunner doesn't own stdout)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    runner.run_cli_args(args)
rendered = strip_ansi(buf.getvalue()).rstrip('\n')
```

Key points:
- `redirect_stdout` stays in the MCP server — ViaRunner is not responsible for output capture
- `ViaRunner` is instantiated **once** at server startup, not per-request
- `PipelineParser` import in `server.py` is removed; `PipelineExecutor` import is removed
- `ViaRunner` import from `via.api` is added

#### What Does Not Change

- MCP tool signature (`via_query(args: list[str]) -> dict`) — unchanged
- JSON result shape (`{"output_type": ..., "result": ..., "total": ..., "shown": ...}`) — unchanged
- Diagram fallback logic — unchanged
- `_detect_output_type` helper — unchanged

#### Contracts

- `ViaRunner.run_cli_args()` added to `via/api/query_builder.py`
- `ViaRunner` exported from `via.api.__init__` (already is — no change needed)
- All existing MCP integration tests pass without modification

---

### Phase Breakdown for Mouse

| Phase | Story | Tasks |
|-------|-------|-------|
| Phase 1 | S21-1 | Create `via/parsers/_js_body.py` with `_BodyAnalyzer` ABC + 3 subclasses; update `javascript_parser.py` to delegate; run tests |
| Phase 2 | S21-2 | Add `ViaRunner.run_cli_args()`; migrate `mcp/server.py`; run tests |

Each phase is 1 implementation task + 1 test task. No cross-phase dependencies.

---

### Open Questions for Smith (Gate 2)

None. Both stories are internal with no new user-visible surface.
The only API addition (`run_cli_args`) is on an already-documented public class, follows existing
naming conventions, and is additive-only.


---


## SPRINT_21_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_21_TASKS.md`


## Sprint 21 Task Board

**Sprint**: 21 — JS Body Analyzer Extraction + MCP Builder Adoption
**Date**: 2026-04-12
**Total Points**: 6pt

---

### Phase 1: S21-1 Body Analyzer Extraction (3pt)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.1 | Create `via/parsers/_js_body.py`: `_BodyAnalyzer` ABC + 3 subclasses (`_CallBodyAnalyzer`, `_HttpCallBodyAnalyzer`, `_StringConstantBodyAnalyzer`) | Neo | TODO |
| 1.2 | Update `javascript_parser.py`: delegate `_extract_all_calls`, `_extract_all_http_calls`, `_extract_all_string_constants` to new classes; remove old free functions | Neo | TODO |
| 1.3 | Run targeted tests; confirm all call/http/string-constant tests pass | Trin | TODO |

**Exit criteria**: All existing body-analysis tests pass; `javascript_parser.py` no longer contains the three `_collect_*_in_body` free functions.

---

### Phase 2: S21-2 MCP ViaRunner Migration (3pt)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 2.1 | Add `ViaRunner.run_cli_args(args: list[str]) -> Optional[Iterator[MatchRecord]]` to `via/api/query_builder.py` | Neo | TODO |
| 2.2 | Migrate `via/mcp/server.py`: create `runner = ViaRunner(mcp_store)` at startup; replace both `PipelineParser+PipelineExecutor` call sites with `runner.run_cli_args()`; remove direct imports | Neo | TODO |
| 2.3 | Run MCP integration tests; confirm behavior unchanged | Trin | TODO |

**Exit criteria**: `mcp/server.py` imports no `PipelineParser` or `PipelineExecutor`; all MCP tests pass.

---

### Sprint References

- Stories: `agents/cypher.docs/SPRINT_21_USER_STORIES.md`
- Architecture: `agents/morpheus.docs/SPRINT_21_ARCHITECTURE.md`
- Smith Gate 1: approved 2026-04-12
- Smith Gate 2: approved 2026-04-12


---
