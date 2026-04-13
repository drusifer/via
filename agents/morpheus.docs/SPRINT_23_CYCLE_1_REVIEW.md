# Sprint 23 Cycle 1 Review — Canned Shortcut Surface

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Verdict**: APPROVED

## Scope Reviewed

- `via/canned.py`
- `via/__main__.py`
- `tests/unit/test_sprint23_c1.py`
- Trin UAT: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18:21.md`

## Findings

### Approved: `--canned` Remains A Template Expander

The implementation keeps canned queries as static argv templates expanded through the existing pipeline path. It does not add a second query engine, strategy branch, or custom executor path.

### Approved: `--show-expanded` Is Transparent And Non-Executing

`--show-expanded` is handled at the canned-command boundary, prints a copyable `via ...` command, and returns success without calling the pipeline executor. This matches the Sprint 23 transparency goal.

### Approved: No Unsupported Shortcut Surface

No direct flags such as `--callers` were added. Deferred names `callees` and `declared-in-file` were not shipped as runnable built-ins.

### Architecture Note: Relationship Orientation Mismatch

Cycle 1 exposed an existing mismatch between Sprint 22 user-facing docs and the runtime executor:

- Sprint 22 docs teach result-stage-first relationship syntax.
- The current executor still evaluates positive relationship queries with the older anchor-left/object-first orientation.

Neo correctly chose task-correct canned expansions against the current runtime. Forcing result-stage-first text into canned shortcuts without changing the executor would have shipped broken shortcuts. This is approved as a bounded implementation exception, not a new relationship design.

## Follow-Up Requirement

Cycle 2 must treat the docs/runtime mismatch carefully when adding help and MCP examples. It should not add examples that promise result-stage-first behavior unless the runtime actually supports that behavior. The long-term fix is a separate relationship-orientation reconciliation task, not part of Cycle 1.

## Verification Reviewed

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

## Decision

Cycle 1 is approved. Proceed to Sprint 23 Cycle 2: task-oriented MCP schema and CLI help examples, followed by Smith HCI review.
