# Sprint 23 Gate 1 Review

**Persona**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Verdict**: APPROVED WITH NOTES

## HCI Assessment

Sprint 23 correctly follows Sprint 22. The stories shift from "make the query system trustworthy" to "make common workflows discoverable," which fits Nielsen #6 Recognition Rather Than Recall and #7 Flexibility and Efficiency.

## Approved Scope

- Task-language shortcuts for common questions.
- Task-oriented MCP examples.
- Diagram fallback that preserves useful data.
- CLI help HCI pass.

## Notes For Morpheus

1. **Shortcut surface must be one coherent path.** Do not ship both direct flags and `--canned` names unless one is explicitly an alias of the other. Multiple shortcut systems create a new recall burden.
2. **Do not ship fake support for `callees` or `declared-in-file`.** If the architecture cannot support one cleanly in Sprint 23, defer that shortcut visibly instead of returning a placeholder error from a command users think exists.
3. **Every shortcut must show its expansion.** This is the main safety rail against hidden semantics.
4. **MCP examples should be task-grouped, not flag-grouped.** Agents ask "find callers" or "read symbol body"; they do not think "compose output flag plus relationship filter."
5. **Help length limit matters.** The Sprint 22 help is already dense. Favor compact examples and point to user guide for longer recipes.

## Gate Decision

Approved to proceed to Morpheus architecture.
