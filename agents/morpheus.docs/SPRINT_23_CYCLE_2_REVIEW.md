# Sprint 23 Cycle 2 Review — Task Examples And CLI Help

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Verdict**: APPROVED

## Scope Reviewed

- `via/__main__.py`
- `via/mcp/schema.py`
- `tests/unit/test_sprint23_c2.py`
- Updated help/schema regression tests
- Trin UAT: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18:27.md`

## Findings

### Approved: Task-First Recognition Surface

CLI help and MCP schema now lead with common tasks instead of forcing users to recall low-level relationship direction. The examples cover the planned task set: symbol lookup, body reading, callers, docs headers, regex, multi-type search, and paged scans.

### Approved: Bounded Help Growth

Help remains compact:

- Sprint 22 baseline: 112 lines
- Sprint 23 actual: 121 lines
- Budget maximum: 137 lines

### Approved: Runtime-Correct Relationship Wording

Cycle 2 correctly handles the Cycle 1 finding that executor behavior still uses current-runtime relationship orientation. The help/schema now frame raw relationship syntax as advanced and point common tasks to `--canned`, avoiding examples that look nice but do not work.

### Approved: No Unsupported Shortcut Advertising

No unsupported direct flags or deferred shortcut names are advertised. `-tH` guidance is explicit, including the lowercase `-th` trap in MCP schema.

## Review Note

This review accepts a deliberate correction from the Sprint 22 documentation direction: user-facing examples must be executable against the current runtime. The broader relationship-orientation reconciliation remains a future architecture task.

## Verification Reviewed

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `via --help` — 121 lines.
- `via mcp schema` — 121 lines.

## Decision

Cycle 2 is approved for Smith HCI wording review.
