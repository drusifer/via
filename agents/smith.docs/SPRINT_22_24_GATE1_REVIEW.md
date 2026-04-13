# Sprint 22-24 HCI/UX Gate 1 Review

**Reviewer**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`  
**Verdict**: APPROVED WITH NOTES

## Overall Assessment

The story batch correctly translates the VIA MCP usability findings into product work. The sequence is right: fix trust-breaking ambiguity first, then add recognition aids, then lock behavior into docs and UAT.

The strongest product decision is keeping Sprint 22 focused on query confidence rather than adding more query power. Silent empty results are currently the highest HCI risk because they destroy the user's ability to diagnose problems.

## Story Verdicts

### Sprint 22

- **S22-1 Structured MCP Errors**: APPROVED. This is the top priority and should not be split below the structured MCP response shape.
- **S22-2 Multi-Match Semantics**: APPROVED. Rejecting ambiguous composition is the right HCI choice until AND/OR semantics are intentionally designed.
- **S22-3 Regex UX**: APPROVED. Keep this scoped to examples plus valid/invalid/no-match distinction.
- **S22-4 File `declares` Pattern**: APPROVED WITH NOTE. Morpheus must choose implementation vs documentation correction before Neo starts; this cannot remain open during implementation.

### Sprint 23

- **S23-1 Relationship Shortcuts**: APPROVED WITH NOTE. Shortcut names must be task-language first: "callers", "callees", "declared in file". Avoid leaking internal relationship direction into the shortcut names.
- **S23-2 MCP Schema Examples**: APPROVED. This directly supports recognition over recall for agents.
- **S23-3 Diagram Fallback**: APPROVED. Preserve data rather than forcing a retry.
- **S23-4 CLI Help HCI Pass**: APPROVED. Keep the length limit; help bloat would create a new UX problem.

### Sprint 24

- **S24-1 HCI UAT Suite**: APPROVED. Must be runnable through Makefile.
- **S24-2 Token-Saving Recipes**: APPROVED. Recipes should match tested behavior exactly.
- **S24-3 Error Style Guide**: APPROVED. The style guide should be short and enforceable by tests.
- **S24-4 UX Debt Closeout**: APPROVED. Good closure mechanism after three UX-focused sprints.

## Gate Notes For Morpheus

1. **S22-1**: Prefer a single error response contract shared by MCP and any future programmatic runner path.
2. **S22-2**: Define "match stage" precisely in architecture. Users should not need to know parser internals, but implementers do.
3. **S22-4**: Decide whether file-to-symbol `declares` is a product feature or docs bug. Do not leave this as an implementation-time choice.
4. **S23-1**: Shortcuts must expand into existing `--via` / `--sans` semantics. No new relationship model.

## HCI Constraints

- Preserve valid empty result behavior. Empty results are not bad; ambiguous empty results are bad.
- Errors must say what happened, why, and the valid alternatives.
- Do not add shortcut syntax that competes with or partially duplicates existing semantics without a clear expansion model.
- MCP examples must be short enough to remain usable in the tool schema.

## Final Verdict

APPROVED WITH NOTES. Proceed to Morpheus architecture for Sprint 22, carrying the notes above as gate constraints.
