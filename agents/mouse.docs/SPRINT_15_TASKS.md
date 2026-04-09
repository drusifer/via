# Sprint 15 — Task Board

**Sprint**: MCP Ergonomics + Index Completeness
**Points**: 9pt (6 stories)
**Baseline**: 1178 Python + 74 JS + 22 E2E
**Arch**: `morpheus.docs/SPRINT_15_ARCHITECTURE.md`
**Stories**: `cypher.docs/SPRINT_15_USER_STORIES.md`

---

## Cycle 1: Small Fixes (3pt) — S15-3 + S15-5 + S15-6

All independent, no new schema, no new architecture.

### S15-3: Fix `--lang` + `-tF` (1pt)
- [x] C1-1: Pass `parse_result.language` to `_store_file_path_symbols()` in `indexing.py`
- [x] C1-2: Add integration test: `--lang py -tF` returns only `.py` files
- [x] C1-3: Add integration test: `--lang js -tF` returns only JS/TS files

### S15-5: Extend `-Q` to Full Path Matching (1pt)
- [x] C1-4: Write test: `-mg 'via/pipeline/*' -tF -Q` → verify current behavior
- [x] C1-5: Fix if broken; if already works, mark as docs-only
- [x] C1-6: Update `-Q` help text in `__main__.py`
- [x] C1-7: Update MCP schema `-Q` description

### S15-6: `--help` Relationship Examples (1pt)
- [x] C1-8: Add "Relationship Queries" section to `_build_pipeline_help()` in `__main__.py`
- [x] C1-9: Add test: `via --help` output contains `Relationship Queries`, `anchor LEFT`, all 5 rel types

**Exit criteria**: All baseline tests pass + new tests green. Hand to Trin UAT.

---

## Cycle 2: `--slice` + `total`/`shown` (2pt) — S15-1

### S15-1: `--slice` Result Windowing (2pt)
- [x] C2-1: Add `parse_result_slice()` to `core/utils.py` (0-based wrapper)
- [x] C2-2: Add `--slice` flag to `pipeline/parser.py`; mutual exclusion with `-n`
- [x] C2-3: Apply LIMIT/OFFSET in `store.py` match() from slice args
- [x] C2-4: Wrap MCP response as `{result, total, shown}` in `server.py`
- [x] C2-5: Update CLI warning in `__main__.py` to mention `--slice`
- [x] C2-6: Update MCP tool description in `schema.py`
- [x] C2-7: Tests: slice parsing, total/shown in JSON, --slice + -n conflict

**Exit criteria**: Baseline + new tests pass. MCP response shape verified. Hand to Trin UAT.

---

## Cycle 3: MCP Output Wrapper + Markdown Declares (4pt) — S15-2 + S15-4

### S15-2: MCP Output Type Wrapper (2pt)
- [x] C3-1: Add `_detect_output_type()` to `server.py`
- [x] C3-2: Implement render capture via `redirect_stdout` + `io.StringIO`
- [x] C3-3: Add `strip_ansi()` to `core/utils.py`
- [x] C3-4: Wrap response with `output_type` field
- [x] C3-5: Handle empty diagram → JSON fallback with `note` field
- [x] C3-6: Update MCP schema to document `output_type` and all `-oX` flags
- [x] C3-7: Tests: each `-oX` flag returns correct `output_type`; backward compat for default

### S15-4: `declares` for Markdown Headers (2pt)
- [x] C3-8: Add header loop in `_store_declares_relationships()` in `indexing.py`
- [x] C3-9: Unit test: index .md file with 3 headers → 3 `declares` rows
- [x] C3-10: Integration test: `--via declares` on .md file returns headers
- [x] C3-11: Integration test: `--sans declares` on .md returns files with no headers
- [x] C3-12: Regression test: Python `declares` unchanged

**Exit criteria**: All tests pass. MCP output types verified. Markdown declares works end-to-end.

---

## Post-Implementation

- [x] Trin UAT (per cycle)
- [x] Morpheus review (per cycle)
- [ ] Oracle doc groom
- [ ] Smith end-to-end user test
- [x] Cypher launch
