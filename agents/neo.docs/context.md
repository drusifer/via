**Context: Sprint 5 Implementation**

**Key Decisions**:

1. Pipeline syntax detection uses flag prefixes (-mg, -mr, -rT, etc.)
2. Legacy syntax (via match -t ...) preserved via subcommand detection
3. MatchRecord system uses polymorphism + factory pattern
4. Renderer system uses abstract base class with format support
5. Relationship queries use --via / -V flags with subject/object patterns
6. resolve_pending_relationships prefers definitions over imports (ORDER BY symbol_type priority)

**Bug Fix (2026-02-09)**: resolve_pending_relationships symbol resolution

- **Root Cause**: `LIMIT 1` with no ORDER BY picked import symbols over definitions when files indexed out of order
- **Fix**: Added ORDER BY CASE to prefer class > function > method > global > module > import
- **Regression tests**: `tests/unit/test_relationship_pipeline.py` (TestRelationshipResolutionOrder)

**Architecture**:

```
via/__main__.py
  ├── _is_pipeline_syntax() → Detect shorthand flags
  ├── _run_pipeline_command() → Pipeline execution
  │     ├── PipelineParser.parse(argv) → List[PipelineStage]
  │     └── PipelineExecutor.execute(stages) → Iterator|None
  └── main() → Routes to pipeline or legacy mode

via/db/store.py
  ├── resolve_pending_relationships() → Resolves cross-file refs after indexing
  ├── query_relationships() → Query by relationship type with filters
  └── insert_relationship() → Store resolved relationship
```

**Test Patterns**:

- Use indexed_project fixture for temp DB
- subprocess.run for CLI integration tests
- Reverse-order indexing to test relationship resolution
- TDD: Write tests first, see red, implement, see green

**Sprint 5 Status**: UAT complete (25/25 pass), 687 total tests passing
