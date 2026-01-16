# VIA - System Architecture Design

**Architect**: Morpheus (Tech Lead)
**Date**: 2026-01-10 19:41:26
**Status**: Draft v1.0
**Addresses**: Oracle Review (agents/oracle.docs/VIA_INDEX_REVIEW.md)

---

## Executive Summary

This document defines the complete system architecture for the VIA index command, addressing all 14 gaps identified by Oracle's review. The architecture follows SOLID principles, supports pluggable parsers, and provides a scalable foundation for future query and filter commands.

**Key Architectural Decisions**:
1. **Layered Architecture**: CLI → Service → Parser → Storage
2. **Strategy Pattern**: Pluggable language parsers
3. **Worker Pool Pattern**: Bounded parallelization with multiprocessing
4. **File-based IPC**: Nested index coordination via filesystem markers
5. **Relative Paths**: Portable database storage
6. **Schema Versioning**: Migration support for future changes

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        CLI Layer                           │
│  (via.cli.index_command)                                   │
│  - Argument parsing (argparse)                             │
│  - Verbosity control                                       │
│  - Signal handling (HUP, INT, TERM)                        │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  (via.services.indexing_service)                            │
│  - IndexingService: Orchestrates indexing                   │
│  - WatchService: Daemon mode with watchdog                  │
│  - NestedIndexCoordinator: Manages nested indexes           │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ├──────────────┬──────────────┬──────────────┐
                 ▼              ▼              ▼              ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  File Discovery  │  │   Parser     │  │   Worker     │  │ Database │
│   (via.core.     │  │  (via.       │  │    Pool      │  │ (via.db. │
│   discovery)     │  │  parsers)    │  │  (via.core.  │  │  store)  │
│                  │  │              │  │   workers)   │  │          │
│ - GitignoreWalker│  │ - PythonPrs  │  │ - IndexWorker│  │ - Schema │
│ - FileFilter     │  │ - MarkdownPrs│  │ - WorkQueue  │  │ - CRUD   │
│ - ExcludePattern │  │ - ParserABC  │  │ - ResultAgg  │  │ - Query  │
└──────────────────┘  └──────────────┘  └──────────────┘  └──────────┘
```

---

## 2. Component Design

### 2.1 CLI Layer (`via/cli/index_command.py`)

**Responsibility**: Parse arguments, configure services, handle user interaction

```python
class IndexCommand:
    """Handles via index CLI command"""

    def run(self, args: argparse.Namespace) -> int:
        """
        Execute index command

        Returns:
            0: Success
            1: Partial success (some files had errors)
            2: Fatal error (indexing failed)
        """
        # Setup logging based on verbosity
        # Validate arguments
        # Create IndexingService
        # Execute indexing or watch mode
        # Return appropriate exit code
```

**Signal Handling**:
- `SIGINT` (Ctrl-C): Graceful shutdown
- `SIGTERM`: Graceful shutdown
- `SIGHUP`: Full re-index (daemon mode)
- `SIGUSR1`: Trigger index validation (custom signal)

---

### 2.2 Service Layer

#### 2.2.1 IndexingService (`via/services/indexing_service.py`)

**Responsibility**: Orchestrate the indexing workflow

```python
class IndexingService:
    """Core indexing orchestration"""

    def __init__(
        self,
        root_dir: Path,
        db_path: Path,
        force: bool = False,
        exclude_patterns: List[str] = None,
        worker_count: int = None  # None = auto (1 per subfolder, max 8)
    ):
        self.root_dir = root_dir
        self.db = DatabaseStore(db_path)
        self.discovery = FileDiscovery(root_dir, exclude_patterns)
        self.parser_registry = ParserRegistry()
        self.worker_pool = WorkerPool(worker_count)

    def index(self, progress_callback=None) -> IndexResult:
        """Run indexing workflow"""
        # 1. Discover files
        # 2. Filter by .gitignore and --exclude
        # 3. Check file sizes (skip > 10MB)
        # 4. Distribute to worker pool (1 worker per subfolder)
        # 5. Collect results
        # 6. Update database
        # 7. Return summary
```

**IndexResult**:
```python
@dataclass
class IndexResult:
    files_indexed: int
    files_parsed: int
    files_oversized: int
    functions_found: int
    classes_found: int
    imports_found: int
    errors: List[ParseError]
    duration: float
```

---

#### 2.2.2 WatchService (`via/services/watch_service.py`)

**Responsibility**: Daemon mode with file watching

```python
class WatchService:
    """File watching daemon for incremental indexing"""

    def __init__(
        self,
        indexing_service: IndexingService,
        log_file: Path,
        pid_file: Path
    ):
        self.indexing_service = indexing_service
        self.observer = Observer()  # watchdog
        self.nested_coordinator = NestedIndexCoordinator()

    def start_watch(self):
        """Start watch mode (foreground only - no daemon)"""
        # Setup Ctrl-L handler for full re-index
        # Start watchdog observer
        # Print live logs to stdout
        # Main event loop
        # Blocks until Ctrl-C

    def on_file_changed(self, event: FileSystemEvent):
        """Handle file change events"""
        # Re-index changed file only
        # Update database incrementally
```

**Watch Mode Lifecycle**:
- **Start**: `via index -w <dir>` (foreground only, no daemon)
- **Stop**: Ctrl-C (SIGINT)
- **Full Re-index**: Ctrl-L (foreground)

---

#### 2.2.3 NestedIndexCoordinator (`via/services/nested_index.py`)

**Responsibility**: Manage nested `.via/watch` markers and coordinate indexes

**Nested Index Discovery Protocol**:

```python
class NestedIndexCoordinator:
    """Coordinates nested index hierarchies"""

    def discover_nested_indexes(self, root_dir: Path) -> List[Path]:
        """
        Find all nested .via/watch markers

        Strategy: Use watchdog to monitor for .via/watch creation
        - When .via/watch is touched, add that directory to watch list
        - Recursively walk tree on startup to find existing markers
        - No polling - event-driven discovery
        """

    def query_hierarchical(self, query: Query) -> HierarchicalResults:
        """
        Query across nested indexes with directory scoping

        - Query starts at current directory index
        - Optionally bubble up to parent indexes
        - Optionally drill down to child indexes
        - Results are tagged with their scope (directory)
        """
```

**IPC Mechanism**: File-based signaling
- **Create/Touch `.via/watch`**: Subfolder signals "include me in nested indexing"
- **Root daemon uses watchdog**: Monitors for `.via/watch` file events
- **No complex IPC**: Simple filesystem-based coordination
- **Race condition handling**: If child starts before parent, parent discovers on next scan

**Nested Index Example**:
```
/home/user/project/          ← Root daemon (via index -w .)
    .via/
        index.db             ← Root index
        via.pid
    src/
        .via/
            watch            ← Signals "I'm a nested index"
            index.db         ← Nested index for src/
    tests/
        .via/
            watch
            index.db         ← Nested index for tests/
```

**Query Scoping**:
- Query from `/home/user/project/src/` searches `src/.via/index.db` first
- Can optionally search parent `/home/user/project/.via/index.db`
- `$VIA_PATHS` can add cross-tree indexes (Phase 2)

---

### 2.3 Parser Layer

#### 2.3.1 ParserABC (`via/parsers/base.py`)

**Responsibility**: Define parser interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ParsedEntity:
    """Generic parsed code entity"""
    type: str  # 'function', 'class', 'import', 'global', etc.
    name: str
    line_start: int
    line_end: int
    byte_offset: int
    byte_length: int
    metadata: dict  # Language-specific metadata

class ParserABC(ABC):
    """Abstract base class for language parsers"""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file"""

    @abstractmethod
    def parse(self, file_path: Path, content: bytes) -> List[ParsedEntity]:
        """
        Parse file and extract entities

        Returns:
            List of ParsedEntity objects

        Raises:
            ParseError: If parsing fails
        """

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions"""
```

---

#### 2.3.2 PythonParser (`via/parsers/python_parser.py`)

**Responsibility**: Parse Python files using `ast` module

```python
class PythonParser(ParserABC):
    """Python AST-based parser"""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix in {'.py', '.pyx', '.pyi'}

    def parse(self, file_path: Path, content: bytes) -> List[ParsedEntity]:
        """
        Parse Python file with AST

        Extracts:
        - Functions (with args, decorators, docstrings)
        - Classes (with bases, methods, decorators)
        - Imports (module, name, alias)
        - Globals (name, value if literal, type hint)
        - Decorators
        - Logging/print statements

        Returns byte_offset and byte_length for each entity
        """
        tree = ast.parse(content)
        entities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                entities.append(self._parse_function(node, content))
            elif isinstance(node, ast.ClassDef):
                entities.append(self._parse_class(node, content))
            # ... etc

        return entities

    def _get_byte_offset(self, node: ast.AST, content: bytes) -> Tuple[int, int]:
        """Calculate byte offset and length from AST node"""
        # Use node.lineno, node.end_lineno, node.col_offset, node.end_col_offset
        # Convert to byte positions in content
```

---

#### 2.3.3 MarkdownParser (`via/parsers/markdown_parser.py`)

**Responsibility**: Parse Markdown headings

```python
class MarkdownParser(ParserABC):
    """Simple regex-based Markdown parser"""

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix == '.md'

    def parse(self, file_path: Path, content: bytes) -> List[ParsedEntity]:
        """
        Extract headings from Markdown

        Pattern: ^(#{1,6})\s+(.+)$

        Returns:
        - Heading text
        - Level (1-6)
        - Line number
        - Byte offset
        """
```

---

#### 2.3.4 ParserRegistry (`via/parsers/registry.py`)

**Responsibility**: Register and discover parsers

```python
class ParserRegistry:
    """Registry for all language parsers"""

    def __init__(self):
        self._parsers: List[ParserABC] = []
        self._register_builtin_parsers()

    def _register_builtin_parsers(self):
        """Register built-in parsers"""
        self.register(PythonParser())
        self.register(MarkdownParser())
        # Future: register(JavaScriptParser())

    def register(self, parser: ParserABC):
        """Add a parser to the registry"""
        self._parsers.append(parser)

    def get_parser(self, file_path: Path) -> Optional[ParserABC]:
        """Find appropriate parser for file"""
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
        return None
```

**Future Plugin Support** (Phase 2):
- Load parsers from `~/.via/parsers/` directory
- Use entry points for parser discovery
- Validate parser interface compliance

---

### 2.4 Worker Pool

#### 2.4.1 WorkerPool (`via/core/workers.py`)

**Responsibility**: Parallel indexing with bounded workers

```python
from multiprocessing import Pool, cpu_count
from typing import List, Callable

class WorkerPool:
    """Manages parallel indexing workers"""

    def __init__(self, worker_count: Optional[int] = None):
        """
        Initialize worker pool

        Args:
            worker_count: Number of workers (None = auto)
                Auto: subfolder_count (no upper limit)
                Rationale: 1 worker per subfolder
        """
        self.worker_count = worker_count or self._auto_worker_count()
        self.pool = None

    def _auto_worker_count(self) -> int:
        """Determine optimal worker count"""
        # Will be calculated based on subfolder count
        # No upper limit - let the OS handle it
        return subfolder_count  # Calculated during discovery

    def map_files_to_workers(
        self,
        files: List[Path],
        parse_func: Callable
    ) -> List[ParseResult]:
        """
        Distribute files across workers

        Strategy: Group files by top-level subfolder
        - All files in same subfolder → same worker
        - Ensures 1 worker per subfolder
        - Better cache locality
        """
        with Pool(self.worker_count) as pool:
            results = pool.map(parse_func, files)
        return results
```

**Threading vs Multiprocessing Decision**:
- **Choice**: Multiprocessing
- **Reason**: AST parsing is CPU-bound, benefits from true parallelism
- **Trade-off**: Higher memory overhead, but better performance on multi-core
- **Python GIL**: Multiprocessing bypasses GIL for CPU-bound work
- **No Worker Limit**: 1 worker per subfolder, no cap - let OS manage resources

---

### 2.5 Database Layer

#### 2.5.1 Refined Schema (`via/db/schema.py`)

**Addresses Oracle's gaps**:

```sql
-- Metadata table (NEW - addresses relative paths)
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT INTO metadata VALUES ('index_root', '/absolute/path/to/project');
INSERT INTO metadata VALUES ('schema_version', '1');

-- Schema versioning table (NEW - addresses migrations)
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL,
    description TEXT
);
INSERT INTO schema_migrations VALUES (1, strftime('%s', 'now'), 'Initial schema');

-- Files table (UPDATED - relative paths)
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,  -- RELATIVE to index_root
    language TEXT,  -- 'python', 'markdown', null for unparsed
    size_bytes INTEGER,
    mtime REAL,
    indexed_at REAL,
    parsed BOOLEAN DEFAULT 0,
    oversized BOOLEAN DEFAULT 0
);

-- Functions table (UPDATED - added class_id, byte offsets)
CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,  -- NULL for global functions
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER NOT NULL,  -- For seeking
    byte_length INTEGER NOT NULL,
    args TEXT,  -- JSON serialized arguments
    decorators TEXT,  -- JSON array
    docstring TEXT
);

-- Classes table (unchanged from spec)
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    bases TEXT,  -- JSON array of base class names
    decorators TEXT,
    docstring TEXT
);

-- Imports table (UPDATED - added byte offsets)
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    name TEXT,  -- for 'from X import Y'
    alias TEXT,
    line_number INTEGER,
    byte_offset INTEGER,  -- NEW
    byte_length INTEGER   -- NEW
);

-- Globals table (UPDATED - added byte offsets)
CREATE TABLE globals (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    value TEXT,  -- if literal/constant
    type_hint TEXT,
    line_number INTEGER,
    byte_offset INTEGER,  -- NEW
    byte_length INTEGER   -- NEW
);

-- Log statements table (UPDATED - added byte offsets)
CREATE TABLE log_statements (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    type TEXT,  -- 'print', 'logging.info', etc.
    args TEXT,  -- JSON serialized
    line_number INTEGER,
    byte_offset INTEGER,  -- NEW
    byte_length INTEGER   -- NEW
);

-- Markdown headings table (unchanged)
CREATE TABLE md_headings (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    level INTEGER,  -- 1-6
    line_number INTEGER,
    byte_offset INTEGER
);

-- Indexes
CREATE INDEX idx_functions_name ON functions(name);
CREATE INDEX idx_functions_class ON functions(class_id);  -- NEW - for method queries
CREATE INDEX idx_classes_name ON classes(name);
CREATE INDEX idx_imports_module ON imports(module);
CREATE INDEX idx_files_path ON files(path);
```

**Key Changes**:
1. ✅ Added `metadata` table for index_root (relative paths)
2. ✅ Added `schema_migrations` for versioning
3. ✅ Added `class_id` to `functions` (methods support)
4. ✅ Added `byte_offset` and `byte_length` to imports, globals, log_statements
5. ✅ Added ON DELETE CASCADE for referential integrity

---

#### 2.5.2 DatabaseStore (`via/db/store.py`)

**Responsibility**: Database CRUD operations

```python
class DatabaseStore:
    """SQLite database operations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        """Create schema if needed, handle migrations"""
        current_version = self._get_schema_version()
        if current_version == 0:
            self._create_initial_schema()
        else:
            self._migrate(current_version)

    def insert_file(self, file_info: FileInfo) -> int:
        """Insert file record, return file_id"""

    def insert_parsed_entities(self, file_id: int, entities: List[ParsedEntity]):
        """Insert all parsed entities for a file"""
        # Batch insert for performance

    def get_stale_files(self) -> List[int]:
        """Find files in DB that no longer exist on disk"""

    def validate_byte_offsets(self) -> List[ValidationError]:
        """Verify all byte offsets are valid"""
        # Read file, check if offset+length is within bounds
```

---

## 3. Addressing Oracle's Gaps

### Gap #1: Nested Index Coordination ✅

**Solution**: File-based IPC with watchdog
- Root daemon uses `watchdog.Observer` to monitor for `.via/watch` file creation
- No polling, event-driven discovery
- Simple, no complex IPC mechanisms
- Race condition: If child starts first, parent discovers on next scan or restart

---

### Gap #2.1: Methods Table ✅

**Solution**: Add `class_id` to `functions` table
- Simple, no extra joins
- Global functions have `class_id = NULL`
- Methods have `class_id` referencing `classes.id`

---

### Gap #2.2: Byte Offsets ✅

**Solution**: Added `byte_offset` and `byte_length` to all entity tables
- imports, globals, log_statements now have byte offsets
- Consistent with functions, classes, md_headings

---

### Gap #3: `--exclude` Pattern Semantics ✅

**Solution**: Use `pathspec` library (same as .gitignore)
- Patterns match file paths relative to index root
- Glob-style syntax: `*.test.py`, `tests/**/*.py`, `**/tmp/*`
- Multiple `--exclude` flags are combined (logical OR)
- Patterns are case-sensitive on Unix, case-insensitive on Windows

---

### Gap #4: Daemon Lifecycle ✅

**Solution**: Watch mode only (no daemon)

```bash
# Foreground watch mode
via index -w [<dir>]
```

**Implementation**:
- Runs in foreground only (no background daemon)
- Stop with Ctrl-C (SIGINT)
- Full re-index with Ctrl-L
- No PID file needed

---

### Gap #5: Parallelization Details ✅

**Solution**: Unbounded worker pool with multiprocessing
- **Worker count**: `subfolder_count` (no upper limit)
- **No cap**: Let OS manage resources
- **Multiprocessing**: Bypasses Python GIL for CPU-bound AST parsing
- **Grouping**: Files in same subfolder go to same worker (cache locality)

---

### Gap #6: mtime Reliability ✅

**Solution**: Use `mtime` for change detection (simple and fast)
- **Incremental indexing**: Check `mtime` to detect file changes
- **Simple**: No hashing overhead
- **Trade-off**: May miss changes if mtime is manipulated (rare in practice)
- **Benefit**: Fast incremental updates

---

### Gap #7: Corrupted Database ✅

**Solution**: Auto-detection and recovery

```python
class DatabaseStore:
    def _ensure_schema(self):
        try:
            # Test DB integrity
            self.conn.execute("PRAGMA integrity_check")
        except sqlite3.DatabaseError:
            logger.warning("Database corrupted, rebuilding...")
            self._rebuild_database()
```

**Recovery Strategy**:
1. Detect corruption on startup (`PRAGMA integrity_check`)
2. Backup corrupted DB to `.via/index.db.backup`
3. Create fresh database
4. Re-index all files
5. Log warning to user

---

### Gap #8: Index Validation Command ✅

**Solution**: Add `via index --validate`

```python
def validate_index(db: DatabaseStore) -> ValidationReport:
    """
    Check index health

    Checks:
    - Stale entries (files deleted from disk)
    - Invalid byte offsets (out of bounds)
    - Orphaned entries (file_id references missing files)
    - Parse errors logged but not marked
    """
```

---

### Gap #9: Index Statistics Command ✅

**Solution**: Add `via index --stats`

```python
def get_index_stats(db: DatabaseStore) -> IndexStats:
    """
    Generate index statistics

    Returns:
    - Database size, location, last updated
    - File counts (total, parsed, unparsed, oversized)
    - Entity counts (functions, classes, imports, etc.)
    - Performance metrics (avg parse time, last run duration)
    """
```

---

### Gap #10: Relative vs Absolute Paths ✅

**Solution**: Store relative paths with metadata table
- `files.path`: Relative to index root
- `metadata` table stores `index_root` (absolute)
- **Benefits**: Portable, smaller DB, easier nested index reasoning

---

### Gap #11: User Documentation ✅

**Solution**: Defer to @Oracle post-architecture
- @Oracle will create `docs/CLI_REFERENCE.md`
- Exit codes: 0=success, 1=partial (some errors), 2=fatal
- Help text specification in CLI layer

---

### Gap #12: Testing Strategy ✅

**Solution**: Defer to @Trin
- Edge cases (empty dirs, permissions, huge files)
- Concurrency (race conditions, parallel indexing)
- Cross-platform (Windows, Linux, macOS)
- .gitignore parsing correctness

---

### Gap #13: Pluggable Parser Architecture ✅

**Solution**: ParserABC + ParserRegistry (see sections 2.3.1, 2.3.4)
- Abstract base class defines interface
- Registry pattern for discovery
- Built-in parsers: Python, Markdown
- Future: Plugin loading from `~/.via/parsers/`

---

### Gap #14: Database Migrations ✅

**Solution**: `schema_migrations` table + migration framework

```python
class MigrationManager:
    """Handle schema migrations"""

    def migrate(self, from_version: int, to_version: int):
        """Apply migrations sequentially"""
        for version in range(from_version + 1, to_version + 1):
            migration = self._load_migration(version)
            migration.apply(self.conn)
            self._record_migration(version)

class Migration_002(Migration):
    """Example: Add content_hash to files table"""

    def apply(self, conn: sqlite3.Connection):
        conn.execute("ALTER TABLE files ADD COLUMN content_hash TEXT")
        conn.commit()
```

---

## 4. Project Structure

```
via/
├── via/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── index_command.py     # via index
│   │   ├── query_command.py     # via query (future)
│   │   └── daemon_command.py    # via daemon start/stop/status
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── indexing_service.py  # Core indexing orchestration
│   │   ├── watch_service.py     # Daemon + watchdog
│   │   └── nested_index.py      # Nested index coordinator
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py              # ParserABC
│   │   ├── registry.py          # ParserRegistry
│   │   ├── python_parser.py     # Python AST parser
│   │   └── markdown_parser.py   # Markdown heading parser
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── discovery.py         # File discovery + .gitignore
│   │   └── workers.py           # Worker pool
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.py            # Schema definitions
│   │   ├── store.py             # DatabaseStore
│   │   └── migrations.py        # Migration framework
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py           # Log setup + rotation
│       ├── signals.py           # Signal handlers
│       └── validation.py        # Index validation
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── CLI_REFERENCE.md         # User docs (TBD by @Oracle)
│   └── ARCHITECTURE.md          # This file
│
├── pyproject.toml               # Project config + dependencies
└── README.md
```

---

## 5. Implementation Phases

### Phase 1: Core Indexing (MVP)
**Goal**: Basic indexing works

**Tasks**:
1. Database schema + migrations
2. Python parser (functions, classes, imports)
3. File discovery + .gitignore support
4. Basic CLI (`via index <dir>`)
5. Worker pool for parallelization
6. Unit tests

**Deliverable**: `via index .` works and creates `.via/index.db`

---

### Phase 2: Watch Mode
**Goal**: Daemon mode works

**Tasks**:
1. WatchService + watchdog integration
2. Daemon lifecycle (start/stop/status)
3. PID file management
4. Log rotation
5. Signal handling (HUP, INT, TERM)

**Deliverable**: `via index -w` keeps index up-to-date

---

### Phase 3: Nested Indexes
**Goal**: Hierarchical indexing works

**Tasks**:
1. NestedIndexCoordinator
2. `.via/watch` marker detection
3. Hierarchical query support
4. Integration tests

**Deliverable**: Nested indexes discovered and queried

---

### Phase 4: Polish
**Goal**: Production-ready

**Tasks**:
1. `--validate` and `--stats` commands
2. Markdown parser
3. Content hash for change detection
4. Error recovery (corrupted DB)
5. User documentation (@Oracle)
6. Cross-platform testing (@Trin)

---

## 6. Key Architectural Decisions

### Decision 1: Multiprocessing over Threading
**Rationale**: AST parsing is CPU-bound, needs true parallelism
**Trade-off**: Higher memory, but better performance on multi-core

---

### Decision 2: File-based IPC for Nested Indexes
**Rationale**: Simple, no network sockets or complex protocols
**Trade-off**: Slight race conditions, but acceptable (eventual consistency)

---

### Decision 3: Relative Paths in Database
**Rationale**: Portability (move project directory without breaking index)
**Trade-off**: Need metadata table for absolute root

---

### Decision 4: mtime for Change Detection
**Rationale**: Simple and fast, no hashing overhead
**Trade-off**: May miss changes if mtime manipulated (rare in practice)

---

### Decision 5: No AST Caching in Database
**Rationale**: Byte offsets allow on-demand parsing, lighter DB
**Trade-off**: Slight performance hit on queries (negligible for most use cases)

---

### Decision 6: Foreground Watch Mode Only
**Rationale**: Simpler implementation, no daemon management complexity
**Trade-off**: User must keep terminal open, but can use tmux/screen

---

### Decision 7: Unbounded Worker Pool
**Rationale**: Let OS manage resources, maximize parallelism
**Trade-off**: May spawn many workers on large codebases, but OS will handle it

---

## 7. Decisions Confirmed

1. ✅ **Watch Mode**: `via index -w` only (foreground, no daemon)
2. ✅ **Worker Pool**: Unbounded (1 per subfolder, no cap)
3. ✅ **Change Detection**: mtime only (no content hashing)

---

## 8. Next Steps

1. **@Oracle**: Review architecture, record key decisions in DECISIONS.md
2. **@Neo**: Begin Phase 1 implementation (database schema + Python parser)
3. **@Trin**: Plan test strategy for Phase 1
4. **@User**: Approve architecture and answer open questions

---

**Morpheus's Signature**: Architecture reviewed and approved for implementation. All Oracle gaps addressed. Ready for build phase.
