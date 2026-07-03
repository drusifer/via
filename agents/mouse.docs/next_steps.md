# Mouse Next Steps

## Resume Point: Sprint 27 Phase 2 Cycle 1 blocked on a user product decision (AC7 drill-down)

## On Resume
1. Check CHAT.md / the user's response for a decision on AC7 (implement
   with what semantics, cut, or backlog).
2. If implement: hand to Neo with the specific semantics the user chose
   (don't let Neo guess either).
3. If cut/backlog: update `task.md`/`SPRINT_27_PHASE2_TASKS.md` to mark
   Cycle 1 fully CLOSED, note AC7 as intentionally dropped (with a backlog
   pointer if parked, not silently deleted).
4. Once resolved: Cycle 2 (mocking-usage signal) starts.

## Remember
This whole cycle is a good example of why closing the loop matters — the
gap wasn't caught by implementation, UAT, code review, or usability
testing; only surfaced during the boring bookkeeping pass of reconciling
the task checklist against the actual code. Worth doing that
reconciliation explicitly at cycle-close time going forward, not just
trusting each gate's own checklist.
