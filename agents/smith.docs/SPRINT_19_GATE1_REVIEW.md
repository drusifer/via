# Sprint 19 Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-08  
**Sprint**: Sprint 19 — ViaQueryBuilder  
**Source Reviewed**: `agents/cypher.docs/SPRINT_19_USER_STORIES.md`

## Verdict

**APPROVED**

## Summary

Sprint 19 targets a real usability problem for programmatic consumers: via is currently easy to use from the CLI but awkward to use in code. The stories keep the mental model grounded by requiring the builder to preserve existing query semantics instead of inventing a new abstraction language.

## Story Verdicts

### S19-1: Fluent Programmatic Query Builder
**Verdict**: APPROVED

Why:
- It addresses a genuine usability issue for Python callers.
- The story correctly distinguishes query construction from query execution.
- Requiring parity with existing CLI semantics prevents a confusing split-brain API.

Notes for Morpheus:
- Transparency matters: the builder should read like via, not like an unrelated ORM.
- Prefer method names users can map back to current via concepts quickly.

### S19-2: Replace Web API Namespace Assembly with Builder Compilation
**Verdict**: APPROVED

Why:
- This is the right proving ground for the new API because the current web layer is already acting as a programmatic caller.
- Removing hand-built `Namespace` objects reduces one of the sharpest maintenance edges.

Notes for Morpheus:
- Preserve existing web behavior exactly; users should not experience a semantic change because an internal adapter changed.
- Keep response shaping separate from query construction so the web layer still reads clearly.

## Gate Notes

1. The builder must preserve via’s existing mental model rather than hiding it behind generic data-access vocabulary.
2. This sprint should not quietly change relationship semantics, output-format behavior, or default limits.
3. Docs and examples should eventually show at least one plain-match and one relationship builder example, even if that doc work lands after the code.

## Handoff

Sprint 19 Gate 1 is approved to proceed to architecture.
