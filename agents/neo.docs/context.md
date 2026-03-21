**Context: Sprint 7 Complete (2026-03-20)**

**Key Decisions**:

1. Pipeline syntax detection uses flag prefixes (-mg, -mr, -rT, etc.)
2. Legacy syntax (via match -t ...) preserved via subcommand detection
3. MatchRecord system uses polymorphism + factory pattern
4. Renderer system uses abstract base class with format support
5. Relationship queries use --via / -V flags with subject/object patterns
6. resolve_pending_relationships prefers definitions over imports (ORDER BY symbol_type priority)
7. RenderType.JSON is universally supported by all MatchRecord subclasses (base class handles it)
8. JsonRenderer._to_dict() is in the renderer, not on MatchRecord (SoC)
9. WAL mode enabled in DatabaseStore.connect() for concurrent watch+query safety
10. WatchService: no `output` param, uses logger.info/debug, has handle_signals param
11. MCP server uses FastMCP (mcp>=1.26), two separate DB connections (read/write), WatchService in daemon thread

**Bug Fix (2026-02-09)**: resolve_pending_relationships symbol resolution
- Root Cause: LIMIT 1 with no ORDER BY picked import symbols over definitions
- Fix: Added ORDER BY CASE to prefer class > function > method > global > module > import

**Bug Fix (2026-03-19)**: SQLite thread safety in WatchService
- Root Cause: threading.Timer runs in different thread; sqlite3 default check_same_thread=True
- Fix: sqlite3.connect(db_path, check_same_thread=False) in DatabaseStore.connect()

**Bug Fix (2026-03-19)**: Missing symbol deletion in WatchService._remove_file
- Root Cause: delete_file_by_path deletes files row but not symbols (no FK cascade)
- Fix: Now uses delete_file_completely() — atomic triad in one transaction

**Architecture**:
```
via/__main__.py
  ├── _is_pipeline_syntax() → Detect shorthand flags
  ├── _run_pipeline_command() → Pipeline execution
  │     ├── PipelineParser.parse(argv) → List[PipelineStage]
  │     └── PipelineExecutor.execute(stages) → Iterator|None
  ├── _run_mcp_command() → via mcp {schema,serve}
  ├── _run_install_command() → via {install,uninstall,status} mcp
  └── main() → Routes to pipeline, watch mode, legacy mode, mcp, install

via/mcp/
  ├── __init__.py
  ├── schema.py — build_tool_schema() → dict (10 examples)
  └── server.py — run_mcp_server(root_dir, db_path) using FastMCP

via/commands/install.py
  ├── InstallTarget (ABC)
  ├── McpInstallTarget — reads/writes .mcp.json
  └── INSTALL_TARGETS = {'mcp': McpInstallTarget}

via/renderers/json_renderer.py — JsonRenderer, _to_dict()
via/services/watch.py — WatchService (no output param, handle_signals param)
via/services/indexing.py — IndexingService.reindex_file() public
via/db/store.py — WAL in connect(), delete_file_completely()
```

**Test Patterns**:
- Use indexed_project fixture for temp DB
- subprocess.run for CLI integration tests
- TDD: Write tests first, see red, implement, see green
- Use `make` skill (not raw Bash) for all test runs
- caplog fixture for logging assertions (not output= StringIO)

**Sprint 6 Status**: COMPLETE (2026-03-19), 713 tests passing
**Sprint 7 Status**: COMPLETE (2026-03-20), 794 tests passing (+81 new tests)
**Sprint 8 Status**: COMPLETE (2026-03-21), 837 tests passing

**Session 2026-03-21 Fixes**:
- Bug: resolve_pending_relationships() not called in IndexingService.index() — all live relationship queries returned empty. Fixed: added call before commit_transaction().
- Bug: MCP server never called initialize_schema() — old DBs missing line_offsets table. Fixed: watch_store.initialize_schema() on startup.
- Bug: MCP tool description was one-liner docstring. Fixed: now uses build_tool_schema() rich description.
- Improvement: WatchService switched from recursive=True to non-recursive per-dir watches using FileDiscovery._should_include_dir(). Excluded dirs (build/, __pycache__, .git) never get OS inotify watches.
- Improvement: watchdog inotify_buffer logger silenced to WARNING in MCP mode.
- Regression test added: tests/integration/test_indexing_resolves_relationships.py

**Tech Debt (from this session)**:
- TD-WATCH-1: Extract PathFilter from FileDiscovery (backlogged in SPRINT_9_USER_STORIES.md)

**Tech Debt (Sprint 7 created)**:
- TD-S7-1: Async queue for DB access (replace WAL+separate-connections) if concurrent writers added
- TD-S7-2: Evaluate lighter MCP stdio transport if dep weight becomes an issue

**Tech Debt (from Morpheus Sprint 6 review — resolved in Sprint 7)**:
- TD-1: IndexingService.reindex_file() ✅ DONE
- TD-2: DatabaseStore.delete_file_completely() ✅ DONE
- TD-3: Move lazy imports to module level in watch.py (still pending)
- TD-4: Make FileDiscovery._should_include_file public (still pending)
- TD-5: Remove unused IOBase import from watch.py ✅ DONE
