# Sprint 21 Task Board

**Sprint**: 21 — JS Body Analyzer Extraction + MCP Builder Adoption
**Date**: 2026-04-12
**Total Points**: 6pt

---

## Phase 1: S21-1 Body Analyzer Extraction (3pt)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.1 | Create `via/parsers/_js_body.py`: `_BodyAnalyzer` ABC + 3 subclasses (`_CallBodyAnalyzer`, `_HttpCallBodyAnalyzer`, `_StringConstantBodyAnalyzer`) | Neo | TODO |
| 1.2 | Update `javascript_parser.py`: delegate `_extract_all_calls`, `_extract_all_http_calls`, `_extract_all_string_constants` to new classes; remove old free functions | Neo | TODO |
| 1.3 | Run targeted tests; confirm all call/http/string-constant tests pass | Trin | TODO |

**Exit criteria**: All existing body-analysis tests pass; `javascript_parser.py` no longer contains the three `_collect_*_in_body` free functions.

---

## Phase 2: S21-2 MCP ViaRunner Migration (3pt)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 2.1 | Add `ViaRunner.run_cli_args(args: list[str]) -> Optional[Iterator[MatchRecord]]` to `via/api/query_builder.py` | Neo | TODO |
| 2.2 | Migrate `via/mcp/server.py`: create `runner = ViaRunner(mcp_store)` at startup; replace both `PipelineParser+PipelineExecutor` call sites with `runner.run_cli_args()`; remove direct imports | Neo | TODO |
| 2.3 | Run MCP integration tests; confirm behavior unchanged | Trin | TODO |

**Exit criteria**: `mcp/server.py` imports no `PipelineParser` or `PipelineExecutor`; all MCP tests pass.

---

## Sprint References

- Stories: `agents/cypher.docs/SPRINT_21_USER_STORIES.md`
- Architecture: `agents/morpheus.docs/SPRINT_21_ARCHITECTURE.md`
- Smith Gate 1: approved 2026-04-12
- Smith Gate 2: approved 2026-04-12
