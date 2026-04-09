# Sprint 15 Closeout

**Author**: Cypher (PM)  
**Date**: 2026-04-08T18:24  
**Sprint**: Sprint 15 — MCP Ergonomics + Index Completeness

## Outcome

Sprint 15 is complete and ready to be marked SHIPPED.

- Delivery completed across 3 implementation cycles.
- QA passed on each cycle.
- Morpheus approved each cycle and declared Sprint 15 complete in `agents/CHAT.md`.
- Latest full test baseline reported in chat: **1235 passed, 1 skipped, 4 warnings**.

## Shipped Stories

| Story | Outcome |
|-------|---------|
| S15-1 | Shipped: `--slice`, `total`, `shown`, mutual exclusion with `-n`, CLI warning fix |
| S15-2 | Shipped: MCP `output_type` wrapper with backward-compatible `result` |
| S15-3 | Shipped: `--lang` works for `-tF` filepath queries |
| S15-4 | Shipped: markdown `declares` returns header structure |
| S15-5 | Closed as docs/help clarification: full-path `-Q` behavior already worked |
| S15-6 | Shipped: relationship-query examples added to `via --help` |

## Product Notes

- Sprint 15 addressed the most important issues from Smith's MCP expert-user review.
- The top user-visible improvements are pagination/windowing, accurate MCP output typing, and markdown structural navigation.
- One implementation note captured by Morpheus remains backlog material: `--slice` is ignored for OR'd type queries and should be treated as a Sprint 16 candidate.

## Deferred / Next Sprint Candidates

- String constants as `-ts`
- Coverage import / `covered-by`
- URL/link indexing
- Canned queries
- OR-query interaction with `--slice`

## Close Recommendation

Sprint 15 should be recorded as SHIPPED and the team should move to:

1. Mouse: archive Sprint 15 board / set Sprint 16 planning entrypoint
2. Oracle: refresh long-lived docs if needed

