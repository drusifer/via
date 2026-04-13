# Sprint 23 Gate 2 Architecture Review

**Persona**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`  
**Verdict**: APPROVED

## HCI Assessment

The architecture preserves Sprint 22's mental model while adding recognition affordances. It correctly chooses one shortcut surface, `--canned`, instead of adding competing direct flags.

## Gate Answers

1. **Is `--canned` acceptable as the single Sprint 23 shortcut surface?**  
   Yes. It is already established, transparent, customizable, and avoids another flag family.

2. **Is `--show-expanded` the clearest name for displaying shortcut expansion?**  
   Yes. It is more direct than `--dry-run` because the user goal is learning the expansion, not simulating execution.

3. **Should `declared-in-file` be deferred unless implemented as an explicit task helper?**  
   Yes. This prevents the Sprint 22 inverse `declares` confusion from reappearing.

## Approval Notes

- Keep `--show-expanded` output copyable as a complete `via ...` command.
- Do not list deferred shortcuts in the primary examples table. Put them in a clearly labeled "Deferred" note if mentioned at all.
- MCP schema examples should remain compact; full recipes belong in Sprint 24.
- `callees` should not appear as a runnable built-in unless tests prove it returns callees.

## Gate Decision

Approved to proceed to Mouse sprint task planning.
