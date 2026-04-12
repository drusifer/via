# Sprint 21 Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-12
**Sprint**: 21 — JS Body Analyzer Extraction + MCP Builder Adoption

---

## S21-1: `_FunctionBodyAnalyzer` Extraction

### Problem

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

### Decision: Placement

**Extract to `via/parsers/_js_body.py`** (private module, `_` prefix).

Rationale: `javascript_parser.py` at 926 lines is already large. The body analysis functions are
cohesive and self-contained. Extracting them is consistent with how Sprint 18 extracted top-level
handlers — those remain in `javascript_parser.py` because they're tightly coupled to the parse
result; body analyzers are not.

### Decision: Pattern

**Abstract base class** — same pattern as Sprint 18's `_TopLevelSymbolHandler`.

The walks are similar but not identical:
- `_CallBodyAnalyzer` recurses into `call_expression.arguments` for chained calls
- `_HttpCallBodyAnalyzer` also checks `new_expression` (XMLHttpRequest)
- `_StringConstantBodyAnalyzer` walks to string-literal nodes

A shared `collect()` entry point and shared `_FUNCTION_BOUNDARIES` constant eliminate the
duplication that matters. Subclasses own their specific `_walk()` implementation.

### Design

```python
# via/parsers/_js_body.py

from abc import ABC, abstractmethod
from typing import Optional

# Mirror the constant from javascript_parser — single source after extraction
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

### Migration in `javascript_parser.py`

1. Remove `_collect_calls_in_body`, `_collect_http_calls_in_body`, `_collect_string_constants_in_body`
2. Remove the duplicated `_FUNCTION_BOUNDARIES` references within those functions (the constant stays
   in `javascript_parser.py` for top-level dispatch — or import from `_js_body.py` if preferred)
3. `_extract_all_calls`, `_extract_all_http_calls`, `_extract_all_string_constants` (the top-level
   walkers that call the body functions) delegate to `_CallBodyAnalyzer().collect(...)`, etc.
4. No changes to `ParseResult`, `IndexingService`, or any other module

### Contracts

- `_FunctionBodyAnalyzer` classes are private to `via/parsers/` — not exported from `via/parsers/__init__.py`
- Behavior is byte-for-byte identical to the original functions (no logic changes)
- All existing tests pass without modification

---

## S21-2: MCP Server → `ViaRunner`

### Problem

`via/mcp/server.py` creates `PipelineParser` and `PipelineExecutor` directly:

```python
stages = PipelineParser().parse(clean_args)
executor = PipelineExecutor(mcp_store)
results = list(executor.execute(stages) or [])
```

`ViaRunner` (Sprint 19–20) wraps these two objects as the canonical shared seam. The MCP server
bypasses it, meaning future improvements to `ViaRunner` don't apply to MCP.

### Decision: Add `ViaRunner.run_cli_args()`

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

### MCP Server Migration

The MCP server creates a `ViaRunner` at server startup (alongside `mcp_store`) and reuses it for
every `via_query` call:

```python
# at server init (near mcp_store creation)
runner = ViaRunner(mcp_store)

# JSON path (was: PipelineParser + PipelineExecutor)
results = list(runner.run_cli_args(clean_args) or [])

# Rendered path (stdout capture stays in MCP — ViaRunner doesn't own stdout)
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

### What Does Not Change

- MCP tool signature (`via_query(args: list[str]) -> dict`) — unchanged
- JSON result shape (`{"output_type": ..., "result": ..., "total": ..., "shown": ...}`) — unchanged
- Diagram fallback logic — unchanged
- `_detect_output_type` helper — unchanged

### Contracts

- `ViaRunner.run_cli_args()` added to `via/api/query_builder.py`
- `ViaRunner` exported from `via.api.__init__` (already is — no change needed)
- All existing MCP integration tests pass without modification

---

## Phase Breakdown for Mouse

| Phase | Story | Tasks |
|-------|-------|-------|
| Phase 1 | S21-1 | Create `via/parsers/_js_body.py` with `_BodyAnalyzer` ABC + 3 subclasses; update `javascript_parser.py` to delegate; run tests |
| Phase 2 | S21-2 | Add `ViaRunner.run_cli_args()`; migrate `mcp/server.py`; run tests |

Each phase is 1 implementation task + 1 test task. No cross-phase dependencies.

---

## Open Questions for Smith (Gate 2)

None. Both stories are internal with no new user-visible surface.
The only API addition (`run_cli_args`) is on an already-documented public class, follows existing
naming conventions, and is additive-only.
