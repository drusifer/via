# Neo Current Task

**Task**: Sprint 14 Cycle 1 — S14-1 JS calls extraction
**Status**: COMPLETE — 1144 passed, 0 failed
**Updated**: 2026-04-05

## Done
- Added `CallEntity` import to `javascript_parser.py`
- Added `_extract_all_calls()` top-level walker
- Added `_collect_calls_in_body()` recursive helper (respects function boundaries)
- Added `_get_callee_name()` for `identifier` and `member_expression` callees
- Wired into `JavaScriptParser.parse()`: `result.calls = _extract_all_calls(...)`
- Fixed stale test `test_sans_declares_raises_error` → `test_sans_declares_works`
- Wrote `tests/unit/test_sprint14_c1.py` (23 tests, all pass)
- **1144 passed** baseline

## Handoff → Trin UAT Cycle 1
