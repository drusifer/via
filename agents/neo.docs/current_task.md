# Neo Current Task - Sprint 5 UAT Test Fixes

## Task: Fix failing Sprint 5 UAT tests
**Status**: COMPLETE (100%)
**Date**: 2026-02-09

## Root Cause

`resolve_pending_relationships()` in `DatabaseStore` used `SELECT id FROM symbols WHERE symbol_name = ? LIMIT 1` to find target symbols. With no ordering, this picked whichever symbol was inserted first. When files were indexed in non-alphabetical order (e.g., fileB before fileA), import symbols were created before definition symbols. The LIMIT 1 then resolved relationships to the import symbol (type='import') instead of the actual class/function definition.

This caused `object_type='class'` filters in `query_relationships` to return empty results, since the relationship target had type='import' instead of type='class'.

## Fix Applied

**File**: `via/db/store.py` line ~1048

Added `ORDER BY CASE symbol_type WHEN 'class' THEN 0 WHEN 'function' THEN 1 ... END` to prefer definitions over imports when resolving pending relationships.

**File**: `tests/uat/test_sprint5_uat.py` line ~365

Fixed UAT-2.1 test: removed incorrect `-ti` type filter on the subject side of an import relationship query. The target module `typing` has type `module`, not `import`.

## Test Results

- **Full suite**: 687 passed, 0 failed
- **Sprint 5 UAT**: 25/25 passed
- **New regression tests**: 9 tests in `test_relationship_pipeline.py`

## Files Modified

- `via/db/store.py` - Fix relationship resolution ordering
- `tests/uat/test_sprint5_uat.py` - Fix UAT-2.1 query
- `tests/unit/test_relationship_pipeline.py` - New regression tests
