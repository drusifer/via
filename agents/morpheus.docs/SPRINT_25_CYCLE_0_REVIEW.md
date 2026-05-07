# Sprint 25 Cycle 0 Review - Dart Parser Dependency Path

**Reviewer**: Morpheus  
**Date**: 2026-05-06  
**Scope**: Dependency viability spike  
**Verdict**: APPROVED

## Reviewed

- `pyproject.toml`
- `tests/unit/test_sprint25_c0.py`
- Trin UAT result: `make test FILE=tests/unit/test_sprint25_c0.py` — 1 passed

## Decision

The Dart parser dependency path is approved for Cycle 1.

`tree-sitter-language-pack>=1.6.2` is acceptable for Sprint 25 because the targeted unit test proves:

- the package is installable through project dependencies;
- `get_language("dart")` returns a `tree_sitter.Language`;
- the resulting parser can parse a Flutter-style Dart fixture without ERROR nodes.

## Binding Guidance For Cycle 1

- Implement `DartParser` against `tree_sitter_language_pack.get_language("dart")`.
- Keep parser initialization lazy and per-process, matching `JavaScriptParser`.
- Preserve graceful `ImportError`/dependency failure behavior by returning `ParseResult.parse_error`.
- Do not add relationships beyond what Cycle 1 needs for symbol extraction and `--lang dart`; deeper relationship coverage belongs to Cycle 2.
- Add unit coverage for the parser foundation before integration wiring.

## Handoff

@Neo: Proceed with Sprint 25 Cycle 1 parser foundation.
