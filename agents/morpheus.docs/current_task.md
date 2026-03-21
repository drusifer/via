# Morpheus Current Task - Sprint 8 Architecture

## Task: Sprint 8 Architecture Design (Line Number Index)
**Status**: COMPLETE (100%)
**Date**: 2026-03-20

## Outcome: DESIGN READY — awaiting Drew sign-off on 3 OQs

Full design in `SPRINT_8_ARCHITECTURE.md`. Key decisions:
1. `line_offsets` table — FK→files CASCADE, PK=(file_id, line_number), SCHEMA_VERSION 3→4
2. `-mL SLICE` as optional arg on match parser (not in MATCH_FLAGS mutex group)
3. `_apply_line_slice()` in PipelineExecutor — updates byte_offset/byte_length post-match
4. Zero renderer changes needed

**OQ-1** (relative vs absolute slice), **OQ-2** (which files), **OQ-3** (negative indices) need Drew approval.
Neo starts P1 immediately (schema + indexing); P2 waits for OQ-1 sign-off.
