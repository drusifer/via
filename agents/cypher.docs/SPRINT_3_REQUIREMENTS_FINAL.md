# Sprint 3 Requirements - Internal Pipeline & Render System

**Version**: 2.0 Final
**Date**: 2026-01-16
**Product Manager**: @Cypher
**Status**: Ready for Architecture Review

---

## Executive Summary

Sprint 3 introduces an **internal pipeline architecture** using the `--via` flag to chain operations within a single command invocation. This eliminates the need for unix pipes and enables powerful shorthand syntax.

**Key Innovation**: Virtual pipelines via repeated `--via` flags
```bash
# Find all classes matching *Match*, then find their __*__ methods, render as diagram
via -mg -c '*Match*' --via -mr -m '^__.*__$' --via -rDm
```

**Out of Scope**:
- ❌ `via list` command (functionality folded into render types)
- ❌ Config file system (backlogged to Sprint 4+)

---

## 1. Internal Pipeline Architecture

### 1.1 Core Concept

**Problem**: Unix pipes are verbose and require understanding of input/output formats
```bash
# Old approach (unix pipes)
via match -t class --glob '*Match*' | via match -t method --regex '^__.*__$' | via render --type diagram --format md
```

**Solution**: Internal pipeline with `--via` flag separator
```bash
# New approach (internal pipeline)
via -mg -c '*Match*' --via -mr -m '^__.*__$' --via -rDm
```

### 1.2 Pipeline Stages

Each `--via` flag starts a new pipeline stage:

**Stage 1: Match** - Select symbols from index
- Flags: `-m` (match), `-g/-r/-s` (glob/regex/sql), `-t` (type), `-I` (case-insensitive), `-n` (limit)
- Example: `-mg -c '*Match*'` = match classes with glob pattern

**Stage 2: Match (again)** - Filter results from previous stage
- Same flags as Stage 1
- Operates on OUTPUT of previous stage (not entire index)
- Example: `-mr -m '^__.*__$'` = match methods matching regex pattern

**Stage 3: Render** - Display results
- Flags: `-r` (render), render_type flag, format flag, context flags
- Example: `-rDm` = render as Diagram in markdown format

### 1.3 Shorthand Flags

**Match Syntax**:
- `-g` = `--glob` (shell wildcards: *, ?)
- `-r` = `--regex` (Python regex)
- `-s` = `--sql` (SQL LIKE: %, _)

**Symbol Types** (use with `-t` or direct):
- `-c` = `--class`
- `-f` = `--function`
- `-m` = `--method`
- `-i` = `--import`
- `-G` = `--global`
- `-F` = `--file` or `--filepath`
- `-N` = `--filename`

**Render Types** (use with `-r`):
- `-L` = `--list` (simple list view)
- `-T` = `--table` (tabular view)
- `-D` = `--diagram` (UML/mermaid diagram)
- `-U` = `--usage` (show usage/references)
- `-R` = `--raw` (source code)

**Output Formats**:
- `-a` = `--ascii` (terminal-friendly)
- `-m` = `--md` (markdown)
- `-h` = `--html` (HTML)
- `-p` = `--png` (image - requires rendering library)

---

## 2. Polymorphic MatchRecord System

### 2.1 MatchRecord Base Class

```python
@dataclass
class MatchRecord:
    """Base class for all match results."""
    symbol_type: SymbolType
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: int

    def supports_render_type(self, render_type: RenderType) -> bool:
        """Check if this record type supports the render type."""
        raise NotImplementedError

    def render(self, render_type: RenderType, format: Format, **options) -> str:
        """Render this record in the specified type and format."""
        raise NotImplementedError
```

### 2.2 Derived MatchRecord Types

**ClassMatchRecord**
- Supports: list, table, diagram, usage, raw
- Diagram: Shows class with methods, inheritance
- Usage: Shows where class is instantiated/imported
- Raw: Shows full class source code

**MethodMatchRecord**
- Supports: list, table, raw, usage
- No diagram (methods are shown in class diagrams)
- Usage: Shows call sites

**FunctionMatchRecord**
- Supports: list, table, raw, usage
- Usage: Shows call sites

**FileMatchRecord**
- Supports: list, table
- No raw (entire file too large)
- No diagram/usage

**ImportMatchRecord**
- Supports: list, table, usage
- Usage: Shows what imports this module

### 2.3 Render Type Behaviors

**List** (default for all types)
- Simple line-by-line output
- Format: `type:file:line:qualified_name`
- Same as current `via match` output

**Table**
- Tabular view with columns
- Columns: Type, Name, File, Line, Parent (for methods)
- Formats: ascii (terminal), md (markdown table), html (HTML table)

**Diagram** (classes only)
- UML class diagram showing relationships
- Formats: md (mermaid syntax), html (mermaid rendered), png (image)
- Shows: inheritance, methods, attributes

**Usage** (classes, methods, functions, imports)
- Shows the formatted docstrings for matches
- formats: md, html, raw, json, jsonl

**Raw** (classes, methods, functions)
- Shows full code for the matches 
- Supports context lines (-A/-B/-C)
- Formats: ascii (terminal colors, and line numbesr), html (syntax highlighted), md (code blocks), raw - no formattings

---

## 3. Command Syntax

### 3.1 Basic Match

```bash
# Long form
via match --type class --glob '*Match*'

# Short form
via -mg -c '*Match*'

# Equivalent to Sprint 2
via match -t class -g '*Match*'
```

### 3.2 Internal Pipeline (Single Match + Render)

```bash
# Match classes, render as table in markdown
via -mg -c '*Match*' --via -rTm

# Equivalent long form
via match --type class --glob '*Match*' --via render --table --md
```

### 3.3 Chained Matches

```bash
# Match classes, then match their methods
via -mg -c '*Match*' --via -mr -m '^__.*__$'

# Explanation:
# Stage 1: Find all classes matching *Match*
# Stage 2: From those classes, find methods matching ^__.*__$ (dunder methods)
# Output: Only the methods
```

### 3.4 Full Pipeline (Match -> Match -> Render)

```bash
# Short form
via -mg -c '*Match*' --via -mr -m '^__.*__$' --via -rDm

# Explanation:
# Stage 1: Match classes *Match*
# Stage 2: Match their __*__ methods
# Stage 3: Render as Diagram in markdown

# Long form equivalent
via match --type class --glob '*Match*' \
  --via match --type method --regex '^__.*__$' \
  --via render --diagram --md
```

### 3.5 Render Options

```bash
# Render with context lines (for raw render type)
via -mg -f 'calculate*' --via -rR -C 5

# Render as table with no limit
via -mg -c 'User*' --via -rT -n 0

# Render as diagram in HTML
via -mg -c 'Database*' --via -rDh
```

---

## 4. Stats Command

### 4.1 Basic Stats

```bash
via stats
```

**Output**:
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

### 4.2 Verbose Stats

```bash
# Level 1: Per-file counts
via stats -v

# Level 2: Top 10 largest classes/functions
via stats -vv

# Level 3: Full breakdown
via stats -vvv
```

### 4.3 JSON Output

```bash
via stats --json
```

Output for scripting/automation.

---

## 5. Theme System

### 5.1 Requirements

- **DO NOT** build custom theme system from scratch
- Use existing theme library (oh-my-posh themes or Python library with themes)
- Auto-detect user's terminal theme preference (light/dark) by default
- Include theme in build (bundle themes, no external dependency at runtime)
- Provide `--preview` mode showing sample content in different themes

### 5.2 Theme Sources

**Option 1: oh-my-posh themes**
- Pros: Large collection, well-maintained
- Cons: May need adaptation for code highlighting

**Option 2: Pygments styles**
- Pros: Built for code highlighting, many styles included
- Cons: Limited to code, not UI elements

**Recommendation**: Use Pygments styles for code, simple ANSI color scheme for UI

### 5.3 Theme Selection

```bash
# Auto-detect (default)
via -mg -c '*' --via -rR

# Specific theme
via -mg -c '*' --via -rR --theme monokai

# Preview themes
via --preview-themes
```

---

## 6. Streaming & Limits

### 6.1 Default Behavior

- **Default limit**: 10 matches
- Always stream results (generator-based)
- Show indicator when there are more results: `... (N more matches, use -n 0 for all)`

### 6.2 Limit Control

```bash
# Default (10 matches)
via -mg -c '*'

# Custom limit
via -mg -c '*' -n 20

# No limit (all matches)
via -mg -c '*' -n 0

# Single match
via -mg -c 'User' -n 1
```

---

## 7. Updated User Stories

### Story 1: Internal Pipeline Architecture (NEW)
**Priority**: P0
**Points**: 5
**Description**: Implement `--via` flag for internal pipeline stages using argparse
**AC**:
- AC1: Use Python's `argparse.ArgumentParser` with `exit_on_error=False` for all flag parsing
- AC2: Create separate ArgumentParser for each stage type (match, render, stats)
- AC3: Split argv on `--via` flags to create pipeline stages
- AC4: Execute stages sequentially, passing `Iterator[MatchRecord]` between stages
- AC5: Support all shorthand flags (-c/-m/-f for types, -g/-r/-s for patterns, -rL/-rT/-rD for renders)
- AC6: Validate flag combinations (catch SystemExit, re-raise as PipelineParseError)
- AC7: Support both long form (`via match --type class`) and short form (`via -mg -c '*'`)

### Story 2: Polymorphic MatchRecord System with Metadata (NEW)
**Priority**: P0
**Points**: 5
**Description**: Create MatchRecord base class with rendering metadata for streaming
**AC**:
- AC1: Base MatchRecord class with metadata fields (column_widths, total_matches)
- AC2: Derived classes for each symbol type (Class, Method, Function, File, Import, Global)
- AC3: Each type implements `supports_render_type()` to declare capabilities
- AC4: Factory pattern creates correct MatchRecord subclass from database row
- AC5: DatabaseStore computes metadata (column widths, total count) with single aggregation query
- AC6: Metadata attached to EVERY MatchRecord so each can render independently
- AC7: `__str__()` method for default list format (Sprint 2 compatible output)

### Story 3: Render Types - List & Table (STREAMING)
**Priority**: P0
**Points**: 3
**Description**: Implement streaming list and table renderers using metadata
**AC**:
- AC1: ListRenderer streams records, outputs using `MatchRecord.__str__()`
- AC2: ListRenderer shows "... (N more matches, use -n 0 for all)" using total_matches metadata
- AC3: TableRenderer STREAMS records (column widths from metadata, no materialization needed)
- AC4: TableRenderer renders header on first record using column_widths metadata
- AC5: Table formatters: ASCII (pipe-separated), MD (markdown table), HTML (HTML table)
- AC6: Support all symbol types (class, method, function, file, import, global)
- AC7: Both renderers use O(1) memory (stream, don't materialize)

### Story 4a: Render Types - Raw (Truly Raw, No Formatting)
**Priority**: P0
**Points**: 2
**Description**: Render pure source code with NO formatting for piping/automation
**AC**:
- AC1: RawRenderer supports ALL symbol types (class, method, function, global, file, import)
- AC2: Extract source using byte_offset + byte_length (seek and read)
- AC3: NO formatting - no colors, no line numbers, no syntax highlighting
- AC4: Support context lines (-A/-B/-C flags)
- AC5: For FileMatchRecord (no byte offset), read entire file
- AC6: For ImportMatchRecord, extract import statement
- AC7: Streams records (O(1) memory)
- AC8: Output pure text suitable for piping to other tools (diff, grep, etc.)

### Story 4b: Render Types - Formatted (Human-Readable Code)
**Priority**: P0
**Points**: 3
**Description**: Render formatted source code with syntax highlighting for humans
**AC**:
- AC1: FormattedRenderer supports code symbols only (class, method, function, global - NOT files/imports)
- AC2: Integrate Pygments for syntax highlighting
- AC3: Add line numbers with proper formatting
- AC4: Support context lines (-A/-B/-C flags)
- AC5: Add header with symbol info (qualified name, file path, line number)
- AC6: Auto-detect terminal theme (light/dark) or use --theme flag
- AC7: Formatters: ASCII (terminal colors), HTML (syntax highlighted), MD (code blocks)
- AC8: Streams records (O(1) memory)

### Story 5: Render Types - Diagram (MUST Materialize)
**Priority**: P1
**Points**: 5
**Description**: Render UML class diagrams using Mermaid (only renderer that materializes)
**AC**:
- AC1: DiagramRenderer explicitly materializes with `list(records)` (needs all classes for relationships)
- AC2: Generate mermaid classDiagram syntax
- AC3: Show class inheritance relationships (parent <|-- child)
- AC4: Show methods for each class
- AC5: Filter for ClassMatchRecord only (ignore other types)
- AC6: Formatters: MD (mermaid code), HTML (rendered with mermaid.js), PNG (optional via mermaid-cli)
- AC7: Handle empty results gracefully ("No classes to diagram")

### Story 6: Render Types - Usage
**Priority**: P1
**Points**: 5
**Description**: Show symbol usage/references
**AC**:
- Query references table
- Show caller -> callee relationships
- Support classes, methods, functions, imports

### Story 7: Stats Command
**Priority**: P1
**Points**: 3
**Description**: Index statistics command
**AC**:
- Basic stats (counts, sizes)
- Verbose levels (-v/-vv/-vvv)
- JSON output (--json)

### Story 8: Theme System
**Priority**: P1
**Points**: 2
**Description**: Integrate theme library for syntax highlighting
**AC**:
- Use Pygments styles or similar
- Auto-detect light/dark terminal
- `--theme` flag to override
- `--preview-themes` to show available themes

### Story 9: Streaming & Limits with Metadata
**Priority**: P0
**Points**: 2
**Description**: Default limit of 10 with metadata-based streaming
**AC**:
- AC1: Default `-n 10` for all queries
- AC2: DatabaseStore.match() computes metadata BEFORE streaming (column widths, total count)
- AC3: Metadata query overhead ~5-10ms regardless of result set size
- AC4: Show indicator when more results exist: "... (N more matches, use -n 0 for all)"
- AC5: `-n 0` for unlimited results
- AC6: All queries use generator-based streaming (yield from cursor)
- AC7: 4 out of 5 renderers stream with O(1) memory (only DiagramRenderer materializes)

---

## Sprint Summary

**Total Story Points**: 34
**Total Estimated Hours**: ~68h
**Sprint Duration**: 3-4 weeks

**Story Breakdown**:
- Story 1: Pipeline Architecture (5pts, P0)
- Story 2: MatchRecord with Metadata (5pts, P0)
- Story 3: List & Table Renderers (3pts, P0)
- Story 4a: Raw Renderer (2pts, P0)
- Story 4b: Formatted Renderer (3pts, P0)
- Story 5: Diagram Renderer (5pts, P1)
- Story 6: Usage Renderer (5pts, P1)
- Story 7: Stats Command (3pts, P1)
- Story 8: Theme System (2pts, P1)
- Story 9: Streaming & Limits (2pts, P0)

**Priority Breakdown**:
- **P0 (Must Have)**: 20 points (Stories 1, 2, 3, 4a, 4b, 9)
- **P1 (Should Have)**: 15 points (Stories 5, 6, 7, 8)

**Critical Path**:
1. Internal Pipeline (Story 1) - BLOCKER for all
2. MatchRecord with Metadata (Story 2) - BLOCKER for render + enables streaming
3. Streaming & Limits (Story 9) - Enables metadata computation
4. Render List/Table (Story 3) - Basic rendering
5. Render Raw (Story 4a) - For automation
6. Render Formatted (Story 4b) - For human viewing

**Optional (P1)**:
7. Render Diagram (Story 5) - UML diagrams
8. Render Usage (Story 6) - Show references
9. Stats (Story 7) - Index statistics
10. Themes (Story 8) - Color schemes

---

## Backlog Items (Sprint 4+)

1. **Config System** - `.via/config.toml` for defaults
2. **Diff Rendering** - Show changes between versions
3. **Watch Mode** - Auto-refresh on file changes
4. **Advanced Stats** - Complexity metrics
5. **Plugin System** - Language server integration

---

## Technical Notes for @Morpheus

1. **Pipeline Parser**: Use argparse.ArgumentParser with `exit_on_error=False` (Python 3.9+), split argv on `--via` flags
2. **Stage Execution**: Each stage returns `Iterator[MatchRecord]`, pass between stages for zero-copy streaming
3. **Metadata Optimization**: DatabaseStore runs single aggregation query before streaming for column widths + total count
4. **Self-Contained Records**: Each MatchRecord contains rendering metadata (column_widths, total_matches)
5. **Streaming Design**: 4 out of 5 renderers stream with O(1) memory (only DiagramRenderer materializes with explicit `list()`)
6. **Raw vs Formatted**: RawRenderer supports ALL types with NO formatting, FormattedRenderer only code symbols with Pygments
7. **Reference Table**: Already exists in schema (symbol_references), ready for usage render type
8. **Mermaid Generation**: Simple string template, no external library needed for MD format
9. **Theme Detection**: Check $TERM, $COLORFGBG env vars for light/dark detection, or use Pygments styles

---

**Next Steps**:
1. ✅ @Morpheus: Architecture complete with metadata-based streaming design
2. @Mouse: Create detailed task breakdown from updated user stories
3. @Neo: Implement P0 stories in order:
   - Phase 1: Pipeline + argparse (Story 1)
   - Phase 2: MatchRecord with metadata (Story 2)
   - Phase 3: Streaming & metadata query (Story 9)
   - Phase 4: List & Table renderers (Story 3)
   - Phase 5: Raw renderer (Story 4a)
   - Phase 6: Formatted renderer (Story 4b)

**Status**: ✅ Requirements & Architecture Complete - Ready for Implementation
