# Sprint 22 Cycle 2 Summary

**Persona**: Neo  
**Date**: 2026-04-12T17:22  
**Status**: Complete — handed to Trin

## Scope

Cycle 2 implemented match-stage validation and regex validation.

## Changes

- Added one-matcher-per-stage validation in `PipelineParser`.
- Validated result stage and relationship filter stage separately.
- Added parse-time regex validation for `-mr` / `--match-regex`.
- Preserved multi-type OR behavior.
- Added `tests/unit/test_sprint22_c2.py`.

## Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c2.py` — 8 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_pipeline_parser.py` — 44 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_relationship_cli.py` — 18 passed.

## Notes

The parser still treats result-stage and relationship filter-stage matchers independently, so a query can use one matcher on each side of `--via` / `--sans`. Multi-type queries remain valid.
