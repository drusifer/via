# VIA - Index Command Specification

**Project**: Via - Python Codebase Indexing & Query Tool
**Component**: `via index` command
**Version**: 0.1.0
**Date**: 2026-01-10
**Status**: Draft

---

## Overview

The `via index` command builds and maintains a searchable index of Python codebases, enabling fast querying and navigation. It walks directory trees, parses Python files using AST APIs, and stores structured metadata in a SQLite database.

---

## Command Syntax

```bash
via index [-w] [-v|-vv|-vvv|-vvvv] [--force] [--exclude PATTERN] [<dir>]
```

**Arguments**:
- `<dir>` (optional): Target directory to index (defaults to current directory)

**Flags**:
- `-w, --watch`: Enable file watching mode (monitors for changes via watchdog)
- `-v, --verbose`: Verbosity levels (1-4 v's for increasing detail)
- `--force`: Force full rebuild of index even if files are unchanged
- `--exclude PATTERN`: Additional exclude patterns (beyond .gitignore)

---

## Core Requirements

### 1. Directory Walking & File Discovery

**REQ-1.1**: Recursively walk directory tree using `os.walk()` or equivalent

**REQ-1.2**: Honor `.gitignore` rules (use `pathspec` or `gitignore_parser` library)
  - Support `.gitignore` in ALL subdirectories (not just root)
  - If no `.gitignore` exists, index all files matching supported types

**REQ-1.3**: File indexing strategy:
  - **Index ALL file types** (not .gitignored) in the `files` table with metadata (path, size, mtime)
  - **Parse only supported types**: `.py`, `.pyx`, `.pyi`, `.md` (Phase 1)
  - Keep architecture flexible for future types: `.js`, `.sql`, `.json`, `.yml`, `.ini`, etc.

**REQ-1.4**: Exclude patterns:
  - `__pycache__/` directories
  - `.pyc`, `.pyo` compiled files
  - Files/dirs excluded by `.gitignore`
  - Custom patterns via `--exclude` flag

**REQ-1.5**: File size limits:
  - Skip parsing files > 10MB
  - Track oversized files in separate table or flag in `files` table
  - Include file stats in index regardless of parse status

---

### 2. Index Storage

**REQ-2.1**: Store index in `.via/index.db` (SQLite database) in target directory root

**REQ-2.2**: Database schema:
  - Metadata tables for fast querying (files, functions, classes, imports, etc.)
  - **NO AST caching** in database (parse on-demand using byte offset + length)
  - Store byte offset and length for all entities to enable fast file seeking

**REQ-2.3**: Auto-create `.via/` directory if it doesn't exist

**REQ-2.4**: Automatically add `.via/` to `.gitignore`

**REQ-2.5**: Nested index architecture:
  - One daemon per project root (PID file in `.via/via.pid`)
  - Subfolder watchers create/touch `.via/watch` to signal root daemon to include nested index
  - No watchers above `$HOME` directory
  - Nested indexes provide natural directory-level scoping for queries
  - `$VIA_PATHS` environment variable for cross-tree database access (Phase 2)

---

### 3. Metadata Extraction (Python)

Use Python's `ast` module to parse files and extract:

**REQ-3.1**: **Function Definitions**
  - Name
  - Line number (start, end)
  - Byte offset + byte length (for seeking)
  - Arguments (names, defaults, type hints)
  - Decorators
  - Docstring (if present)

**REQ-3.2**: **Class Definitions**
  - Name
  - Line number (start, end)
  - Byte offset + byte length
  - Base classes (inheritance)
  - Methods (see function definitions)
  - Decorators
  - Docstring

**REQ-3.3**: **Imports**
  - Module names (`import X`)
  - From imports (`from X import Y`)
  - Aliases (`import X as Y`)
  - Line numbers

**REQ-3.4**: **Global Variables/Constants**
  - Variable name
  - Assigned value (if literal)
  - Line number
  - Type hint (if present)

**REQ-3.5**: **Decorators**
  - Decorator name/expression
  - Applied to (function/class reference)
  - Line number

**REQ-3.6**: **Logging/Print Statements**
  - Statement type (`print`, `logging.info`, `logger.debug`, etc.)
  - Arguments (if extractable)
  - Line number

**REQ-3.7**: **Markdown Headings** (from `.md` files)
  - Heading text
  - Level (#, ##, ###, etc.)
  - Line number
  - Byte offset

**REQ-3.8**: Store byte offset + byte length for all entities (enables fast file seeking)

---

### 4. Multi-Language Support (Future)

**REQ-4.1**: Architecture must support pluggable language parsers
**REQ-4.2**: Phase 2 will add JavaScript support
**REQ-4.3**: Use abstraction layer for language-specific parsing logic

---

### 5. Watch Mode (`-w`)

**REQ-5.1**: Use `watchdog` library to monitor file system changes

**REQ-5.2**: On file change/creation/deletion:
  - Re-index ONLY the affected file(s)
  - Update database incrementally (don't rebuild entire index)

**REQ-5.3**: Full re-index triggers:
  - `kill -HUP` signal (if running as daemon)
  - `Ctrl-L` (if running in foreground)
  - Restart of `via index -w`
  - `--force` flag

**REQ-5.4**: Can run as:
  - **Foreground process**: Blocks terminal, shows live logs to stdout
  - **Background daemon**:
    - One daemon per project root
    - PID file at `.via/via.pid`
    - Logs to `.via/index.log` with log rotation
    - No watchers above `$HOME`

**REQ-5.5**: Nested watch support:
  - Subfolder `via index -w` creates/touches `.via/watch` marker
  - Signals root daemon to include nested index
  - Provides directory-level query scoping

---

### 6. Progress & Feedback

**REQ-6.1**: Show progress during indexing:
  - "Indexing: 150/500 files (30%)" or similar
  - Update in-place (overwrite line) if TTY supports it

**REQ-6.2**: Summary on completion:
  ```
  ✓ Indexed 500 files in 2.3s
    - 1,234 functions
    - 456 classes
    - 789 imports
    - Index: .via/index.db (2.1 MB)
  ```

**REQ-6.3**: Verbosity levels (`-v`, `-vv`, `-vvv`, `-vvvv`):
  - No flags: Progress bar + summary only
  - `-v`: Add file names as they're indexed
  - `-vv`: Add counts per file (X functions, Y classes)
  - `-vvv`: Add warnings (parse errors, skipped files)
  - `-vvvv`: Debug mode (full AST parsing details, timing)

---

### 7. Error Handling

**REQ-7.1**: Gracefully handle parse errors:
  - Log warning with filename and line number
  - Continue indexing other files
  - Include in summary: "3 files had parse errors"

**REQ-7.2**: Handle permission errors (unreadable files):
  - Log warning and skip

**REQ-7.3**: Validate directory exists before indexing

**REQ-7.4**: Handle SQLite errors (disk full, corruption, etc.)

---

### 8. Performance & Optimization

**REQ-8.1**: Parallelization:
  - Use 1 worker per subfolder for concurrent indexing
  - Multi-threading or multi-processing based on workload

**REQ-8.2**: Incremental indexing by default:
  - Skip unchanged files (check mtime)
  - Only re-parse modified files
  - `--force` flag bypasses this optimization

**REQ-8.3**: Duplicate tracking:
  - Do NOT deduplicate imports across files
  - Keep all imports for future n-gram duplicate code detection

---

### 9. CLI Flags & Behavior

**REQ-9.1**: `--force` flag:
  - Force full rebuild of index
  - Ignore file modification times
  - Re-parse all files

**REQ-9.2**: `--exclude PATTERN` flag:
  - Additional exclude patterns beyond `.gitignore`
  - Can be specified multiple times
  - Uses glob-style patterns

---

## Database Schema (Draft)

### Tables

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    language TEXT,  -- 'python', 'javascript', 'markdown', null for unparsed
    size_bytes INTEGER,
    mtime REAL,  -- last modified timestamp
    indexed_at REAL,
    parsed BOOLEAN DEFAULT 0,  -- whether file was parsed or just indexed
    oversized BOOLEAN DEFAULT 0  -- true if file > 10MB (skipped parsing)
);

-- Functions table
CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER,
    byte_length INTEGER,
    args TEXT,  -- JSON serialized arguments
    decorators TEXT,  -- JSON array
    docstring TEXT
);

-- Classes table
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER,
    byte_length INTEGER,
    bases TEXT,  -- JSON array of base class names
    decorators TEXT,
    docstring TEXT
);

-- Imports table
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    module TEXT NOT NULL,
    name TEXT,  -- for 'from X import Y'
    alias TEXT,
    line_number INTEGER
);

-- Global variables
CREATE TABLE globals (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    name TEXT NOT NULL,
    value TEXT,  -- if literal/constant
    type_hint TEXT,
    line_number INTEGER
);

-- Logging/print statements
CREATE TABLE log_statements (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    type TEXT,  -- 'print', 'logging.info', etc.
    args TEXT,  -- JSON serialized
    line_number INTEGER
);

-- Markdown headings (for .md files)
CREATE TABLE md_headings (
    id INTEGER PRIMARY KEY,
    file_id INTEGER REFERENCES files(id),
    text TEXT NOT NULL,
    level INTEGER,  -- 1-6 for #, ##, ###, etc.
    line_number INTEGER,
    byte_offset INTEGER
);
```

**Indexes**:
```sql
CREATE INDEX idx_functions_name ON functions(name);
CREATE INDEX idx_classes_name ON classes(name);
CREATE INDEX idx_imports_module ON imports(module);
CREATE INDEX idx_files_path ON files(path);
```

---

## Dependencies

- **pathspec** or **gitignore_parser**: `.gitignore` parsing (supports nested .gitignore files)
- **watchdog**: File system monitoring for watch mode
- **sqlite3**: Built-in (Python stdlib) - database storage
- **ast**: Built-in (Python stdlib) - Python AST parsing
- **logging** with log rotation: For daemon mode logging to `.via/index.log`

---

## Summary of Key Decisions

Based on user answers, the following key architectural decisions have been made:

1. **Universal File Indexing**: Index ALL files (stats only), parse only `.py`, `.pyx`, `.pyi`, `.md`
2. **No AST Caching**: Parse on-demand using byte offsets (lighter database)
3. **Nested Index Architecture**: Directory-scoped indexes with `.via/watch` signaling
4. **Parallelization**: 1 worker per subfolder
5. **Incremental by Default**: Skip unchanged files unless `--force`
6. **Daemon Logging**: `.via/index.log` with rotation
7. **Future n-gram Deduplication**: Keep all imports/code for duplicate detection
8. **10MB Parse Limit**: Track oversized files but include in index
9. **Multi-language Ready**: Pluggable parsers for JS, SQL, YAML, etc. (Phase 2)
10. **Cross-tree Queries**: `$VIA_PATHS` support (Phase 2)

---

## Open Questions - ANSWERED

### File Filtering
1. **Q**: Should we include `.md` files for indexing headings?
   **A**: Yes

2. **Q**: Any other file types for phase 1 besides .py, .pyx, .pyi, .md?
   **A**: potential for more types (.js, .sql, .json,.yml, .ini, many more perhaps) so keep the model flexble .py, and .md are good for now but all files types (not .gitignored) can be included in teh file index just not parsed

3. **Q**: Should we have a max file size limit (e.g., skip files > 10MB)?
   **A**: sure 10 MB sounds big enough but keep a list of files that are too big so I'll know (file stats are includend in the index anyways)

### .gitignore Handling
4. **Q**: Should we support `.gitignore` in subdirectories or just root?
   **A**: All dirs

5. **Q**: What if there's no `.gitignore` file? Index everything in the tree?
   **A**: sure but stick to the file types we support

### Database Storage
6. **Q**: Should AST cache be gzipped/compressed in the database?
   **A**: prob not. with the byte index and length we can read the objects directly from the files on demand.  Let's do ast on demand for now.

7. **Q**: Should we automatically add `.via/` to `.gitignore`, or just recommend it?
   **A**: auto

### Watch Mode Details
8. **Q**: When running as daemon (background), should it create a PID file in `.via/`?
   **A**: No - it will create a pid file at the project root's .via/  In daemon mode there will only be one via instance per project.  Creating watchers in sub folders simply crates (or touches) .via/watch which signals the root via daemon to include a nested index there.  The users $HOME is the limit so no watchers above there and no root watchers.  Nested index provide natural directory level scoping for indexes so that queries are bound to the folder heriarcy.  $VIA_PATHS can provide cross tree dbs if desired (phase 2)

9. **Q**: Should daemon mode log to `.via/index.log` or stdout?
   **A**: log but set up log rolling etc..

10. **Q**: Should we support multiple watch processes for different directories?
    **A**: see above

### Performance & Optimization
11. **Q**: Should we parallelize file indexing (multi-threading/processing)?
    **A**: yes - 1 worker per sub-folder

12. **Q**: Should we deduplicate identical imports across files in the DB?
    **A**: No, they need to be catalogued so we can use the tool to find duplicate code segments (using ngrams)

### CLI Behavior
13. **Q**: Should we add a `--force` flag to rebuild index even if up-to-date?
    **A**: Yes + signal handing and (local web api - phase 2)

14. **Q**: Should indexing be incremental by default (skip unchanged files)?
    **A**: Yes

15. **Q**: Should we support `--exclude` patterns (beyond .gitignore)?
    **A**: Yes See filtering requiremetns

---

## Next Steps (After Questions Answered)

1. @Oracle: Review spec, check for gaps, suggest improvements
2. @Morpheus: Review architecture, plan implementation phases
3. @Neo: Prototype AST extraction + SQLite schema
4. @Trin: Plan test cases for index command
