# Sprint 22 Gate 2 Architecture Review

**Reviewer**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/morpheus.docs/SPRINT_22_ARCHITECTURE.md`  
**Verdict**: APPROVED

## Assessment

Morpheus preserved the HCI intent of Sprint 22. The architecture improves user confidence without adding a new relationship model or expanding into shortcut syntax prematurely.

## Gate Questions

### 1. `output_type: "error"` Response Shape

Approved. This is clear for MCP agents because it keeps the existing wrapper shape and gives a direct branch condition. Keeping `result`, `total`, and `shown` present also reduces caller special-casing.

Requirement: expected query/user errors must not be logged as generic server failures. Unexpected exceptions can still be logged as internal errors.

### 2. "Result Stage" / "Filter Stage" Vocabulary

Approved. This is the right user-facing vocabulary. It maps cleanly to the user's clarified mental model:

```text
via <result stage> [--via|--sans <relationship> <filter stage>]
```

Docs should avoid leading with "known anchor left." That phrase can remain as an advanced implementation note only if needed.

### 3. S22-4 Documentation Correction

Approved. Correcting the misleading `declares` quick reference is the right Sprint 22 scope. A true "symbols declared in file" task belongs in Sprint 23 shortcut design, where it can be named in user language and expanded intentionally.

## HCI Constraints For Implementation

- Preserve valid empty result behavior.
- Invalid syntax, invalid regex, ambiguous multi-match, and unsupported documented patterns must not look like valid empty results.
- Multi-type OR queries must remain valid and visible in docs as a token-saving workflow.
- Error messages must include what happened, why, and a valid next action.
- CLI and MCP wording should be consistent even if response shapes differ.

## Final Verdict

APPROVED. Proceed to Mouse sprint phase planning.
