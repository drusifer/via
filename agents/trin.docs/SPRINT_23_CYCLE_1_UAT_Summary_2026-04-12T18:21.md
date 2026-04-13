# Sprint 23 Cycle 1 UAT Summary — Canned Shortcut Surface

**Persona**: Trin  
**Date**: 2026-04-12T18:21  
**Status**: PASS

## Verification

- Confirmed Sprint 23 canned built-ins are registered:
  - `callers`
  - `methods-calling`
  - `inheritors`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- Confirmed deferred shortcuts are not advertised as runnable built-ins:
  - `callees`
  - `declared-in-file`
- Confirmed `callers`, `methods-calling`, and `inheritors` return the same result as their explicit expanded queries.
- Confirmed `--show-expanded` prints a copyable `via ...` command without executing.
- Confirmed missing canned args remain actionable.
- Confirmed docs-header and paged-scan templates expand to normal argv.

## Tests

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

## QA Note

The shortcut expansions are verified against current runtime behavior. There remains a known product/architecture follow-up: Sprint 22 result-stage-first documentation and the executor's actual relationship orientation are divergent. Cycle 1 does not introduce new relationship semantics.
