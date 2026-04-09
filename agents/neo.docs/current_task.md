# Neo Current Task

## Sprint 20 — COMPLETE
**Status**: DONE
**Date**: 2026-04-08

## Scope
- S20-1: shared CLI/builder construction seam
- S20-2: Python API docs/examples

## Changes Made
- Added `via/pipeline/stage_builder.py` for shared match-stage construction
- Migrated `via/pipeline/parser.py` and `via/api/query_builder.py` to the shared seam
- Added Python API docs to `README.md` and `docs/USER_GUIDE.md`
- Added focused parity tests in `tests/unit/test_sprint20_c1.py`

## Verification
- 50 targeted tests passed locally through `make test`

## Summary Doc
- `agents/neo.docs/SPRINT_20_Summary_2026-04-08T21:58.md`
