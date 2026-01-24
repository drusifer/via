# Design: Internal Pipeline Architecture (Sprint 3)

## Actual Requirements from Cypher's PRD

**Key Insight**: NOT separate `render` and `pipeline` commands!  
**Instead**: Single command with `--via` flag for internal pipeline stages

---

## Problem & Solution

### Problem: Unix Pipes are Verbose
```bash
# Old approach (verbose, hard to discover)
via match -tc --mglob '*Match*' | \
  via match -tm --mregex '^__.*__$' | \
  via render --type diagram --format md
```

### Solution: Internal Pipeline with `--via` Flag
```bash
# New approach (compact, self-contained)
via -mg -tc '*Match*' --via -mr -tm '^__.*__$' -oD -fm
```

---

## Architecture Design

### 1. Unified Command Entry Point

The main `via` command supports **two modes**:

**Mode A: Single Stage (No Pipeline)**
```bash
# Match + Render in one command (most common)
via -mg -tc '*Match*' -oT -fm
```

**Mode B: Multi-Stage Pipeline (Optional)**
```bash
# Chain multiple filtering stages
via [STAGE1_FLAGS] --via [STAGE2_FLAGS] --via [STAGE3_FLAGS]
```

**Key Insight**: Rendering is NOT a separate stage—it's part of the MATCH command!
- Match flags: `-m` `-mg/-r/-s` `-t` `-I` `-n`
- Render flags: `-r` render_type format (applied to match output)
- Only use `--via` when you need to FILTER previous results

### 2. Three Pipeline Stage Types

**Stage 1: Match** (Search indexed database)
- Flags: `-m` (match mode), `-mg/-r/-s` (glob/regex/sql), `-t` (type), `-I` (case-insensitive), `-n` (limit)
- Example: `-mg -tc '*Match*'` = match classes with glob pattern `*Match*`

**Stage 2+: Match** (Filter previous results) - OPTIONAL
- Same flags as Stage 1
- Operates on OUTPUT of previous stage (not entire index)
- Only needed for chained filtering
- Example: `-mr -tm '^__.*__$'` = from previous results, match methods with regex `^__.*__$`

**Render Stage: INTEGRATED** (NOT separate!)
- Part of first stage, not a separate `--via` stage
- Flags: `-r` (enable render), render_type, format, context
- Example: `-oT -fm` = render Table, markdown format
- Applied AFTER matching but BEFORE any filtering

### 3. Shorthand Flags

**Match Syntax**:
```
-mg = --mglob       (shell wildcards: *, ?)
-r = --mregex      (Python regex)
-s = --msql        (SQL LIKE: %, _)
```

**Symbol Types** (with `-t` or direct):
```
-c = --class
-f = --function
-m = --method
-i = --import
-G = --mglobal
-F = --file or --filepath
-N = --filename
-h = --header
```

**Render Types** (with `-r`):
```
-L = --list       (simple list: type:file:line:name)
-T = --table      (tabular view with columns)
-D = --diagram    (UML/mermaid diagram - classes only)
-U = --usage      (usage/references patterns)
-R = --raw        (source code with syntax highlighting)
```

**Output Formats**:
```
-a = --ascii      (terminal with colors)
-m = --md         (markdown format)
-h = --html       (HTML output)
-p = --png        (image - requires rendering)
```

---

## CLI Examples (Updated)

### Example 1: Match + Render (Most Common - NO Pipeline!)
```bash
# Long form
via match -tc --mglob '*Match*' -mr --table --md

# Short form (same thing, no --via needed!)
via -mg -tc '*Match*' -oT -fm
```

Output: Classes matching `*Match*` rendered as markdown table

### Example 2: Match Only (No Render)
```bash
via -mg -tc '*Match*'
```

Output: List format (default)

### Example 3: Match + Filter (Uses --via)
```bash
# Find classes matching *Match*, then find their dunder methods
via -mg -tc '*Match*' --via -mr -tm '^__.*__$'

# Explanation:
# Stage 1: Find all classes matching *Match*
# Stage 2: From those classes, find methods matching ^__.*__$
```

Output: Filtered methods list

### Example 4: Match + Filter + Render (Full Pipeline)
```bash
# Match -> Filter -> Render
via -mg -tc '*Match*' --via -mr -tm '^__.*__$' -oD -fm

# Stages:
# 1. Find all classes matching *Match*
# 2. From those classes, find methods matching ^__.*__$
# 3. Render as Diagram in markdown format
```

Output: Diagram of filtered methods

### Example 5: With Context
```bash
# Match functions, render raw code with 3 lines before/after
via -mg -tf 'calculate*' -oR -B 3 -A 3

# Context flags:
# -A N = N lines after
# -B N = N lines before
# -C N = N lines before AND after (shorthand)
```

Output: Functions with context lines

---

## Implementation Strategy

### Phase 1: Refactor Argument Parser

**Current State**: Match command uses subparser  
**Goal**: Enable `--via` flag to chain multiple subparsers

**Key Changes**:
1. Detect `--via` flag in sys.argv
2. Split arguments into stages at each `--via`
3. Create argument parser for each stage
4. Parse each stage independently

```python
# Pseudocode
def main():
    # Check if --via flag exists in arguments
    if '--via' in sys.argv:
        stages = split_at_via_flags(sys.argv[1:])
        result = None
        for stage in stages:
            result = execute_stage(stage, input=result)
    else:
        # Traditional single-stage execution
        result = execute_stage(sys.argv[1:])
```

### Phase 2: Implement Pipeline Execution

**Pipeline Flow**:
1. Parse arguments for each stage
2. Execute Stage 1 (match on full database) → generates MatchRecords
3. Execute Stage 2 (match on previous results) → filters MatchRecords
4. Execute Final Stage (render) → formats output

**Key Files to Modify**:
- `via/__main__.py` - Add `--via` detection and pipeline orchestration
- `via/commands/match.py` - Accept MatchRecords as input (not just db)
- `via/commands/render.py` - New command to handle rendering stage
- `via/core/interfaces.py` - Update ArgumentProvider to support staged parsing

### Phase 3: Add Render Command

```python
# via/commands/render.py

class RenderCommand(ArgumentProvider, HelpProvider):
    """Render match results with various output formats."""
    
    HELP = """
    Render match results using different output formats.
    
    Render types (use with -r):
      -oL, --list       : Simple list (type:file:line:name)
      -oT, --table      : Tabular format
      -oD, --diagram    : UML/mermaid diagram (classes only)
      -oU, --usage      : Show usage/references
      -oR, --raw        : Source code with syntax highlighting
    
    Output formats (use with format flag):
      -a, --ascii      : Terminal output with colors
      -m, --md         : Markdown format
      -h, --html       : HTML output
      -p, --png        : PNG image
    
    Context control:
      -A N             : Show N lines after symbol
      -B N             : Show N lines before symbol
      -C N             : Show N lines before and after
    """
    
    @classmethod
    def add_arguments(cls, parser):
        # Render type (mutually exclusive)
        render_group = parser.add_mutually_exclusive_group()
        render_group.add_argument('-L', '--list', action='store_true')
        render_group.add_argument('-T', '--table', action='store_true')
        render_group.add_argument('-D', '--diagram', action='store_true')
        render_group.add_argument('-U', '--usage', action='store_true')
        render_group.add_argument('-R', '--raw', action='store_true')
        
        # Format (mutually exclusive)
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument('-a', '--ascii', action='store_true')
        format_group.add_argument('-m', '--md', action='store_true')
        format_group.add_argument('-h', '--html', action='store_true')
        format_group.add_argument('-p', '--png', action='store_true')
        
        # Context control
        parser.add_argument('-A', type=int, default=0, help='Lines after')
        parser.add_argument('-B', type=int, default=0, help='Lines before')
        parser.add_argument('-C', type=int, help='Lines before and after')
    
    def execute(self, records: List[MatchRecord], args):
        # 1. Determine render type and format from args
        # 2. Select appropriate renderer
        # 3. Apply context settings
        # 4. Render each record
        # 5. Output result
        pass
```

---

## Changes to Existing Code

### 1. `via/__main__.py`

```python
def main():
    # NEW: Detect --via flag
    if '--via' in sys.argv:
        stages = split_at_via_flags(sys.argv[1:])
        pipeline_main(stages)
    else:
        traditional_main(sys.argv[1:])

def pipeline_main(stages):
    """Execute multi-stage pipeline."""
    result = None
    for i, stage_args in enumerate(stages):
        if i == 0:
            # First stage: match from database
            result = execute_match_stage(stage_args, db_store)
        elif i == len(stages) - 1:
            # Last stage: may be render
            if is_render_stage(stage_args):
                result = execute_render_stage(result, stage_args)
            else:
                # Could be another match
                result = execute_match_stage(stage_args, records=result)
        else:
            # Middle stages: filter previous results
            result = execute_match_stage(stage_args, records=result)
    
    # Output final result
    for record in result:
        print(record.to_string())
```

### 2. `via/commands/match.py`

```python
class MatchCommand(ArgumentProvider, HelpProvider):
    """Match command now accepts optional input records for pipeline."""
    
    @classmethod
    def add_arguments(cls, parser):
        # Existing arguments...
        parser.add_argument('-m', action='store_true', help='Match mode')
        # ... more args
    
    def execute(self, args, input_records=None):
        """Execute match.
        
        Args:
            args: Parsed arguments
            input_records: Optional MatchRecords from previous stage
        
        Returns:
            Generator of MatchRecords
        """
        if input_records:
            # Filter input records (don't query database)
            yield from self.filter_records(input_records, args)
        else:
            # Query database (traditional behavior)
            yield from self.query_database(args)
```

### 3. MatchRecord Support Matrix

Each MatchRecord type declares what render types it supports:

```python
class ClassMatchRecord(MatchRecord):
    """Class records support all render types."""
    
    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in [
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.DIAGRAM,
            RenderType.USAGE,
            RenderType.RAW
        ]

class FileMatchRecord(MatchRecord):
    """File records support limited render types."""
    
    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in [
            RenderType.LIST,
            RenderType.TABLE
        ]
```

---

## CLI Structure (Final)

```
via [FLAGS] [--via [FLAGS]] [--via [FLAGS]]

Examples:
  via -mg -tc '*Match*'                           # Simple match
  via -mg -tc '*Match*' -oT -fm                # Match + render table
  via -mg -tc '*Match*' --via -mr '^__.*__$'      # Match + filter
  via -mg '*' --via -mr '_.*' -oD -fm        # Full pipeline
```

---

## Risk & Mitigation

### Risk: Complex Argument Parsing
**Mitigation**: Build parser incrementally, test each stage separately

### Risk: User Confusion with Shorthand Flags
**Mitigation**: Excellent help text, clear examples, `--explain` flag for debugging

### Risk: Breaking Changes
**Mitigation**: `--via` flag is optional; traditional CLI still works

---

## Files to Create/Modify

| File | Operation | Lines | Notes |
|------|-----------|-------|-------|
| `via/__main__.py` | Modify | ~100 | Add `--via` detection and pipeline orchestration |
| `via/commands/render.py` | Create | ~150 | New RenderCommand class |
| `via/commands/__init__.py` | Modify | ~5 | Export RenderCommand |
| `via/core/interfaces.py` | Modify | ~20 | Add pipeline input support to ArgumentProvider |
| Tests | Create | ~200 | Unit and integration tests for pipeline |

**Total Implementation**: ~475 lines of code

---

**Key Difference from Initial Design**: 
NOT separate `via render` and `via pipeline` commands.  
INSTEAD: Single `via` command with `--via` flag for internal pipeline stages.  
This matches the actual Sprint 3 requirements!

