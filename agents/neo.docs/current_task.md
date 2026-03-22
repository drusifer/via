# Neo Current Task

## Task: Fix UX-001 + UX-002 (post-beta defects)
**Status**: COMPLETE (100%)
**Date**: 2026-03-22

## UX-001: MCP Schema stale -Q text — FIXED
- File: `via/mcp/schema.py:54`
- Changed: "Full-path matching not yet supported" → "For full-path matching, add -Q (e.g. via -mg 'via/core/*' -tF -Q)"
- Test: `test_schema_description_mentions_Q_flag_for_full_path` added to `tests/unit/test_sprint7_p4.py`

## UX-002: Diagram arrows missing in relationship queries — FIXED
Root cause: `base_classes` field on `ClassMatchRecord` was never populated from DB.

**Files changed:**
- `via/renderers/diagram.py`: removed `if base in class_names` guard (unconditional arrow draw); removed unused `class_names` variable
- `via/db/store.py:match()`: added LEFT JOIN on `symbol_references` to get `base_names` (GROUP_CONCAT of parent names); passes `base_names` in row_dict
- `via/db/store.py:_match_with_regex()`: same LEFT JOIN added
- `via/db/store.py:query_relationships()`: same LEFT JOIN added for result symbol
- `via/core/match_record.py:create_from_row()`: splits `base_names` into `base_classes` list for class records
- Test: `test_render_inheritance_arrow_when_parent_not_in_result_set` added to `tests/unit/test_diagram_renderer.py`

## Test Results
- **970 passed** (was 968, +2 new tests)
- Live verification: `via -mg 'MatchRecord' -tc -Vinh -mg '*' -tc -oD` now shows `MatchRecord <|-- ClassMatchRecord` etc.
