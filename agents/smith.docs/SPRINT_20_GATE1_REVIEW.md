# Sprint 20 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 20 — Builder Adoption + Library Usability  
**Source Reviewed**: `agents/cypher.docs/SPRINT_20_USER_STORIES.md`

## Verdict

**APPROVED**

## Summary

Sprint 20 is pointed at the right follow-up problem: Sprint 19 made the builder real, but not yet fully central or discoverable. The stories are acceptable because they keep the work bounded to adoption and documentation instead of turning it into a sweeping parser redesign.

## Story Verdicts

### S20-1: CLI/Programmatic Query Construction Shares the Builder Seam
**Verdict**: APPROVED

Why:
- This addresses real maintainability and consistency risk after Sprint 19.
- The story explicitly forbids executor redesign and full parser replacement, which is the right guardrail.
- Keeping semantics frozen preserves user trust in existing CLI behavior.

Notes for Morpheus:
- Favor a shared translation seam over clever bidirectional coupling between parser and builder.
- Keep the implementation explainable; if it becomes hard to describe, it is probably too large for this sprint.

### S20-2: Document `ViaQueryBuilder` as the Supported Python API
**Verdict**: APPROVED

Why:
- The product value of Sprint 19 is incomplete if users still have to inspect source to discover the API.
- Plain and relationship examples are the right minimum set.

Notes for Morpheus:
- Documentation should describe the builder in terms users already know from via semantics.
- Ensure docs do not imply the builder supports more than the CLI actually does.

## Gate Notes

1. Sprint 20 must preserve current CLI defaults and result behavior exactly.
2. Documentation and exports must agree on what is public.
3. If the shared construction seam starts to look like a parser rewrite, split the work instead of forcing it through this sprint.

## Handoff

Sprint 20 Gate 1 is approved to proceed to architecture.
