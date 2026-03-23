# Neo Current Task

## Task: Sprint 11 Cycle 2 — Schema + JavaScriptParser
**Status**: COMPLETE (100%)
**Date**: 2026-03-22

## Schema Migration v6 — DONE
- `via/db/schema.py`: SCHEMA_VERSION 5→6; added `language TEXT` + `symbol_subtype TEXT` to `CREATE_SYMBOLS_TABLE`
- `via/db/store.py`: v6 migration block — ALTER TABLE + backfill language from files + indexes
- `via/db/store.py:insert_symbol()`: new `language` + `symbol_subtype` params
- `via/services/indexing.py`: all 6 `insert_symbol` calls now pass `language=parse_result.language`

## JavaScriptParser — DONE
- Full AST walking: functions, arrow functions, classes with inheritance, methods
- Imports: default, named (one per specifier), namespace (alias)
- Globals: module-level const/let/var (not arrow functions)
- TS: interfaces → ClassEntity, enums → ClassEntity, type aliases → GlobalEntity
- Partial parse: ERROR nodes skipped, parse_error set
- 10MB size limit enforced

## pyproject.toml — DONE
- Added: tree-sitter>=0.23, tree-sitter-javascript>=0.23, tree-sitter-typescript>=0.23

## Tests
- 29 new tests in tests/unit/test_sprint11_c2.py
- test_line_index.py: schema version assertions updated 5→6
- 1022 total, 0 regressions

## Next
- Awaiting Trin UAT → Morpheus review → Sprint 11 complete
