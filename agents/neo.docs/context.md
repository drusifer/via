**Context: Sprint 6 Complete (2026-03-19)**

**Key Decisions**:

1. Pipeline syntax detection uses flag prefixes (-mg, -mr, -rT, etc.)
2. Legacy syntax (via match -t ...) preserved via subcommand detection
3. MatchRecord system uses polymorphism + factory pattern
4. Renderer system uses abstract base class with format support
5. Relationship queries use --via / -V flags with subject/object patterns
6. resolve_pending_relationships prefers definitions over imports (ORDER BY symbol_type priority)

**Bug Fix (2026-02-09)**: resolve_pending_relationships symbol resolution
- Root Cause: LIMIT 1 with no ORDER BY picked import symbols over definitions
- Fix: Added ORDER BY CASE to prefer class > function > method > global > module > import

**Bug Fix (2026-03-19)**: SQLite thread safety in WatchService
- Root Cause: threading.Timer runs in different thread; sqlite3 default check_same_thread=True
- Fix: sqlite3.connect(db_path, check_same_thread=False) in DatabaseStore.connect()

**Bug Fix (2026-03-19)**: Missing symbol deletion in WatchService._remove_file
- Root Cause: delete_file_by_path deletes files row but not symbols (no FK cascade)
- Fix: Added delete_symbols_by_file(path) call before delete_file_by_path(path)

**Architecture**:
```
via/__main__.py
  ├── _is_pipeline_syntax() → Detect shorthand flags
  ├── _run_pipeline_command() → Pipeline execution
  │     ├── PipelineParser.parse(argv) → List[PipelineStage]
  │     └── PipelineExecutor.execute(stages) → Iterator|None
  └── main() → Routes to pipeline, watch mode, or legacy mode

via/services/watch.py (NEW - Sprint 6)
  ├── WatchService.start() → initial index + watchdog observer + SIGINT loop
  ├── _schedule(path, action) → debounce via threading.Timer (500ms)
  ├── _execute(path, action) → dispatch to _reindex_file or _remove_file
  ├── _reindex_file(path) → calls indexing_service._index_file(DiscoveredFile)
  └── _remove_file(path) → delete_relationships + delete_symbols + delete_file
```

**Test Patterns**:
- Use indexed_project fixture for temp DB
- subprocess.run for CLI integration tests
- TDD: Write tests first, see red, implement, see green
- Use `make` skill (not raw Bash) for all test runs

**Sprint 5 Status**: UAT complete (25/25 pass)
**Sprint 6 Status**: COMPLETE (2026-03-19), 709 tests passing
- WatchService: via/services/watch.py
- watchdog Observer + debounce threading.Timer (500ms)
- SIGINT: threading.Event, loop exits, prints "Watch mode stopped."
- Story 5 (SIGUSR1 force re-index): P2, not implemented

**Tech Debt (from Morpheus Sprint 6 review)**:
- TD-1: Add IndexingService.reindex_file(path) — public method with transaction
- TD-2: Add DatabaseStore.delete_file_completely(path) — deletion triad
- TD-3: Move lazy imports to module level in watch.py
- TD-4: Make FileDiscovery._should_include_file public
- TD-5: Remove unused IOBase import from watch.py
