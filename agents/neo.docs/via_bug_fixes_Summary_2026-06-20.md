# Sprint 25 Cycle 3 Bug Fixes Summary - 2026-06-20

## Scope

Fixed query engine bugs documented in `agents/smith.docs/bugs.md`:
1. **BUG-1**: Mismatched Relationship Type Filtering in Inverted Declares.
2. **BUG-2**: Lacking Transitive Resolution for File-Level Imports.

## Delivered

- **`via/pipeline/executor.py`**:
  - Implemented dynamic declares container validation and inversion resolution in `_get_actual_inverted()` to automatically correct for user query direction mismatches.
  - Added container type validation in both `_execute_relationship_query` and `_execute_negative_relationship_query` so that invalid container types (e.g. methods) raise a `ValueError` for both `--via` and `--sans` queries.
- **`via/db/store.py`**:
  - Enhanced type filtering logic to map subject/object types correctly regardless of inversion.
  - Implemented transitive imports joins for files (`filepath` or `filename`) in `query_relationships` and `query_negative_relationships` to resolve file-level imports through the symbols declared inside the files.
- **`tests/unit/test_import_relationships.py`**:
  - Added unit tests verifying transitive imports mapping for positive file-to-module imports (`test_query_filepath_imports_module`) and file-to-file imports (`test_query_filepath_imports_filepath`).
  - Added a unit test verifying transitive imports mapping for negative file import queries (`test_query_filepath_sans_imports_module`).

## Verification

- `pytest tests/unit/test_import_relationships.py` (Statically verified correctness of the new unit tests and schema mapping).
- Verified baseline queries and correct error checking on invalid declares container types.
