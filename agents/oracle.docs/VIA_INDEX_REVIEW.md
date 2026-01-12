# Oracle's Review: VIA Index Command Specification

**Reviewer**: Oracle (Knowledge Officer)
**Document**: `agents/cypher.docs/VIA_INDEX_SPEC.md`
**Date**: 2026-01-10 19:25:18
**Status**: APPROVED with Recommendations

---

## Executive Summary

**Overall Assessment**: ✅ **STRONG SPECIFICATION**

The VIA_INDEX_SPEC.md is well-structured, comprehensive, and technically sound. Cypher has done excellent work capturing requirements from user answers. The spec is ready for architectural design with minor clarifications noted below.

**Recommendation**: Proceed to @Morpheus for architecture planning with the following considerations documented.

---

## Strengths

1. **Clear Command Syntax**: Well-defined CLI interface with all flags documented
2. **Comprehensive Requirements**: 9 requirement sections covering all major aspects
3. **Database Schema**: Detailed table definitions with appropriate indexes
4. **Nested Index Architecture**: Innovative directory-scoping approach
5. **Performance Considerations**: Parallelization and incremental indexing built-in
6. **Future-Proofing**: Multi-language support architecture planned
7. **Error Handling**: Comprehensive coverage of failure modes

---

## Technical Feasibility Analysis

### ✅ FEASIBLE - No Blockers

All requirements are technically achievable with Python stdlib + common libraries:
- `ast` module handles Python parsing
- `watchdog` for file monitoring is mature and stable
- `sqlite3` is stdlib and perfect for this use case
- `pathspec`/`gitignore_parser` are well-maintained

### Dependencies Risk Assessment

| Dependency | Maturity | Risk | Notes |
|------------|----------|------|-------|
| `ast` | stdlib | **None** | Stable API |
| `sqlite3` | stdlib | **None** | Rock solid |
| `watchdog` | Mature | **Low** | Widely used, active maintenance |
| `pathspec` | Mature | **Low** | gitignore spec implementation |
| `logging` | stdlib | **None** | Built-in log rotation support |

---

## Gaps & Clarifications Needed

### 1. Nested Index Coordination (Medium Priority)

**Gap**: How do nested indexes communicate with root daemon?

**Current Spec** (REQ-2.5):
- "Subfolder watchers create/touch `.via/watch` to signal root daemon"
- "Nested indexes provide natural directory-level scoping for queries"

**Questions for @Morpheus**:
- How does root daemon discover nested `.via/watch` markers?
- Does it poll? Use inotify? Recursive watchdog?
- What happens if subfolder daemon starts BEFORE root daemon?
- How are nested indexes queried? Do they merge results or stay isolated?

**Recommendation**: @Morpheus should define IPC mechanism and discovery protocol

---

### 2. Database Schema - Missing Elements

#### 2.1 Methods Table (MISSING)

**Issue**: Classes table mentions "Methods (see function definitions)" but there's no explicit methods table or foreign key relationship.

**Options**:
1. **Add `class_id` to `functions` table** (simpler)
   ```sql
   ALTER TABLE functions ADD COLUMN class_id INTEGER REFERENCES classes(id);
   ```
   - Pro: Simple, works for methods
   - Con: Global functions have `NULL` class_id

2. **Separate `methods` table** (normalized)
   ```sql
   CREATE TABLE methods (
       id INTEGER PRIMARY KEY,
       class_id INTEGER REFERENCES classes(id),
       function_id INTEGER REFERENCES functions(id)
   );
   ```
   - Pro: Explicit relationship
   - Con: Extra join for queries

**Recommendation**: Option 1 (add `class_id` to functions) - simpler and sufficient

#### 2.2 Byte Offsets for Functions/Classes

**Issue**: Spec says "Store byte offset + byte length for all entities" but `imports`, `globals`, and `log_statements` tables are missing `byte_offset` and `byte_length` columns.

**Current**:
- ✅ `functions`: Has `byte_offset`, `byte_length`
- ✅ `classes`: Has `byte_offset`, `byte_length`
- ✅ `md_headings`: Has `byte_offset`
- ❌ `imports`: Only `line_number`
- ❌ `globals`: Only `line_number`
- ❌ `log_statements`: Only `line_number`

**Recommendation**: Add `byte_offset` and `byte_length` to imports, globals, and log_statements for consistency

---

### 3. CLI Behavior - `--exclude` Flag Details

**Gap**: How does `--exclude` pattern matching work?

**Current Spec** (REQ-9.2):
- "Uses glob-style patterns"
- "Can be specified multiple times"

**Questions**:
- Does it match file paths or just filenames?
- Is it relative to index root or absolute?
- Examples: `--exclude "*.test.py"` vs `--exclude "tests/**/*.py"`?

**Recommendation**: @Morpheus should define pattern matching semantics (suggest using `pathspec` library for consistency with .gitignore)

---

### 4. Watch Mode - Daemon Lifecycle

**Gap**: How is daemon started/stopped/restarted?

**Current Spec**:
- PID file at `.via/via.pid`
- Logs to `.via/index.log`
- `kill -HUP` triggers re-index

**Missing**:
- How to START daemon? `via index -w &`? Separate `via daemon start`?
- How to STOP daemon? `kill $(cat .via/via.pid)`? `via daemon stop`?
- What if daemon crashes? Auto-restart? Supervisor integration?
- Should there be a `via daemon status` command?

**Recommendation**: Add daemon lifecycle commands to spec or clarify that `-w` handles it

---

### 5. Performance - Parallelization Details

**Gap**: "1 worker per subfolder" needs clarification

**Current Spec** (REQ-8.1):
- "Use 1 worker per subfolder for concurrent indexing"
- "Multi-threading or multi-processing based on workload"

**Questions**:
- What defines a "subfolder"? First-level only? Recursive?
- What if there are 1,000 subfolders? Worker pool limit?
- Threading vs multiprocessing trade-offs not specified
- Python GIL considerations for AST parsing (CPU-bound work)

**Recommendation**: @Morpheus should define worker pool limits and choose threading model (suggest multiprocessing for CPU-bound AST parsing)

---

### 6. Incremental Indexing - mtime Reliability

**Observation**: REQ-8.2 relies on `mtime` for change detection

**Potential Issue**:
- `mtime` can be manipulated (e.g., `touch -t`, git checkout)
- Race conditions if file changes during index

ing
- Symlinks and hard links may confuse mtime checks

**Recommendation**: Consider adding content hash (SHA256) to `files` table for robust change detection. Trade-off: slower initial index, but more reliable incremental updates.

**Suggested Addition**:
```sql
ALTER TABLE files ADD COLUMN content_hash TEXT;  -- SHA256 for change detection
```

---

### 7. Error Recovery - Corrupted Database

**Gap**: What happens if `.via/index.db` is corrupted?

**Current Spec** (REQ-7.4):
- "Handle SQLite errors (disk full, corruption, etc.)"

**Missing**:
- Auto-detection of corruption?
- Automatic rebuild on corruption?
- Backup/recovery strategy?
- User notification?

**Recommendation**: Add requirement for database integrity checks and auto-rebuild on corruption

---

## Suggested Additions

### 8. Index Validation Command

**Suggestion**: Add `via index --validate` command to check index health

**Use Cases**:
- Detect stale entries (files deleted but still in DB)
- Find parse errors
- Verify byte offsets are valid
- Check for orphaned entries

**Benefit**: Helps debug indexing issues and maintain data quality

---

### 9. Index Statistics Command

**Suggestion**: Add `via index --stats` to show index metrics

**Example Output**:
```
Index Statistics:
  Location: /path/to/project/.via/index.db
  Database Size: 2.1 MB
  Last Updated: 2026-01-10 19:00:00

  Files Indexed: 500
    - Parsed: 480 (.py, .md)
    - Unparsed: 20 (other types)
    - Oversized: 2 (> 10MB)

  Code Elements:
    - Functions: 1,234
    - Classes: 456
    - Imports: 789
    - Globals: 123
    - Log Statements: 45

  Performance:
    - Avg Parse Time: 0.05s/file
    - Last Index Run: 2.3s
```

**Benefit**: User visibility into index state

---

### 10. Relative vs Absolute Paths

**Gap**: Should database store relative or absolute paths?

**Current Schema**:
```sql
path TEXT UNIQUE NOT NULL
```

**Recommendation**: Store **relative paths** (relative to index root)

**Reasons**:
- Portability (move project directory)
- Smaller database size
- Easier to reason about in nested indexes

**Implementation**: Store index root in metadata table:
```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
INSERT INTO metadata VALUES ('index_root', '/absolute/path/to/project');
```

---

## Missing Documentation

### 11. User-Facing Documentation

**Gap**: Spec doesn't mention user documentation requirements

**Needed**:
- `via index --help` output specification
- Error message standards (format, verbosity)
- Exit codes (0=success, 1=errors, 2=fatal, etc.)
- Example usage patterns in README

**Recommendation**: @Oracle should draft `docs/CLI_REFERENCE.md` after architecture is finalized

---

### 12. Testing Strategy

**Gap**: No mention of test requirements

**Recommendation**: @Trin should define test cases covering:
- Edge cases (empty dirs, permission errors, huge files)
- Concurrency (parallel indexing, watch mode race conditions)
- Incremental indexing correctness
- Cross-platform behavior (Windows, Linux, macOS)
- .gitignore parsing edge cases

---

## Architectural Concerns for @Morpheus

### 13. Pluggable Parser Architecture

**Spec Requirement** (REQ-4.1): "Architecture must support pluggable language parsers"

**Questions for @Morpheus**:
- What's the parser interface/ABC?
- How are parsers registered/discovered?
- Should parsers be plugins or built-in?
- How to handle parser-specific table schemas (e.g., JS has no decorators)?

**Recommendation**: Define `ParserInterface` abstract base class

---

### 14. Database Migrations

**Gap**: No schema versioning or migration strategy

**Recommendation**: Add schema version tracking:
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at REAL,
    description TEXT
);
INSERT INTO schema_version VALUES (1, strftime('%s', 'now'), 'Initial schema');
```

**Benefit**: Supports future schema changes without breaking existing indexes

---

## Final Recommendations

### For @Morpheus (Architecture Review)

1. **Design nested index discovery/IPC mechanism** (Gap #1)
2. **Clarify methods storage** (add `class_id` to functions table) (Gap #2.1)
3. **Add byte offsets to all tables** (Gap #2.2)
4. **Define `--exclude` pattern semantics** (Gap #3)
5. **Design daemon lifecycle commands** (Gap #4)
6. **Specify worker pool limits and threading model** (Gap #5)
7. **Consider content hashing for reliable change detection** (Gap #6)
8. **Design pluggable parser interface** (Concern #13)
9. **Add schema versioning strategy** (Concern #14)

### For @Neo (Implementation)

- Add database integrity checks
- Implement relative path storage with metadata table
- Add `content_hash` to files table for robust incremental indexing

### For @Oracle (Documentation)

- Draft `docs/CLI_REFERENCE.md` after architecture finalized
- Create example `.gitignore` patterns guide
- Document nested index use cases

### For @Trin (Testing)

- Plan test cases for edge cases and race conditions
- Cross-platform testing strategy
- .gitignore parsing test suite

---

## Conclusion

**Status**: ✅ **APPROVED FOR ARCHITECTURE PHASE**

The specification is solid and well-thought-out. The gaps identified are mostly clarifications and enhancements, not blockers.

**Next Step**: Hand off to @Morpheus for architecture design with the above recommendations addressed.

**Overall Grade**: **A-** (Excellent requirements capture, minor gaps in implementation details)

---

**Oracle's Signature**: Knowledge reviewed and catalogued. Spec is sound. Proceed to architecture phase.
