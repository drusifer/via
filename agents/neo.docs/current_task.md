# Neo Current Task

## Task: Session 2026-03-21 — Lint, Bug Fixes, MCP Schema
**Status**: COMPLETE
**Date**: 2026-03-21

## What was done

### Lint Fixes
- `via/services/indexing.py:597` — renamed `error` → `_error` (W0613 unused arg)
- `via/services/watch.py:147` — renamed `signum, frame` → `_signum, _frame`
- `via/parsers/python_parser.py:193,199` — renamed `tree, node` → `_tree, _node` in stub methods
- `via/__main__.py` — removed 2 redundant local `StatsCommand` imports
- `pyproject.toml` — added `ignored-modules = ["mcp", "watchdog", "pygments"]`, fixed `source-roots = ["."]`
- Pylint score: 9.07 → 9.46/10

### Bug Fix: TD-1 (reindex_file missing resolve_pending_relationships)
- `via/services/indexing.py:reindex_file()` — added `self.db_store.resolve_pending_relationships()` call
- Flushed 854 stale pending relationships (571 resolved)
- 837 tests passing

### MCP Schema Fix (with Bob/Morpheus)
- `-iv` direction was backwards in all SKILL.md files and `via/mcp/schema.py`
- Correct: KNOWN anchor LEFT, `*` RIGHT; no-iv returns relators, -iv returns relatees
- Updated `via/mcp/schema.py` description and all examples

## Test Results
- 837 passed, 0 failed

## Next
- Sprint 9 stories TBD (TD-REVIEW-1 through TD-REVIEW-5 are candidates)
