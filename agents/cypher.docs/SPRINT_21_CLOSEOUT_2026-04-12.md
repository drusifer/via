# Sprint 21 Closeout

**Author**: Cypher
**Date**: 2026-04-12

## Outcome

Sprint 21 is SHIPPED.

### Delivered

- S21-1: `_FunctionBodyAnalyzer` extracted — `_js_body.py` (244 lines) with `_BodyAnalyzer` ABC
  + `_CallBodyAnalyzer`, `_HttpCallBodyAnalyzer`, `_StringConstantBodyAnalyzer`. 
  `javascript_parser.py` reduced from 926 → 754 lines.
- S21-2: `ViaRunner.run_cli_args(args: list[str])` added. MCP server migrated from direct
  `PipelineParser+PipelineExecutor` to `ViaRunner`. No `PipelineParser` or `PipelineExecutor`
  imports remain in `mcp/server.py`.

### Verification

- 1259 tests passed, 1 skipped — both phases

### Backlog Items Added

- Add explicit `_js_body` unit tests if body analysis logic diverges further (Trin/Smith)
- Executor strategy / full CLI parser replacement (Morpheus — defer unless planned)
