# Sprint 1: Detailed Task Breakdown

**Sprint Goal**: Deliver Core Indexing MVP - `via index <dir>` command
**Total Story Points**: 39
**Duration**: TBD by team

---

## 📋 Task Organization

Tasks are organized by story with dependencies clearly marked.
- **[S1.1]** = Story 1, Task 1
- **Depends on**: Shows task dependencies
- **Est**: Estimated hours (rough guide)

---

## Story 1: Database Schema Setup (3 pts)

### [S1.1] Create project structure
- [ ] Create `via/` package directory
- [ ] Create `via/db/` subpackage
- [ ] Create `via/__init__.py` and `via/db/__init__.py`
- [ ] Create `pyproject.toml` with project metadata
- [ ] Setup `.gitignore` for Python project
- **Est**: 0.5h

### [S1.2] Define SQL schema in schema.py
- [ ] Create `via/db/schema.py`
- [ ] Define `metadata` table CREATE statement
- [ ] Define `schema_migrations` table CREATE statement
- [ ] Define `files` table with relative paths (no content_hash)
- [ ] Define `functions` table with `class_id` column
- [ ] Define `classes` table
- [ ] Define `imports` table with byte_offset/byte_length
- [ ] Define `globals` table with byte_offset/byte_length
- [ ] Define `log_statements` table with byte_offset/byte_length
- [ ] Define `md_headings` table
- [ ] Define all indexes (idx_functions_name, idx_classes_name, etc.)
- **Depends on**: [S1.1]
- **Est**: 2h

### [S1.3] Implement DatabaseStore class
- [ ] Create `via/db/store.py`
- [ ] Implement `DatabaseStore.__init__(db_path)`
- [ ] Implement `_ensure_schema()` method
- [ ] Implement `_create_initial_schema()` using schema.py
- [ ] Implement `_get_schema_version()` method
- [ ] Add database integrity check on open
- [ ] Add auto-recovery for corrupted DB (backup + rebuild)
- **Depends on**: [S1.2]
- **Est**: 3h

### [S1.4] Add CRUD methods for files table
- [ ] Implement `insert_file(file_info)` → returns file_id
- [ ] Implement `update_file_mtime(file_id, mtime)`
- [ ] Implement `get_file_by_path(relative_path)` → FileInfo
- [ ] Implement `delete_file(file_id)`
- [ ] Implement `get_stale_files()` → List[file_id] (files in DB but not on disk)
- **Depends on**: [S1.3]
- **Est**: 2h

### [S1.5] Add CRUD methods for entity tables
- [ ] Implement `insert_function(function_info)`
- [ ] Implement `insert_class(class_info)`
- [ ] Implement `insert_import(import_info)`
- [ ] Implement `insert_global(global_info)`
- [ ] Implement batch insert methods for performance
- [ ] Implement `delete_entities_for_file(file_id)` (cascading delete)
- **Depends on**: [S1.4]
- **Est**: 3h

### [S1.6] Unit tests for database layer
- [ ] Test schema creation
- [ ] Test metadata table initialization
- [ ] Test file CRUD operations
- [ ] Test entity CRUD operations
- [ ] Test batch inserts
- [ ] Test database recovery (corruption handling)
- **Depends on**: [S1.5]
- **Est**: 2h

**Story 1 Total**: ~12.5h

---

## Story 2: File Discovery with .gitignore Support (5 pts)

### [S2.1] Setup pathspec dependency
- [ ] Add `pathspec` to `pyproject.toml` dependencies
- [ ] Document why pathspec over gitignore_parser (better maintained)
- **Depends on**: [S1.1]
- **Est**: 0.5h

### [S2.2] Create GitignoreWalker class
- [ ] Create `via/core/` package
- [ ] Create `via/core/discovery.py`
- [ ] Implement `GitignoreWalker.__init__(root_dir)`
- [ ] Implement `_load_gitignore(directory)` → PathSpec
- [ ] Implement logic to find and load `.gitignore` in all subdirectories
- [ ] Cache loaded PathSpec objects for performance
- **Depends on**: [S2.1]
- **Est**: 3h

### [S2.3] Implement file walking
- [ ] Implement `walk()` generator method
- [ ] Use `os.walk()` for directory traversal
- [ ] Apply `.gitignore` filters at each level
- [ ] Exclude `__pycache__/`, `.pyc`, `.pyo` by default
- [ ] Yield `(file_path, file_stat)` tuples
- **Depends on**: [S2.2]
- **Est**: 2h

### [S2.4] Add file filtering logic
- [ ] Implement `FileFilter` class
- [ ] Filter by extension (.py, .pyx, .pyi)
- [ ] Check file size (flag if > 10MB)
- [ ] Return `FileInfo(path, size, mtime, oversized, language)`
- **Depends on**: [S2.3]
- **Est**: 1.5h

### [S2.5] Unit tests for file discovery
- [ ] Test .gitignore parsing (root and subdirectories)
- [ ] Test default exclusions (__pycache__, .pyc)
- [ ] Test file size detection (>10MB)
- [ ] Test extension filtering
- [ ] Test on fixture directory with various .gitignore patterns
- **Depends on**: [S2.4]
- **Est**: 3h

**Story 2 Total**: ~10h

---

## Story 3: Python AST Parser (8 pts)

### [S3.1] Create ParsedEntity data class
- [ ] Create `via/parsers/` package
- [ ] Create `via/parsers/base.py`
- [ ] Define `ParsedEntity` dataclass with type, name, line_start, line_end, byte_offset, byte_length, metadata
- [ ] Define entity types: 'function', 'class', 'import', 'global'
- **Depends on**: [S1.1]
- **Est**: 1h

### [S3.2] Implement byte offset calculation
- [ ] Create utility function `calculate_byte_offset(node, content)` → (offset, length)
- [ ] Use AST node's lineno, end_lineno, col_offset, end_col_offset
- [ ] Convert line/col to byte positions in file content
- [ ] Handle edge cases (multiline strings, comments)
- **Depends on**: [S3.1]
- **Est**: 2h

### [S3.3] Implement function extraction
- [ ] Create `via/parsers/python_parser.py`
- [ ] Create `PythonParser` class
- [ ] Implement `_parse_function(node, content)` → ParsedEntity
- [ ] Extract name, args (names, defaults, type hints), decorators, docstring
- [ ] Calculate byte offsets
- [ ] Handle async functions
- **Depends on**: [S3.2]
- **Est**: 3h

### [S3.4] Implement class extraction
- [ ] Implement `_parse_class(node, content)` → ParsedEntity
- [ ] Extract name, bases, decorators, docstring
- [ ] Calculate byte offsets
- [ ] Link methods to class (store class context)
- **Depends on**: [S3.3]
- **Est**: 2h

### [S3.5] Implement import extraction
- [ ] Implement `_parse_import(node, content)` → ParsedEntity
- [ ] Handle `import X` statements
- [ ] Handle `from X import Y` statements
- [ ] Handle `import X as Y` aliases
- [ ] Calculate byte offsets
- **Depends on**: [S3.2]
- **Est**: 1.5h

### [S3.6] Implement global extraction
- [ ] Implement `_parse_global(node, content)` → ParsedEntity
- [ ] Detect module-level assignments
- [ ] Extract variable name
- [ ] Extract value if literal (str, int, bool, None)
- [ ] Extract type hint if present
- [ ] Calculate byte offsets
- **Depends on**: [S3.2]
- **Est**: 2h

### [S3.7] Implement main parse() method
- [ ] Implement `parse(file_path, content)` → List[ParsedEntity]
- [ ] Use `ast.parse()` to get AST
- [ ] Walk AST using `ast.walk()` or custom visitor
- [ ] Call extraction methods for each node type
- [ ] Handle parse errors gracefully (catch SyntaxError, log and return empty list)
- [ ] Track class context for method linking
- **Depends on**: [S3.3, S3.4, S3.5, S3.6]
- **Est**: 3h

### [S3.8] Unit tests for Python parser
- [ ] Test function extraction (simple, async, with decorators, with args)
- [ ] Test class extraction (simple, with inheritance, with methods)
- [ ] Test import extraction (various forms)
- [ ] Test global extraction (various types)
- [ ] Test byte offset accuracy (random seeking)
- [ ] Test parse error handling (malformed Python)
- [ ] Test method-to-class linking
- **Depends on**: [S3.7]
- **Est**: 4h

**Story 3 Total**: ~18.5h

---

## Story 4: Parser Registry (3 pts)

### [S4.1] Define ParserABC abstract class
- [ ] Add `ParserABC` to `via/parsers/base.py`
- [ ] Define abstract methods: `can_parse()`, `parse()`, `get_supported_extensions()`
- [ ] Add docstrings with interface contract
- **Depends on**: [S3.1]
- **Est**: 1h

### [S4.2] Update PythonParser to implement ParserABC
- [ ] Make `PythonParser` inherit from `ParserABC`
- [ ] Implement `can_parse(file_path)` → check for .py/.pyx/.pyi extension
- [ ] Implement `get_supported_extensions()` → return ['.py', '.pyx', '.pyi']
- [ ] Ensure `parse()` matches ABC signature
- **Depends on**: [S4.1, S3.7]
- **Est**: 1h

### [S4.3] Implement ParserRegistry
- [ ] Create `via/parsers/registry.py`
- [ ] Create `ParserRegistry` class
- [ ] Implement `register(parser: ParserABC)` method
- [ ] Implement `get_parser(file_path)` → Optional[ParserABC]
- [ ] Implement `_register_builtin_parsers()` (auto-register PythonParser)
- [ ] Handle case where no parser found (return None)
- **Depends on**: [S4.2]
- **Est**: 1.5h

### [S4.4] Unit tests for parser registry
- [ ] Test parser registration
- [ ] Test parser lookup by file extension
- [ ] Test case where no parser available
- [ ] Test builtin parser auto-registration
- **Depends on**: [S4.3]
- **Est**: 1.5h

**Story 4 Total**: ~5h

---

## Story 5: Indexing Service (5 pts)

### [S5.1] Define IndexResult dataclass
- [ ] Create `via/services/` package
- [ ] Create `via/services/indexing_service.py`
- [ ] Define `IndexResult` dataclass with: files_indexed, files_parsed, files_oversized, functions_found, classes_found, imports_found, globals_found, errors, duration
- **Depends on**: [S1.1]
- **Est**: 0.5h

### [S5.2] Implement IndexingService class
- [ ] Create `IndexingService` class
- [ ] Implement `__init__(root_dir, db_path)`
- [ ] Initialize DatabaseStore, GitignoreWalker, ParserRegistry
- [ ] Store root_dir as absolute path
- **Depends on**: [S1.5, S2.4, S4.3]
- **Est**: 1h

### [S5.3] Implement file discovery phase
- [ ] Implement `_discover_files()` → List[FileInfo]
- [ ] Use GitignoreWalker to walk directory
- [ ] Apply FileFilter to get FileInfo objects
- [ ] Return list of files to index
- **Depends on**: [S5.2]
- **Est**: 1h

### [S5.4] Implement parsing phase
- [ ] Implement `_parse_files(files)` → Dict[file_id, List[ParsedEntity]]
- [ ] For each file, get parser from registry
- [ ] If no parser, mark file as unparsed in DB
- [ ] If parser available, parse file and collect entities
- [ ] Handle parse errors (log and continue)
- [ ] Return mapping of file_id to entities
- **Depends on**: [S5.3]
- **Est**: 2h

### [S5.5] Implement database update phase
- [ ] Implement `_update_database(files, entities)`
- [ ] Insert/update files in database (with relative paths)
- [ ] For each file, delete old entities (if re-indexing)
- [ ] Batch insert entities for performance
- [ ] Use transactions for atomicity
- [ ] Track counts for IndexResult
- **Depends on**: [S5.4]
- **Est**: 2h

### [S5.6] Implement main index() method
- [ ] Implement `index(progress_callback=None)` → IndexResult
- [ ] Call discovery, parsing, database update phases in sequence
- [ ] Measure duration
- [ ] Call progress_callback after each phase (if provided)
- [ ] Return IndexResult with all counts
- **Depends on**: [S5.3, S5.4, S5.5]
- **Est**: 1.5h

### [S5.7] Unit tests for indexing service
- [ ] Test end-to-end indexing on fixture project
- [ ] Test with various file types (.py, .pyx, .md, .txt)
- [ ] Test with .gitignore exclusions
- [ ] Test with parse errors (malformed Python)
- [ ] Test IndexResult accuracy
- [ ] Test progress callbacks
- **Depends on**: [S5.6]
- **Est**: 3h

**Story 5 Total**: ~11h

---

## Story 6: Multiprocessing Worker Pool (5 pts)

### [S6.1] Create WorkerPool class
- [ ] Create `via/core/workers.py`
- [ ] Create `WorkerPool` class
- [ ] Implement `__init__(worker_count=None)` (None = auto)
- [ ] Implement `_auto_worker_count()` → count subfolders (unbounded)
- **Depends on**: [S1.1]
- **Est**: 1h

### [S6.2] Implement file grouping by subfolder
- [ ] Implement `_group_files_by_subfolder(files)` → Dict[subfolder, List[files]]
- [ ] Group files by their top-level parent directory
- [ ] Ensure all files in same subfolder go to same worker
- **Depends on**: [S6.1]
- **Est**: 1.5h

### [S6.3] Implement worker function
- [ ] Create module-level `_parse_file_worker(file_path, parser)` function
- [ ] Must be picklable (top-level function, not nested)
- [ ] Parse file using provided parser
- [ ] Return (file_path, entities, error) tuple
- [ ] Handle exceptions and return error info
- **Depends on**: [S4.3, S3.7]
- **Est**: 1h

### [S6.4] Implement pool execution
- [ ] Implement `map_files_to_workers(files, parse_func)` → List[ParseResult]
- [ ] Create `multiprocessing.Pool` with calculated worker count
- [ ] Use `pool.map()` or `pool.starmap()` for parallel execution
- [ ] Aggregate results from all workers
- [ ] Handle worker failures gracefully
- [ ] Close and join pool properly
- **Depends on**: [S6.2, S6.3]
- **Est**: 2h

### [S6.5] Integrate with IndexingService
- [ ] Update `IndexingService._parse_files()` to use WorkerPool
- [ ] Pass parser and files to worker pool
- [ ] Handle results (successful parses and errors)
- **Depends on**: [S6.4, S5.4]
- **Est**: 1.5h

### [S6.6] Unit tests for worker pool
- [ ] Test worker count calculation
- [ ] Test file grouping by subfolder
- [ ] Test parallel parsing (mock files)
- [ ] Test worker failure handling
- [ ] Test performance improvement (time single vs multi)
- **Depends on**: [S6.5]
- **Est**: 2h

**Story 6 Total**: ~9h

---

## Story 7: CLI Command - Basic Indexing (3 pts)

### [S7.1] Setup CLI structure
- [ ] Create `via/cli/` package
- [ ] Create `via/__main__.py` as entry point
- [ ] Setup argparse with `via` as main command
- [ ] Add `index` subcommand parser
- **Depends on**: [S1.1]
- **Est**: 1h

### [S7.2] Implement index command arguments
- [ ] Create `via/cli/index_command.py`
- [ ] Create `IndexCommand` class
- [ ] Add `<dir>` positional argument (default=current directory)
- [ ] Add argument validation (check directory exists)
- [ ] Convert to absolute path
- **Depends on**: [S7.1]
- **Est**: 1h

### [S7.3] Implement index execution
- [ ] Implement `run(args)` method
- [ ] Create `IndexingService` with specified directory
- [ ] Call `index()` method
- [ ] Return exit code (0=success, 1=partial, 2=fatal)
- **Depends on**: [S7.2, S5.6]
- **Est**: 1h

### [S7.4] Implement summary output
- [ ] Print indexing summary after completion
- [ ] Show: files indexed, functions found, classes found, imports, duration
- [ ] Show database location and size
- [ ] If errors, show count and suggest checking logs
- **Depends on**: [S7.3]
- **Est**: 1h

### [S7.5] Add entry point configuration
- [ ] Update `pyproject.toml` with console_scripts entry point
- [ ] Configure `via = via.__main__:main`
- [ ] Test installation with `pip install -e .`
- [ ] Test running `via index .`
- **Depends on**: [S7.4]
- **Est**: 0.5h

### [S7.6] Integration tests for CLI
- [ ] Test `via index .` on fixture project
- [ ] Test with non-existent directory (error handling)
- [ ] Test exit codes
- [ ] Test summary output format
- **Depends on**: [S7.5]
- **Est**: 2h

**Story 7 Total**: ~6.5h

---

## Story 8: Progress Feedback (2 pts)

### [S8.1] Implement progress callback interface
- [ ] Define `ProgressCallback` protocol/type
- [ ] Takes (phase: str, current: int, total: int, message: str)
- **Depends on**: [S5.6]
- **Est**: 0.5h

### [S8.2] Add progress calls to IndexingService
- [ ] Call callback at start of each phase (discovery, parsing, database update)
- [ ] Call callback during file iteration (every N files)
- [ ] Call callback on completion with final counts
- **Depends on**: [S8.1]
- **Est**: 1h

### [S8.3] Implement CLI progress display
- [ ] Create `ProgressReporter` class
- [ ] Show "Indexing: X/Y files (Z%)" with in-place update
- [ ] Use `\r` for terminal overwrite (if TTY)
- [ ] Fall back to line-by-line if not TTY
- **Depends on**: [S8.2]
- **Est**: 1.5h

### [S8.4] Test progress display
- [ ] Test on small fixture (verify counts)
- [ ] Test on large fixture (verify updates)
- [ ] Test TTY vs non-TTY output
- **Depends on**: [S8.3]
- **Est**: 1h

**Story 8 Total**: ~4h

---

## Story 9: Incremental Indexing (3 pts)

### [S9.1] Add mtime comparison logic
- [ ] In `IndexingService._discover_files()`, check DB for existing file
- [ ] Compare filesystem mtime with DB mtime
- [ ] Skip file if mtime unchanged (unless --force)
- [ ] Re-index if mtime newer
- **Depends on**: [S5.3, S1.4]
- **Est**: 2h

### [S9.2] Implement stale file cleanup
- [ ] In `IndexingService`, detect files in DB but not on filesystem
- [ ] Delete stale files and their entities from database
- [ ] Report count in IndexResult
- **Depends on**: [S9.1]
- **Est**: 1h

### [S9.3] Add --force flag to CLI
- [ ] Add `--force` argument to index command
- [ ] Pass to IndexingService
- [ ] Bypass mtime check if --force enabled
- **Depends on**: [S7.2]
- **Est**: 0.5h

### [S9.4] Test incremental indexing
- [ ] Test: index, modify file, re-index (should only re-parse modified)
- [ ] Test: index, delete file, re-index (should remove from DB)
- [ ] Test: index, no changes, re-index (should be fast)
- [ ] Test: --force flag (should re-index everything)
- **Depends on**: [S9.1, S9.2, S9.3]
- **Est**: 2h

**Story 9 Total**: ~5.5h

---

## Story 10: Auto-add .via/ to .gitignore (2 pts)

### [S10.1] Implement gitignore check/update
- [ ] Create utility function `ensure_via_in_gitignore(root_dir)`
- [ ] Check if `.gitignore` exists in root
- [ ] If exists, check if `.via/` already present
- [ ] If not present, append `.via/` with comment
- [ ] If `.gitignore` doesn't exist, create it with `.via/`
- [ ] Handle permissions errors gracefully
- **Depends on**: [S1.1]
- **Est**: 1.5h

### [S10.2] Integrate with IndexingService
- [ ] Call `ensure_via_in_gitignore()` at start of `index()`
- [ ] Log action if .gitignore was modified
- **Depends on**: [S10.1, S5.6]
- **Est**: 0.5h

### [S10.3] Test .gitignore auto-add
- [ ] Test with no .gitignore (creates new)
- [ ] Test with existing .gitignore without .via/ (appends)
- [ ] Test with existing .gitignore with .via/ (no change)
- [ ] Test with read-only filesystem (graceful failure)
- **Depends on**: [S10.2]
- **Est**: 1h

**Story 10 Total**: ~3h

---

## 📊 Sprint Summary

| Story | Title | Tasks | Est Hours |
|-------|-------|-------|-----------|
| S1 | Database Schema Setup | 6 | 12.5h |
| S2 | File Discovery | 5 | 10h |
| S3 | Python AST Parser | 8 | 18.5h |
| S4 | Parser Registry | 4 | 5h |
| S5 | Indexing Service | 7 | 11h |
| S6 | Worker Pool | 6 | 9h |
| S7 | CLI Command | 6 | 6.5h |
| S8 | Progress Feedback | 4 | 4h |
| S9 | Incremental Indexing | 4 | 5.5h |
| S10 | Auto .gitignore | 3 | 3h |

**Total Tasks**: 53
**Total Estimated Hours**: ~85h

---

## 🔗 Critical Path

Minimum viable path to working `via index .`:

1. **[S1.1-S1.5]** → Database layer (10h)
2. **[S2.1-S2.4]** → File discovery (7.5h)
3. **[S3.1-S3.7]** → Python parser (14.5h)
4. **[S4.1-S4.3]** → Parser registry (3.5h)
5. **[S5.1-S5.6]** → Indexing service (8h)
6. **[S7.1-S7.4]** → CLI (4h)

**Critical Path Total**: ~47.5h (can be parallelized with multiple developers)

---

## 🎯 Recommended Task Assignment Strategy

**Week 1** (Parallel tracks):
- **Track A**: Database (S1) → Indexing Service (S5)
- **Track B**: File Discovery (S2) → CLI (S7)
- **Track C**: Parser (S3, S4)

**Week 2** (Integration):
- Integrate all components
- Add Worker Pool (S6)
- Add Progress (S8)
- Add Incremental (S9)
- Add .gitignore (S10)
- Testing and bug fixes

---

## ✅ Definition of Done (per task)

- [ ] Code written and follows PEP-8
- [ ] Unit tests written (where applicable)
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documented (docstrings)
- [ ] No known bugs

---

## 📝 Notes

- **Story 3 (Python Parser)** is the heaviest - assign to most experienced developer
- **Stories 1, 2, 4** can be done in parallel (low coupling)
- **Story 6 (Worker Pool)** can be added at end if time is short (single-threaded works)
- **Stories 8, 9, 10** are polish - nice-to-have if time permits
- All tests should use fixtures in `tests/fixtures/` directory
