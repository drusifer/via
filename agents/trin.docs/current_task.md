# Trin Current Task

## Task: Triage + Verify UX-001 + UX-002
**Status**: COMPLETE
**Date**: 2026-03-22

## Results

### UX-001 ✅ CLOSED
- Root cause: `via/mcp/schema.py:54` hardcoded stale text
- Fix: string updated to document `-Q` flag
- Test: `test_schema_description_mentions_Q_flag_for_full_path` — PASS

### UX-002 ✅ CLOSED
- Root cause: `ClassMatchRecord.base_classes` never populated (required JOIN on symbol_references)
- Fix: LEFT JOIN in all 3 query paths; `create_from_row` splits base_names
- Test: `test_render_inheritance_arrow_when_parent_not_in_result_set` — PASS
- Live: `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD` shows correct arrows

## Test Results
- **970 passed** (was 968)

## Next
- Sprint 11 when directed
