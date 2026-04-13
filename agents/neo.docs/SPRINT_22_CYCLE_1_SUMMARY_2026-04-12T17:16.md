# Sprint 22 Cycle 1 Summary

**Persona**: Neo  
**Date**: 2026-04-12T17:16  
**Status**: Complete — handed to Trin

## Scope

Cycle 1 implemented the structured query error contract for expected query/parser failures.

## Changes

- Added `via/pipeline/errors.py`:
  - `QueryError`
  - enhanced `PipelineParseError`
- Updated `via/pipeline/parser.py` to raise structured parse errors with codes and hints.
- Updated `via/mcp/server.py` so expected parser errors return:
  - `output_type: "error"`
  - `result: []`
  - `total: 0`
  - `shown: 0`
  - `error: {code, message, hint}`
- Preserved valid empty JSON result behavior.
- Updated CLI parse error handling to print `Hint:` when available.
- Added `tests/unit/test_sprint22_c1.py`.

## Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_pipeline_parser.py` — 44 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c3.py` — 19 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint7_p4.py` — 16 passed.

## Known Test Environment Note

`make test FILE=tests/unit/test_sprint22_c1.py` still fails before this sprint's tests because the default target invokes the broader test loader in an environment where `pytest` is missing. The project-specific `Makefile.prj` target is the working targeted test path used by recent sprint work.
