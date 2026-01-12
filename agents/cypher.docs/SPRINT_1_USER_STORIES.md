# Sprint 1: User Stories - Core Indexing MVP

**Sprint Goal**: Deliver basic `via index <dir>` command that creates a searchable SQLite index of Python files

**Sprint Duration**: TBD by team
**Target**: Phase 1 from VIA_ARCHITECTURE.md

---

## Epic: As a developer, I want to index my Python codebase so I can search it later

---

### Story 1: Database Schema Setup

**As a** developer
**I want** the system to create a `.via/index.db` database
**So that** my code metadata can be stored persistently

**Acceptance Criteria**:
- [ ] Running `via index .` creates `.via/` directory if it doesn't exist
- [ ] Creates `index.db` with all tables from architecture schema
- [ ] Includes `metadata` table with `index_root` and `schema_version`
- [ ] Includes `schema_migrations` table for versioning
- [ ] Files table uses relative paths
- [ ] Functions table includes `class_id` for methods
- [ ] All entity tables have `byte_offset` and `byte_length` columns
- [ ] All indexes are created (idx_functions_name, idx_classes_name, etc.)

**Technical Notes**:
- Implementation: `via/db/schema.py` + `via/db/store.py`
- Reference: VIA_ARCHITECTURE.md section 2.5.1

**Story Points**: 3

---

### Story 2: File Discovery with .gitignore Support

**As a** developer
**I want** the indexer to honor my `.gitignore` rules
**So that** build artifacts and dependencies aren't indexed

**Acceptance Criteria**:
- [ ] Recursively walks directory tree from specified root
- [ ] Respects `.gitignore` in root directory
- [ ] Respects `.gitignore` in all subdirectories
- [ ] Excludes `__pycache__/`, `.pyc`, `.pyo` by default
- [ ] Indexes `.py`, `.pyx`, `.pyi` files
- [ ] Records ALL files in database (metadata), marks which are parsed
- [ ] Flags files > 10MB as oversized, includes in DB but doesn't parse

**Technical Notes**:
- Use `pathspec` or `gitignore_parser` library
- Implementation: `via/core/discovery.py`
- Reference: VIA_ARCHITECTURE.md section 2.4, REQ-1.2, REQ-1.3

**Story Points**: 5

---

### Story 3: Python AST Parser

**As a** developer
**I want** Python files to be parsed using AST
**So that** functions, classes, and imports are extracted

**Acceptance Criteria**:
- [ ] Parses `.py` files using Python's `ast` module
- [ ] Extracts functions with: name, line numbers, byte offset/length, args, decorators, docstring
- [ ] Extracts classes with: name, line numbers, byte offset/length, bases, decorators, docstring
- [ ] Extracts imports: module, name, alias, line number, byte offset/length
- [ ] Extracts globals: name, value (if literal), type hint, line number, byte offset/length
- [ ] Methods are linked to their class via `class_id`
- [ ] Handles parse errors gracefully (log and continue)
- [ ] All byte offsets are accurate for file seeking

**Technical Notes**:
- Implementation: `via/parsers/python_parser.py`
- Must implement `ParserABC` interface
- Reference: VIA_ARCHITECTURE.md section 2.3.2

**Story Points**: 8

---

### Story 4: Parser Registry

**As a** developer
**I want** parsers to be pluggable
**So that** new languages can be added later (e.g., JavaScript)

**Acceptance Criteria**:
- [ ] Defines `ParserABC` abstract base class
- [ ] Has `can_parse(file_path)`, `parse(file_path, content)`, `get_supported_extensions()` methods
- [ ] `ParserRegistry` registers built-in parsers (PythonParser)
- [ ] Registry can find appropriate parser for a given file
- [ ] Returns `None` if no parser available for file type

**Technical Notes**:
- Implementation: `via/parsers/base.py`, `via/parsers/registry.py`
- Reference: VIA_ARCHITECTURE.md sections 2.3.1, 2.3.4

**Story Points**: 3

---

### Story 5: Indexing Service

**As a** developer
**I want** an orchestration service to coordinate indexing
**So that** file discovery, parsing, and database updates work together

**Acceptance Criteria**:
- [ ] `IndexingService` accepts root directory and database path
- [ ] Discovers files using file discovery component
- [ ] Gets appropriate parser from registry for each file
- [ ] Parses files and extracts entities
- [ ] Stores entities in database (batch inserts for performance)
- [ ] Returns `IndexResult` with counts (files indexed, functions found, etc.)
- [ ] Handles errors gracefully (continues on parse errors)

**Technical Notes**:
- Implementation: `via/services/indexing_service.py`
- Reference: VIA_ARCHITECTURE.md section 2.2.1

**Story Points**: 5

---

### Story 6: Multiprocessing Worker Pool

**As a** developer
**I want** indexing to use multiple CPU cores
**So that** large codebases index quickly

**Acceptance Criteria**:
- [ ] Creates worker pool using `multiprocessing.Pool`
- [ ] Worker count = number of top-level subfolders (unbounded)
- [ ] Groups files by subfolder (all files in same folder go to same worker)
- [ ] Each worker parses its assigned files independently
- [ ] Results are aggregated and returned to main process
- [ ] Handles worker failures gracefully

**Technical Notes**:
- Implementation: `via/core/workers.py`
- Use multiprocessing (not threading) for CPU-bound AST parsing
- Reference: VIA_ARCHITECTURE.md section 2.4.1

**Story Points**: 5

---

### Story 7: CLI Command - Basic Indexing

**As a** developer
**I want** to run `via index <dir>`
**So that** I can index a directory from the command line

**Acceptance Criteria**:
- [ ] CLI accepts `via index <dir>` (defaults to current directory if omitted)
- [ ] Parses command line arguments with `argparse`
- [ ] Creates `IndexingService` with specified directory
- [ ] Runs indexing workflow
- [ ] Prints summary on completion (files indexed, functions found, duration)
- [ ] Exit code 0 on success, 1 on partial success (some errors), 2 on fatal error

**Technical Notes**:
- Implementation: `via/cli/index_command.py`, `via/__main__.py`
- Reference: VIA_ARCHITECTURE.md section 2.1

**Story Points**: 3

---

### Story 8: Progress Feedback

**As a** developer
**I want** to see progress during indexing
**So that** I know the tool is working on large codebases

**Acceptance Criteria**:
- [ ] Shows "Indexing: X/Y files (Z%)" during indexing
- [ ] Updates in-place if TTY supports it (overwrite line)
- [ ] Shows final summary with counts and duration
- [ ] Summary includes: files indexed, functions, classes, imports, database size

**Technical Notes**:
- Implementation: `via/services/indexing_service.py` (progress callbacks)
- Reference: VIA_ARCHITECTURE.md REQ-6.1, REQ-6.2

**Story Points**: 2

---

### Story 9: Incremental Indexing

**As a** developer
**I want** the indexer to skip unchanged files
**So that** re-indexing is fast

**Acceptance Criteria**:
- [ ] Checks `mtime` of files in database vs filesystem
- [ ] Skips files where mtime hasn't changed
- [ ] Re-indexes files where mtime is newer
- [ ] Removes database entries for deleted files
- [ ] `--force` flag bypasses mtime check and re-indexes everything

**Technical Notes**:
- Implementation: `via/services/indexing_service.py`
- Uses `files.mtime` column for comparison
- Reference: VIA_ARCHITECTURE.md REQ-8.2, Gap #6

**Story Points**: 3

---

### Story 10: Auto-add .via/ to .gitignore

**As a** developer
**I want** `.via/` automatically added to `.gitignore`
**So that** the index isn't committed to version control

**Acceptance Criteria**:
- [ ] Checks if `.gitignore` exists in root directory
- [ ] If exists, checks if `.via/` is already in it
- [ ] If not present, appends `.via/` to `.gitignore`
- [ ] If `.gitignore` doesn't exist, creates it with `.via/`
- [ ] Handles edge cases (read-only filesystem, permissions errors)

**Technical Notes**:
- Implementation: `via/services/indexing_service.py` or separate utility
- Reference: VIA_ARCHITECTURE.md REQ-2.4

**Story Points**: 2

---

## Story Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| 1 | Database Schema Setup | 3 | P0 (Blocker) |
| 2 | File Discovery with .gitignore | 5 | P0 (Blocker) |
| 3 | Python AST Parser | 8 | P0 (Blocker) |
| 4 | Parser Registry | 3 | P0 (Blocker) |
| 5 | Indexing Service | 5 | P0 (Blocker) |
| 6 | Multiprocessing Worker Pool | 5 | P1 (Important) |
| 7 | CLI Command - Basic Indexing | 3 | P0 (Blocker) |
| 8 | Progress Feedback | 2 | P2 (Nice-to-have) |
| 9 | Incremental Indexing | 3 | P1 (Important) |
| 10 | Auto-add .via/ to .gitignore | 2 | P2 (Nice-to-have) |

**Total Story Points**: 39

**P0 Stories (Must Have)**: 27 points
**P1 Stories (Important)**: 8 points
**P2 Stories (Nice-to-have)**: 4 points

---

## Definition of Done

A story is "Done" when:
- [ ] Code is written and follows Python best practices (PEP-8)
- [ ] Unit tests are written and passing
- [ ] Code is reviewed by team
- [ ] Acceptance criteria are met
- [ ] No known bugs
- [ ] Documented (docstrings, comments where needed)

---

## Out of Scope for Sprint 1

The following features are intentionally deferred:
- ❌ Watch mode (`-w` flag) - Sprint 2
- ❌ Verbosity levels (`-v`, `-vv`, etc.) - Sprint 2
- ❌ `--exclude` patterns - Sprint 2
- ❌ Nested index support - Sprint 3
- ❌ Markdown parsing - Sprint 4
- ❌ `--validate` and `--stats` commands - Sprint 4
- ❌ Log statements extraction - Sprint 4
- ❌ Decorators extraction - Sprint 4

---

## Dependencies

**External Libraries Needed**:
- `pathspec` or `gitignore_parser` - .gitignore parsing
- `argparse` - CLI (stdlib)
- `sqlite3` - Database (stdlib)
- `ast` - Python parsing (stdlib)
- `multiprocessing` - Worker pool (stdlib)

**No external dependencies** beyond one .gitignore library!

---

## Sprint Success Criteria

Sprint 1 is successful when:
1. ✅ User can run `via index /path/to/project`
2. ✅ Creates `.via/index.db` with schema
3. ✅ Discovers Python files (honors .gitignore)
4. ✅ Parses functions, classes, imports, globals
5. ✅ Stores data in SQLite database
6. ✅ Shows progress and summary
7. ✅ Re-running is fast (incremental indexing)
8. ✅ `.via/` is auto-added to `.gitignore`

---

## Notes for Implementation

- Start with Stories 1, 2, 4, 7 in parallel (low coupling)
- Story 3 (Python Parser) is the heaviest - assign to strongest developer
- Story 6 (Worker Pool) can be added later if needed (single-threaded first)
- Story 8 (Progress) is cosmetic - do last
- Focus on P0 stories first, then P1, then P2 if time permits
