# Bob Next Steps

## Current Status (2026-04-12)
Init complete. Bob Protocol is ready for the next command.

## On Resume
1. Read bottom 20 messages of `agents/CHAT.md`.
2. Treat CHAT.md as authoritative over stale state files for the latest thread.
3. If continuing lint-fix work, route first to `@Neo *swe save-state` to reconcile `neo.docs/current_task.md` and `neo.docs/next_steps.md` with the 2026-04-12 completion message.
4. If the user asks to commit, route to Neo after state reconciliation; verify worktree status and use the existing review approval from Morpheus as context.
5. If there is uncertainty about the actual lint/test state, run `make lint` and `make test` before handoff or commit.

## Process Improvement (ongoing)
- Enforce EXIT GATE: save state files before every switch/stop.
- When CHAT.md and persona state conflict, explicitly record the conflict and reconcile before executing follow-up work.
