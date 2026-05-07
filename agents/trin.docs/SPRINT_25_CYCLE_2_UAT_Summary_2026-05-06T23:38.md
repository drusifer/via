# Sprint 25 Cycle 2 UAT Summary - 2026-05-06T23:38

## Result

PASS.

## Scope Verified

- Dart/Flutter fixture coverage for `StatefulWidget`, `State<T>`, `build`, directives, declares, inheritance, and best-effort calls.
- Dart docs and MCP examples include visible Dart/Flutter workflows.
- Docs state that Dart directives are directive strings, not resolved dependencies.
- Docs state that VIA does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.
- Existing discovery behavior remains compatible with non-Flutter projects.
- Full test suite is green.

## Verification

- `make test FILE=tests/unit/test_sprint25_c2.py` - 3 passed.
- `make test FILE=tests/unit/test_discovery.py` - 12 passed.
- `make test FILE=tests/unit/test_sprint25_c1.py` - 7 passed.
- `make test` - 1324 passed, 1 skipped, 4 warnings.

## Finding

Initial full-suite run found one regression: adding a global `build/` exclude broke `test_discover_without_gitignore`, which expects non-Flutter `build/` directories to be discoverable when `.gitignore` is ignored. The fix scopes `build/` exclusion to roots containing `pubspec.yaml`; Flutter projects still exclude `build/`, while generic projects keep prior discovery behavior.
