# Neo Next Steps

## Resume Point: Lint fix COMPLETE (Sprint 21 post-ship)

### On Resume
1. Read `agents/CHAT.md` bottom 20 lines
2. Read `agents/neo.docs/current_task.md` — full list of remaining C901 fixes

### Critical Context
- `make lint` currently failing with C901 complexity errors
- Do NOT suppress — user said to actually refactor
- Use polymorphic child-type dispatch (handler registry/dict) instead of `if child.type == X / elif child.type == Y` chains
- All Sprint 21 tests still passing (1259) — don't break them

### Next Action
Fix `_extract_all_string_constants` in `via/parsers/javascript_parser.py` (complexity 20):
- Same pattern as `_extract_all_calls` / `_extract_all_http_calls` — use `_collect_var_bodies`, `_collect_function_bodies`, `_collect_class_bodies`
- String constants also handle top-level `const X = 'string'` — extract that into `_collect_string_var_bodies(node, content, out)` helper
- Then fix remaining 12 functions across other files

### Files Still Needing Fixes
- `via/parsers/javascript_parser.py` — `_extract_all_string_constants` (20)
- `via/__main__.py` — `main` (14)
- `via/api/query_builder.py` — `to_cli_args` (12)
- `via/commands/coverage.py` — `import_coverage_xml` (13)
- `via/db/store.py` — `match` (12), `query_relationships` (13), `query_negative_relationships` (11)
- `via/parsers/python_parser.py` — `_extract_string_constants` (12), `_extract_class_structural_references` (15), `_extract_annotation_references` (15)
- `via/pipeline/executor.py` — `_execute_match_stage` (13)
- `via/services/indexing.py` — `_store_declares_relationships` (16)
- `via/web/api/query.py` — `_builder_from_body` (16)
