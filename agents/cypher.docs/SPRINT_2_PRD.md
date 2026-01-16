# Product Requirements Document - Sprint 2
## Query & Render Commands

**Version**: 1.0
**Date**: 2026-01-11
**Product Manager**: @Cypher
**Status**: Draft - Awaiting User Answers

---

## Executive Summary

Sprint 2 adds search and display capabilities to VIA, enabling developers to query their indexed codebase and view source code with context. This transforms VIA from an indexing tool into a practical code exploration utility.

**Core Features**:
- `via query` - Search for functions, classes, imports, and globals
- `via render` - Display source code with syntax highlighting
- `via list` - Browse all indexed entities
- `via stats` - View codebase statistics

---

## Requirements

### 1. Query Command (`via query`)

**Purpose**: Search the indexed database for code entities by name or pattern.

**Command Syntax**:
```bash
via query <search-term> [OPTIONS]
```

**Required Options**:
- `--type TYPE` - Filter by entity type (function, class, import, global, all)
- `--file PATTERN` - Filter by file path pattern (e.g., `src/*.py`)
- `--case-sensitive` - Enable case-sensitive search (default: case-insensitive)

**Functional Requirements**:
- **REQ-Q1**: Support exact name matching (e.g., `via query calculate_total`)
- **REQ-Q2**: Support pattern matching with wildcards (e.g., `via query calc*`)
- **REQ-Q3**: Support entity type filtering (function, class, import, global)
- **REQ-Q4**: Support file path filtering (glob patterns)
- **REQ-Q5**: Display results with: entity name, type, file path, line number
- **REQ-Q6**: Show result count summary (e.g., "Found 5 matches")
- **REQ-Q7**: Handle zero results gracefully ("No matches found")
- **REQ-Q8**: Case-insensitive by default, case-sensitive with flag

**Non-Functional Requirements**:
- **REQ-Q9**: Query performance < 500ms for databases with <10k entities
- **REQ-Q10**: Results sorted by relevance (exact matches first, then partial)

---

### 2. Render Command (`via render`)

**Purpose**: Display source code for query results with context and syntax highlighting.

**Command Syntax**:
```bash
via render <search-term> [OPTIONS]
```

**Required Options**:
- `--context N` - Number of lines before/after to show (default: 3)
- `--no-color` - Disable syntax highlighting
- `--type TYPE` - Filter by entity type (same as query)
- `--file PATTERN` - Filter by file path (same as query)

**Functional Requirements**:
- **REQ-R1**: Display source code for matching entities
- **REQ-R2**: Show context lines before/after the entity
- **REQ-R3**: Syntax highlight Python code (using pygments or similar)
- **REQ-R4**: Display file path and line number for each result
- **REQ-R5**: Handle multiple results (show all or prompt user)
- **REQ-R6**: Handle file-not-found errors gracefully (file moved/deleted)
- **REQ-R7**: Handle permission errors gracefully
- **REQ-R8**: Support --no-color for plain text output

**Non-Functional Requirements**:
- **REQ-R9**: Render performance < 100ms per result
- **REQ-R10**: Syntax highlighting library must not bloat binary significantly

---

### 3. List Command (`via list`)

**Purpose**: Browse all indexed entities by type.

**Command Syntax**:
```bash
via list <entity-type> [OPTIONS]
```

**Entity Types**:
- `files` - List all indexed files
- `functions` - List all functions
- `classes` - List all classes
- `imports` - List all imports
- `globals` - List all global variables

**Required Options**:
- `--file PATTERN` - Filter by file path pattern
- `--limit N` - Limit results to N items

**Functional Requirements**:
- **REQ-L1**: List all entities of specified type
- **REQ-L2**: Show entity name, file path, line number
- **REQ-L3**: Support file path filtering
- **REQ-L4**: Show count summary (e.g., "150 functions")
- **REQ-L5**: Sort results alphabetically by name
- **REQ-L6**: Respect --limit flag for large result sets

---

### 4. Stats Command (`via stats`)

**Purpose**: Display summary statistics about the indexed codebase.

**Command Syntax**:
```bash
via stats
```

**Functional Requirements**:
- **REQ-S1**: Show total files indexed
- **REQ-S2**: Show entity counts (functions, classes, imports, globals)
- **REQ-S3**: Show last indexed timestamp
- **REQ-S4**: Show database file size
- **REQ-S5**: Show supported languages (currently: Python)
- **REQ-S6**: Show index directory path

---

## Open Questions for User

Please answer these questions directly in this document (replace "ANSWER:" with your response):

### Q1: Result Limits
**Question**: Should query/list results be limited by default to prevent overwhelming output?

**Options**:
- A) No limit (show all results)
- B) Default limit of 100, user can override with --limit
- C) Default limit of 50, user can override with --limit
- D) Other (specify)

**ANSWER**:
Default is no limit but can be limited with --limit n to limit ot a fixed number of results.  For the console render, it's important that results are streame (yield) so users can use `| less`, etc..


---

### Q2: Syntax Highlighting
**Question**: Is syntax highlighting a must-have or nice-to-have feature?

**Context**: Syntax highlighting requires the `pygments` library (~1MB dependency). We can make it optional or require it.

**Options**:
- A) Must-have - always install pygments
- B) Optional - install only if user wants it (via extra dependency)
- C) Nice-to-have - defer to later sprint
- D) Not needed - plain text is finz

**ANSWER**:
A) must have
---

### Q3: Pagination
**Question**: Do we need interactive pagination for long result lists?

**Context**: Pagination would allow browsing results page-by-page (like `less` or `more`). Without it, all results scroll past.

**Options**:
- A) Yes - implement pagination (adds complexity)
- B) No - just use --limit flag and let user pipe to `less` if needed
- C) Defer to Sprint 3+
**ANSWER**:
B) just use --limit flag and let user pipe to `less` if needed


---

### Q4: Export Formats
**Question**: Should we support exporting results to structured formats?

**Context**: Users might want to export query results to JSON/CSV for further processing.

**Options**:
- A) Yes - add --format flag (json, csv, text)
- B) No - just display to terminal
- C) Defer to Sprint 3+

**ANSWER**:
A) Yes - add --format flag (json, csv, text, json_lines, ascii_table)
These are render options. we can just do text for now but we'll want to add a bunch later one so use and interface for the output.

Also I want short hand flags for everything 
---

### Q5: Pattern Matching
**Question**: What level of pattern matching should we support?

**Options**:
- A) Simple wildcards only (`*` and `?`) - easiest to implement
- B) SQL LIKE patterns (`%` and `_`) - familiar to SQL users
- C) Full regex support - most powerful but complex
- D) Both wildcards and regex (flag to switch modes)

**ANSWER**:

E) all of the above, but.. I want to stick with what people know.  Let's start with 'grep' style query so use thy python glob module to match things.  We'll add different matchers so use and interface.
---

### Q6: Multiple Results in Render
**Question**: When `via render` matches multiple entities, what should we do?

**Options**:
- A) Show all results sequentially (could be long)
- B) Show first result only, warn about others
- C) Prompt user to select which one to render
- D) Show first N results (e.g., 5), with option to see more

**ANSWER**:

 We should have flags for selecting the different types of objects in the index (`-type <file, function, class, import, global>` etc)  and show matches for any of the types selectged.  the default shoudl be all. and have shorthand opts for type seelction.
 Show all that match and don't worry about pagination or anything we have --limit
---

### Q7: Context Lines Default
**Question**: What should the default number of context lines be for `via render`?

**Context**: Context lines are shown before/after the entity (function, class, etc.)

**Options**:
- A) 3 lines (compact)
- B) 5 lines (balanced)
- C) 10 lines (generous)
- D) Other (specify)

**ANSWER**:
Default 0.  Use grep style optins for context before / after etc..
---

### Q8: File Path Display
**Question**: How should file paths be displayed in results?

**Options**:
- A) Absolute paths (e.g., `/home/user/project/src/utils.py`)
- B) Relative to index root (e.g., `src/utils.py`)
- C) Relative to current directory
- D) User configurable

**ANSWER**:

---
D) User configurable (flags)
---


### Q9: Color Scheme
**Question**: What color scheme should we use for syntax highlighting?

**Options**:
- A) Default (pygments default - typically dark-friendly)
- B) Monokai (popular dark theme)
- C) GitHub (light theme)
- D) Auto-detect terminal (dark/light) and adapt
- E) User configurable in config file

**ANSWER**:

D) + E
---

### Q10: Entity Disambiguation
**Question**: If multiple entities have the same name (e.g., `__init__` in different classes), how should we distinguish them?

**Options**:
- A) Show all matches with file path
- B) Show all matches with full qualified name (e.g., `MyClass.__init__`)
- C) Show all matches, let user filter with --file flag
- D) All of the above

**ANSWER**:
if it matches the query we show it. We should have a "fully qullified path" column to make more preceise matches based on herichies. for files it's the direcotory for code, the packages, etc...  the full path should be up to the root of the heriachry ( relative to project root).

---

## Dependencies

### External Libraries
- **pygments** (optional) - For syntax highlighting
  - Version: >=2.14.0
  - License: BSD
  - Size: ~1MB

### Internal Dependencies
- ✅ DatabaseStore (from Sprint 1)
- ✅ CLI framework (from Sprint 1)
- ✅ Parser infrastructure (from Sprint 1)

---

## Success Criteria

Sprint 2 is **DONE** when:

1. ✅ Users can search for any indexed entity by name
2. ✅ Users can view source code for search results
3. ✅ Users can list all entities of a specific type
4. ✅ Users can see codebase statistics
5. ✅ All commands have comprehensive tests
6. ✅ Test coverage remains >80%
7. ✅ Documentation updated with new commands
8. ✅ All open questions answered and implemented

---

## Out of Scope (Future Sprints)

- Advanced query syntax (boolean operators, nested queries)
- Cross-project queries
- Query history / saved queries
- Interactive TUI for browsing results
- Watch mode integration (live query updates)
- Filter command (post-query filtering)
- Git integration (show git blame, history)

---

## User Stories Reference

See `agents/cypher.docs/SPRINT_2_USER_STORIES.md` for detailed breakdown of:
- 6 user stories
- 19 story points
- ~41 hour estimate
- Task-level breakdown

---

## Next Steps

1. **User**: Answer the 10 open questions above
2. **@Morpheus**: Review technical feasibility once questions answered
3. **@Mouse**: Create sprint plan and task breakdown
4. **@Neo**: Implement stories in priority order

---

**Created by**: @Cypher (Product Manager)
**Status**: ⏳ Awaiting User Answers
**Review Date**: TBD after answers provided
