# Sprint 8 - Line Number Index

**Author**: Cypher (PM)
**Date**: 2026-02-11
**Theme**: Line-Level Indexing & Slice Queries
**Points**: 6

---

## Epic: Line Number Index (`-mL`)

Add line numbers as a queryable dimension. This lets agents and developers extract content at specific lines or line ranges using the pre-built index, without scanning files. Uses a new match type `-mL` with Python-style slice syntax.

### Decisions (Drew, 2026-02-11)

| Decision | Answer |
|----------|--------|
| Query syntax | Match type: `-mL 5:10` (not `--lines`) |
| Storage | Line start byte offsets + per-line byte length |

---

### Story 1: Line Number Indexing (P0, 3pts)

**As a developer**, I want `via` to index line number positions (byte offsets) for every file, so I can quickly extract content at specific lines without scanning.

**Acceptance Criteria**:
- [ ] During indexing, line start byte offsets and per-line byte length are stored for each file
- [ ] New symbol type: `line` (flag: `-tL`)
- [ ] Database schema extended to store line-to-byte-offset mapping per file
- [ ] Incremental: line index updates when file is re-indexed
- [ ] Index size impact is reasonable (line offsets are compact)

---

### Story 2: Line Slice Queries (P0, 3pts)

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
# Extract lines 10-20 from a specific file
via -mg 'store.py' -tF -mL 10:20 -oR

# Last 10 lines of a file
via -mg 'main.py' -tF -mL -10: -oR

# First 5 lines of a class definition
via -mg 'DatabaseStore' -tc -mL 1:5 -oR

# Lines 1-3 of all test functions (see signatures)
via -mg 'test_*' -tf -mL 1:3 -oR
```

**Notes**:
- `-mL` follows the `-m<X>` match type convention (like `-mg`, `-mr`, `-ms`)
- Slice syntax mirrors Python slice notation
- Byte offsets make extraction O(1) seek + read instead of O(n) line scan

---

## Sprint 8 Summary

| Story | Points | Priority | Description |
|-------|--------|----------|-------------|
| Story 1 | 3 | P0 | Line number indexing (byte offsets) |
| Story 2 | 3 | P0 | Line slice queries (`-mL`) |
| **Total** | **6** | | |

---

## Technical Context

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
