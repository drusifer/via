# Trin Next Steps

## Resume Point: Sprint 27 Phase 2 Cycle 1 UAT complete (PASSES), handed to Morpheus

## On Resume
1. Check CHAT.md for Morpheus's code review verdict on Cycle 1.
2. If Morpheus approves: next stop is Smith's usability test (real
   browser) — I explicitly flagged that my UAT did not (couldn't) cover
   real D3 rendering, the colorblind-safe scale, or the outlier visual
   marker, since none of that is exercised by jsdom/CI.
3. If Morpheus flags an issue: back to Neo for that specific fix, then
   re-UAT just the changed part — don't re-run the whole cycle from scratch.
4. Once Cycle 1 fully closes: Cycle 2 (mocking-usage signal) is next per
   `agents/mouse.docs/SPRINT_27_PHASE2_TASKS.md`.

## Remember
- `make test FILE=<path>` for targeted runs; full suite at checkpoints.
- `make via_index && make test-coverage` regenerates real coverage data
  against this project's own index — useful for any future ground-truth
  cross-check like the one I just did for Cycle 1. Both now have proper
  public `make` stubs (they didn't before this cycle).
- `tests/uat/test_sprint27_phase2_cycle1_uat.py` is rerunnable anytime
  a real `.via/index.db` exists — skips cleanly otherwise.
