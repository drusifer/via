# Sprint 2 Consolidated Documentation

This document consolidates all documentation for Sprint 2.

## Table of Contents

- [SPRINT_2_PRD.md](#sprint-2-prdmd) (originally `agents/cypher.docs/SPRINT_2_PRD.md`)

- [SPRINT_2_PRD_20260111214515.md](#sprint-2-prd-20260111214515md) (originally `.history/agents/cypher.docs/SPRINT_2_PRD_20260111214515.md`)

- [SPRINT_2_PRD_20260111221055.md](#sprint-2-prd-20260111221055md) (originally `.history/agents/cypher.docs/SPRINT_2_PRD_20260111221055.md`)

- [SPRINT_2_REQUIREMENTS_FINAL.md](#sprint-2-requirements-finalmd) (originally `agents/cypher.docs/SPRINT_2_REQUIREMENTS_FINAL.md`)

- [SPRINT_2_REQUIREMENTS_REVISED.md](#sprint-2-requirements-revisedmd) (originally `agents/cypher.docs/SPRINT_2_REQUIREMENTS_REVISED.md`)

- [SPRINT_2_USER_STORIES.md](#sprint-2-user-storiesmd) (originally `agents/cypher.docs/SPRINT_2_USER_STORIES.md`)

- [SPRINT_2_TASKS.md](#sprint-2-tasksmd) (originally `agents/mouse.docs/SPRINT_2_TASKS.md`)

- [SPRINT_2_TEST_PLAN.md](#sprint-2-test-planmd) (originally `agents/trin.docs/archive/SPRINT_2_TEST_PLAN.md`)


---


## SPRINT_2_PRD.md

**Original Location**: `agents/cypher.docs/SPRINT_2_PRD.md`


## Product Requirements Document - Sprint 2
### Query & Render Commands

**Version**: 1.0
**Date**: 2026-01-11
**Product Manager**: @Cypher
**Status**: Draft - Awaiting User Answers

---

### Executive Summary

Sprint 2 adds search and display capabilities to VIA, enabling developers to query their indexed codebase and view source code with context. This transforms VIA from an indexing tool into a practical code exploration utility.

**Core Features**:
- `via query` - Search for functions, classes, imports, and globals
- `via render` - Display source code with syntax highlighting
- `via list` - Browse all indexed entities
- `via stats` - View codebase statistics

---

### Requirements

#### 1. Query Command (`via query`)

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

#### 2. Render Command (`via render`)

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

#### 3. List Command (`via list`)

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

#### 4. Stats Command (`via stats`)

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

### Open Questions for User

Please answer these questions directly in this document (replace "ANSWER:" with your response):

#### Q1: Result Limits
**Question**: Should query/list results be limited by default to prevent overwhelming output?

**Options**:
- A) No limit (show all results)
- B) Default limit of 100, user can override with --limit
- C) Default limit of 50, user can override with --limit
- D) Other (specify)

**ANSWER**:
Default is no limit but can be limited with --limit n to limit ot a fixed number of results.  For the console render, it's important that results are streame (yield) so users can use `| less`, etc..


---

#### Q2: Syntax Highlighting
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

#### Q3: Pagination
**Question**: Do we need interactive pagination for long result lists?

**Context**: Pagination would allow browsing results page-by-page (like `less` or `more`). Without it, all results scroll past.

**Options**:
- A) Yes - implement pagination (adds complexity)
- B) No - just use --limit flag and let user pipe to `less` if needed
- C) Defer to Sprint 3+
**ANSWER**:
B) just use --limit flag and let user pipe to `less` if needed


---

#### Q4: Export Formats
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

#### Q5: Pattern Matching
**Question**: What level of pattern matching should we support?

**Options**:
- A) Simple wildcards only (`*` and `?`) - easiest to implement
- B) SQL LIKE patterns (`%` and `_`) - familiar to SQL users
- C) Full regex support - most powerful but complex
- D) Both wildcards and regex (flag to switch modes)

**ANSWER**:

E) all of the above, but.. I want to stick with what people know.  Let's start with 'grep' style query so use thy python glob module to match things.  We'll add different matchers so use and interface.
---

#### Q6: Multiple Results in Render
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

#### Q7: Context Lines Default
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

#### Q8: File Path Display
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


#### Q9: Color Scheme
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

#### Q10: Entity Disambiguation
**Question**: If multiple entities have the same name (e.g., `__init__` in different classes), how should we distinguish them?

**Options**:
- A) Show all matches with file path
- B) Show all matches with full qualified name (e.g., `MyClass.__init__`)
- C) Show all matches, let user filter with --file flag
- D) All of the above

**ANSWER**:
if it matches the query we show it. We should have a "fully qullified path" column to make more preceise matches based on herichies. for files it's the direcotory for code, the packages, etc...  the full path should be up to the root of the heriachry ( relative to project root).

---

### Dependencies

#### External Libraries
- **pygments** (optional) - For syntax highlighting
  - Version: >=2.14.0
  - License: BSD
  - Size: ~1MB

#### Internal Dependencies
- ✅ DatabaseStore (from Sprint 1)
- ✅ CLI framework (from Sprint 1)
- ✅ Parser infrastructure (from Sprint 1)

---

### Success Criteria

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

### Out of Scope (Future Sprints)

- Advanced query syntax (boolean operators, nested queries)
- Cross-project queries
- Query history / saved queries
- Interactive TUI for browsing results
- Watch mode integration (live query updates)
- Filter command (post-query filtering)
- Git integration (show git blame, history)

---

### User Stories Reference

See `agents/cypher.docs/SPRINT_2_USER_STORIES.md` for detailed breakdown of:
- 6 user stories
- 19 story points
- ~41 hour estimate
- Task-level breakdown

---

### Next Steps

1. **User**: Answer the 10 open questions above
2. **@Morpheus**: Review technical feasibility once questions answered
3. **@Mouse**: Create sprint plan and task breakdown
4. **@Neo**: Implement stories in priority order

---

**Created by**: @Cypher (Product Manager)
**Status**: ⏳ Awaiting User Answers
**Review Date**: TBD after answers provided


---


## SPRINT_2_PRD_20260111214515.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_2_PRD_20260111214515.md`


## Product Requirements Document - Sprint 2
### Query & Render Commands

**Version**: 1.0
**Date**: 2026-01-11
**Product Manager**: @Cypher
**Status**: Draft - Awaiting User Answers

---

### Executive Summary

Sprint 2 adds search and display capabilities to VIA, enabling developers to query their indexed codebase and view source code with context. This transforms VIA from an indexing tool into a practical code exploration utility.

**Core Features**:
- `via query` - Search for functions, classes, imports, and globals
- `via render` - Display source code with syntax highlighting
- `via list` - Browse all indexed entities
- `via stats` - View codebase statistics

---

### Requirements

#### 1. Query Command (`via query`)

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

#### 2. Render Command (`via render`)

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

#### 3. List Command (`via list`)

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

#### 4. Stats Command (`via stats`)

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

### Open Questions for User

Please answer these questions directly in this document (replace "ANSWER:" with your response):

#### Q1: Result Limits
**Question**: Should query/list results be limited by default to prevent overwhelming output?

**Options**:
- A) No limit (show all results)
- B) Default limit of 100, user can override with --limit
- C) Default limit of 50, user can override with --limit
- D) Other (specify)

**ANSWER**:

---

#### Q2: Syntax Highlighting
**Question**: Is syntax highlighting a must-have or nice-to-have feature?

**Context**: Syntax highlighting requires the `pygments` library (~1MB dependency). We can make it optional or require it.

**Options**:
- A) Must-have - always install pygments
- B) Optional - install only if user wants it (via extra dependency)
- C) Nice-to-have - defer to later sprint
- D) Not needed - plain text is fine

**ANSWER**:

---

#### Q3: Pagination
**Question**: Do we need interactive pagination for long result lists?

**Context**: Pagination would allow browsing results page-by-page (like `less` or `more`). Without it, all results scroll past.

**Options**:
- A) Yes - implement pagination (adds complexity)
- B) No - just use --limit flag and let user pipe to `less` if needed
- C) Defer to Sprint 3+

**ANSWER**:

---

#### Q4: Export Formats
**Question**: Should we support exporting results to structured formats?

**Context**: Users might want to export query results to JSON/CSV for further processing.

**Options**:
- A) Yes - add --format flag (json, csv, text)
- B) No - just display to terminal
- C) Defer to Sprint 3+

**ANSWER**:

---

#### Q5: Pattern Matching
**Question**: What level of pattern matching should we support?

**Options**:
- A) Simple wildcards only (`*` and `?`) - easiest to implement
- B) SQL LIKE patterns (`%` and `_`) - familiar to SQL users
- C) Full regex support - most powerful but complex
- D) Both wildcards and regex (flag to switch modes)

**ANSWER**:

---

#### Q6: Multiple Results in Render
**Question**: When `via render` matches multiple entities, what should we do?

**Options**:
- A) Show all results sequentially (could be long)
- B) Show first result only, warn about others
- C) Prompt user to select which one to render
- D) Show first N results (e.g., 5), with option to see more

**ANSWER**:

---

#### Q7: Context Lines Default
**Question**: What should the default number of context lines be for `via render`?

**Context**: Context lines are shown before/after the entity (function, class, etc.)

**Options**:
- A) 3 lines (compact)
- B) 5 lines (balanced)
- C) 10 lines (generous)
- D) Other (specify)

**ANSWER**:

---

#### Q8: File Path Display
**Question**: How should file paths be displayed in results?

**Options**:
- A) Absolute paths (e.g., `/home/user/project/src/utils.py`)
- B) Relative to index root (e.g., `src/utils.py`)
- C) Relative to current directory
- D) User configurable

**ANSWER**:

---

#### Q9: Color Scheme
**Question**: What color scheme should we use for syntax highlighting?

**Options**:
- A) Default (pygments default - typically dark-friendly)
- B) Monokai (popular dark theme)
- C) GitHub (light theme)
- D) Auto-detect terminal (dark/light) and adapt
- E) User configurable in config file

**ANSWER**:

---

#### Q10: Entity Disambiguation
**Question**: If multiple entities have the same name (e.g., `__init__` in different classes), how should we distinguish them?

**Options**:
- A) Show all matches with file path
- B) Show all matches with full qualified name (e.g., `MyClass.__init__`)
- C) Show all matches, let user filter with --file flag
- D) All of the above

**ANSWER**:

---

### Dependencies

#### External Libraries
- **pygments** (optional) - For syntax highlighting
  - Version: >=2.14.0
  - License: BSD
  - Size: ~1MB

#### Internal Dependencies
- ✅ DatabaseStore (from Sprint 1)
- ✅ CLI framework (from Sprint 1)
- ✅ Parser infrastructure (from Sprint 1)

---

### Success Criteria

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

### Out of Scope (Future Sprints)

- Advanced query syntax (boolean operators, nested queries)
- Cross-project queries
- Query history / saved queries
- Interactive TUI for browsing results
- Watch mode integration (live query updates)
- Filter command (post-query filtering)
- Git integration (show git blame, history)

---

### User Stories Reference

See `agents/cypher.docs/SPRINT_2_USER_STORIES.md` for detailed breakdown of:
- 6 user stories
- 19 story points
- ~41 hour estimate
- Task-level breakdown

---

### Next Steps

1. **User**: Answer the 10 open questions above
2. **@Morpheus**: Review technical feasibility once questions answered
3. **@Mouse**: Create sprint plan and task breakdown
4. **@Neo**: Implement stories in priority order

---

**Created by**: @Cypher (Product Manager)
**Status**: ⏳ Awaiting User Answers
**Review Date**: TBD after answers provided


---


## SPRINT_2_PRD_20260111221055.md

**Original Location**: `.history/agents/cypher.docs/SPRINT_2_PRD_20260111221055.md`


## Product Requirements Document - Sprint 2
### Query & Render Commands

**Version**: 1.0
**Date**: 2026-01-11
**Product Manager**: @Cypher
**Status**: Draft - Awaiting User Answers

---

### Executive Summary

Sprint 2 adds search and display capabilities to VIA, enabling developers to query their indexed codebase and view source code with context. This transforms VIA from an indexing tool into a practical code exploration utility.

**Core Features**:
- `via query` - Search for functions, classes, imports, and globals
- `via render` - Display source code with syntax highlighting
- `via list` - Browse all indexed entities
- `via stats` - View codebase statistics

---

### Requirements

#### 1. Query Command (`via query`)

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

#### 2. Render Command (`via render`)

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

#### 3. List Command (`via list`)

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

#### 4. Stats Command (`via stats`)

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

### Open Questions for User

Please answer these questions directly in this document (replace "ANSWER:" with your response):

#### Q1: Result Limits
**Question**: Should query/list results be limited by default to prevent overwhelming output?

**Options**:
- A) No limit (show all results)
- B) Default limit of 100, user can override with --limit
- C) Default limit of 50, user can override with --limit
- D) Other (specify)

**ANSWER**:
Default is no limit but can be limited with --limit n to limit ot a fixed number of results.  For the console render, it's important that results are streame (yield) so users can use `| less`, etc..


---

#### Q2: Syntax Highlighting
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

#### Q3: Pagination
**Question**: Do we need interactive pagination for long result lists?

**Context**: Pagination would allow browsing results page-by-page (like `less` or `more`). Without it, all results scroll past.

**Options**:
- A) Yes - implement pagination (adds complexity)
- B) No - just use --limit flag and let user pipe to `less` if needed
- C) Defer to Sprint 3+
**ANSWER**:
B) just use --limit flag and let user pipe to `less` if needed


---

#### Q4: Export Formats
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

#### Q5: Pattern Matching
**Question**: What level of pattern matching should we support?

**Options**:
- A) Simple wildcards only (`*` and `?`) - easiest to implement
- B) SQL LIKE patterns (`%` and `_`) - familiar to SQL users
- C) Full regex support - most powerful but complex
- D) Both wildcards and regex (flag to switch modes)

**ANSWER**:

E) all of the above, but.. I want to stick with what people know.  Let's start with 'grep' style query so use thy python glob module to match things.  We'll add different matchers so use and interface.
---

#### Q6: Multiple Results in Render
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

#### Q7: Context Lines Default
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

#### Q8: File Path Display
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


#### Q9: Color Scheme
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

#### Q10: Entity Disambiguation
**Question**: If multiple entities have the same name (e.g., `__init__` in different classes), how should we distinguish them?

**Options**:
- A) Show all matches with file path
- B) Show all matches with full qualified name (e.g., `MyClass.__init__`)
- C) Show all matches, let user filter with --file flag
- D) All of the above

**ANSWER**:
if it matches the query we show it. We should have a "fully qullified path" column to make more preceise matches based on herichies. for files it's the direcotory for code, the packages, etc...  the full path should be up to the root of the heriachry ( relative to project root).

---

### Dependencies

#### External Libraries
- **pygments** (optional) - For syntax highlighting
  - Version: >=2.14.0
  - License: BSD
  - Size: ~1MB

#### Internal Dependencies
- ✅ DatabaseStore (from Sprint 1)
- ✅ CLI framework (from Sprint 1)
- ✅ Parser infrastructure (from Sprint 1)

---

### Success Criteria

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

### Out of Scope (Future Sprints)

- Advanced query syntax (boolean operators, nested queries)
- Cross-project queries
- Query history / saved queries
- Interactive TUI for browsing results
- Watch mode integration (live query updates)
- Filter command (post-query filtering)
- Git integration (show git blame, history)

---

### User Stories Reference

See `agents/cypher.docs/SPRINT_2_USER_STORIES.md` for detailed breakdown of:
- 6 user stories
- 19 story points
- ~41 hour estimate
- Task-level breakdown

---

### Next Steps

1. **User**: Answer the 10 open questions above
2. **@Morpheus**: Review technical feasibility once questions answered
3. **@Mouse**: Create sprint plan and task breakdown
4. **@Neo**: Implement stories in priority order

---

**Created by**: @Cypher (Product Manager)
**Status**: ⏳ Awaiting User Answers
**Review Date**: TBD after answers provided


---


## SPRINT_2_REQUIREMENTS_FINAL.md

**Original Location**: `agents/cypher.docs/SPRINT_2_REQUIREMENTS_FINAL.md`


## Sprint 2 Requirements - Match Command

**Version**: 4.0 Final
**Date**: 2026-01-12
**Product Manager**: @Cypher
**Status**: Ready for Implementation

---

### Executive Summary

Sprint 2 delivers the `via match` command for searching indexed entities. Users can specify **what to match against** (`--type`) and **the pattern to match** (using glob, regex, or SQL syntax).

**Core Concept**:
- `--type` = The field/entity type to match against (filename, filepath, method, class, function, import, global)
- Pattern syntax: `--glob`, `--regex`, or `--sql` (default: glob)
- Multiple type/pattern pairs combine with **AND** logic for precise filtering

**Out of Scope**:
- ❌ `via render` command (backlogged to Sprint 3)
- ❌ `via list` command (backlogged to Sprint 3)
- ❌ `via stats` command (backlogged to Sprint 3)
- ❌ Pipeline operators (backlogged to future sprint)

---

### 1. Core Design Principles

#### Match Semantics

**`--type TYPE`**: Specifies what field to match against
- `filename` - Match against file name only (e.g., `matcher.py`)
- `filepath` - Match against full file path (e.g., `via/utils/matcher.py`)
- `method` - Match against method names
- `class` - Match against class names
- `function` - Match against function names (top-level, non-method)
- `import` - Match against import module names
- `global` - Match against global variable names

**Pattern SYNTAX**: Specifies the test value and syntax
- Pattern: The string pattern to match (positional argument)
- Syntax: `--glob` / `-g`, `--regex` / `-r`, or `--sql` / `-s` (default: glob)

**Multiple Filters**: When multiple `--type` and pattern pairs are provided, they combine with **AND** logic.

---

### 2. Command Syntax

#### Basic Syntax

```bash
via match --type TYPE --SYNTAX 'PATTERN'
```

#### Short Form

```bash
via match -t TYPE -SYNTAX 'PATTERN'
## Even shorter
via m -t TYPE -SYNTAX 'PATTERN'
```

#### Multiple Type/Pattern Pairs (AND Logic)

```bash
via match --type TYPE1 --SYNTAX1 'PATTERN1' --type TYPE2 --SYNTAX2 'PATTERN2'
```

**Short form**:
```bash
via m -t TYPE1 -SYNTAX1 'PATTERN1' -t TYPE2 -SYNTAX2 'PATTERN2'
```

**Examples**:
```bash
## Single filter: find files in utils/
via m -t filepath -g '**/utils/*.py'

## Two filters (AND): find functions in utils/ files
via m -t filepath -g '**/utils/*.py' -t function -r '^calculate_.*'
```

---

### 3. Object Types

#### Supported Types for `--type` Flag

| Type | Short | Matches Against | Database Source |
|------|-------|-----------------|-----------------|
| `filename` | `-t filename` | File name only | `files` table (basename of `file_path`) |
| `filepath` | `-t filepath` | Full file path | `files` table (`file_path` column) |
| `method` | `-t method` | Method names | `functions` table where `parent_entity_id IS NOT NULL` |
| `class` | `-t class` | Class names | `classes` table |
| `function` | `-t function` | Function names | `functions` table where `parent_entity_id IS NULL` |
| `import` | `-t import` | Import module names | `imports` table (`module_name` column) |
| `global` | `-t global` | Global variable names | `globals` table |

**Default**: If no `--type` specified, match against **all** entity name fields (method, class, function, import, global names - NOT files).

---

### 4. Match Syntax Types

#### Three Supported Syntaxes

| Syntax | Long Flag | Short Flag | Description | Example Pattern |
|--------|-----------|------------|-------------|-----------------|
| **Glob** | `--glob` | `-g` | Shell-style wildcards (default) | `*ToString()` |
| **Regex** | `--regex` | `-r` | Regular expressions | `__.*__\(` |
| **SQL** | `--sql` | `-s` | SQL LIKE patterns | `%ToString()` |

**Default**: If no syntax flag provided, use `--glob`.

**Mutual Exclusivity**: Each `--match` clause can only have ONE syntax type.

#### Glob Syntax (Default)

**Implementation**: Python `fnmatch` module + SQLite GLOB

**Wildcards**:
- `*` - Match zero or more characters
- `?` - Match exactly one character
- `[abc]` - Match any character in set
- `[!abc]` - Match any character NOT in set

**Examples**:
```bash
via m -t method -g '*ToString()'       # Methods ending with ToString()
via m -t filepath -g '**/utils/*.py'   # Files in any utils/ directory
via m -t class -g '[A-Z]*Model'        # Classes starting with capital + ending in Model
```

#### Regex Syntax

**Implementation**: Python `re` module (with SQLite fallback or Python-side filtering)

**Examples**:
```bash
via m -t method -r '__.*__\('          # Magic methods
via m -t function -r '^test_.*'        # Test functions
via m -t class -r '^[A-Z][a-z]+$'      # Pascal case single-word classes
```

#### SQL LIKE Syntax

**Implementation**: SQLite LIKE operator

**Wildcards**:
- `%` - Match zero or more characters
- `_` - Match exactly one character

**Examples**:
```bash
via m -t import -s '%os%'              # Imports containing "os"
via m -t global -s 'DEBUG%'            # Globals starting with DEBUG
```

---

### 5. Multiple Match Clauses (AND Logic)

#### Syntax

**Long Form**:
```bash
via match --match --type TYPE1 --SYNTAX1 'PATTERN1' \
          --match --type TYPE2 --SYNTAX2 'PATTERN2'
```

**Short Form**:
```bash
via m -t TYPE1 -SYNTAX1 'PATTERN1' -t TYPE2 -SYNTAX2 'PATTERN2'
```

#### How AND Logic Works

When multiple `--match` clauses are provided:
1. Each match clause filters independently
2. Results must satisfy **ALL** match clauses (intersection)
3. If match types differ (e.g., filename + method), we filter files first, then entities within those files

#### Examples

**Example 1**: Match files in utils/ AND functions matching regex pattern
```bash
via m -t filepath -g '**/utils/*.py' -t function -r '^calculate_.*'
```

**SQL Logic**:
```sql
SELECT 'function' as type, f.file_path, fn.line_number, fn.name
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NULL                -- functions only
  AND f.file_path GLOB '**/utils/*.py'           -- first match clause
  AND fn.name REGEXP '^calculate_.*'             -- second match clause
```

**Example 2**: Match classes in models.py files
```bash
via m -t filename -g 'models.py' -t class -g '*User*'
```

**SQL Logic**:
```sql
SELECT 'class' as type, f.file_path, c.line_number, c.name
FROM classes c
JOIN files f ON c.file_id = f.id
WHERE f.file_path LIKE '%models.py'              -- first match (filename)
  AND c.name GLOB '*User*'                       -- second match (class name)
```

**Example 3**: Match test functions in test files
```bash
via m -t filepath -g 'tests/**/*.py' -t function -g 'test_*'
```

---

### 6. Additional Qualifiers

#### Case Sensitivity

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--case-insensitive` | `-I` | Case-insensitive matching | `false` |

**Applies to**: All `--match` clauses in the query.

**Implementation**:
- **Glob/Regex**: Convert pattern and text to lowercase
- **SQL LIKE**: Use SQLite `LIKE` (case-insensitive) instead of `GLOB`

**Example**:
```bash
via m -t class -g 'user' -I          # Matches: User, USER, user, UsEr
```

#### Result Limit

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--limit N` | `-n N` | Limit results to N items | `unlimited` |

**Example**:
```bash
via m -t method -g '*' -n 10         # First 10 methods
```

---

### 7. Output Format

#### Simple Text Output (Sprint 2)

**Format**: `type:file_path:line_number:qualified_name`

**Fields**:
- `type` - Entity type (file, method, class, function, import, global)
- `file_path` - Relative path from project root
- `line_number` - Starting line number (0 for files)
- `qualified_name` - Fully qualified name

#### Qualified Name Format

| Entity Type | Format | Example |
|-------------|--------|---------|
| **File** | `file_path` | `via/utils/matcher.py` |
| **Function** | `module.function_name` | `utils.matcher.calculate_total` |
| **Method** | `module.ClassName.method_name` | `utils.matcher.Helper.ToString` |
| **Class** | `module.ClassName` | `models.user.User` |
| **Import** | `module_name` | `os.path` |
| **Global** | `module.GLOBAL_NAME` | `config.settings.DEBUG` |

#### Example Output

```bash
$ via m -t filepath -g '**/utils/matcher*.py' -t function -r '__.*__'

file:via/utils/matcher.py:0:via/utils/matcher.py
function:via/utils/matcher.py:45:utils.matcher.__init__
function:via/utils/matcher.py:67:utils.matcher.__str__
```

```bash
$ via m -t method -g '*ToString()'

method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

#### No Header/Footer

Output is **streaming** (grep-style) for piping:
- ✅ One result per line
- ❌ No header (e.g., "Found 3 results")
- ❌ No footer (e.g., "Total: 3")

---

### 8. Command-Line Flag Summary

#### Primary Flags

| Long Flag | Short | Description | Example |
|-----------|-------|-------------|---------|
| `--type TYPE` | `-t TYPE` | What to match against | `-t method`, `-t filepath` |

#### Syntax Flags (mutually exclusive per match clause)

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--glob` | `-g` | Glob pattern (default) |
| `--regex` | `-r` | Regex pattern |
| `--sql` | `-s` | SQL LIKE pattern |

#### Qualifier Flags

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--case-insensitive` | `-I` | Case-insensitive matching |
| `--limit N` | `-n N` | Limit results to N items |

#### Global Flags (inherited from CLI)

| Long Flag | Short | Description |
|-----------|-------|-------------|
| `--verbose` | `-v` | Increase verbosity |
| `--quiet` | `-q` | Suppress output |
| `--db PATH` | (none) | Custom database path |

---

### 9. Implementation Architecture

#### Pattern Matcher Interface

```python
from abc import ABC, abstractmethod

class PatternMatcher(ABC):
    """Abstract base class for pattern matchers."""

    @abstractmethod
    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        """Convert pattern to SQL WHERE clause."""
        pass

    @abstractmethod
    def matches(self, pattern: str, text: str, case_sensitive: bool) -> bool:
        """Test if text matches pattern (for validation)."""
        pass
```

#### Query Service Architecture

```python
from dataclasses import dataclass
from typing import Iterator, List

@dataclass
class MatchClause:
    """Represents a single match clause."""
    type: str           # filename, filepath, method, class, function, import, global
    pattern: str        # The pattern to match
    syntax: str         # glob, regex, sql

@dataclass
class QueryResult:
    """Represents a single query result."""
    type: str           # Entity type
    file_path: str      # Relative file path
    line_number: int    # Starting line number
    qualified_name: str # Fully qualified name

class QueryService:
    """Service for querying indexed entities."""

    def query(
        self,
        match_clauses: List[MatchClause],
        case_sensitive: bool = True,
        limit: int = None
    ) -> Iterator[QueryResult]:
        """Execute query with multiple match clauses (AND logic).

        Yields results one at a time (streaming).
        """
        # Build dynamic SQL query based on match clauses
        sql = self._build_query(match_clauses, case_sensitive, limit)

        # Execute and yield results
        for row in self.db.execute(sql):
            yield self._row_to_result(row)

    def _build_query(self, match_clauses: List[MatchClause], case_sensitive: bool, limit: int) -> str:
        """Build SQL query from match clauses."""
        # Complex logic to combine multiple match types with AND
        pass
```

#### CLI Argument Parsing

```python
## Match command parser
match_parser = subparsers.add_parser('match', aliases=['m'], help='Search indexed entities')

## Type and pattern are paired - use action='append' for multiple filters
match_parser.add_argument('-t', '--type', action='append',
                          choices=['filename', 'filepath', 'method', 'class', 'function', 'import', 'global'],
                          help='Type to match against')

## Syntax flags (mutually exclusive per type/pattern pair in implementation)
match_parser.add_argument('-g', '--glob', action='store_true', help='Use glob pattern (default)')
match_parser.add_argument('-r', '--regex', action='store_true', help='Use regex pattern')
match_parser.add_argument('-s', '--sql', action='store_true', help='Use SQL LIKE pattern')

## Qualifiers
match_parser.add_argument('-I', '--case-insensitive', action='store_true', help='Case-insensitive matching')
match_parser.add_argument('-n', '--limit', type=int, help='Limit results to N items')

## Pattern (positional, multiple allowed)
match_parser.add_argument('pattern', nargs='*', help='Pattern to match')
```

---

### 10. User Stories (Revised)

#### Story 1: Pattern Matcher Foundation (3 pts, 6h)

**Acceptance Criteria**:
- [ ] Create `PatternMatcher` ABC
- [ ] Implement `GlobMatcher`
- [ ] Implement `SqlLikeMatcher`
- [ ] Create `MatcherRegistry`
- [ ] Support case-sensitive/insensitive modes
- [ ] 15 unit tests (100% coverage)

#### Story 2: Query Service Layer (5 pts, 10h)

**Acceptance Criteria**:
- [ ] Create `QueryService` class
- [ ] Support all object types (filename, filepath, method, class, function, import, global)
- [ ] Support multiple match clauses with AND logic
- [ ] Build dynamic SQL queries
- [ ] Construct qualified names
- [ ] Yield results as generator (streaming)
- [ ] 20 unit tests (90% coverage)

#### Story 3: CLI Match Command (3 pts, 6h)

**Acceptance Criteria**:
- [ ] Implement `via match` subcommand (with `m` alias)
- [ ] Support multiple `-t` flags for type/pattern pairs
- [ ] Support all type options (`-t filename`, `-t method`, etc.)
- [ ] Support all syntax flags (`-g`, `-r`, `-s`)
- [ ] Support qualifiers (`-I`, `-n`)
- [ ] Format output as `type:file_path:line_number:qualified_name`
- [ ] Stream output (no header/footer)
- [ ] 12 integration tests

#### Story 4: Regex Matcher (Optional - 3 pts, 6h)

**Acceptance Criteria**:
- [ ] Implement `RegexMatcher`
- [ ] Support full Python regex syntax
- [ ] Performance < 1s for 10k entities
- [ ] 5 unit tests

**Total**: 11 P0 points (22h), 14 total points (28h)

---

### 11. Example Usage

#### Single Match Clause

```bash
## Find methods ending with ToString()
via m -t method -g '*ToString()'

## Find files in utils/ directory
via m -t filepath -g '**/utils/*.py'

## Find classes starting with "User" (case-insensitive)
via m -t class -g 'User*' -I

## Find imports containing "os" (SQL LIKE)
via m -t import -s '%os%'

## Find magic methods (regex)
via m -t method -r '__.*__\('
```

#### Multiple Match Clauses (AND Logic)

```bash
## Find functions in utils/ files
via m -t filepath -g '**/utils/*.py' -t function -g '*'

## Find test functions in test files
via m -t filepath -g 'tests/**/*.py' -t function -g 'test_*'

## Find User classes in models.py files
via m -t filename -g 'models.py' -t class -g '*User*'

## Find magic methods in utils/ (complex)
via m -t filepath -g '**/utils/*.py' -t method -r '__.*__\('
```

#### With Qualifiers

```bash
## Case-insensitive search for classes
via m -t class -g 'user' -I

## Limit to first 10 results
via m -t method -g 'calculate*' -n 10

## Case-insensitive, limited, multiple matches
via m -t filepath -g '**/models/*.py' -t class -g '*user*' -I -n 5
```

#### Piping Results

```bash
## Pipe to less for browsing
via m -t function -g 'test_*' | less

## Count results
via m -t method -g '*' | wc -l

## Filter with grep
via m -t class -g '*' | grep 'Model'
```

---

### 12. Success Criteria

Sprint 2 is **DONE** when:

1. ✅ Users can match against any object type (filename, filepath, method, class, function, import, global)
2. ✅ Users can specify patterns with glob, regex, or SQL LIKE syntax
3. ✅ Users can combine multiple match clauses with AND logic
4. ✅ Files are treated as object types (no separate file filter)
5. ✅ Output format: `type:file_path:line_number:qualified_name`
6. ✅ Results stream for piping
7. ✅ Case-insensitive mode works (`-I`)
8. ✅ Result limiting works (`-n`)
9. ✅ All tests pass (47 total: 15 matcher + 20 service + 12 CLI)
10. ✅ Test coverage > 80%
11. ✅ Documentation updated

---

### 13. Backlog (Future Sprints)

#### Sprint 3 Backlog
- `via render` command with syntax highlighting
- `via list` command for browsing entities
- `via stats` command for database statistics
- Context lines (`-A`, `-B`, `-C` flags)
- Color scheme configuration
- Multiple output formats (JSON, CSV, table)

#### Sprint 4+ Backlog
- Pipeline operators (OR, NOT)
- Field-specific queries (docstring search)
- Boolean query syntax
- Cross-project queries
- Query history

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Final - Ready for Implementation
**Next**: @Morpheus technical review, @Mouse sprint planning


---


## SPRINT_2_REQUIREMENTS_REVISED.md

**Original Location**: `agents/cypher.docs/SPRINT_2_REQUIREMENTS_REVISED.md`


## Sprint 2 Requirements - Query Command (Match-Style Filtering)

**Version**: 2.0 (Revised Scope)
**Date**: 2026-01-12
**Product Manager**: @Cypher
**Status**: Ready for Technical Review (@Morpheus)

---

### Executive Summary

Sprint 2 is now **narrowly focused** on implementing the `via query` command with match-style filtering only. All rendering, listing, and stats functionality is **deferred to future sprints**.

**Core Goal**: Enable users to search indexed entities using pattern matching with flexible syntax options.

**Out of Scope for Sprint 2**:
- ❌ `via render` command (deferred to Sprint 3)
- ❌ `via list` command (deferred to Sprint 3)
- ❌ `via stats` command (deferred to Sprint 3)
- ❌ Syntax highlighting (deferred to Sprint 3)
- ❌ Context lines (-A/-B/-C flags) (deferred to Sprint 3)
- ❌ Multiple output formats (json, csv, etc.) (deferred to Sprint 3)

---

### 1. Query Command Overview

#### Purpose

Search indexed code entities using pattern matching with:
1. **Match Syntax Selection**: Choose between glob, regex, or SQL LIKE patterns
2. **Object Type Filtering**: Filter by specific entity types (method, class, function, import, global)
3. **Standard Qualifiers**: Case sensitivity, limit, file path filters

#### Command Syntax

```bash
## Long form with explicit flags
via query --match <PATTERN> --glob --method --case-insensitive

## Short form (preferred)
via -qMmg '<PATTERN>'
```

**Key Design Principle**: The `-M` (match mode) flag is the primary mode for Sprint 2.

---

### 2. Match Syntax Types

#### Three Supported Syntaxes

| Syntax | Long Flag | Short Flag | Description | Example |
|--------|-----------|------------|-------------|---------|
| **Glob** | `--glob` | `-g` | Shell-style wildcards | `*ToString()` |
| **Regex** | `--regex` | `-r` | Regular expressions | `.*ToString\(\)$` |
| **SQL** | `--sql` | `-s` | SQL LIKE patterns | `%ToString()` |

**Default**: If no syntax flag provided, use `--glob` (most user-friendly)

**Mutual Exclusivity**: Only ONE syntax type can be specified per query

#### Glob Syntax (Default)

**Implementation**: Python `fnmatch` module

**Supported Wildcards**:
- `*` - Match zero or more characters
- `?` - Match exactly one character
- `[abc]` - Match any character in set
- `[!abc]` - Match any character NOT in set

**Examples**:
```bash
via -qMmg '*ToString()'       # Any method ending with ToString()
via -qMmg 'get*'              # Any entity starting with "get"
via -qMmg 'calculate_???'     # calculate_ followed by exactly 3 chars
via -qMmg '[A-Z]*'            # Starts with uppercase letter
```

#### Regex Syntax

**Implementation**: Python `re` module

**Supported Patterns**: Full Python regex syntax

**Examples**:
```bash
via -qMmr '.*ToString\(\)$'           # Methods ending with ToString()
via -qMmr '^get[A-Z][a-z]+'           # getXxx pattern (camelCase)
via -qMmr '__(init|str|repr)__'       # Magic methods
via -qMmr '^test_.*'                  # Test functions
```

#### SQL LIKE Syntax

**Implementation**: SQLite LIKE operator (database-native)

**Supported Wildcards**:
- `%` - Match zero or more characters (equivalent to `*` in glob)
- `_` - Match exactly one character (equivalent to `?` in glob)

**Examples**:
```bash
via -qMms '%ToString()'       # Methods ending with ToString()
via -qMms 'get%'              # Starts with "get"
via -qMms 'calculate___'      # calculate followed by exactly 3 chars
```

**Note**: SQL LIKE is the most efficient (database-native) but least expressive.

---

### 3. Object Type Filters

#### Supported Entity Types

| Type | Long Flag | Short Flag | Database Mapping | Description |
|------|-----------|------------|------------------|-------------|
| **Method** | `--method` | `-m` | `functions` table where `parent_entity_id IS NOT NULL` | Class methods |
| **Class** | `--class` | `-c` | `classes` table | Class definitions |
| **Function** | `--function` | `-f` | `functions` table where `parent_entity_id IS NULL` | Top-level functions |
| **Import** | `--import` | `-i` | `imports` table | Import statements |
| **Global** | `--global` | `-G` | `globals` table | Global variables |
| **All** | (default) | (none) | All tables | All entity types |

**Default Behavior**: If no type flags specified, search ALL entity types.

**Multiple Types Allowed**: Users can specify multiple type filters.

**Examples**:
```bash
## Search only methods
via -qMm -g '*ToString()'

## Search methods AND functions
via -qMmf -g 'calculate*'

## Search classes AND imports
via -qMci -g '*User*'

## Search all types (default - no type flags)
via -qM -g 'get*'
```

#### Query Logic for Multiple Types

When multiple type flags are specified, use **OR logic**:

```sql
SELECT * FROM (
    SELECT ... FROM functions WHERE parent_entity_id IS NOT NULL  -- methods
    UNION ALL
    SELECT ... FROM functions WHERE parent_entity_id IS NULL      -- functions
) WHERE name LIKE '%pattern%'
```

---

### 4. Standard Qualifiers

#### Case Sensitivity

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--case-insensitive` | `-I` | Case-insensitive matching | `false` (case-sensitive) |

**Implementation**:
- **Glob/Regex**: Convert both pattern and text to lowercase before matching
- **SQL LIKE**: Use `LIKE` (case-insensitive) instead of `GLOB` (case-sensitive)

**Examples**:
```bash
## Case-sensitive (default)
via -qMmg 'ToString'      # Matches: ToString, but NOT tostring

## Case-insensitive
via -qMmgI 'ToString'     # Matches: ToString, tostring, TOSTRING, etc.
```

#### Result Limit

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--limit N` | `-n N` | Limit results to N items | `unlimited` |

**Implementation**: SQL `LIMIT` clause

**Examples**:
```bash
## Get first 10 matches
via -qMmg '*ToString()' -n 10

## Get first 100 matches
via -qMmg 'get*' --limit 100
```

#### File Path Filter

| Long Flag | Short Flag | Description | Default |
|-----------|------------|-------------|---------|
| `--file PATTERN` | `-F PATTERN` | Filter by file path (glob pattern) | `*` (all files) |

**Implementation**: Apply glob pattern to `file_path` column

**Examples**:
```bash
## Search only in src/ directory
via -qMmg '*ToString()' -F 'src/**/*.py'

## Search in models.py files
via -qMmg 'User' -F '**/models.py'

## Search in test files
via -qMmg 'test_*' -F 'tests/**/*.py'
```

---

### 5. Command-Line Interface

#### Primary Mode: Match Mode (`-M`)

The `-M` flag activates "match mode" for the query command.

#### Full Syntax Breakdown

```bash
via [GLOBAL_FLAGS] query [QUERY_FLAGS] --match <PATTERN> [MATCH_SYNTAX] [TYPE_FILTERS] [QUALIFIERS]
```

**Simplified with short flags**:
```bash
via -q -M [TYPE_FLAGS] [SYNTAX_FLAG] [QUALIFIERS] '<PATTERN>'
```

**Ultra-short form** (combining short flags):
```bash
via -qMmg '<PATTERN>'
```

#### Flag Categories

##### Global Flags (apply to all commands)
- `-v` / `--verbose` - Increase verbosity
- `-q` / `--quiet` - Suppress output
- `--db PATH` - Custom database path

##### Query Mode Flags
- `-M` / `--match` - Enable match mode (required for Sprint 2)

##### Match Syntax Flags (mutually exclusive)
- `-g` / `--glob` - Glob pattern (default)
- `-r` / `--regex` - Regex pattern
- `-s` / `--sql` - SQL LIKE pattern

##### Type Filter Flags (combinable with OR logic)
- `-m` / `--method` - Search methods only
- `-c` / `--class` - Search classes only
- `-f` / `--function` - Search functions only
- `-i` / `--import` - Search imports only
- `-G` / `--global` - Search globals only
- (none) - Search all types (default)

##### Qualifier Flags
- `-I` / `--case-insensitive` - Case-insensitive matching
- `-n N` / `--limit N` - Limit results to N items
- `-F PATTERN` / `--file PATTERN` - Filter by file path

#### Examples

```bash
## Find all methods ending with ToString()
via -qMmg '*ToString()'

## Find classes named User (case-insensitive) with regex
via -qMcrI '^user$'

## Find functions starting with "test_" in test files
via -qMfg 'test_*' -F 'tests/**/*.py'

## Find first 10 imports containing "os" (SQL LIKE)
via -qMis '%os%' -n 10

## Find methods OR functions matching "calculate" pattern
via -qMmfg 'calculate*'

## Case-insensitive search for classes containing "model"
via -qMcgI '*model*'
```

---

### 6. Output Format (Sprint 2 - Text Only)

#### Simple Text Output

For Sprint 2, output will be **simple, plain text** with one result per line.

#### Output Schema

Each result line contains:
```
<type>:<file_path>:<line_number>:<qualified_name>
```

**Fields**:
- `type` - Entity type (method, class, function, import, global)
- `file_path` - Relative path from project root
- `line_number` - Starting line number
- `qualified_name` - Fully qualified name (see section 7)

#### Example Output

```bash
$ via -qMmg '*ToString()'

method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

```bash
$ via -qMcg 'User*'

class:src/models/user.py:10:models.user.User
class:src/models/user.py:89:models.user.UserProfile
class:tests/test_user.py:5:tests.test_user.UserTestCase
```

#### No Header/Footer (Sprint 2)

To support piping, Sprint 2 output has:
- ❌ No header (e.g., "Found 3 results")
- ❌ No footer (e.g., "Total: 3 matches")
- ✅ Only result lines (grep-style)

**Future**: Add `--no-header` / `--no-footer` flags for fine control.

---

### 7. Fully Qualified Names

#### Purpose

Disambiguate entities with the same name across different modules/classes.

#### Qualification Rules

| Entity Type | Qualification Format | Example |
|-------------|---------------------|---------|
| **Module-level Function** | `module.function_name` | `utils.helpers.calculate_total` |
| **Class** | `module.ClassName` | `models.user.User` |
| **Method** | `module.ClassName.method_name` | `models.user.User.__init__` |
| **Import** | `imported_module` | `os.path` |
| **Global** | `module.GLOBAL_NAME` | `config.settings.DEBUG` |

#### Implementation

Qualified names are constructed by:
1. Getting the module path from the file path (e.g., `src/models/user.py` → `models.user`)
2. Appending the class name (if applicable)
3. Appending the entity name

**Note**: The `files` table already stores `file_path` (relative path). We can derive the module path by:
```python
def get_module_path(file_path: str) -> str:
    """Convert file path to module path."""
    # Remove .py extension and convert / to .
    return file_path.replace('/', '.').replace('.py', '')
```

**Database Consideration**: May want to add a `qualified_name` column to entity tables for efficiency.

---

### 8. Query Service Architecture

#### Service Layer

Create a new `QueryService` class in `via/services/query_service.py`.

**Responsibilities**:
1. Accept query parameters (pattern, syntax, types, qualifiers)
2. Validate parameters
3. Build SQL query dynamically based on filters
4. Execute query against database
5. Yield results one at a time (generator pattern)

#### Pattern Matcher Interface

Create pluggable pattern matchers for extensibility:

```python
from abc import ABC, abstractmethod

class PatternMatcher(ABC):
    """Abstract base class for pattern matchers."""

    @abstractmethod
    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        """Convert pattern to SQL WHERE clause."""
        pass

    @abstractmethod
    def matches(self, pattern: str, text: str, case_sensitive: bool) -> bool:
        """Test if text matches pattern (for validation)."""
        pass

class GlobMatcher(PatternMatcher):
    """Glob-style pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        if case_sensitive:
            return f"{column} GLOB '{pattern}'"
        else:
            return f"LOWER({column}) GLOB '{pattern.lower()}'"

class RegexMatcher(PatternMatcher):
    """Regex pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        # SQLite has limited regex support - may need to fetch all and filter in Python
        # For now, use LIKE as fallback or enable regex extension
        raise NotImplementedError("Regex requires SQLite regex extension or Python filtering")

class SqlLikeMatcher(PatternMatcher):
    """SQL LIKE pattern matching."""

    def to_sql_clause(self, pattern: str, column: str, case_sensitive: bool) -> str:
        if case_sensitive:
            # SQLite LIKE is case-insensitive by default, use GLOB for case-sensitive
            return f"{column} GLOB '{pattern.replace('%', '*').replace('_', '?')}'"
        else:
            return f"{column} LIKE '{pattern}'"
```

#### Query Builder

The `QueryService` dynamically builds SQL queries based on:
1. **Entity types selected**: UNION queries across tables
2. **Pattern matcher**: WHERE clause from matcher
3. **File filter**: Additional WHERE clause on `file_path`
4. **Limit**: SQL LIMIT clause

**Example Generated SQL** (for `via -qMmg '*ToString()' -n 10`):

```sql
-- Query methods only
SELECT
    'method' as type,
    f.file_path,
    fn.line_number,
    fn.name,
    fn.parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NOT NULL
  AND fn.name GLOB '*ToString()'
ORDER BY f.file_path, fn.line_number
LIMIT 10
```

**Example for Multiple Types** (`via -qMmfg 'calculate*'`):

```sql
-- Union of methods and functions
SELECT 'method' as type, f.file_path, fn.line_number, fn.name, fn.parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NOT NULL AND fn.name GLOB 'calculate*'

UNION ALL

SELECT 'function' as type, f.file_path, fn.line_number, fn.name, NULL as parent_entity_id
FROM functions fn
JOIN files f ON fn.file_id = f.id
WHERE fn.parent_entity_id IS NULL AND fn.name GLOB 'calculate*'

ORDER BY file_path, line_number
LIMIT <limit_value>
```

---

### 9. Implementation Tasks

#### Story 1: Pattern Matcher Foundation (3 pts, 6h)

**Tasks**:
1. Create `PatternMatcher` ABC in `via/core/pattern_matcher.py`
2. Implement `GlobMatcher` class
3. Implement `SqlLikeMatcher` class
4. Create `MatcherRegistry` for pattern matcher lookup
5. Write 15 unit tests (5 per matcher)

**Acceptance Criteria**:
- ✅ All matchers generate correct SQL clauses
- ✅ Case-sensitive and case-insensitive variants work
- ✅ Unit tests pass with 100% coverage

#### Story 2: Query Service Layer (5 pts, 10h)

**Tasks**:
1. Create `QueryService` class in `via/services/query_service.py`
2. Implement `query()` method with generator pattern
3. Add support for entity type filters (method, class, function, import, global)
4. Add support for file path filters
5. Add support for result limits
6. Build dynamic SQL queries using pattern matchers
7. Handle qualified name construction
8. Write 20 unit tests

**Acceptance Criteria**:
- ✅ Can query by single entity type
- ✅ Can query by multiple entity types (OR logic)
- ✅ File path filtering works
- ✅ Result limiting works
- ✅ Qualified names constructed correctly
- ✅ Yields results one at a time (streaming)

#### Story 3: CLI Query Command (3 pts, 6h)

**Tasks**:
1. Add `query` subcommand to `via/__main__.py`
2. Implement match mode (`-M` / `--match`)
3. Add syntax flags (`-g`, `-r`, `-s`)
4. Add type filter flags (`-m`, `-c`, `-f`, `-i`, `-G`)
5. Add qualifier flags (`-I`, `-n`, `-F`)
6. Wire `QueryService` to CLI
7. Format and print results
8. Write 12 integration tests

**Acceptance Criteria**:
- ✅ All flag combinations work correctly
- ✅ Short flags combine properly (e.g., `-qMmg`)
- ✅ Output format matches specification
- ✅ Error messages are clear and helpful
- ✅ Integration tests pass

#### Story 4: Regex Matcher (Optional - 3 pts, 6h)

**Tasks**:
1. Research SQLite regex extension options
2. Implement `RegexMatcher` (possibly with Python fallback)
3. Add unit tests for regex patterns
4. Update CLI to support `-r` flag

**Acceptance Criteria**:
- ✅ Regex patterns work correctly
- ✅ Performance is acceptable (< 1s for 10k entities)

---

### 10. Success Criteria

Sprint 2 is **DONE** when:

1. ✅ Users can search for entities using glob patterns (`-g`)
2. ✅ Users can search for entities using SQL LIKE patterns (`-s`)
3. ✅ Users can filter by entity type (method, class, function, import, global)
4. ✅ Users can filter by file path
5. ✅ Users can limit results with `-n` flag
6. ✅ Users can toggle case sensitivity with `-I` flag
7. ✅ Output shows: type, file path, line number, qualified name
8. ✅ All short flags work (`-qMmg`, `-qMcr`, etc.)
9. ✅ Results stream (generator pattern) for piping
10. ✅ 47 unit tests pass (15 matcher + 20 service + 12 CLI)
11. ✅ Test coverage > 80%
12. ✅ Documentation updated

**Nice to Have** (Optional):
- ✅ Regex matcher implemented (`-r` flag)

---

### 11. Out of Scope (Deferred to Sprint 3+)

The following features are **explicitly out of scope** for Sprint 2:

#### Rendering Features (Sprint 3)
- `via render` command
- Syntax highlighting with Pygments
- Context lines (`-A`, `-B`, `-C` flags)
- Color scheme configuration

#### Listing Features (Sprint 3)
- `via list` command
- Browse all entities by type

#### Statistics Features (Sprint 3)
- `via stats` command
- Database statistics

#### Output Formats (Sprint 3+)
- JSON output (`-F json`)
- CSV output (`-F csv`)
- JSON Lines output (`-F json_lines`)
- ASCII table output (`-F ascii_table`)

#### Advanced Query Features (Sprint 4+)
- Boolean query operators (AND, OR, NOT)
- Field-specific queries (e.g., search by docstring)
- Cross-project queries
- Query history

---

### 12. Database Schema Notes

#### Current Schema (From Sprint 1)

The existing schema supports all required queries:

**Files Table**:
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL
);
```

**Functions Table** (includes both functions AND methods):
```sql
CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    end_line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    parent_entity_id INTEGER,  -- NULL for functions, set for methods
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Classes Table**:
```sql
CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    end_line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Imports Table**:
```sql
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,
    imported_names TEXT,  -- JSON array
    line_number INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

**Globals Table**:
```sql
CREATE TABLE globals (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

#### Potential Optimization: Add Qualified Name Column

**Consideration**: For performance, we could add a `qualified_name` column to each entity table. This would avoid runtime computation.

**Recommendation**: Start without it. Add it if profiling shows it's a bottleneck.

**Migration Query** (if needed later):
```sql
-- Add qualified_name column to functions table
ALTER TABLE functions ADD COLUMN qualified_name TEXT;

-- Populate it (pseudo-code)
UPDATE functions
SET qualified_name = (
    SELECT replace(replace(file_path, '/', '.'), '.py', '') || '.' ||
           CASE
               WHEN parent_entity_id IS NOT NULL THEN (SELECT name FROM classes WHERE id = parent_entity_id) || '.' || name
               ELSE name
           END
    FROM files WHERE id = functions.file_id
);
```

---

### 13. Testing Strategy

#### Unit Tests (35 tests)

**Pattern Matchers** (15 tests):
- 5 tests for GlobMatcher (pattern conversion, case sensitivity, edge cases)
- 5 tests for SqlLikeMatcher
- 5 tests for RegexMatcher (if implemented)

**Query Service** (20 tests):
- 5 tests for single entity type queries
- 5 tests for multiple entity type queries
- 3 tests for file path filtering
- 3 tests for result limiting
- 4 tests for qualified name construction

#### Integration Tests (12 tests)

**CLI Tests** (12 tests):
- Test glob pattern matching
- Test SQL LIKE pattern matching
- Test entity type filtering (each type individually)
- Test multiple entity types (OR logic)
- Test file path filtering
- Test result limiting
- Test case-insensitive flag
- Test combined short flags (`-qMmg`)
- Test error handling (invalid pattern, no results)
- Test output format (verify each field)

#### Test Coverage Target

**Goal**: > 80% coverage for new code

**Critical Areas**:
- QueryService: 100% coverage
- Pattern matchers: 100% coverage
- CLI query subcommand: > 90% coverage

---

### 14. Documentation Requirements

#### User-Facing Documentation

1. **README.md**: Update with `via query` examples
2. **USAGE.md**: Create detailed usage guide with all flag combinations

#### Developer Documentation

1. **ARCHITECTURE.md**: Document QueryService and pattern matcher architecture
2. **API.md**: Document QueryService public API for future integrations

#### Inline Documentation

1. **Docstrings**: All public methods must have docstrings
2. **TLDR sections**: Follow Oracle's template for all new files

---

### 15. Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Simple query (< 100 results) | < 100ms | `via -qMmg 'User' -n 100` |
| Complex query (< 1000 results) | < 500ms | `via -qMmfg 'test_*'` |
| Large query (< 10k results) | < 2s | `via -qMg '*'` (all entities) |

**Optimization Strategy**:
1. Use database indexes on `name` columns
2. Use SQL GLOB/LIKE natively (avoid Python filtering)
3. Stream results (generator pattern) to avoid memory overhead

---

### Next Steps

1. **@Morpheus**: Review architecture, suggest optimizations, validate SQL query generation strategy
2. **@Mouse**: Create detailed task breakdown from 4 stories
3. **@Neo**: Implement stories in priority order (1 → 2 → 3 → 4)
4. **@Trin**: Create test plan and acceptance criteria checklist

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Ready for Technical Review
**Review Date**: 2026-01-12


---


## SPRINT_2_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_2_USER_STORIES.md`


## Sprint 2 User Stories - Query Command (Match-Style Filtering)

**Created**: 2026-01-12 (Revised)
**Product Manager**: @Cypher
**Sprint Goal**: Implement `via query` command with match-style filtering for searching indexed code

---

### Sprint 2 Overview

**Goal**: Enable users to search indexed code using flexible pattern matching.

**Scope**:
- `via query` command with match mode (`-M`)
- 3 match syntaxes: glob, regex, SQL LIKE
- 5 entity type filters: method, class, function, import, global
- Simple text output (no rendering)

**Out of Scope** (Sprint 3+):
- `via render` command (syntax highlighting, context lines)
- `via list` command
- `via stats` command
- Multiple output formats (JSON, CSV, etc.)

---

### User Stories

#### Story 1: Pattern Matcher Foundation (3 pts)
**As a** developer
**I want** pluggable pattern matching strategies
**So that** I can search using glob, regex, or SQL LIKE patterns

**Acceptance Criteria**:
- [ ] Create `PatternMatcher` abstract base class in `via/core/pattern_matcher.py`
- [ ] Implement `GlobMatcher` with SQLite GLOB support
- [ ] Implement `SqlLikeMatcher` with SQLite LIKE support
- [ ] Create `MatcherRegistry` for pattern matcher lookup
- [ ] Support case-sensitive and case-insensitive matching
- [ ] Each matcher generates correct SQL WHERE clauses
- [ ] Unit tests with 100% coverage (15 tests total)

**Tasks**:
- [S1.1] Design `PatternMatcher` ABC interface (0.5h)
- [S1.2] Implement `GlobMatcher` class (1.5h)
- [S1.3] Implement `SqlLikeMatcher` class (1h)
- [S1.4] Create `MatcherRegistry` class (0.5h)
- [S1.5] Unit tests for GlobMatcher (1h)
- [S1.6] Unit tests for SqlLikeMatcher (1h)
- [S1.7] Unit tests for MatcherRegistry (0.5h)

**Estimated**: 6h

**Example Code**:
```python
## Usage
matcher = GlobMatcher()
sql = matcher.to_sql_clause('*ToString()', 'name', case_sensitive=False)
## Output: "LOWER(name) GLOB '*tostring()'"
```

---

#### Story 2: Query Service Layer (5 pts)
**As a** developer
**I want** a query service that searches the database using pattern matching
**So that** I can find code entities by pattern, type, and file path

**Acceptance Criteria**:
- [ ] Create `QueryService` class in `via/services/query_service.py`
- [ ] Support entity type filtering (method, class, function, import, global, all)
- [ ] Support multiple entity types with OR logic
- [ ] Support file path filtering (glob patterns)
- [ ] Support result limiting (`--limit N`)
- [ ] Build dynamic SQL queries using pattern matchers
- [ ] Construct fully qualified names (e.g., `module.Class.method`)
- [ ] Yield results as generator (streaming for pipes)
- [ ] Return structured results (type, file_path, line_number, qualified_name)
- [ ] Unit tests with 90%+ coverage (20 tests total)

**Tasks**:
- [S2.1] Design QueryService interface and result dataclass (1h)
- [S2.2] Implement single entity type queries (2h)
- [S2.3] Implement multiple entity type queries (UNION ALL) (2h)
- [S2.4] Implement file path filtering (1h)
- [S2.5] Implement result limiting (0.5h)
- [S2.6] Implement qualified name construction (1.5h)
- [S2.7] Unit tests for QueryService (2h)

**Estimated**: 10h

**Example Code**:
```python
## Usage
service = QueryService(db_store)
results = service.query(
    pattern='*ToString()',
    matcher='glob',
    entity_types=['method'],
    file_filter='src/**/*.py',
    case_sensitive=False,
    limit=10
)

for result in results:
    print(f"{result.type}:{result.file_path}:{result.line_number}:{result.qualified_name}")
```

---

#### Story 3: CLI Query Command (3 pts)
**As a** developer
**I want** a `via query` command with ultra-short syntax
**So that** I can quickly search my codebase from the command line

**Acceptance Criteria**:
- [ ] Implement `via query` subcommand in `via/__main__.py`
- [ ] Support match mode flag (`-M` / `--match`)
- [ ] Support syntax flags: `-g` (glob), `-r` (regex), `-s` (sql)
- [ ] Support type flags: `-m` (method), `-c` (class), `-f` (function), `-i` (import), `-G` (global)
- [ ] Support qualifier flags: `-I` (case-insensitive), `-n N` (limit), `-F PATTERN` (file filter)
- [ ] Support ultra-short combined syntax (e.g., `-qMmg`)
- [ ] Wire QueryService to CLI
- [ ] Format output as: `type:file_path:line_number:qualified_name`
- [ ] Stream output for piping (no header/footer)
- [ ] Handle errors gracefully (no results, invalid pattern, etc.)
- [ ] Integration tests (12 tests total)

**Command Syntax**:
```bash
## Long form
via query --match <PATTERN> --glob --method --case-insensitive

## Short form
via -qMmg '<PATTERN>'

## Examples
via -qMmg '*ToString()'                      # Find methods ending with ToString()
via -qMcrI '^user$'                          # Find classes named "user" (case-insensitive, regex)
via -qMfg 'test_*' -F 'tests/**/*.py'        # Find test functions in tests/
via -qMmfg 'calculate*' -n 10                # Find methods or functions, limit to 10
```

**Tasks**:
- [S3.1] Add `query` subcommand to argparse (1h)
- [S3.2] Add all flags (match mode, syntax, types, qualifiers) (1.5h)
- [S3.3] Wire QueryService to CLI (1h)
- [S3.4] Implement result formatting (0.5h)
- [S3.5] Add error handling (0.5h)
- [S3.6] Integration tests for CLI (1.5h)

**Estimated**: 6h

**Output Format**:
```
method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

---

#### Story 4: Regex Matcher (Optional - 3 pts)
**As a** developer
**I want** full regex pattern matching
**So that** I can use advanced patterns for complex searches

**Acceptance Criteria**:
- [ ] Implement `RegexMatcher` class
- [ ] Support full Python regex syntax
- [ ] Research SQLite regex extension options
- [ ] Implement Python-side filtering if SQLite regex unavailable
- [ ] Support case-sensitive and case-insensitive modes
- [ ] Performance acceptable (< 1s for 10k entities)
- [ ] Unit tests with 100% coverage (5 tests)

**Tasks**:
- [S4.1] Research SQLite regex extension (0.5h)
- [S4.2] Implement RegexMatcher (3h)
- [S4.3] Add performance optimization (1h)
- [S4.4] Unit tests (1.5h)

**Estimated**: 6h

**Note**: This story is optional if time permits. Regex support can be deferred to Sprint 3.

---

### Story Point Summary

| Story | Priority | Points | Est Hours |
|-------|----------|--------|-----------|
| S1: Pattern Matcher | **P0** | 3 | 6h |
| S2: Query Service | **P0** | 5 | 10h |
| S3: CLI Query | **P0** | 3 | 6h |
| S4: Regex Matcher | **P1** (optional) | 3 | 6h |
| **TOTAL (P0)** | | **11** | **22h** |
| **TOTAL (P0+P1)** | | **14** | **28h** |

---

### Sprint 2 Dependencies

#### From Sprint 1 (Complete)
- ✅ Database schema with all entity tables (files, functions, classes, imports, globals)
- ✅ DatabaseStore with CRUD operations
- ✅ CLI framework with argparse
- ✅ Test infrastructure (pytest)

#### New Dependencies
- None required for P0 stories
- SQLite regex extension (optional, for Story 4)

---

### Implementation Order

#### Phase 1: Pattern Matcher Foundation (Day 1)
1. **Story 1: Pattern Matcher** (6h)
   - Build pluggable matcher architecture
   - Implement glob and SQL LIKE matchers
   - Full test coverage

**Deliverable**: Pattern matcher infrastructure ready

#### Phase 2: Query Service (Day 2)
2. **Story 2: Query Service** (10h)
   - Build query engine with dynamic SQL generation
   - Support all entity type filters
   - Streaming results with generators

**Deliverable**: QueryService with full test coverage

#### Phase 3: CLI Integration (Day 3)
3. **Story 3: CLI Query** (6h)
   - Wire everything to CLI
   - Support ultra-short syntax
   - Integration tests

**Deliverable**: Working `via query` command

#### Phase 4: Regex Support (Optional - Day 4)
4. **Story 4: Regex Matcher** (6h)
   - Add regex pattern support
   - Optimize performance

**Deliverable**: Regex pattern matching

---

### Acceptance Criteria for Sprint 2

Sprint 2 is **DONE** when:

1. ✅ Users can search by glob patterns (`via -qMmg '*pattern'`)
2. ✅ Users can search by SQL LIKE patterns (`via -qMms '%pattern%'`)
3. ✅ Users can filter by entity type (method, class, function, import, global)
4. ✅ Users can filter by multiple types with OR logic (`via -qMmfg 'pattern'`)
5. ✅ Users can filter by file path (`via -qMmg 'pattern' -F 'src/**/*.py'`)
6. ✅ Users can limit results (`via -qMmg 'pattern' -n 10`)
7. ✅ Users can toggle case sensitivity (`via -qMmgI 'pattern'`)
8. ✅ Output shows: type, file_path, line_number, qualified_name
9. ✅ Results stream for piping to `less`, `grep`, etc.
10. ✅ All P0 stories have tests (47 total: 15 matcher + 20 service + 12 CLI)
11. ✅ Test coverage > 80%
12. ✅ Documentation updated

**Optional** (if Story 4 completed):
- ✅ Users can search by regex patterns (`via -qMmr '.*pattern$'`)

---

### Example Usage

```bash
## Find all methods ending with ToString()
via -qMmg '*ToString()'

## Find classes named "User" (case-insensitive)
via -qMcgI 'user'

## Find functions starting with "test_" in test files
via -qMfg 'test_*' -F 'tests/**/*.py'

## Find first 10 imports containing "os"
via -qMis '%os%' -n 10

## Find methods OR functions matching "calculate" pattern
via -qMmfg 'calculate*'

## Case-insensitive search for classes containing "model"
via -qMcgI '*model*'

## Regex search for magic methods (if Story 4 complete)
via -qMmr '__(init|str|repr)__'

## Pipe results to less for browsing
via -qMfg 'test_*' | less

## Count matching results
via -qMcg 'User*' | wc -l

## Search and filter with grep
via -qMmg '*' | grep 'src/models'
```

---

### Output Format (Sprint 2 - Simple Text)

**Format**: `type:file_path:line_number:qualified_name`

**Example Output**:
```
method:src/models/user.py:45:models.user.User.ToString
method:src/models/post.py:78:models.post.Post.ToString
method:src/utils/helpers.py:12:utils.helpers.Helper.ToString
```

**Future Formats** (Sprint 3+):
- JSON: `--format json`
- CSV: `--format csv`
- Table: `--format table`

---

### Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex performance on large databases | Medium | Use Python-side filtering with generator pattern |
| SQLite GLOB/LIKE case-sensitivity platform differences | Low | Explicit UPPER()/LOWER() conversion |
| Complex query patterns causing SQL errors | Medium | Validate patterns before query, catch SQL exceptions |
| Qualified name construction edge cases | Low | Comprehensive unit tests for all entity types |

---

### Technical Notes

#### Entity Type to Database Mapping

| Entity Type | Database Query |
|-------------|----------------|
| **method** | `SELECT FROM functions WHERE parent_entity_id IS NOT NULL` |
| **function** | `SELECT FROM functions WHERE parent_entity_id IS NULL` |
| **class** | `SELECT FROM classes` |
| **import** | `SELECT FROM imports` |
| **global** | `SELECT FROM globals` |
| **all** | UNION ALL of above queries |

#### Qualified Name Construction

- **Function**: `module.function_name`
  - Example: `utils.helpers.calculate_total`
- **Method**: `module.ClassName.method_name`
  - Example: `models.user.User.__init__`
- **Class**: `module.ClassName`
  - Example: `models.user.User`
- **Import**: `module_name`
  - Example: `os.path`
- **Global**: `module.GLOBAL_NAME`
  - Example: `config.settings.DEBUG`

#### Module Path Derivation

```python
def get_module_path(file_path: str) -> str:
    """Convert file path to module path.

    Example: 'src/models/user.py' -> 'models.user'
    """
    # Remove .py extension and convert / to .
    path = file_path.replace('.py', '').replace('/', '.')

    # Remove 'src.' prefix if present
    if path.startswith('src.'):
        path = path[4:]

    return path
```

---

### Deferred to Sprint 3+

The following features are **explicitly out of scope** for Sprint 2:

#### Rendering Features (Sprint 3)
- `via render` command
- Syntax highlighting with Pygments
- Context lines (`-A`, `-B`, `-C` flags)
- Color scheme configuration

#### Listing Features (Sprint 3)
- `via list` command
- Browse all entities by type

#### Statistics Features (Sprint 3)
- `via stats` command
- Database statistics

#### Output Formats (Sprint 3+)
- JSON output (`--format json`)
- CSV output (`--format csv`)
- JSON Lines output (`--format json_lines`)
- ASCII table output (`--format table`)

#### Advanced Query Features (Sprint 4+)
- Boolean operators (AND, OR, NOT)
- Field-specific queries (docstring search)
- Cross-project queries
- Query history

---

**Created by**: @Cypher (Product Manager)
**Status**: ✅ Ready for Sprint Planning (@Mouse)
**Next**: @Mouse create detailed task breakdown


---


## SPRINT_2_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_2_TASKS.md`


## Sprint 2 Task Breakdown - Match Command (v5.0 Denormalized)

**Created**: 2026-01-13
**Task Manager**: @Mouse
**Architecture**: v5.0 Denormalized (single `symbols` table)
**Sprint Goal**: Implement `via match` command with simple pattern matching

---

### Overview

**Architecture Change**: v5.0 uses a denormalized `symbols` table, eliminating JOINs and SQL templates. This drastically simplifies implementation.

**Key Simplifications**:
- No PatternMatcher classes needed (just enum values)
- No QueryService layer (DatabaseStore.match() is sufficient)
- Trivial SQL: `SELECT * FROM symbols WHERE symbol_type = ? AND symbol_name {op} ?`

---

### Phase 1: Schema Migration (CRITICAL - Must Complete First)

#### Task 1.1: Create New Schema (2h)
**Owner**: @Neo
**Priority**: P0 - BLOCKER
**File**: `via/db/schema.py`

**Subtasks**:
- [x] Review current schema (functions, classes, imports, globals, files tables)
- [ ] Create `symbols` table schema with indexes
- [ ] Create `references` table schema (for future use)
- [ ] Update `SCHEMA_VERSION` to 2
- [ ] Keep `files` table for metadata
- [ ] Add schema migration logic for v1 → v2

**Schema Details**:
```sql
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_name TEXT NOT NULL,
    symbol_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    byte_offset INTEGER,
    byte_length INTEGER,
    qualified_name TEXT NOT NULL,
    parent_name TEXT
);

CREATE INDEX idx_symbols_name ON symbols(symbol_name);
CREATE INDEX idx_symbols_type ON symbols(symbol_type);
CREATE INDEX idx_symbols_type_name ON symbols(symbol_type, symbol_name);
CREATE INDEX idx_symbols_file ON symbols(file_path);

CREATE TABLE references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol_id INTEGER NOT NULL,
    to_symbol_id INTEGER NOT NULL,
    reference_type TEXT NOT NULL,
    line_number INTEGER,
    FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    FOREIGN KEY (to_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
);

CREATE INDEX idx_references_from ON references(from_symbol_id);
CREATE INDEX idx_references_to ON references(to_symbol_id);
CREATE INDEX idx_references_type ON references(reference_type);
```

**Acceptance Criteria**:
- [ ] Schema v2 defined in schema.py
- [ ] Migration logic handles v1 databases
- [ ] New databases create v2 schema
- [ ] `files` table retained for metadata
- [ ] All indexes created

**Estimated**: 2h

---

#### Task 1.2: Migrate Indexer to Symbols Table (4h)
**Owner**: @Neo
**Priority**: P0 - BLOCKER
**Files**: `via/indexer/*.py`

**Subtasks**:
- [ ] Update function indexing to insert into `symbols` table
- [ ] Update class indexing to insert into `symbols` table
- [ ] Update import indexing to insert into `symbols` table
- [ ] Update global indexing to insert into `symbols` table
- [ ] Add file path indexing (filename + filepath types)
- [ ] Calculate qualified names during indexing
- [ ] Track parent_name for methods
- [ ] Remove old table inserts (functions, classes, imports, globals)

**Qualified Name Logic**:
```python
def calculate_qualified_name(file_path, entity_name, parent_class=None):
    """Calculate fully qualified name for entity."""
    # Convert file path to module: src/models/user.py -> models.user
    module = file_path.replace('.py', '').replace('/', '.')
    if module.startswith('src.'):
        module = module[4:]

    # Build qualified name
    if parent_class:
        return f"{module}.{parent_class}.{entity_name}"
    else:
        return f"{module}.{entity_name}"
```

**Acceptance Criteria**:
- [ ] All entity types insert into `symbols` table
- [ ] Qualified names calculated correctly
- [ ] Parent class names tracked for methods
- [ ] Byte offset and length captured
- [ ] File entries created for filename/filepath matching
- [ ] Old table inserts removed
- [ ] Existing tests updated

**Estimated**: 4h

---

#### Task 1.3: Test Schema Migration (1h)
**Owner**: @Trin
**Priority**: P0
**Files**: `tests/db/test_schema_migration.py`

**Subtasks**:
- [ ] Test v1 → v2 migration on existing database
- [ ] Test fresh v2 schema creation
- [ ] Verify all indexes created
- [ ] Verify data integrity after migration
- [ ] Test rollback if migration fails

**Acceptance Criteria**:
- [ ] Migration tests pass
- [ ] No data loss during migration
- [ ] Indexes functioning
- [ ] Can query migrated data

**Estimated**: 1h

---

### Phase 2: Core Types (Simple)

#### Task 2.1: Create Core Types (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/core/types.py`

**Subtasks**:
- [ ] Create `SymbolType` enum (method, class, function, filepath, filename, import, global)
- [ ] Create `MatchOp` enum (EXACT, GLOB, LIKE, REGEXP)
- [ ] Create `MatchResult` dataclass

**Code**:
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class SymbolType(Enum):
    """Symbol types for matching."""
    METHOD = 'method'
    CLASS = 'class'
    FUNCTION = 'function'
    FILEPATH = 'filepath'
    FILENAME = 'filename'
    IMPORT = 'import'
    GLOBAL = 'global'


class MatchOp(Enum):
    """Match operators mapping to SQL operators."""
    # (name, sql_op, needs_escaping)
    EXACT = ('exact', '=', True)
    GLOB = ('glob', 'GLOB', True)
    LIKE = ('like', 'LIKE', True)
    REGEXP = ('regexp', 'REGEXP', True)

    def __init__(self, op_name, sql_op, needs_escaping):
        self.op_name = op_name
        self.sql_op = sql_op
        self.needs_escaping = needs_escaping


@dataclass
class MatchResult:
    """Match result with position information."""
    symbol_type: str
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: Optional[int]
    byte_offset: Optional[int]
    byte_length: Optional[int]
    parent_name: Optional[str]
```

**Acceptance Criteria**:
- [ ] All enums defined
- [ ] MatchResult dataclass complete
- [ ] Type hints correct

**Estimated**: 1h

---

### Phase 3: Database Match Method (Simple)

#### Task 3.1: Implement DatabaseStore.match() (2h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/db/store.py`

**Subtasks**:
- [ ] Add `match()` method to DatabaseStore
- [ ] Build simple WHERE clause dynamically
- [ ] Support case-sensitive/insensitive matching
- [ ] Support result limit
- [ ] Yield MatchResult objects
- [ ] Handle SQL escaping

**Code**:
```python
def match(
    self,
    symbol_type: SymbolType,
    match_op: MatchOp,
    pattern: str,
    case_sensitive: bool = True,
    limit: Optional[int] = None
) -> Iterator[MatchResult]:
    """Match symbols using denormalized table."""
    # Build WHERE clause
    where_parts = ["symbol_type = ?"]
    params = [symbol_type.value]

    # Add name match
    column = "symbol_name"
    if not case_sensitive:
        column = "LOWER(symbol_name)"
        pattern = pattern.lower()

    # Escape if needed
    if match_op.needs_escaping:
        pattern = pattern.replace("'", "''")

    where_parts.append(f"{column} {match_op.sql_op} ?")
    params.append(pattern)

    # Build query
    query = f"""
        SELECT symbol_name, symbol_type, file_path, line_number,
               byte_offset, byte_length, qualified_name, parent_name
        FROM symbols
        WHERE {' AND '.join(where_parts)}
        ORDER BY file_path, line_number
    """

    if limit:
        query += f"\nLIMIT {limit}"

    # Execute and yield
    cursor = self.conn.execute(query, params)
    for row in cursor:
        yield MatchResult(
            symbol_name=row[0],
            symbol_type=row[1],
            file_path=row[2],
            line_number=row[3],
            byte_offset=row[4],
            byte_length=row[5],
            qualified_name=row[6],
            parent_name=row[7]
        )
```

**Acceptance Criteria**:
- [ ] match() method implemented
- [ ] WHERE clause construction works
- [ ] All MatchOp operators supported
- [ ] Case sensitivity works
- [ ] Limit works
- [ ] Returns MatchResult generator

**Estimated**: 2h

---

#### Task 3.2: Unit Test DatabaseStore.match() (2h)
**Owner**: @Trin
**Priority**: P0
**File**: `tests/db/test_store_match.py`

**Test Cases**:
- [ ] Test each SymbolType (7 tests)
- [ ] Test each MatchOp (4 tests)
- [ ] Test case-insensitive matching (1 test)
- [ ] Test limit (1 test)
- [ ] Test empty results (1 test)
- [ ] Test byte_offset/byte_length in results (1 test)

**Total Tests**: 15

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 100% coverage of match() method

**Estimated**: 2h

---

### Phase 4: CLI Integration

#### Task 4.1: Add Match Subcommand (2h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Add `match` subcommand (alias `m`) to argparse
- [ ] Add `-t/--type` flag (choices: method, class, function, etc.)
- [ ] Add pattern positional argument
- [ ] Add `-g/--glob` flag (default)
- [ ] Add `-r/--regex` flag
- [ ] Add `-s/--sql` flag (SQL LIKE)
- [ ] Add `-I/--case-insensitive` flag
- [ ] Add `-n/--limit` flag
- [ ] Wire to DatabaseStore.match()

**Command Examples**:
```bash
via match -t method -g '*save()'
via m -t class -r '^User'
via m -t function -s 'test_%' -I
via m -t method '*ToString()' -n 10
```

**Acceptance Criteria**:
- [ ] match subcommand works
- [ ] All flags implemented
- [ ] Short alias `m` works
- [ ] Calls DatabaseStore.match() correctly

**Estimated**: 2h

---

#### Task 4.2: Implement Output Formatting (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Format as `type:file_path:line_number:qualified_name`
- [ ] Add byte position if available: `:@byte_offset+byte_length`
- [ ] Stream output (no header/footer)
- [ ] Handle empty results gracefully

**Output Format**:
```
method:src/models/user.py:45:models.user.User.save:@1234+56
class:src/models/user.py:10:models.user.User:@234+1000
function:src/utils.py:15:utils.calculate_sum:@567+48
file:src/utils.py:0:src/utils.py
```

**Acceptance Criteria**:
- [ ] Output format correct
- [ ] Byte position included when available
- [ ] Streams for piping
- [ ] No errors on empty results

**Estimated**: 1h

---

#### Task 4.3: Add Error Handling (1h)
**Owner**: @Neo
**Priority**: P0
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Handle invalid symbol type
- [ ] Handle invalid pattern (malformed regex/glob)
- [ ] Handle database not found
- [ ] Handle database corruption
- [ ] Provide helpful error messages

**Acceptance Criteria**:
- [ ] Graceful error handling
- [ ] User-friendly messages
- [ ] Non-zero exit codes on error

**Estimated**: 1h

---

### Phase 5: Integration Testing

#### Task 5.1: CLI Integration Tests (3h)
**Owner**: @Trin
**Priority**: P0
**File**: `tests/cli/test_match_command.py`

**Test Cases**:
- [ ] Test match with each SymbolType (7 tests)
- [ ] Test GLOB matching (1 test)
- [ ] Test REGEXP matching (1 test)
- [ ] Test SQL LIKE matching (1 test)
- [ ] Test case-insensitive flag (1 test)
- [ ] Test limit flag (1 test)
- [ ] Test output format (1 test)
- [ ] Test byte position in output (1 test)
- [ ] Test empty results (1 test)
- [ ] Test error cases (3 tests)

**Total Tests**: 18

**Acceptance Criteria**:
- [ ] All integration tests pass
- [ ] Tests use real indexed database
- [ ] Output format validated
- [ ] Error handling tested

**Estimated**: 3h

---

#### Task 5.2: End-to-End Testing (2h)
**Owner**: @Trin
**Priority**: P1
**File**: `tests/e2e/test_match_workflow.py`

**Test Scenarios**:
- [ ] Index codebase → match methods → verify results
- [ ] Index codebase → match classes → verify qualified names
- [ ] Index codebase → match files → verify file paths
- [ ] Complex patterns (wildcards, regex)
- [ ] Case-insensitive searches
- [ ] Large result sets with limit

**Acceptance Criteria**:
- [ ] E2E workflow works
- [ ] Realistic test data
- [ ] Performance acceptable

**Estimated**: 2h

---

### Phase 6: Documentation

#### Task 6.1: Update README (1h)
**Owner**: @Neo
**Priority**: P1
**File**: `README.md`

**Subtasks**:
- [ ] Add `via match` command documentation
- [ ] Add usage examples
- [ ] Add pattern syntax guide
- [ ] Update feature list

**Estimated**: 1h

---

#### Task 6.2: Add Command Help (0.5h)
**Owner**: @Neo
**Priority**: P1
**File**: `via/__main__.py`

**Subtasks**:
- [ ] Add detailed help text for match command
- [ ] Add examples in help
- [ ] Document all flags

**Estimated**: 0.5h

---

### Task Summary

#### By Phase

| Phase | Tasks | Est Hours | Priority |
|-------|-------|-----------|----------|
| 1. Schema Migration | 3 | 7h | P0 |
| 2. Core Types | 1 | 1h | P0 |
| 3. Database Match | 2 | 4h | P0 |
| 4. CLI Integration | 3 | 4h | P0 |
| 5. Integration Testing | 2 | 5h | P0 |
| 6. Documentation | 2 | 1.5h | P1 |
| **TOTAL P0** | **11** | **21h** | |
| **TOTAL P0+P1** | **13** | **22.5h** | |

#### By Owner

| Owner | Tasks | Est Hours |
|-------|-------|-----------|
| @Neo | 8 | 13.5h |
| @Trin | 4 | 8h |
| @Mouse | 1 | 1h (this doc) |
| **TOTAL** | **13** | **22.5h** |

---

### Critical Path

**BLOCKERS** (must complete in order):
1. Task 1.1: Create New Schema (2h)
2. Task 1.2: Migrate Indexer (4h)
3. Task 1.3: Test Schema Migration (1h)

**PARALLEL** (can work simultaneously after blockers):
- Task 2.1: Core Types (1h)
- Task 3.1: DatabaseStore.match() (2h)
- Task 4.1: CLI Integration (2h)

**PARALLEL TESTING** (after implementation):
- Task 3.2: Unit Tests (2h)
- Task 5.1: Integration Tests (3h)
- Task 5.2: E2E Tests (2h)

**FINAL**:
- Task 6.1: Documentation (1h)
- Task 6.2: Help Text (0.5h)

**Total Critical Path**: ~7h (if perfectly parallel) to ~22.5h (if sequential)

---

### Risk Assessment

#### High Risk
- **Schema Migration**: Breaking change to database schema
  - **Mitigation**: Thorough migration testing, backup before migration
  - **Fallback**: Keep migration reversible

#### Medium Risk
- **Indexer Changes**: Must update all entity indexing logic
  - **Mitigation**: Update tests first, then implementation
  - **Fallback**: Can revert to v1 schema if needed

#### Low Risk
- **CLI Integration**: Straightforward wiring
- **Match Logic**: Simple SQL, well-defined

---

### Definition of Done

Sprint 2 is complete when:
- ✅ Schema v2 created and tested
- ✅ Indexer populates `symbols` table correctly
- ✅ `via match` command works with all flags
- ✅ All unit tests pass (15+ tests)
- ✅ All integration tests pass (18+ tests)
- ✅ E2E tests pass
- ✅ Documentation updated
- ✅ Help text complete
- ✅ Zero regressions in `via index` command

---

### Notes

**Architecture Benefits**:
- Much simpler than original user stories (no PatternMatcher classes, no QueryService)
- Denormalized schema eliminates all complexity
- Single query pattern for all symbol types
- Easy to test and maintain

**Deferred to Sprint 3**:
- Multiple match clauses with AND logic
- File path filtering (`-F` flag)
- `via render` command
- Multiple output formats (JSON, CSV)

**Comparison to Original Estimate**:
- Original user stories: 22-28h
- New v5.0 tasks: 22.5h
- Similar time but MUCH simpler implementation!

---

**Created by**: @Mouse (Task Manager)
**Reviewed by**: @Morpheus (Architecture alignment)
**Status**: ✅ Ready for Sprint Planning
**Next**: @Neo start Phase 1 (Schema Migration)


---


## SPRINT_2_TEST_PLAN.md

**Original Location**: `agents/trin.docs/archive/SPRINT_2_TEST_PLAN.md`


## Sprint 2 Test Plan - Match Command

**Created**: 2026-01-13
**QA Engineer**: @Trin
**Feature**: `via match` command with denormalized symbols table
**Architecture**: v5.0 (Denormalized)

---

### Test Strategy

**Approach**: Bottom-up testing from unit tests to integration tests

**Test Pyramid**:
1. **Unit Tests** (70%): Test individual components in isolation
2. **Integration Tests** (25%): Test CLI → Database → Output flow
3. **End-to-End Tests** (5%): Test complete user workflows

**Coverage Goal**: 95%+ for new code

---

### Test Suite 1: Core Types Unit Tests

**File**: `tests/unit/test_core_types.py`

#### Test 1.1: SymbolType Enum
**Purpose**: Verify SymbolType enum has all required values

```python
def test_symbol_type_enum_values():
    """Test that SymbolType has all required enum values."""
    assert SymbolType.METHOD.value == 'method'
    assert SymbolType.CLASS.value == 'class'
    assert SymbolType.FUNCTION.value == 'function'
    assert SymbolType.FILEPATH.value == 'filepath'
    assert SymbolType.FILENAME.value == 'filename'
    assert SymbolType.IMPORT.value == 'import'
    assert SymbolType.GLOBAL.value == 'global'

def test_symbol_type_count():
    """Test that we have exactly 7 symbol types."""
    assert len(SymbolType) == 7
```

#### Test 1.2: MatchOp Enum
**Purpose**: Verify MatchOp enum has correct SQL operator mappings

```python
def test_match_op_exact():
    """Test EXACT match operator."""
    assert MatchOp.EXACT.op_name == 'exact'
    assert MatchOp.EXACT.sql_op == '='
    assert MatchOp.EXACT.needs_escaping is True

def test_match_op_glob():
    """Test GLOB match operator."""
    assert MatchOp.GLOB.op_name == 'glob'
    assert MatchOp.GLOB.sql_op == 'GLOB'
    assert MatchOp.GLOB.needs_escaping is True

def test_match_op_like():
    """Test LIKE match operator."""
    assert MatchOp.LIKE.op_name == 'like'
    assert MatchOp.LIKE.sql_op == 'LIKE'
    assert MatchOp.LIKE.needs_escaping is True

def test_match_op_regexp():
    """Test REGEXP match operator."""
    assert MatchOp.REGEXP.op_name == 'regexp'
    assert MatchOp.REGEXP.sql_op == 'REGEXP'
    assert MatchOp.REGEXP.needs_escaping is True
```

#### Test 1.3: MatchResult Dataclass
**Purpose**: Verify MatchResult dataclass and string formatting

```python
def test_match_result_creation():
    """Test creating a MatchResult."""
    result = MatchResult(
        symbol_type='method',
        symbol_name='save',
        qualified_name='models.user.User.save',
        file_path='src/models/user.py',
        line_number=45,
        byte_offset=1234,
        byte_length=56,
        parent_name='User'
    )
    assert result.symbol_type == 'method'
    assert result.symbol_name == 'save'
    assert result.qualified_name == 'models.user.User.save'

def test_match_result_str_with_byte_position():
    """Test MatchResult string formatting with byte position."""
    result = MatchResult(
        symbol_type='method',
        symbol_name='save',
        qualified_name='models.user.User.save',
        file_path='src/models/user.py',
        line_number=45,
        byte_offset=1234,
        byte_length=56,
        parent_name='User'
    )
    expected = 'method:src/models/user.py:45:models.user.User.save:@1234+56'
    assert str(result) == expected

def test_match_result_str_without_byte_position():
    """Test MatchResult string formatting without byte position."""
    result = MatchResult(
        symbol_type='filepath',
        symbol_name='user.py',
        qualified_name='src/models/user.py',
        file_path='src/models/user.py',
        line_number=0,
        byte_offset=None,
        byte_length=None,
        parent_name=None
    )
    expected = 'filepath:src/models/user.py:0:src/models/user.py'
    assert str(result) == expected
```

**Total Test 1**: 10 tests

---

### Test Suite 2: DatabaseStore.match() Unit Tests

**File**: `tests/unit/test_database_match.py`

#### Setup Fixture
```python
@pytest.fixture
def test_db():
    """Create a test database with sample symbols."""
    db = DatabaseStore(':memory:', '/test/root')
    db.connect()
    db.initialize_schema()

    # Insert test symbols
    db.insert_symbol('save', 'method', 'src/user.py', 10, 'user.User.save', 100, 50, 'User')
    db.insert_symbol('load', 'method', 'src/user.py', 20, 'user.User.load', 200, 40, 'User')
    db.insert_symbol('User', 'class', 'src/user.py', 5, 'user.User', 50, 200, None)
    db.insert_symbol('calculate', 'function', 'src/utils.py', 15, 'utils.calculate', 300, 80, None)
    db.insert_symbol('user.py', 'filename', 'src/user.py', 0, 'src/user.py', None, None, None)
    db.insert_symbol('json', 'import', 'src/user.py', 1, 'json', 0, 11, None)
    db.insert_symbol('MAX_SIZE', 'global', 'src/config.py', 3, 'config.MAX_SIZE', 30, 15, None)

    yield db
    db.close()
```

#### Test 2.1: Match by Symbol Type
**Purpose**: Verify matching works for each symbol type

```python
def test_match_methods(test_db):
    """Test matching methods."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True))
    assert len(results) == 2
    assert all(r.symbol_type == 'method' for r in results)

def test_match_classes(test_db):
    """Test matching classes."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'User'

def test_match_functions(test_db):
    """Test matching functions."""
    results = list(test_db.match(SymbolType.FUNCTION, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'calculate'

def test_match_filenames(test_db):
    """Test matching filenames."""
    results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'user.py'

def test_match_imports(test_db):
    """Test matching imports."""
    results = list(test_db.match(SymbolType.IMPORT, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'json'

def test_match_globals(test_db):
    """Test matching globals."""
    results = list(test_db.match(SymbolType.GLOBAL, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'MAX_SIZE'
```

#### Test 2.2: Match by Operator
**Purpose**: Verify each match operator works correctly

```python
def test_match_with_glob_wildcard(test_db):
    """Test GLOB pattern matching with wildcard."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sa*', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_glob_question(test_db):
    """Test GLOB pattern matching with ? wildcard."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'sav?', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_exact(test_db):
    """Test EXACT pattern matching."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, 'save', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'

def test_match_with_like(test_db):
    """Test LIKE pattern matching."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.LIKE, 's%', True))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'
```

#### Test 2.3: Case Sensitivity
**Purpose**: Verify case-sensitive and case-insensitive matching

```python
def test_match_case_sensitive(test_db):
    """Test case-sensitive matching."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', True))
    assert len(results) == 0  # 'User' != 'user'

def test_match_case_insensitive(test_db):
    """Test case-insensitive matching."""
    results = list(test_db.match(SymbolType.CLASS, MatchOp.GLOB, 'user', False))
    assert len(results) == 1
    assert results[0].symbol_name == 'User'

def test_match_case_insensitive_pattern(test_db):
    """Test case-insensitive with wildcard pattern."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'SA*', False))
    assert len(results) == 1
    assert results[0].symbol_name == 'save'
```

#### Test 2.4: Result Limiting
**Purpose**: Verify limit parameter works correctly

```python
def test_match_with_limit(test_db):
    """Test limiting results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=1))
    assert len(results) == 1

def test_match_with_limit_zero(test_db):
    """Test limit=0 returns no results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=0))
    assert len(results) == 0

def test_match_with_limit_greater_than_total(test_db):
    """Test limit greater than total results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, '*', True, limit=100))
    assert len(results) == 2  # Only 2 methods exist
```

#### Test 2.5: Empty Results
**Purpose**: Verify behavior with no matches

```python
def test_match_no_results(test_db):
    """Test matching with no results."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'nonexistent', True))
    assert len(results) == 0

def test_match_empty_pattern(test_db):
    """Test matching with empty pattern."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.EXACT, '', True))
    assert len(results) == 0
```

#### Test 2.6: Byte Position Data
**Purpose**: Verify byte position data is included correctly

```python
def test_match_result_has_byte_position(test_db):
    """Test that methods have byte position data."""
    results = list(test_db.match(SymbolType.METHOD, MatchOp.GLOB, 'save', True))
    assert len(results) == 1
    assert results[0].byte_offset == 100
    assert results[0].byte_length == 50

def test_match_result_no_byte_position_for_files(test_db):
    """Test that filenames don't have byte position data."""
    results = list(test_db.match(SymbolType.FILENAME, MatchOp.GLOB, '*', True))
    assert len(results) == 1
    assert results[0].byte_offset is None
    assert results[0].byte_length is None
```

#### Test 2.7: SQL Injection Protection
**Purpose**: Verify pattern escaping works correctly

```python
def test_match_escapes_single_quotes(test_db):
    """Test that single quotes in patterns are escaped."""
    # Insert a symbol with single quote
    test_db.insert_symbol("O'Connor", 'class', 'src/test.py', 10, "test.O'Connor", 100, 50, None)

    results = list(test_db.match(SymbolType.CLASS, MatchOp.EXACT, "O'Connor", True))
    assert len(results) == 1
    assert results[0].symbol_name == "O'Connor"
```

**Total Test 2**: 20 tests

---

### Test Suite 3: CLI Integration Tests

**File**: `tests/integration/test_cli_match.py`

#### Setup Fixture
```python
@pytest.fixture
def indexed_db(tmp_path):
    """Create a temporary indexed database for testing."""
    # Create test Python files
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()

    # Create test file with various entities
    (test_dir / "module.py").write_text('''
class TestClass:
    def test_method(self):
        pass

def test_function():
    pass

TEST_GLOBAL = 42
''')

    # Index the directory
    db_path = test_dir / ".via" / "index.db"
    db_path.parent.mkdir()

    with DatabaseStore(str(db_path), str(test_dir)) as db:
        db.initialize_schema()
        # ... populate with test data ...

    yield test_dir, db_path
```

#### Test 3.1: CLI Command Parsing
**Purpose**: Verify CLI correctly parses arguments

```python
def test_match_command_with_required_args(indexed_db):
    """Test match command with required arguments."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', 'test_*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'test_function' in result.stdout

def test_match_command_alias(indexed_db):
    """Test match command with 'm' alias."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'm', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_command_missing_type(indexed_db):
    """Test match command fails without --type."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', 'pattern', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'required' in result.stderr.lower()
```

#### Test 3.2: Match Syntax Flags
**Purpose**: Verify syntax flags work correctly

```python
def test_match_with_glob_flag(indexed_db):
    """Test -g/--glob flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', 'test_*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_with_regex_flag(indexed_db):
    """Test -r/--regex flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-r', '^test_.*$', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_match_with_sql_flag(indexed_db):
    """Test -s/--sql flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-s', 'test_%', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
```

#### Test 3.3: Symbol Type Filters
**Purpose**: Verify all symbol type filters work

```python
def test_match_methods(indexed_db):
    """Test matching methods."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'method', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'method:' in result.stdout

def test_match_classes(indexed_db):
    """Test matching classes."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'class', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'class:' in result.stdout

def test_match_functions(indexed_db):
    """Test matching functions."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'function:' in result.stdout
```

#### Test 3.4: Qualifier Flags
**Purpose**: Verify qualifier flags work correctly

```python
def test_match_case_insensitive_flag(indexed_db):
    """Test -I/--case-insensitive flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'class', '-g', 'testclass', '-I', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert 'TestClass' in result.stdout

def test_match_limit_flag(indexed_db):
    """Test -n/--limit flag."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-n', '1', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    lines = result.stdout.strip().split('\n')
    assert len(lines) == 1
```

#### Test 3.5: Output Format
**Purpose**: Verify output format is correct

```python
def test_match_output_format_with_byte_position(indexed_db):
    """Test output includes byte position."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'method', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # Format: type:file:line:qualified:@offset+length
    assert '@' in result.stdout
    assert '+' in result.stdout

def test_match_output_format_without_byte_position(indexed_db):
    """Test output for files doesn't include byte position."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'filename', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert '@' not in result.stdout  # No byte position for files
```

#### Test 3.6: Error Handling
**Purpose**: Verify error cases are handled gracefully

```python
def test_match_database_not_found(tmp_path):
    """Test error when database doesn't exist."""
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(tmp_path)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'Database not found' in result.stderr
    assert 'via index' in result.stderr  # Suggests running index first

def test_match_invalid_symbol_type(indexed_db):
    """Test error with invalid symbol type."""
    test_dir, db_path = indexed_db
    result = subprocess.run(
        ['via', 'match', '-t', 'invalid', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode != 0

def test_match_directory_not_found():
    """Test error when directory doesn't exist."""
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', '/nonexistent'],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert 'does not exist' in result.stderr.lower()
```

#### Test 3.7: Streaming Output
**Purpose**: Verify results stream correctly (for piping)

```python
def test_match_streams_results(indexed_db):
    """Test that results are streamed (not buffered)."""
    test_dir, db_path = indexed_db
    # This test would verify generator-based streaming
    # In practice, verify no "Indexing complete" type headers
    result = subprocess.run(
        ['via', 'match', '-t', 'function', '-g', '*', '-d', str(test_dir)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    # Should only have result lines, no headers/footers
    assert '====' not in result.stdout
    assert 'COMPLETE' not in result.stdout
```

**Total Test 3**: 18 tests

---

### Test Suite 4: Indexer Symbol Population Tests

**File**: `tests/unit/test_indexer_symbols.py`

#### Test 4.1: Symbol Insertion
**Purpose**: Verify indexer populates symbols table correctly

```python
def test_indexer_creates_function_symbols(test_db):
    """Test that indexer creates symbol entries for functions."""
    # Index a file with a function
    # Verify symbol table has function entry

def test_indexer_creates_class_symbols(test_db):
    """Test that indexer creates symbol entries for classes."""
    # Index a file with a class
    # Verify symbol table has class entry

def test_indexer_creates_method_symbols(test_db):
    """Test that indexer creates symbol entries for methods."""
    # Index a file with a method
    # Verify symbol table has method entry with parent_name

def test_indexer_creates_import_symbols(test_db):
    """Test that indexer creates symbol entries for imports."""
    # Index a file with imports
    # Verify symbol table has import entries

def test_indexer_creates_global_symbols(test_db):
    """Test that indexer creates symbol entries for globals."""
    # Index a file with global variables
    # Verify symbol table has global entries

def test_indexer_creates_file_symbols(test_db):
    """Test that indexer creates filename and filepath symbols."""
    # Index a file
    # Verify symbol table has both filename and filepath entries
```

#### Test 4.2: Qualified Name Calculation
**Purpose**: Verify qualified names are calculated correctly

```python
def test_qualified_name_for_function():
    """Test qualified name calculation for functions."""
    qname = _calculate_qualified_name('src/utils.py', 'calculate', None)
    assert qname == 'utils.calculate'

def test_qualified_name_for_method():
    """Test qualified name calculation for methods."""
    qname = _calculate_qualified_name('src/models/user.py', 'save', 'User')
    assert qname == 'models.user.User.save'

def test_qualified_name_removes_src_prefix():
    """Test that src/ prefix is removed from module path."""
    qname = _calculate_qualified_name('src/models/user.py', 'User', None)
    assert qname == 'models.user.User'
    assert 'src' not in qname
```

#### Test 4.3: Symbol Deletion on Re-index
**Purpose**: Verify symbols are deleted when file is re-indexed

```python
def test_reindex_deletes_old_symbols(test_db):
    """Test that re-indexing a file deletes old symbols."""
    # Index a file
    # Verify symbols exist
    # Modify file
    # Re-index
    # Verify old symbols deleted and new symbols inserted
```

**Total Test 4**: 10 tests

---

### Test Summary

| Test Suite | Tests | Type | File |
|------------|-------|------|------|
| Suite 1: Core Types | 10 | Unit | `tests/unit/test_core_types.py` |
| Suite 2: DatabaseStore.match() | 20 | Unit | `tests/unit/test_database_match.py` |
| Suite 3: CLI Integration | 18 | Integration | `tests/integration/test_cli_match.py` |
| Suite 4: Indexer Symbols | 10 | Unit | `tests/unit/test_indexer_symbols.py` |
| **TOTAL** | **58** | | |

---

### Edge Cases to Test

1. **Special Characters in Patterns**:
   - Patterns with SQL wildcards (%, _)
   - Patterns with glob wildcards (*, ?)
   - Patterns with regex metacharacters
   - Patterns with single quotes (SQL injection)

2. **Unicode Support**:
   - Symbol names with unicode characters
   - File paths with unicode
   - Patterns with unicode

3. **Large Result Sets**:
   - Matching pattern that returns 1000+ results
   - Verify streaming works efficiently
   - Verify limit works with large result sets

4. **Empty Database**:
   - Match command on empty symbols table
   - Should return 0 results gracefully

5. **Concurrent Access**:
   - Multiple match queries simultaneously
   - SQLite handles this via locking

---

### Performance Tests

**File**: `tests/performance/test_match_performance.py`

#### Test P.1: Query Performance
```python
def test_match_performance_with_10k_symbols():
    """Test match query completes in < 100ms with 10k symbols."""
    # Create database with 10,000 symbols
    # Time a match query
    # Assert time < 100ms

def test_match_performance_with_complex_pattern():
    """Test regex match completes in reasonable time."""
    # Test regex pattern matching performance
```

#### Test P.2: Index Creation Performance
```python
def test_index_lookup_uses_composite_index():
    """Test that queries use the composite (type, name) index."""
    # Use EXPLAIN QUERY PLAN to verify index usage
```

**Total Performance Tests**: 3

---

### Coverage Goals

**Target Coverage**: 95%+

**Critical Paths to Cover**:
- ✅ All SymbolType enum values
- ✅ All MatchOp operators (EXACT, GLOB, LIKE, REGEXP)
- ✅ Case-sensitive and case-insensitive matching
- ✅ Result limiting
- ✅ Empty results
- ✅ Byte position inclusion
- ✅ SQL escaping
- ✅ CLI argument parsing
- ✅ Error handling (database not found, invalid type, etc.)
- ✅ Output formatting

---

### Test Execution Order

1. **Unit Tests First**: Run all unit tests (Suites 1, 2, 4)
2. **Integration Tests**: Run CLI integration tests (Suite 3)
3. **Performance Tests**: Run performance tests (Suite P)

**Continuous Integration**:
- Run all unit tests on every commit
- Run integration tests on pull requests
- Run performance tests nightly

---

### Test Data Requirements

**Minimal Test Database**:
- 1-2 Python files with:
  - At least 1 class with methods
  - At least 2 top-level functions
  - At least 3 imports
  - At least 2 global variables
  - Various naming patterns (CamelCase, snake_case, etc.)

**Test Files Location**: `tests/fixtures/test_project/`

---

### Acceptance Criteria

Sprint 2 testing is complete when:
- ✅ All 58 core tests pass
- ✅ All 3 performance tests pass
- ✅ Code coverage ≥ 95% for new code
- ✅ Zero critical bugs found
- ✅ All edge cases handled gracefully
- ✅ Performance benchmarks met (< 100ms for 10k symbols)

---

**Created by**: @Trin (QA Engineer)
**Status**: ✅ Ready for Test Implementation
**Next**: Implement tests in test files


---
