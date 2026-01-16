# Sprint 3 User Stories - Render, List, Stats Commands

**Version**: 1.0
**Date**: 2026-01-16
**Product Manager**: @Cypher
**Status**: Draft - Awaiting User Review

---

## Executive Summary

Sprint 3 delivers the backlogged features from Sprint 2 planning:
- **`via render`** - Display source code with syntax highlighting and context
- **`via stats`** - Show index statistics and summaries

These commands complete the core query-and-view workflow for the VIA tool.

---

## Sprint Goals

**Primary Goals**:
1. Enable users to view source code for matched symbols
2. Provide browsing capabilities for exploring the index
3. Display useful statistics about the indexed codebase

**Success Criteria**:
- Users can pipe `via match` output to `via render` to view code
- Users can browse all entities of a given type
- Users can get quick stats on codebase size/composition

---

## User Stories

### Story 1: Render Symbol Source Code
**Priority**: P0 (Must Have)
**Story Points**: 5
**Estimated Hours**: 10h

**As a** developer
**I want to** view the source code for symbols found by `via match`
**So that** I can quickly inspect implementations without opening files manually

-------------
FEEDBACK FROM DREW (User): I want to try "virtural" pipelines to make the command easier to use.  the key is having a really powerful short hand for the differnt args and then repating --via to describe the next stage of the pipeline.  So something like this:
`via -mg -c '*Match*' --via -rTh`
Would be equlivient to 
`via match  -t class --glob '*Match*' | via render --render-type table --format html`

Try to rework this story based on my 'internal pipeline' approach.  The power comes from using multiple successive --via options like this:
`via -mg -c '*Match*' --via -mr -m '^__.*__$' --via -rDm` 

that does a glob match on all clasess called `*Match*` and then finds all methods of those classes matching the regex `__.*__$` and then renders those methods as a diagram in md/mermaid format
Add
- AC9: via render accepts a set of match results and an optional render_type (list, table, diagram, usage, raw) and formats (ascii, md, html, png)

and update the usage examples
----------


**Acceptance Criteria**:
- AC1: `via render` accepts input from stdin (piped from `via match`)
- AC2: Input format matches `via match` output: `type:file:line:qualified:@byte+len`
- AC3: Renders source code with syntax highlighting (using `pygments`)
- AC4: Shows configurable context lines before/after the symbol (-A/-B/-C flags like grep)
- AC5: Displays file path, line numbers, and symbol name as header
- AC6: Supports multiple symbols in single invocation (batch rendering)
- AC7: Falls back to plain text if pygments not available
- AC8: Respects color scheme from config or auto-detects terminal

**Examples**:
```bash
# Render a single match
via match -t function -g "calculate*" | via render

# Render with context
via match -t method -g "save" | via render -C 3

# Render multiple matches
via match -t class -g "User*" | via render
```

**Technical Notes**:
- Use byte_offset + byte_length from match output to seek exact symbol location
- Pygments for syntax highlighting
- Support both light/dark terminal themes

---

### Story 2: Context Line Control
**Priority**: P1 (Should Have)
**Story Points**: 2
**Estimated Hours**: 4h

**As a** developer
**I want to** control how many context lines are shown
**So that** I can see more or less surrounding code as needed

**Acceptance Criteria**:
- AC1: `-A N` shows N lines after the symbol
- AC2: `-B N` shows N lines before the symbol
- AC3: `-C N` shows N lines before AND after (shorthand for -A N -B N)
- AC4: Default context is 0 (symbol only)
- AC5: Context lines are visually distinguished (dimmed or different style)

**Examples**:
```bash
# Show 5 lines after
via match -t function -g "main" | via render -A 5

# Show 3 lines before and after
via match -t class -g "Database*" | via render -C 3
```

---

### Story 3: List Command - Browse Entities
**Priority**: P0 (Must Have)
**Story Points**: 3
**Estimated Hours**: 6h

**As a** developer
**I want to** list all entities of a specific type
**So that** I can browse and explore the codebase structure

--------------------------
FEEDBACK FROM Drew (user): fold this into the render types
-------------------------

**Acceptance Criteria**:
- AC1: `via render list` command lists entities by type
- AC2: Supports all symbol types: file, class, function, method, import, global
- AC3: Output format matches `via match` (for pipeline compatibility)
- AC4: Supports filtering with glob patterns (optional)
- AC5: Supports pagination or streaming for large result sets
- AC6: Shows count summary at the end (optional with --no-summary flag)

**Examples**:
```bash
# List all classes
via rendfer --render type list --type class

# List all functions matching pattern
via list --type function --glob "test_*"

# List all files
via list --type file
```

**Technical Notes**:
- Essentially `via match -t <type> -g '*'` with nicer formatting
- Could be implemented as alias/wrapper around match command

---

### Story 4: Stats Command - Codebase Statistics
**Priority**: P1 (Should Have)
**Story Points**: 3
**Estimated Hours**: 6h

**As a** developer
**I want to** see statistics about my indexed codebase
**So that** I can understand the size and composition of the project

**Acceptance Criteria**:
- AC1: `via stats` shows summary statistics
- AC2: Displays counts by entity type (classes, functions, methods, imports, globals)
- AC3: Displays file counts by type (.py, .pyx, .pyi, .md)
- AC4: Shows total files indexed vs parsed
- AC5: Shows index database size and last updated timestamp
- AC6: Supports detailed breakdowns with `-v` flag
- AC7: Supports JSON output for scripting (--json flag)

**Examples**:
```bash
# Basic stats
via stats

# Detailed stats
via stats -v

# JSON output for scripting
via stats --json
```

**Sample Output**:
```
VIA Index Statistics
====================
Index: /home/user/project/.via/index.db
Last Updated: 2026-01-16 11:30:00

Files:
  Total Indexed: 150
  Python Files:  44
  Database Size: 2.3 MB

Symbols:
  Classes:   59
  Functions: 339
  Methods:   124
  Imports:   87
  Globals:   23
  Total:     632
```

---

### Story 5: Multiple Output Formats (Render)
**Priority**: P2 (Nice to Have)
**Story Points**: 2
**Estimated Hours**: 4h

**As a** developer
**I want to** choose different output formats for rendered code
**So that** I can integrate with different tools and workflows

**Acceptance Criteria**:
- AC1: Default format is terminal-friendly with ANSI colors
- AC2: `--format plain` outputs plain text (no colors)
- AC3: `--format html` outputs HTML with syntax highlighting
- AC4: `--format json` outputs structured JSON with metadata
- AC4.5: `--format md` Outputs .md file
- AC5: Format choice applies to all render operations

**Examples**:
```bash
# Plain text output
via match -t function -g "main" | via render --format plain

# HTML output (for web view)
via match -t function -g "main" | via render --format html > output.html

# JSON output (for tooling)
via match -t function -g "main" | via render --format json
```

---

### Story 6: Render Configuration
FEEDBACK FROM Drew (user): backlog this story we'll do configs later

**Priority**: P2 (Nice to Have)
**Story Points**: 2
**Estimated Hours**: 4h

**As a** developer
**I want to** configure render defaults
**So that** I don't have to specify options every time

**Acceptance Criteria**:
- AC1: Config file at `.via/config.toml` or `~/.config/via/config.toml`
- AC2: Configure default color scheme
- AC3: Configure default context lines
- AC4: Configure default output format
- AC5: CLI flags override config values
- AC6: `via config` command to view/edit settings

**Config Example**:
```toml
[render]
color_scheme = "monokai"
context_lines = 3
format = "terminal"
show_line_numbers = true

[match]
case_sensitive = false
default_limit = 100
```

---

## Sprint Summary

**Total Story Points**: 17 (13 P0/P1, 4 P2)
**Total Estimated Hours**: 34h
**Sprint Duration**: 2 weeks (recommended)

**Priority Breakdown**:
- **P0 (Must Have)**: 8 points - Stories 1, 3 (Render, List)
- **P1 (Should Have)**: 5 points - Stories 2, 4 (Context, Stats)
- **P2 (Nice to Have)**: 4 points - Stories 5, 6 (Formats, Config)

**Dependencies**:
- All stories depend on Sprint 2 (match command) being complete
- Story 2 depends on Story 1
- Story 5 depends on Story 1
- Story 6 depends on Story 1

**Risks**:
- Pygments dependency adds complexity (mitigate: graceful fallback)
- Config file parsing adds scope (mitigate: defer to P2)

---

## Open Questions for User

1. **Render Input Format**: Should `via render` ONLY accept piped input from `via match`, or should it also accept:
   - File paths directly: `via render src/utils.py:42`
   - Symbol names: `via render utils.calculate`

   Answer:
   Render should accept a list of Generic MatchRecords that can be different types (classes) depending on the type selected for the match.  Each MatchRecord Type (derived class) supports one or more of the rendering types (table, list, diagram etc...) and it's output is tailored to the type of object being rendered.  We'll iuse the internal pipe idea instead of unix pipe line for now

2. **Render Batch Behavior**: When rendering multiple symbols, should we:
   - Show separators between symbols (recommended)
   - Page through them interactively
   - Stream continuously
   
   Answer: 
   This Depends on the format type and different formats can have different options for showing groups of matches, tables might have group by and sort options and HTML could have some style options, etc.. In general, let's not bother with options that are easily handled with other unix commands. for instance if we want to page we can  do `via | less`.

  So in general we want flags to modify the rendering_type and the format but only ones that make sense.  This will be determined by the polymophic of each MatchRecord Type and Renderer / Formatter sub class so it is easly extensiable

3. **List Command Alias**: Should `via list` be:
   - A separate command with its own implementation
   - An alias for `via match -t <type> -g '*'`
   - A wrapper that adds formatting/summaries

   Drop via list all together

4. **Stats Granularity**: Should stats include:
   - Per-file symbol counts
   - Largest classes/functions (by line count)
   - Import dependency graphs
   - Or just high-level summaries?

   Have -v -vv for stats to control granualarity

5. **Color Scheme Defaults**: What should the default color scheme be:
   - Auto-detect terminal background (light/dark)
   - Always use a specific scheme (monokai, solarized, etc.)
   - No colors by default (opt-in with --color)

   For rendering formats that support colors we should allow different schemes. When possible use user's existing light/dark or terminal theme preference by default.  To provide flexability allow any 'oh-my-posh' or a python library with themes (include in the build and add a good --preview mode that shows canned content in the different themes).  Don't build a theaming system from scratch.

6. **Context Line Limits**: Should we limit context lines to prevent massive output:
   - Cap at 50 lines before/after
   - No limit (user responsibility)
   - Warn if context would exceed N lines
   
   Always Stream matches - but make the default 10 matches - include an indication that there are more.  add an option to set the limit higher or no limit

---

## Backlog Items (Sprint 4+)

Items deferred from this sprint planning:

2. **Diff Rendering** - Show changes between versions
4. **Watch Mode for Render** - Auto-refresh when files change
5. **Advanced Stats** - Complexity metrics, dependency graphs
6. **Plugin System** - Add support for language server integration for other languages

---

**Next Steps**:
1. User answers open questions in this document
2. @Morpheus reviews technical feasibility
3. @Mouse creates task breakdown
4. @Neo implements Sprint 3

**Status**: ⏳ Awaiting User Review
