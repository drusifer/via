# Sprint 22 Cycle 3 Summary

**Persona**: Neo  
**Date**: 2026-04-12T17:32  
**Status**: Complete — handed to Trin

## Scope

Cycle 3 corrected user-facing docs, MCP schema, and CLI help so VIA teaches the result-stage-first command model.

## Changes

- Updated `agents/PROJECT.md` quick reference:
  - removed misleading "Find all symbols in a file"
  - added result-stage-first relationship examples
  - clarified that relationship stages filter the initial result stage
- Updated `via/mcp/schema.py`:
  - added command structure: `via <result stage> [--via|--sans REL <filter stage>]`
  - documented one match flag per stage
  - added a regex stage example
  - rewrote relationship examples away from anchor-left wording
  - clarified that `--via declares` does not invert a file result stage into returned child symbols
- Updated `via/__main__.py` help text:
  - replaced anchor-left rule with result-stage-first rule
  - added corrected relationship examples
  - removed the "all symbols declared in a file" example
- Updated `docs/USER_GUIDE.md`:
  - rewrote relationship syntax and type descriptions
  - renamed container docs to "Container Filters"
  - updated practical relationship examples to result-stage-first wording
- Updated `tests/unit/test_sprint15_c1.py` for the new help rule.
- Added `tests/unit/test_sprint22_c3.py` for docs/schema/help assertions.

## Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p4.py` — 16 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c2.py` — 8 passed.

Total targeted baseline: 56 passed.

## Notes

No query execution semantics were changed in Cycle 3. This was a docs/schema/help correction pass with regression coverage for the user-facing wording.
