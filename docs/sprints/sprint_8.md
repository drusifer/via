# Sprint 8 Consolidated Documentation

This document consolidates all documentation for Sprint 8.

## Table of Contents

- [SPRINT_8_USER_STORIES.md](#sprint-8-user-storiesmd) (originally `agents/cypher.docs/SPRINT_8_USER_STORIES.md`)

- [ARCH_REVIEW_SPRINT_8.md](#arch-review-sprint-8md) (originally `agents/morpheus.docs/ARCH_REVIEW_SPRINT_8.md`)

- [SPRINT_8_ARCHITECTURE.md](#sprint-8-architecturemd) (originally `agents/morpheus.docs/SPRINT_8_ARCHITECTURE.md`)

- [SPRINT_8_TASKS.md](#sprint-8-tasksmd) (originally `agents/mouse.docs/SPRINT_8_TASKS.md`)


---


## SPRINT_8_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_8_USER_STORIES.md`


## Sprint 8 - Line Number Index

**Author**: Cypher (PM)
**Date**: 2026-02-11
**Theme**: Line-Level Indexing & Slice Queries
**Points**: 6

---

### Epic: Line Number Index (`-mL`)

Add line numbers as a queryable dimension. This lets agents and developers extract content at specific lines or line ranges using the pre-built index, without scanning files. Uses a new match type `-mL` with Python-style slice syntax.

#### Decisions (Drew, 2026-02-11)

| Decision | Answer |
|----------|--------|
| Query syntax | Match type: `-mL 5:10` (not `--lines`) |
| Storage | Line start byte offsets + per-line byte length |

---

#### Story 1: Line Number Indexing (P0, 3pts)

**As a developer**, I want `via` to index line number positions (byte offsets) for every file, so I can quickly extract content at specific lines without scanning.

**Acceptance Criteria**:
- [ ] During indexing, line start byte offsets and per-line byte length are stored for each file
- [ ] New symbol type: `line` (flag: `-tL`)
- [ ] Database schema extended to store line-to-byte-offset mapping per file
- [ ] Incremental: line index updates when file is re-indexed
- [ ] Index size impact is reasonable (line offsets are compact)

---

#### Story 2: Line Slice Queries (P0, 3pts)

**As a developer**, I want to query for specific lines or line ranges using slice syntax, so I can extract code snippets by line number.

**Acceptance Criteria**:
- [ ] New match type flag: `-mL` (line match)
- [ ] Slice syntax supported: `5:10` (lines 5-10), `5:` (line 5 to end), `:10` (start to line 10), `-10:` (last 10 lines)
- [ ] Query: `via -mg 'myfile.py' -tF -mL 5:10 -oR` extracts lines 5-10 of myfile.py
- [ ] Uses byte offsets from index (no file scanning needed for offset lookup)
- [ ] Works with all output formats (`-oR`, `-oF`, `-oT`)
- [ ] Line numbers in output match actual file line numbers
- [ ] Supports combining with symbol queries: `via -mg 'MyClass' -tc -mL 1:5 -oR` (first 5 lines of class)

**Examples**:
```bash
## Extract lines 10-20 from a specific file
via -mg 'store.py' -tF -mL 10:20 -oR

## Last 10 lines of a file
via -mg 'main.py' -tF -mL -10: -oR

## First 5 lines of a class definition
via -mg 'DatabaseStore' -tc -mL 1:5 -oR

## Lines 1-3 of all test functions (see signatures)
via -mg 'test_*' -tf -mL 1:3 -oR
```

**Notes**:
- `-mL` follows the `-m<X>` match type convention (like `-mg`, `-mr`, `-ms`)
- Slice syntax mirrors Python slice notation
- Byte offsets make extraction O(1) seek + read instead of O(n) line scan

---

### Sprint 8 Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| Story 1 | 3 | P0 | Line number indexing (byte offsets) |
| Story 2 | 3 | P0 | Line slice queries (`-mL`) |
| **Total** | **6** | | |

---

### Technical Context

**What already exists**:
- Byte offsets already tracked per symbol in the database
- Match type flags follow `-m<X>` convention (`-mg`, `-mr`, `-ms`)
- `flag_groups.py` defines flag groups for easy extension
- `PipelineParser` handles match type dispatch

**What needs to be built**:
- Line offset table in database schema (`line_offsets` or extension of `files`)
- Line indexing pass in `IndexingService` (scan file, record byte offset per line)
- `-mL` match type in `flag_groups.py` and `PipelineParser`
- Slice parser (parse `5:10`, `-10:`, etc.)
- Integration with output renderers


---


## ARCH_REVIEW_SPRINT_8.md

**Original Location**: `agents/morpheus.docs/ARCH_REVIEW_SPRINT_8.md`


## Architecture Review - Sprints 6, 7, 8
**Author**: Morpheus (Tech Lead)
**Date**: 2026-02-13
**Scope**: Feature architecture for Sprints 6-8 + codebase audit

---

### SPRINT OVERVIEW

| Sprint | Theme | Points | Status |
|--------|-------|--------|--------|
| 6 | Watch Mode (`via index -w`) | 12 | Planning |
| 7 | MCP Integration (`via --mcp`) | 10 | Planning |
| 8 | Line Number Index (`-mL`) | 6 | Planning |
| **Total** | | **28** | |

---

## SPRINT 6: WATCH MODE ARCHITECTURE

### Overview
Enable `via` to run in the foreground, monitoring file changes and automatically re-indexing affected files using the `watchdog` library.

### Component Design

#### New Files
```
via/services/watch.py        # WatchService class (NEW)
```

#### Modified Files
```
via/__main__.py              # Wire -w flag to WatchService
via/services/indexing.py     # Add delete_file_symbols() method
```

### Class Design

```python
## via/services/watch.py

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

#### Event Handler (watchdog integration)

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

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Foreground only | Yes | No daemon/PID complexity |
| Debounce | 500ms | Balance responsiveness vs editor save storms |
| Library | `watchdog` | Cross-platform, stable, well-documented |
| Relationship re-resolution | 2-pass | Reuse existing incremental logic |

### Integration Points

1. **Existing `IndexingService`**: Reuse `index_file()` for re-indexing
2. **Existing `FileDiscovery`**: Reuse exclusion pattern logic
3. **New method needed**: `indexing_service.delete_file_symbols(path)` to clean up on delete

### Error Handling Strategy

| Error | Response |
|-------|----------|
| Syntax error in file | Log warning, continue watching |
| DB locked | Retry after 100ms, max 3 retries |
| Directory deleted | Log warning, continue watching |
| Memory leak | Use weak refs for event handlers |

### Testing Strategy

- Unit tests: WatchService with mocked watchdog
- Integration test: Create/modify/delete files, verify DB updates
- Stability test: 1-hour soak test with rapid file changes

---

## SPRINT 7: MCP INTEGRATION ARCHITECTURE

### Overview
Make `via` a first-class tool for AI agents via Model Context Protocol (MCP). Run as JSON-RPC 2.0 server over stdio.

### Component Design

#### New Files
```
via/mcp/__init__.py          # Package init
via/mcp/server.py            # MCP server (JSON-RPC 2.0)
via/mcp/schema.py            # Tool schema generator
via/mcp/handlers.py          # Request handlers
via/mcp/installer.py         # Agent config deployer
```

#### Modified Files
```
via/__main__.py              # Wire --mcp flag and mcp subcommand
```

### Class Design

```python
## via/mcp/server.py

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

#### Schema Generator

```python
## via/mcp/schema.py

class MCPSchemaGenerator:
    """Generates MCP tool schema from via's flag groups."""

    def generate(self) -> dict:
        """Return full MCP tool spec as JSON-serializable dict."""

    def _generate_search_schema(self) -> dict:
        """Schema for search operation."""

    def _generate_relationship_schema(self) -> dict:
        """Schema for relationship query."""
```

#### Agent Installer

```python
## via/mcp/installer.py

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

### JSON-RPC Protocol

#### Request Format
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

#### Response Format
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

#### Error Response
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

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | stdio | Universal, no port conflicts |
| Protocol | JSON-RPC 2.0 | MCP standard |
| Query syntax | Same as CLI | No learning curve, reuse parser |
| Auto-config scope | Claude Code only | Gemini/ChatGPT deferred to backlog (2026-02-13) |

### Integration Points

1. **Existing `PipelineParser`**: Reuse for query parsing
2. **Existing `PipelineExecutor`**: Execute queries
3. **New JSON serialization**: Convert MatchRecord → JSON

### Testing Strategy

- Unit tests: JSON-RPC request/response handling
- Integration test: Full round-trip via subprocess
- Compatibility test: Verify against MCP spec

---

## SPRINT 8: LINE NUMBER INDEX ARCHITECTURE

### Overview
Add line numbers as a queryable dimension. Store line byte offsets during indexing, enable extraction via `-mL` slice syntax.

### Component Design

#### Modified Files
```
via/core/schema.py           # Add line_offsets table
via/core/store.py            # Add line offset CRUD
via/services/indexing.py     # Extract line offsets during parse
via/pipeline/parser.py       # Add -mL match type
via/pipeline/flag_groups.py  # Define LINE_MATCH flag group
via/pipeline/executor.py     # Handle -mL queries
```

### Database Schema Extension

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

### Slice Syntax Parser

```python
## via/pipeline/slice_parser.py (or inline in executor.py)

def parse_line_slice(slice_str: str, total_lines: int) -> tuple[int, int]:
    """Parse Python-style slice syntax.

    Examples:
        "5:10"  -> (5, 10)
        "5:"    -> (5, total_lines)
        ":10"   -> (1, 10)
        "-10:"  -> (total_lines - 10, total_lines)
    """
```

### Query Flow

```
via -mg 'store.py' -tF -mL 10:20 -oR

1. -mg 'store.py' -tF  →  Find file matching 'store.py'
2. -mL 10:20           →  Extract lines 10-20 using indexed offsets
3. -oR                 →  Render as raw output
```

### Store Methods

```python
## via/core/store.py additions

def store_line_offsets(self, file_id: int, offsets: list[tuple[int, int, int]]) -> None:
    """Store (line_number, byte_offset, byte_length) tuples."""

def get_line_offsets(self, file_id: int, start_line: int, end_line: int) -> list[LineOffset]:
    """Get byte offsets for line range."""

def get_file_line_count(self, file_id: int) -> int:
    """Get total line count for a file."""
```

### Indexing Integration

```python
## In indexing.py, during file processing

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

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Query syntax | `-mL 5:10` | Follows `-m<X>` convention |
| Storage | Separate `line_offsets` table | Not symbols, positional metadata (Drew 2026-02-13) |
| Data model | Per-line byte offset + length | O(1) extraction |
| Slice syntax | Python-style | Familiar to developers |

**Design Note (2026-02-13)**: Separate table chosen over symbol-based storage, but with unified query interface. `-mL` works like `-mg`/`-mr` from user perspective — same `-m<X>` pattern, same pipeline flow, just queries `line_offsets` instead of `symbols`.

### Testing Strategy

- Unit tests: Slice parser with edge cases
- Integration test: Index file, query lines, verify content
- Performance test: Large file (10K+ lines) extraction timing

---

## CODEBASE AUDIT (Pre-Sprint Cleanup)

### VERDICT: SIGNIFICANT CLEANUP NEEDED

The codebase carries legacy weight from schema v1 that is **never used in production**. Removing it will simplify indexing, testing, and the DB layer substantially.

---

### 1. DEAD DATABASE TABLES (HIGH - Remove)

#### Legacy Tables Written But Never Queried in Production:
| Table | Written By | Read By | Verdict |
|-------|-----------|---------|---------|
| `functions` | indexing.py:345,360 | **tests only** | REMOVE |
| `classes` | indexing.py:332 | **tests only** | REMOVE |
| `imports` | indexing.py:374 | **tests only** | REMOVE |
| `globals` | indexing.py:386 | **tests only** | REMOVE |

#### Tables Created But Never Used At All:
| Table | Verdict |
|-------|---------|
| `log_statements` | REMOVE (never written, never read) |
| `markdown_headings` | REMOVE (markdown goes to `symbols` table instead) |

#### Impact of Removal:
- **schema.py**: Remove 6 CREATE TABLE statements, ~60 lines
- **schema.py**: Remove 12 legacy indexes, ~12 lines
- **store.py**: Remove ~350 lines of legacy CRUD methods (insert_function, insert_class, insert_import, insert_global, get_*_by_file, get_*_by_name)
- **indexing.py**: Remove `_store_entities()` method (~70 lines) and all calls to it
- **Tests**: Remove/rewrite tests that verify legacy table writes (test_database.py, test_indexing_service.py)
- **Net savings**: ~500 lines of dead code

---

### 2. DEAD CODE (HIGH - Remove)

#### A. Legacy `match` Subcommand
- `via/__main__.py:320` defines `_run_match_command()` — the old subcommand path
- `via/__main__.py:583` — only caller, behind the `match` subcommand parser
- **All modern queries use pipeline syntax** (`via -mg 'pattern'`)
- `via/commands/match.py` — entire file may be legacy (MatchCommand class)
- **Decision**: Remove `_run_match_command()` from `__main__.py` and `commands/match.py`. All matching goes through `PipelineExecutor`.

#### B. Legacy Store Methods (only used by tests for legacy tables)
- `store.py: get_functions_by_file()`, `get_functions_by_name()`
- `store.py: get_classes_by_file()`, `get_classes_by_name()`
- `store.py: get_imports_by_file()`
- `store.py: get_globals_by_file()`
- **Action**: Remove when legacy tables are removed. Rewrite tests against `symbols` table.

---

### 3. LAYERING VIOLATIONS (MEDIUM - Refactor)

#### A. Rendering Metadata in Database Layer
`store.py:697 _get_match_metadata()` computes MAX(LENGTH(...)) for column widths — a **rendering concern** in the **database layer**.

**Current**: `DatabaseStore` → computes column widths → attaches to every MatchRecord
**Better**: Renderers compute their own widths from the data they receive

#### B. Executor Knows Rendering Internals
`executor.py:292-337` has deep knowledge of RenderType, FormatType, and renderer options.

**Current**: `PipelineExecutor._execute_render_stage()` parses render options, creates renderers
**Better**: A `RenderStageHandler` or the `RendererFactory` should own this entirely

---

### 4. DUPLICATION (MEDIUM - Consolidate)

#### A. Pattern Matching in Two Places
- `store.py:742-838` — SQL pattern matching (GLOB, LIKE, REGEXP)
- `executor.py:214-290` — Python pattern matching (fnmatch, re.search) for chained filters

**Analysis**: Python-side filtering IS required for chained `--via` stages. Stage 2+ operates on in-memory results, not fresh DB queries.

**Recommendation**: Extract shared `PatternMatcher` utility for logical consistency.

#### B. Metadata Extraction Pattern
Every streaming renderer repeats this pattern:
```python
if total_matches is None and record.total_matches is not None:
    total_matches = record.total_matches
```
**Action**: Extract to base class helper.

---

### 5. STRUCTURAL SIMPLIFICATIONS (MEDIUM)

#### A. Schema Versioning Mismatch
- `schema.py` says `SCHEMA_VERSION = 2`
- But `pending_relationships` table comment says "Schema v3"
- **Action**: Reconcile version numbering

#### B. File Count Summary
| Area | Current Lines | Est. After Cleanup |
|------|--------------|-------------------|
| schema.py | 224 | ~100 |
| store.py | ~1273 | ~900 |
| indexing.py | ~653 | ~580 |
| **Total savings** | | **~570 lines** |

---

### RECOMMENDED REFACTORING ORDER

#### Phase 1: Dead Code Removal (Safest, Biggest Impact) - BEFORE SPRINTS 6-8
1. Remove 6 legacy tables from schema.py
2. Remove 12 legacy indexes from schema.py
3. Remove legacy CRUD from store.py (~350 lines)
4. Remove `_store_entities()` from indexing.py (~70 lines)
5. Rewrite affected tests to use `symbols` table
6. Remove `_run_match_command()` from `__main__.py` (~70 lines)
7. Remove `commands/match.py` if fully dead

#### Phase 2: Layering Fixes
8. Extract `_get_match_metadata()` from store.py into utility
9. Executor calls helper before streaming, passes metadata to renderers

#### Phase 3: DRY Consolidation
10. Extract `PatternMatcher` utility
11. Extract common renderer metadata pattern to base class
12. Reconcile schema version numbering

---

### SPRINT DEPENDENCIES

```
[Phase 1: Dead Code] ──┬──> [Sprint 6: Watch Mode]
                       │
                       ├──> [Sprint 7: MCP Integration]
                       │
                       └──> [Sprint 8: Line Index]
```

**Recommendation**: Complete Phase 1 cleanup before starting Sprint 6. This reduces complexity for all three sprints.

---

### WHAT'S WORKING WELL (Keep)

- **Renderer hierarchy**: Base class, ContextOptions, source_extraction — well factored
- **Pipeline architecture**: parser.py + executor.py + types.py — clean separation
- **SymbolType/MatchOp enums**: Simple, no class hierarchies — exactly right
- **MatchRecord hierarchy**: Clean polymorphism for different result types
- **RendererFactory**: Good pattern for renderer creation


---


## SPRINT_8_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_8_ARCHITECTURE.md`


## Sprint 8 Architecture Design — Line Number Index

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-20
**Status**: ✅ APPROVED — all decisions resolved. Neo cleared to implement.

---

### Context

Sprint 8 adds line-level byte offset indexing so that `via -mL 1:5` can extract
specific lines from any matched symbol or file using the pre-built index — no
file scanning needed for offset lookup.

#### What already exists

| Item | Location | Note |
|------|----------|------|
| `files.id` FK anchor | `via/db/schema.py` | All line data will foreign-key here |
| `symbols.byte_offset / byte_length` | `via/db/schema.py` | Per-symbol ranges — same model extended to lines |
| `MATCH_FLAGS (-mg/-mr/-ms)` | `via/core/flag_groups.py` | `-mL` follows same prefix convention |
| `PipelineParser` match parser | `via/pipeline/parser.py` | Will add `-mL` as optional argument |
| `PipelineExecutor.execute()` | `via/pipeline/executor.py` | Will add post-match line slice step |
| `RawRenderer` / `FormattedRenderer` | `via/renderers/` | Already seek to byte_offset — no change needed |
| `SCHEMA_VERSION = 3` | `via/db/schema.py` | Bump to 4 |

---

### Open Questions (need Drew sign-off)

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| **OQ-1** | Are line number slice values **relative to the matched symbol** or **absolute file line numbers**? | ✅ **RELATIVE** — line 1 = first line of the matched thing. For a file, symbol start = line 1 = file line 1, so relative and absolute coincide. For a class at file line 50, `-mL 1:5` = file lines 50-54. |
| **OQ-2** | Index line offsets for ALL indexed files, or only parsed files? | ✅ **ALL text-indexed files** — same gate as symbol indexing (`parsed=True`). Binary/oversized files skipped. |

---

### Design 1: `line_offsets` Table

New table in `via/db/schema.py`. Every indexed line gets one row.

```sql
CREATE TABLE line_offsets (
    file_id     INTEGER NOT NULL,
    line_number INTEGER NOT NULL,   -- 1-based
    byte_offset INTEGER NOT NULL,   -- file byte offset of line start
    byte_length INTEGER NOT NULL,   -- bytes in this line (incl. newline)
    PRIMARY KEY (file_id, line_number),
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_line_offsets_file ON line_offsets(file_id);
```

**FK cascade**: `files ON DELETE CASCADE` — no manual cleanup needed in `delete_file_completely()`.
The FK handles it automatically, matching the existing `symbol_references` pattern.

**Why not store in `files` BLOB?** SQL queries by line number would be impossible.
Clean separate table is consistent with `symbol_references` design.

#### Storage estimate

| File size | Lines | Rows | Row size | Total |
|-----------|-------|------|----------|-------|
| 1K lines | 1,000 | 1,000 | ~20 bytes | 20 KB |
| 10K lines | 10,000 | 10,000 | ~20 bytes | 200 KB |
| 100K lines | 100,000 | 100,000 | ~20 bytes | 2 MB |

Acceptable for any reasonably-sized codebase.

#### Schema migration

Bump `SCHEMA_VERSION = 3 → 4`. Add migration in `initialize_schema()`:
```python
if current_version < 4:
    conn.execute(CREATE_LINE_OFFSETS_TABLE)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_line_offsets_file ON line_offsets(file_id)")
```

---

### Design 2: Indexing Pass

Add `_index_line_offsets(file_id, content: bytes)` to `IndexingService`.
Called immediately after symbol indexing for a file (same content bytes already in memory).

```python
def _index_line_offsets(self, file_id: int, content: bytes) -> None:
    """Record byte offset of each line start."""
    offsets = []
    pos = 0
    for line_num, line in enumerate(content.splitlines(keepends=True), start=1):
        offsets.append((file_id, line_num, pos, len(line)))
        pos += len(line)
    self._db_store.upsert_line_offsets(file_id, offsets)
```

`splitlines(keepends=True)` handles `\n`, `\r\n`, `\r` correctly. O(file_size) — same as parsing.

#### `DatabaseStore` additions

```python
def upsert_line_offsets(self, file_id: int,
                         offsets: list[tuple[int,int,int,int]]) -> None:
    """Insert/replace line offsets for a file (atomic)."""
    with self.transaction():
        self.conn.execute(
            "DELETE FROM line_offsets WHERE file_id = ?", (file_id,)
        )
        self.conn.executemany(
            "INSERT INTO line_offsets (file_id,line_number,byte_offset,byte_length)"
            " VALUES (?,?,?,?)",
            offsets,
        )

def get_line_byte_range(self, file_path: str,
                         abs_start: int, abs_end: int
                         ) -> tuple[int, int]:
    """Return (byte_offset, byte_length) for lines abs_start..abs_end (inclusive, 1-based).

    Returns (0, 0) if file or lines not found.
    """
    row = self.conn.execute("""
        SELECT
            MIN(lo.byte_offset)                                    AS start_off,
            MAX(lo.byte_offset) + MAX(lo.byte_length) -
            MIN(lo.byte_offset)                                    AS length
        FROM line_offsets lo
        JOIN files f ON lo.file_id = f.id
        WHERE f.path = ?
          AND lo.line_number BETWEEN ? AND ?
    """, (file_path, abs_start, abs_end)).fetchone()
    if not row or row[0] is None:
        return (0, 0)
    return (row[0], row[1])

def get_line_count(self, file_path: str) -> int:
    """Return total line count for a file (for negative slice resolution)."""
    row = self.conn.execute("""
        SELECT MAX(lo.line_number)
        FROM line_offsets lo
        JOIN files f ON lo.file_id = f.id
        WHERE f.path = ?
    """, (file_path,)).fetchone()
    return row[0] if row and row[0] else 0
```

**Note**: `delete_file_completely()` does NOT need to change — FK cascade in the DDL
handles `line_offsets` deletion automatically when the `files` row is deleted.

---

### Design 3: `-mL` Flag and Pipeline Integration

#### Flag placement

`-mL SLICE` is **not** added to `MATCH_FLAGS` (which is for mutually-exclusive primary
match syntax). Instead it is added directly to `PipelineParser._create_match_parser()` as
an optional standalone argument, similar to `-I`, `-n`, `-Q`:

```python
## in _create_match_parser()
parser.add_argument(
    '-mL', '--match-lines',
    dest='line_slice',
    metavar='SLICE',
    default=None,
    help='Line slice (Python-style): 5:10, 1:, -10:, :20'
)
```

This means `-mL` is always combined with `-mg/-tF` etc.; it does not trigger a new
stage on its own. `_is_match_stage()` requires no change (the `-mg` or `-tF` will
still trigger match detection).

#### Slice syntax

```python
## via/core/utils.py — add parse_line_slice()
def parse_line_slice(s: str) -> tuple[Optional[int], Optional[int]]:
    """Parse Python-style slice string into (start, end).

    '5:10'  → (5, 10)    lines 5 through 10 (inclusive, 1-based relative)
    '1:'    → (1, None)   from line 1 to end
    ':5'    → (None, 5)   from start through line 5
    '-10:'  → (-10, None) last 10 lines
    '7'     → (7, 7)      single line 7
    """
    if ':' not in s:
        n = int(s)
        return (n, n)
    left, right = s.split(':', 1)
    start = int(left) if left else None
    end = int(right) if right else None
    return (start, end)
```

#### Absolute line resolution

Given a MatchRecord with `line_number = symbol_line` (absolute, 1-based), and a
parsed slice `(rel_start, rel_end)` (1-based relative):

```python
def resolve_abs_lines(symbol_line: int, total_lines: int,
                       rel_start: Optional[int], rel_end: Optional[int],
                       symbol_length_lines: int
                       ) -> tuple[int, int]:
    """Resolve relative slice to absolute file line numbers."""
    # symbol_length_lines = approx lines in symbol (from byte_length + line_offsets)
    # For a file: symbol_line=1, symbol_length_lines=total_lines
    sym_end = symbol_line + symbol_length_lines - 1

    start = (symbol_line + rel_start - 1) if rel_start and rel_start > 0 \
            else (sym_end + rel_start + 1) if rel_start and rel_start < 0 \
            else symbol_line
    end = (symbol_line + rel_end - 1) if rel_end and rel_end > 0 \
          else (sym_end + rel_end + 1) if rel_end and rel_end < 0 \
          else sym_end

    return (max(start, symbol_line), min(end, sym_end))
```

**Simplification**: For the initial implementation, restrict to non-negative slices only.
Negative-index support (last N lines) can be added iteratively. Flag as OQ-3 below.

#### PipelineExecutor changes

Add post-match step in `execute()` after MATCH stages:

```python
## in PipelineExecutor.execute()
if last_match_stage and getattr(last_match_stage.args, 'line_slice', None):
    result_iter = self._apply_line_slice(result_iter, last_match_stage.args)
```

```python
def _apply_line_slice(self, records: Iterator[MatchRecord],
                       args: Namespace) -> Iterator[MatchRecord]:
    """Update byte_offset/byte_length on each record to cover the requested lines."""
    slice_str = args.line_slice
    rel_start, rel_end = parse_line_slice(slice_str)

    for record in records:
        # Resolve relative lines to absolute file lines
        abs_start = record.line_number + (rel_start - 1 if rel_start else 0)
        abs_end = record.line_number + (rel_end - 1 if rel_end else 9999)

        new_offset, new_length = self.db.get_line_byte_range(
            record.file_path, abs_start, abs_end
        )
        if new_length > 0:
            record.byte_offset = new_offset
            record.byte_length = new_length
            record.line_number = abs_start
        yield record
```

The updated `byte_offset` / `byte_length` flow straight into `RawRenderer` and
`FormattedRenderer` with **zero changes** to those renderers.

---

### Design 4: Open Questions for Drew

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| OQ-1 | Relative vs absolute slice? | Relative to symbol start (see above) |
| OQ-2 | Which files to line-index? | All `parsed=True` files |
| **OQ-3** | Negative slice support (last N lines) in Sprint 8 or defer? | **Defer negative indices to Sprint 9 / post-MVP** — requires `get_line_count()` per record, adds DB round-trip. Positive slices cover 95% of use cases. |

---

### Updated File Change Summary

| File | Change |
|------|--------|
| `via/db/schema.py` | Add `CREATE_LINE_OFFSETS_TABLE`, bump `SCHEMA_VERSION` to 4, add to `ALL_TABLES`, add index |
| `via/db/store.py` | Add `upsert_line_offsets()`, `get_line_byte_range()`, `get_line_count()` |
| `via/services/indexing.py` | Add `_index_line_offsets(file_id, content)` called after symbol indexing |
| `via/pipeline/parser.py` | Add `-mL` / `--match-lines` optional arg to `_create_match_parser()` |
| `via/pipeline/executor.py` | Add `_apply_line_slice()`, call after last MATCH stage if `line_slice` present |
| `via/core/utils.py` | Add `parse_line_slice()` |
| `tests/unit/test_line_index.py` | New — schema, store, indexer, slice parser, executor |
| `tests/uat/test_sprint8_uat.py` | New — E2E UAT |

**No new files in `via/`** — all changes slot into existing modules.

---

### Implementation Order for Neo

```
P1 — DB Schema + Indexing (Story 1 prerequisite)
  P1-1  Add CREATE_LINE_OFFSETS_TABLE to schema.py; bump SCHEMA_VERSION → 4
  P1-2  Add migration in DatabaseStore.initialize_schema()
  P1-3  Add upsert_line_offsets() + get_line_byte_range() to store.py
  P1-4  Add _index_line_offsets() to IndexingService._index_file()
  P1-5  Unit tests: schema created, offsets stored, range lookup returns correct bytes
  P1-6  Regression: make test (existing suite green)

P2 — Pipeline Integration (Story 2)
  P2-1  Add parse_line_slice() to via/core/utils.py
  P2-2  Add -mL argument to PipelineParser._create_match_parser()
  P2-3  Add _apply_line_slice() to PipelineExecutor; wire into execute()
  P2-4  Unit tests: slice parsing, round-trip via -mL flag, byte range accuracy
  P2-5  Integration smoke: via -mg 'store.py' -tF -mL 1:5 -oR extracts correct lines

P3 — UAT (Trin)
  P3-1  UAT: file line extraction
  P3-2  UAT: symbol line extraction
  P3-3  UAT: open-ended slices (5:, :10)
  P3-4  Regression: make test full suite
```

---

### Sprint 8 Tech Debt Created

| ID | Item |
|----|------|
| TD-S8-1 | Negative line indices (last N lines) — deferred per OQ-3 |
| TD-S8-2 | Line offset coverage for non-parsed files (binary metadata) — deferred |


---


## SPRINT_8_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_8_TASKS.md`


## Sprint 8 Task Breakdown — Line Number Index

**Scrum Master**: Mouse
**Date**: 2026-03-20
**Sprint Points**: 6 (2 user stories)
**Architecture**: `agents/morpheus.docs/SPRINT_8_ARCHITECTURE.md` ✅ APPROVED
**Stories**: `agents/cypher.docs/SPRINT_8_USER_STORIES.md` ✅ READY

---

### Sprint Goal

Ship `-mL` line slice queries — developers and AI agents can extract specific lines or
line ranges from any matched file or symbol using the pre-built index, with O(1) byte
seeks instead of file scanning.

---

### Phase Summary

| Phase | Name | Owner | Gates | Pts |
|-------|------|-------|-------|-----|
| P1 | DB Schema + Line Indexing | Neo | line_offsets table populated, unit tests pass | Story 1 |
| P2 | Pipeline Integration | Neo | `via -mg 'f.py' -tF -mL 1:5 -oR` works end-to-end | Story 2 |
| P3 | UAT | Trin | All UAT pass, make test green | 6pts done |

---

### Phase 1 — DB Schema + Line Indexing (Story 1)

**Goal**: New `line_offsets` table in schema; every indexed file's line byte offsets
are stored and updated on re-index. No pipeline changes yet.

#### Tasks

- [ ] **P1-1** Add `CREATE_LINE_OFFSETS_TABLE` DDL to `via/db/schema.py`:
  ```sql
  CREATE TABLE line_offsets (
      file_id     INTEGER NOT NULL,
      line_number INTEGER NOT NULL,
      byte_offset INTEGER NOT NULL,
      byte_length INTEGER NOT NULL,
      PRIMARY KEY (file_id, line_number),
      FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
  );
  ```
  Add `"CREATE INDEX IF NOT EXISTS idx_line_offsets_file ON line_offsets(file_id);"` to `CREATE_INDEXES`.
  Add to `ALL_TABLES`. Bump `SCHEMA_VERSION = 3 → 4`.

- [ ] **P1-2** Add schema migration in `DatabaseStore.initialize_schema()`:
  - If `current_version < 4`: execute `CREATE_LINE_OFFSETS_TABLE` + index DDL, update version

- [ ] **P1-3** Add `DatabaseStore.upsert_line_offsets(file_id, offsets)`:
  - Atomic: DELETE existing rows for file_id, then `executemany` INSERT
  - Use existing `transaction()` context manager

- [ ] **P1-4** Add `DatabaseStore.get_line_byte_range(file_path, abs_start, abs_end) -> tuple[int, int]`:
  - Returns `(byte_offset, byte_length)` for lines abs_start..abs_end inclusive (1-based)
  - Single SQL query (JOIN files, MIN/MAX aggregate)
  - Returns `(0, 0)` if not found

- [ ] **P1-5** Add `IndexingService._index_line_offsets(file_id, content: bytes)`:
  - `content.splitlines(keepends=True)` → enumerate byte offsets
  - Call `db_store.upsert_line_offsets(file_id, offsets)`

- [ ] **P1-6** Wire `_index_line_offsets()` into `IndexingService._index_file()`:
  - Called immediately after symbol indexing (same `content` bytes already in memory)
  - Only for `parsed=True` files (same gate as symbol indexing)

- [ ] **P1-7** Unit tests (`tests/unit/test_line_index.py`):
  - Schema: `line_offsets` table exists after `initialize_schema()`
  - Migration: existing DB at version 3 migrates to 4 cleanly
  - `upsert_line_offsets` idempotent (re-index same file → same data, no duplicates)
  - `get_line_byte_range` returns correct byte range for known content
  - `get_line_byte_range` returns `(0, 0)` for unknown file/lines
  - Line offsets match actual file content when read at returned byte offset

- [ ] **P1-8** FK cascade test: deleting a file record cascades to `line_offsets`

**Gate**: `line_offsets` table populated after `via index .`. All P1 unit tests pass. Existing 794 tests unbroken.

---

### Phase 2 — Pipeline Integration (Story 2)

**Goal**: `-mL SLICE` modifier wired into the pipeline. Matched records have their
`byte_offset`/`byte_length` updated before rendering. No renderer changes.

#### Tasks

- [ ] **P2-1** Add `parse_line_slice(s: str) -> tuple[int | None, int | None]` to `via/core/utils.py`:
  - `'5:10'` → `(5, 10)`, `'1:'` → `(1, None)`, `':5'` → `(None, 5)`, `'7'` → `(7, 7)`
  - Negative values parsed but treated as "end of symbol" (resolved in executor)
  - Raises `ValueError` on invalid input

- [ ] **P2-2** Add `-mL` / `--match-lines` argument to `PipelineParser._create_match_parser()`:
  - `dest='line_slice'`, `default=None`, `metavar='SLICE'`
  - **Not** in `MATCH_FLAGS` mutex group — optional modifier alongside `-mg/-tF`

- [ ] **P2-3** Add `PipelineExecutor._apply_line_slice(records, args)` method:
  - For each record: resolve `(rel_start, rel_end)` to absolute file lines using `record.line_number`
  - Call `self.db.get_line_byte_range(record.file_path, abs_start, abs_end)`
  - Update `record.byte_offset`, `record.byte_length`, `record.line_number` in place
  - Yield updated record (skip if `new_length == 0`)

- [ ] **P2-4** Wire `_apply_line_slice()` into `PipelineExecutor.execute()`:
  - After all MATCH stages complete and `result_iter` is ready
  - Only if `getattr(last_match_stage.args, 'line_slice', None)` is truthy

- [ ] **P2-5** Unit tests (extend `tests/unit/test_line_index.py`):
  - `parse_line_slice`: all slice forms (`5:10`, `1:`, `:5`, `7`, `-10:`)
  - `parse_line_slice` raises on garbage input
  - `_apply_line_slice` updates byte_offset/byte_length correctly
  - Open-ended slice `1:` covers to symbol end
  - Slice out-of-bounds → record skipped (byte_length=0)

- [ ] **P2-6** Integration smoke test (`tests/integration/test_cli_line_slice.py`):
  - `via -mg '*.py' -tF -mL 1:3 -oR` → returns first 3 lines of matched files
  - `via -mg 'MyClass' -tc -mL 1:5 -oR` → first 5 lines of class
  - `via -mg 'store.py' -tF -mL 2:2 -oR` → single line
  - Combined with `-oF` (syntax highlight): works with correct lines

**Gate**: All P2 tests pass. `via -mg 'store.py' -tF -mL 1:5 -oR` extracts correct first 5 lines. Existing 794+ tests unbroken.

---

### Phase 3 — UAT (Trin)

**Goal**: End-to-end acceptance tests covering all Story 2 acceptance criteria.

#### Tasks

- [ ] **P3-1** UAT test file: `tests/uat/test_sprint8_uat.py`

- [ ] **P3-2** UAT cases:
  - `TestUAT81_FileLineExtraction`: `via -mg '*.py' -tF -mL 1:3 -oR` returns correct content
  - `TestUAT82_SymbolLineExtraction`: `via -mg 'MyClass' -tc -mL 1:5 -oR` correct first 5 lines of class
  - `TestUAT83_OpenSlice`: `via -mg 'file.py' -tF -mL 3: -oR` returns line 3 to end
  - `TestUAT84_SingleLine`: `-mL 1:1` returns exactly one line
  - `TestUAT85_LineNumbersMatch`: output line numbers match actual file line numbers
  - `TestUAT86_IncrementalUpdate`: modify a file, re-index, `-mL` returns updated content
  - `TestUAT87_FormattedOutput`: `-mL` works with `-oF` (syntax highlighting)

- [ ] **P3-3** Regression: `make test` — all 794+ tests pass, 0 failures

**Gate**: All UAT cases pass. Sprint 8 = SHIPPED.

---

### Dependency Chain

```
P1 (DB Schema + Line Indexing)
  └─ P2 (Pipeline) depends on P1 complete
  └─ P3 (UAT) depends on P1 + P2 complete
```

**P1 is unblocked** — start immediately.
**P2 can start after P1-4 done** (needs `get_line_byte_range()` in store).

---

### Task Count

| Phase | Tasks | Testable After |
|-------|-------|----------------|
| P1 | 8 | P1 complete |
| P2 | 6 | P2 complete |
| P3 | 3 | P3 = done |
| **Total** | **17** | |

---

### OQs Status (from Morpheus arch)

| # | Question | Status |
|---|----------|--------|
| OQ-1 | Relative vs absolute slice? | Implement as **relative** (Morpheus rec) — confirm with Drew |
| OQ-2 | Which files? | `parsed=True` only (Morpheus rec) — proceed |
| OQ-3 | Negative indices? | **Defer** to TD-S8-1 — proceed without |


---
