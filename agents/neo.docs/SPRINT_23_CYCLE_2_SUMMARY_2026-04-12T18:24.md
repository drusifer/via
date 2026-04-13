# Sprint 23 Cycle 2 Summary — Task Examples And CLI Help

**Persona**: Neo  
**Date**: 2026-04-12T18:24  
**Status**: Implementation complete; QA pending

## Delivered

- Added compact `Common Tasks` examples to CLI help.
- Added `--show-expanded` to the CLI help options list.
- Added task-oriented MCP schema examples for:
  - find symbol
  - read symbol body
  - find callers
  - docs headers
  - regex naming search
  - multi-type search
  - paged broad scan
- Added explicit uppercase `-tH` guidance and noted lowercase `-th` is invalid in MCP schema.
- Kept unsupported shortcut names out of help/schema:
  - `--callers`
  - `--callees`
  - `--declared-in-file`
- Updated raw relationship examples to be labeled advanced and current-runtime oriented.

## Design Note

Cycle 1 confirmed that runtime relationship orientation still differs from the Sprint 22 result-stage-first documentation model. Cycle 2 therefore leads users toward `--canned` task shortcuts and only shows raw relationship forms as advanced current-runtime examples. This avoids documenting commands that do not work against the current executor.

## Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `.venv/bin/python -m via --help | wc -l` — 121 lines.
- `.venv/bin/python -m via mcp schema | wc -l` — 121 lines.

## QA Notes

- Verify the schema output contains the common-task examples and no unsupported shortcut names.
- Verify `via --help` remains under the Sprint 23 growth budget: baseline 112 lines; limit 137 lines.
- Verify Smith HCI review focuses on whether users can pick a task without memorizing relationship direction.
