# Sprint 23 Cycle 1 Summary — Canned Shortcut Surface

**Persona**: Neo  
**Date**: 2026-04-12T18:18  
**Status**: Implementation complete; QA pending

## Delivered

- Added Sprint 23 canned shortcuts in `via/canned.py`:
  - `methods-calling`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- Preserved existing task-useful shortcuts:
  - `unused`
  - `potentially-unused`
  - `callers`
  - `inheritors`
  - `dead-docs`
- Added `--show-expanded` handling for `--canned` in `via/__main__.py`.
- `--show-expanded` prints a copyable `via ...` command and exits without running the query.
- Deferred unsupported shortcut names are not added as built-ins:
  - `callees`
  - `declared-in-file`
- Added focused tests in `tests/unit/test_sprint23_c1.py`.

## Important Finding

The current executor relationship implementation still uses the older runtime orientation:

```text
before --via = known anchor / object
after --via = returned subject filter
```

Sprint 22 documentation moved toward a result-stage-first mental model, but the executor was not changed in that sprint. Cycle 1 therefore keeps `callers` and `inheritors` expanded in the orientation that returns correct runtime results today. This avoids shipping a shortcut that looks correct in documentation but returns the wrong symbols.

## Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed after QA added coverage for `methods-calling` and `inheritors`.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

## QA Notes

- Verify shortcut output against explicit expanded queries, not only against template text.
- Confirm `--show-expanded` does not require an index and does not execute.
- Confirm deferred names remain absent from `load_canned_queries()`.
- Morpheus should review the docs/runtime orientation mismatch as a follow-up risk, but no new relationship semantics were added in Cycle 1.
