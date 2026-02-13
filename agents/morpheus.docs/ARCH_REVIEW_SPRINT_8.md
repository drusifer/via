# Architecture Review - Sprints 6, 7, 8
**Author**: Morpheus (Tech Lead)
**Date**: 2026-02-13
**Scope**: Feature architecture for Sprints 6-8 + codebase audit

---

## SPRINT OVERVIEW

| Sprint | Theme | Points | Status |
|--------|-------|--------|--------|
| 6 | Watch Mode (`via index -w`) | 12 | Planning |
| 7 | MCP Integration (`via --mcp`) | 10 | Planning |
| 8 | Line Number Index (`-mL`) | 6 | Planning |
| **Total** | | **28** | |

---

# SPRINT 6: WATCH MODE ARCHITECTURE

## Overview
Enable `via` to run in the foreground, monitoring file changes and automatically re-indexing affected files using the `watchdog` library.

## Component Design

### New Files
```
via/services/watch.py        # WatchService class (NEW)
```

### Modified Files
```
via/__main__.py              # Wire -w flag to WatchService
via/services/indexing.py     # Add delete_file_symbols() method
```

## Class Design

```python
# via/services/watch.py

class WatchService:
    """Watches filesystem and triggers incremental re-indexing."""

    def __init__(self, root_path: Path, indexing_service: IndexingService):
        self.root_path = root_path
        self.indexing_service = indexing_service
        self.observer = Observer()  # watchdog
        self._debounce: dict[Path, float] = {}  # path -> last_event_time

    def start(self) -> None:
        """Start watching (blocking). Ctrl-C to stop."""

    def stop(self) -> None:
        """Graceful shutdown."""

    def _on_modified(self, path: Path) -> None:
        """Re-index single file with 500ms debounce."""

    def _on_created(self, path: Path) -> None:
        """Index new file."""

    def _on_deleted(self, path: Path) -> None:
        """Remove file's symbols from database."""

    def _should_process(self, path: Path) -> bool:
        """Check exclusions (.gitignore, --exclude)."""
```

### Event Handler (watchdog integration)

```python
class ViaEventHandler(FileSystemEventHandler):
    """Watchdog event handler wired to WatchService."""

    def __init__(self, watch_service: WatchService):
        self.watch_service = watch_service

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watch_service._on_modified(Path(event.src_path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watch_service._on_created(Path(event.src_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watch_service._on_deleted(Path(event.src_path))
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Foreground only | Yes | No daemon/PID complexity |
| Debounce | 500ms | Balance responsiveness vs editor save storms |
| Library | `watchdog` | Cross-platform, stable, well-documented |
| Relationship re-resolution | 2-pass | Reuse existing incremental logic |

## Integration Points

1. **Existing `IndexingService`**: Reuse `index_file()` for re-indexing
2. **Existing `FileDiscovery`**: Reuse exclusion pattern logic
3. **New method needed**: `indexing_service.delete_file_symbols(path)` to clean up on delete

## Error Handling Strategy

| Error | Response |
|-------|----------|
| Syntax error in file | Log warning, continue watching |
| DB locked | Retry after 100ms, max 3 retries |
| Directory deleted | Log warning, continue watching |
| Memory leak | Use weak refs for event handlers |

## Testing Strategy

- Unit tests: WatchService with mocked watchdog
- Integration test: Create/modify/delete files, verify DB updates
- Stability test: 1-hour soak test with rapid file changes

---

# SPRINT 7: MCP INTEGRATION ARCHITECTURE

## Overview
Make `via` a first-class tool for AI agents via Model Context Protocol (MCP). Run as JSON-RPC 2.0 server over stdio.

## Component Design

### New Files
```
via/mcp/__init__.py          # Package init
via/mcp/server.py            # MCP server (JSON-RPC 2.0)
via/mcp/schema.py            # Tool schema generator
via/mcp/handlers.py          # Request handlers
via/mcp/installer.py         # Agent config deployer
```

### Modified Files
```
via/__main__.py              # Wire --mcp flag and mcp subcommand
```

## Class Design

```python
# via/mcp/server.py

class MCPServer:
    """MCP-compatible server using JSON-RPC 2.0 over stdio."""

    def __init__(self, store: DatabaseStore):
        self.store = store
        self.executor = PipelineExecutor(store)

    def run(self) -> None:
        """Main loop: read JSON-RPC requests from stdin, write responses to stdout."""

    def handle_request(self, request: dict) -> dict:
        """Route request to appropriate handler."""

    def _handle_search(self, params: dict) -> dict:
        """Execute match query, return structured JSON results."""

    def _handle_relationships(self, params: dict) -> dict:
        """Execute relationship query."""

    def _handle_stats(self, params: dict) -> dict:
        """Return index statistics."""

    def _handle_index(self, params: dict) -> dict:
        """Trigger re-indexing."""
```

### Schema Generator

```python
# via/mcp/schema.py

class MCPSchemaGenerator:
    """Generates MCP tool schema from via's flag groups."""

    def generate(self) -> dict:
        """Return full MCP tool spec as JSON-serializable dict."""

    def _generate_search_schema(self) -> dict:
        """Schema for search operation."""

    def _generate_relationship_schema(self) -> dict:
        """Schema for relationship query."""
```

### Agent Installer

```python
# via/mcp/installer.py

class AgentInstaller:
    """Installs/uninstalls via as MCP tool for AI agents."""

    AGENTS = ['claude', 'gemini', 'chatgpt']

    def install(self, agent: str | None = None) -> None:
        """Install to specific agent or all."""

    def uninstall(self, agent: str | None = None) -> None:
        """Remove configuration."""

    def status(self) -> dict:
        """Return installation status per agent."""

    def _install_claude(self) -> None:
        """Write to ~/.claude/ or .mcp.json"""

    def _install_gemini(self) -> None:
        """Write to .gemini/"""

    def _install_chatgpt(self) -> None:
        """Write to appropriate location"""
```

## JSON-RPC Protocol

### Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "search",
  "params": {
    "pattern": "*Renderer*",
    "symbol_type": "class",
    "output": "json"
  },
  "id": 1
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "result": {
    "matches": [
      {
        "name": "ListRenderer",
        "symbol_type": "class",
        "file_path": "via/renderers/list.py",
        "line_number": 15,
        "byte_offset": 234,
        "qualified_name": "ListRenderer"
      }
    ],
    "total": 5
  },
  "id": 1
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid pattern syntax"
  },
  "id": 1
}
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | stdio | Universal, no port conflicts |
| Protocol | JSON-RPC 2.0 | MCP standard |
| Query syntax | Same as CLI | No learning curve, reuse parser |
| Auto-config scope | Claude Code only | Gemini/ChatGPT deferred to backlog (2026-02-13) |

## Integration Points

1. **Existing `PipelineParser`**: Reuse for query parsing
2. **Existing `PipelineExecutor`**: Execute queries
3. **New JSON serialization**: Convert MatchRecord → JSON

## Testing Strategy

- Unit tests: JSON-RPC request/response handling
- Integration test: Full round-trip via subprocess
- Compatibility test: Verify against MCP spec

---

# SPRINT 8: LINE NUMBER INDEX ARCHITECTURE

## Overview
Add line numbers as a queryable dimension. Store line byte offsets during indexing, enable extraction via `-mL` slice syntax.

## Component Design

### Modified Files
```
via/core/schema.py           # Add line_offsets table
via/core/store.py            # Add line offset CRUD
via/services/indexing.py     # Extract line offsets during parse
via/pipeline/parser.py       # Add -mL match type
via/pipeline/flag_groups.py  # Define LINE_MATCH flag group
via/pipeline/executor.py     # Handle -mL queries
```

## Database Schema Extension

```sql
-- New table for line byte offsets
CREATE TABLE IF NOT EXISTS line_offsets (
    file_id INTEGER NOT NULL,
    line_number INTEGER NOT NULL,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    PRIMARY KEY (file_id, line_number),
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_line_offsets_file ON line_offsets(file_id);
```

## Slice Syntax Parser

```python
# via/pipeline/slice_parser.py (or inline in executor.py)

def parse_line_slice(slice_str: str, total_lines: int) -> tuple[int, int]:
    """Parse Python-style slice syntax.

    Examples:
        "5:10"  -> (5, 10)
        "5:"    -> (5, total_lines)
        ":10"   -> (1, 10)
        "-10:"  -> (total_lines - 10, total_lines)
    """
```

## Query Flow

```
via -mg 'store.py' -tF -mL 10:20 -oR

1. -mg 'store.py' -tF  →  Find file matching 'store.py'
2. -mL 10:20           →  Extract lines 10-20 using indexed offsets
3. -oR                 →  Render as raw output
```

## Store Methods

```python
# via/core/store.py additions

def store_line_offsets(self, file_id: int, offsets: list[tuple[int, int, int]]) -> None:
    """Store (line_number, byte_offset, byte_length) tuples."""

def get_line_offsets(self, file_id: int, start_line: int, end_line: int) -> list[LineOffset]:
    """Get byte offsets for line range."""

def get_file_line_count(self, file_id: int) -> int:
    """Get total line count for a file."""
```

## Indexing Integration

```python
# In indexing.py, during file processing

def _index_line_offsets(self, file_id: int, content: bytes) -> int:
    """Scan file content, store byte offset per line.

    Returns total line count.
    """
    offsets = []
    offset = 0
    line_num = 1
    for line in content.split(b'\n'):
        offsets.append((line_num, offset, len(line)))
        offset += len(line) + 1  # +1 for newline
        line_num += 1
    self.store.store_line_offsets(file_id, offsets)
    return line_num - 1
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Query syntax | `-mL 5:10` | Follows `-m<X>` convention |
| Storage | Separate `line_offsets` table | Not symbols, positional metadata (Drew 2026-02-13) |
| Data model | Per-line byte offset + length | O(1) extraction |
| Slice syntax | Python-style | Familiar to developers |

**Design Note (2026-02-13)**: Separate table chosen over symbol-based storage, but with unified query interface. `-mL` works like `-mg`/`-mr` from user perspective — same `-m<X>` pattern, same pipeline flow, just queries `line_offsets` instead of `symbols`.

## Testing Strategy

- Unit tests: Slice parser with edge cases
- Integration test: Index file, query lines, verify content
- Performance test: Large file (10K+ lines) extraction timing

---

# CODEBASE AUDIT (Pre-Sprint Cleanup)

## VERDICT: SIGNIFICANT CLEANUP NEEDED

The codebase carries legacy weight from schema v1 that is **never used in production**. Removing it will simplify indexing, testing, and the DB layer substantially.

---

## 1. DEAD DATABASE TABLES (HIGH - Remove)

### Legacy Tables Written But Never Queried in Production:
| Table | Written By | Read By | Verdict |
|-------|-----------|---------|---------|
| `functions` | indexing.py:345,360 | **tests only** | REMOVE |
| `classes` | indexing.py:332 | **tests only** | REMOVE |
| `imports` | indexing.py:374 | **tests only** | REMOVE |
| `globals` | indexing.py:386 | **tests only** | REMOVE |

### Tables Created But Never Used At All:
| Table | Verdict |
|-------|---------|
| `log_statements` | REMOVE (never written, never read) |
| `markdown_headings` | REMOVE (markdown goes to `symbols` table instead) |

### Impact of Removal:
- **schema.py**: Remove 6 CREATE TABLE statements, ~60 lines
- **schema.py**: Remove 12 legacy indexes, ~12 lines
- **store.py**: Remove ~350 lines of legacy CRUD methods (insert_function, insert_class, insert_import, insert_global, get_*_by_file, get_*_by_name)
- **indexing.py**: Remove `_store_entities()` method (~70 lines) and all calls to it
- **Tests**: Remove/rewrite tests that verify legacy table writes (test_database.py, test_indexing_service.py)
- **Net savings**: ~500 lines of dead code

---

## 2. DEAD CODE (HIGH - Remove)

### A. Legacy `match` Subcommand
- `via/__main__.py:320` defines `_run_match_command()` — the old subcommand path
- `via/__main__.py:583` — only caller, behind the `match` subcommand parser
- **All modern queries use pipeline syntax** (`via -mg 'pattern'`)
- `via/commands/match.py` — entire file may be legacy (MatchCommand class)
- **Decision**: Remove `_run_match_command()` from `__main__.py` and `commands/match.py`. All matching goes through `PipelineExecutor`.

### B. Legacy Store Methods (only used by tests for legacy tables)
- `store.py: get_functions_by_file()`, `get_functions_by_name()`
- `store.py: get_classes_by_file()`, `get_classes_by_name()`
- `store.py: get_imports_by_file()`
- `store.py: get_globals_by_file()`
- **Action**: Remove when legacy tables are removed. Rewrite tests against `symbols` table.

---

## 3. LAYERING VIOLATIONS (MEDIUM - Refactor)

### A. Rendering Metadata in Database Layer
`store.py:697 _get_match_metadata()` computes MAX(LENGTH(...)) for column widths — a **rendering concern** in the **database layer**.

**Current**: `DatabaseStore` → computes column widths → attaches to every MatchRecord
**Better**: Renderers compute their own widths from the data they receive

### B. Executor Knows Rendering Internals
`executor.py:292-337` has deep knowledge of RenderType, FormatType, and renderer options.

**Current**: `PipelineExecutor._execute_render_stage()` parses render options, creates renderers
**Better**: A `RenderStageHandler` or the `RendererFactory` should own this entirely

---

## 4. DUPLICATION (MEDIUM - Consolidate)

### A. Pattern Matching in Two Places
- `store.py:742-838` — SQL pattern matching (GLOB, LIKE, REGEXP)
- `executor.py:214-290` — Python pattern matching (fnmatch, re.search) for chained filters

**Analysis**: Python-side filtering IS required for chained `--via` stages. Stage 2+ operates on in-memory results, not fresh DB queries.

**Recommendation**: Extract shared `PatternMatcher` utility for logical consistency.

### B. Metadata Extraction Pattern
Every streaming renderer repeats this pattern:
```python
if total_matches is None and record.total_matches is not None:
    total_matches = record.total_matches
```
**Action**: Extract to base class helper.

---

## 5. STRUCTURAL SIMPLIFICATIONS (MEDIUM)

### A. Schema Versioning Mismatch
- `schema.py` says `SCHEMA_VERSION = 2`
- But `pending_relationships` table comment says "Schema v3"
- **Action**: Reconcile version numbering

### B. File Count Summary
| Area | Current Lines | Est. After Cleanup |
|------|--------------|-------------------|
| schema.py | 224 | ~100 |
| store.py | ~1273 | ~900 |
| indexing.py | ~653 | ~580 |
| **Total savings** | | **~570 lines** |

---

## RECOMMENDED REFACTORING ORDER

### Phase 1: Dead Code Removal (Safest, Biggest Impact) - BEFORE SPRINTS 6-8
1. Remove 6 legacy tables from schema.py
2. Remove 12 legacy indexes from schema.py
3. Remove legacy CRUD from store.py (~350 lines)
4. Remove `_store_entities()` from indexing.py (~70 lines)
5. Rewrite affected tests to use `symbols` table
6. Remove `_run_match_command()` from `__main__.py` (~70 lines)
7. Remove `commands/match.py` if fully dead

### Phase 2: Layering Fixes
8. Extract `_get_match_metadata()` from store.py into utility
9. Executor calls helper before streaming, passes metadata to renderers

### Phase 3: DRY Consolidation
10. Extract `PatternMatcher` utility
11. Extract common renderer metadata pattern to base class
12. Reconcile schema version numbering

---

## SPRINT DEPENDENCIES

```
[Phase 1: Dead Code] ──┬──> [Sprint 6: Watch Mode]
                       │
                       ├──> [Sprint 7: MCP Integration]
                       │
                       └──> [Sprint 8: Line Index]
```

**Recommendation**: Complete Phase 1 cleanup before starting Sprint 6. This reduces complexity for all three sprints.

---

## WHAT'S WORKING WELL (Keep)

- **Renderer hierarchy**: Base class, ContextOptions, source_extraction — well factored
- **Pipeline architecture**: parser.py + executor.py + types.py — clean separation
- **SymbolType/MatchOp enums**: Simple, no class hierarchies — exactly right
- **MatchRecord hierarchy**: Clean polymorphism for different result types
- **RendererFactory**: Good pattern for renderer creation
