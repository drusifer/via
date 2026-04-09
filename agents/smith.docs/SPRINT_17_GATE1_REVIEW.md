# Sprint 17 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 17 — Link Intelligence + HTTP Bridge Primitives  
**Source Reviewed**: `agents/cypher.docs/SPRINT_17_USER_STORIES.md`

## Verdict

**APPROVED**

## Summary

Sprint 17 is pointed at a real user workflow instead of abstract "cross-language tracing" claims. The revised S17-3 is the key improvement: `--contains` is now framed as a filter over already-matched symbols, which preserves via's mental model and avoids collapsing the product into repo-wide grep.

## Story Verdicts

### S17-1: URL/Link Indexing as `link` Symbols
**Verdict**: APPROVED

Why:
- Matches user expectations for docs/config navigation.
- Keeps scope grounded in structured link targets rather than arbitrary text.
- Markdown-first scoping is a good risk boundary.

Notes for Morpheus:
- Keep the flag naming consistent with existing type aliases and long-form help text.
- Ensure rendered output exposes the URL target clearly; optional label metadata is useful but secondary.

### S17-2: Pragmatic HTTP Bridge via JS HTTP Call Sites
**Verdict**: APPROVED WITH NOTES

Why:
- The story now avoids the misleading promise of automatic route resolution.
- It aligns with Smith's earlier recommendation: expose HTTP call primitives and let users bridge with `-ts` and relationships.

Notes for Morpheus:
- The user mental model should stay simple: "show me outbound HTTP call sites" is clearer than introducing a magical cross-language abstraction.
- If a new relationship type is introduced, the CLI/help text must explain it in plain language and show one example query.

### S17-3: `--contains` as Symbol-Body Filtering
**Verdict**: APPROVED

Why:
- This matches the user's feedback and is materially different from grep.
- Returning symbols instead of line snippets preserves consistency with the rest of via.
- The explicit separation from `-ts` and external grep tools addresses the biggest Sprint 16 risk.

Notes for Morpheus:
- Unsupported symbol/body cases must fail clearly or skip clearly; silent partial behavior would be a UX defect.
- If body retrieval depends on existing raw output internals, keep the public model simple: `--contains` filters symbols, it does not change the result type by default.

## Gate Notes

1. `-ts`, `link`, and `--contains` must remain distinct concepts in docs/help:
   - `-ts`: structured string-constant symbols
   - `-tl`/`link`: structured URL/link symbols
   - `--contains`: body-text filter over matched symbols
2. Sprint 17 should ship at least one help/doc example for each new surface; this sprint is prone to semantic confusion if examples are missing.
3. The HTTP bridge story is acceptable only if the team keeps the claim at the primitive/workflow level and avoids overstating automatic linkage.

## Handoff

Sprint 17 Gate 1 is approved to proceed to architecture.
