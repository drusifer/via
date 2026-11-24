# Trin Next Steps

## Resume Point: MCP 2 migration QA complete (PASSES), handed to Morpheus

## On Resume
1. Check CHAT.md for Morpheus's MCP 2 review verdict.
2. If Morpheus flags implementation changes, return the exact scope to Neo and
   re-run only the affected MCP tests before a final checkpoint.
3. Preserve the real `ClientSession` stdio UAT; do not restore the obsolete
   batch-stdin-plus-immediate-EOF protocol simulation.

## Remember
- Focused gate: `make test FILE='tests/subprocess/test_sprint7_uat.py tests/unit/test_sprint22_c1.py tests/unit/test_sprint23_c3.py tests/unit/test_sprint25_c1.py'`.
- Full checkpoint on 2026-08-06: 1424 passed, 2 skipped.
- `make via_index && make test-coverage` regenerates real coverage data
  against this project's own index — useful for any future ground-truth
  cross-check like the one I just did for Cycle 1. Both now have proper
  public `make` stubs (they didn't before this cycle).
- `tests/uat/test_sprint27_phase2_cycle1_uat.py` is rerunnable anytime
  a real `.via/index.db` exists — skips cleanly otherwise.
