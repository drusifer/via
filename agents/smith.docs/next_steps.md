# Smith Next Steps

## Current State: Sprint 21 Gate 1 APPROVED (2026-04-12)

## Pending Actions
1. Wait for Morpheus arch review (Gate 2) — then re-engage for architecture review
2. After implementation: end-to-end user testing of MCP runner migration (S21-2 is the only behavior-adjacent change)

## Risks To Watch
- S21-2 `ViaRunner.run_cli_args` naming — ensure it's clear in docs/API surface
- MCP server behavior regression — run `via mcp` smoke test in UAT
- No new user-visible surface expected; flag any surprises in UAT
