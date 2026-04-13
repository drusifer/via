# Sprint 23 Cycle 2 UAT Summary — Task Examples And CLI Help

**Persona**: Trin  
**Date**: 2026-04-12T18:27  
**Status**: PASS

## Verification

- CLI help includes compact common-task examples.
- CLI help documents `--show-expanded`.
- MCP schema includes task-oriented examples for symbol lookup, body reading, callers, docs headers, regex, multi-type, and paged scans.
- Uppercase `-tH` guidance is present; lowercase `-th` is identified as invalid in schema guidance.
- Unsupported shortcut names are not advertised:
  - `--callers`
  - `--callees`
  - `--declared-in-file`
- Raw relationship examples are labeled advanced and use current-runtime behavior.
- Help growth stays within Sprint 23 budget:
  - Sprint 22 baseline: 112 lines
  - Budget: <=137 lines
  - Actual: 121 lines

## Tests

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `.venv/bin/python -m via --help | wc -l` — 121.
- `.venv/bin/python -m via mcp schema | wc -l` — 121.

## QA Note

This is ready for Morpheus review and then Smith HCI wording review. The remaining risk is product-facing wording around the known relationship-orientation mismatch; QA confirms examples are runtime-correct.
