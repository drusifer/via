Sprint 3 design spec for composable CLI pipeline with integrated rendering stages.

TLDR:
    Problem: Sprint 2 had separate match and render commands with no composable
    pipeline. Solution: Sprint 3 introduces a unified entry point with shorthand
    flags (-ml, -mt, -mr, -md) and a --via separator for multi-stage pipelines,
    enabling match | filter | render in a single CLI invocation. Covers architecture,
    CLI examples, implementation phases, and a files-to-modify checklist.

# Design: Sprint 3 Internal Pipeline with Integrated Rendering

**Based on**: Cypher's PRD + Morpheus's SPRINT_3_ARCHITECTURE.md + Drew's feedback
**Date**: January 22, 2026
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 3 implements an **internal pipeline architecture** that chains operations within a single `via` command. The key insight: **rendering is NOT a separate stage**—it's integrated into the match command as optional output formatting.

**Design principle**: Most queries are single-stage (match + optional render), but complex queries can chain multiple match stages with `--via` for filtering.

---

## Problem Statement

### Current Limitations (Sprint 2)
```bash
# Users must use Unix pipes to combine operations
via match -tc --mglob '*Match*' | via render --table --md

# Verbose and hard to discover
# Requires understanding of input format
# Multiple processes overhead
```

### Solution (Sprint 3)
```bash
# Single command for match + render (most common case)
via -mg -tc '*Match*' -oT -fm

# Internal pipeline for filtering (optional)
via -mg -tc '*Match*' --via -mr '^__.*__$' -oD -fm
```

---

## Architecture Design

### 1. Unified Command Entry Point

The main `via` command supports **two modes**:

**Mode A: Single Stage (No Pipeline)** - Most Common (~90% of use cases)
```bash
# Match + optional render in one command
via -mg -tc '*Match*'          # Match, default list render
via -mg -tc '*Match*' -oT -fm     # Match, render as table in markdown
```

**Mode B: Multi-Stage Pipeline (Optional)** - Advanced (~10% of use cases)
```bash
# Chain multiple filtering stages with --via
via -mg -tc '*Match*' --via -mr -tm '^__.*__$' -oD -fm

# Explanation:
# Stage 1: Match classes matching glob '*Match*'
# Stage 2: From those results, match methods matching regex '^__.*__$'
# Stage 3: Render as diagram in markdown format
```

**Key Insight**: `--via` is OPTIONAL. Rendering is part of match command, not a separate stage.

### 2. Pipeline Stages Explained

**Stage 1: Match** (Search indexed database)
- **Mode**: Single-stage or pipeline first stage
- **Input**: Database (first stage only) or previous results (pipeline)
- **Output**: MatchRecords stream
- **Flags**: `-m` `-mg/-r/-s` `-t` `-I` `-n`
- **Example**: `-mg -tc '*Match*'` = match classes with glob pattern

**Stage 2+: Match (Optional)** (Filter previous results)
- **Mode**: Pipeline only (requires `--via`)
- **Input**: Previous stage's MatchRecords
- **Output**: Filtered MatchRecords stream
- **Flags**: Same as Stage 1
- **Example**: `-mr -tm '^__.*__$'` = filter to methods matching regex

**Render: INTEGRATED** (NOT a separate stage!)
- **Mode**: Part of any match stage (can appear on Stage 1, Stage 2, or last stage)
- **Input**: MatchRecords from current stage
- **Output**: Formatted strings
- **Flags**: `-r` render_type `-a/-m/-h/-p` format `-A/-B/-C` context
- **Example**: `-oT -fm` = render table in markdown format

### 3. Shorthand Flags Reference

**Match Mode**:
```
-m = match mode enabled
```

**Match Syntax** (mutually exclusive):
```
-mg PATTERN = --mglob       (shell wildcards: *, ?)
-r PATTERN = --mregex      (Python regex)
-s PATTERN = --msql        (SQL LIKE: %, _)
```

**Symbol Types** (use with `-t` or directly):
```
-c = --class
-m = --method
-f = --function
-i = --import
-G = --mglobal
-F = --file or --filepath
-N = --filename
-h = --header
```

**Render Types** (use with `-r` in output format):
```
-oL = --list       (simple list: type:file:line:name)
-oT = --table      (tabular view with columns)
-oD = --diagram    (UML/mermaid diagram - classes only)
-oU = --usage      (usage/references patterns)
-oR = --raw        (source code with syntax highlighting)
```

**Output Formats**:
```
-a = --ascii       (terminal with colors)
-m = --md          (markdown format)
-h = --html        (HTML output)
-p = --png         (image - requires rendering)
```

**Context Control** (for `-oR` raw format):
```
-A N = --after N   (show N lines after symbol)
-B N = --before N  (show N lines before symbol)
-C N = --context N (show N lines before AND after)
```

---

## CLI Examples

### Example 1: Simple Match (No Render) - Defaults to List
```bash
via -mg -tc '*Match*'
```
**Output**: List of classes matching glob pattern

### Example 2: Match + Render Table (Most Common)
```bash
via -mg -tc '*Match*' -oT -fm
```
**Output**: Classes rendered as markdown table

### Example 3: Match + Raw Code with Context
```bash
via -mg -tf 'calculate*' -oR -B 3 -A 3
```
**Output**: Functions matching glob, raw code with 3 lines before/after

### Example 4: Match + Filter (Uses --via)
```bash
via -mg -tc '*Match*' --via -mr -tm '^__.*__$'
```
**Output**: 
- Stage 1: Find all classes matching `*Match*`
- Stage 2: From those classes, find methods matching `^__.*__$`

### Example 5: Full Pipeline (Match + Filter + Render)
```bash
via -mg -tc '*Match*' --via -mr -tm '^__.*__$' -oD -fm
```
**Output**: Diagram showing methods of matching classes in markdown format

### Example 6: Complex Multi-Stage
```bash
via -mg '*' --via -mr -mg 'test_*' -oL
```
**Output**:
- Stage 1: Match all entities
- Stage 2: From results, match methods matching glob `test_*`
- Stage 3: Render as list

---

## Implementation Strategy

### Phase 1: Add Render Flags to Match Command

**Current State**: Match command outputs list format only  
**Goal**: Match command can output any render format without needing separate command

**Changes to `via/commands/match.py`**:
1. Add render type arguments (`-oL`, `-oT`, `-oD`, `-oU`, `-oR`)
2. Add format arguments (`-a`, `-m`, `-h`, `-p`)
3. Add context arguments (`-A`, `-B`, `-C`)
4. Update `execute()` to apply rendering

**Code Example**:
```python
@classmethod
def add_arguments(cls, parser):
    # Existing match arguments
    parser.add_argument('-m', action='store_true', help='Match mode')
    parser.add_argument('-mg', '--mglob', dest='pattern')
    parser.add_argument('-t', '--type', dest='symbol_type')
    
    # NEW: Render type (mutually exclusive)
    render_group = parser.add_mutually_exclusive_group()
    render_group.add_argument('-oL', '--list', dest='render_type', action='store_const', const='list')
    render_group.add_argument('-oT', '--table', dest='render_type', action='store_const', const='table')
    render_group.add_argument('-oD', '--diagram', dest='render_type', action='store_const', const='diagram')
    render_group.add_argument('-oU', '--usage', dest='render_type', action='store_const', const='usage')
    render_group.add_argument('-oR', '--raw', dest='render_type', action='store_const', const='raw')
    
    # NEW: Output format (mutually exclusive)
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument('-a', '--ascii', dest='format', action='store_const', const='ascii')
    format_group.add_argument('-m', '--md', dest='format', action='store_const', const='md')
    format_group.add_argument('-h', '--html', dest='format', action='store_const', const='html')
    format_group.add_argument('-p', '--png', dest='format', action='store_const', const='png')
    
    # NEW: Context control
    parser.add_argument('-A', type=int, default=0, help='Lines after')
    parser.add_argument('-B', type=int, default=0, help='Lines before')
    parser.add_argument('-C', type=int, help='Lines before and after')

def execute(self, args, input_records=None):
    """Execute match with optional rendering.
    
    Args:
        args: Parsed arguments (includes match AND render flags)
        input_records: Optional MatchRecords from previous pipeline stage
    
    Yields:
        Formatted output strings
    """
    # Get match results
    if input_records:
        # Pipeline mode: filter previous results
        records = self.filter_records(input_records, args)
    else:
        # Single-stage mode: query database
        records = self.query_database(args)
    
    # Apply rendering if requested
    if hasattr(args, 'render_type') and args.render_type:
        renderer = get_renderer(args.render_type)
        formatter = get_formatter(getattr(args, 'format', 'ascii'))
        context = self._build_context_args(args)
        
        for record in records:
            if record.supports_render_type(args.render_type):
                yield renderer.render(record, formatter, context)
            else:
                # Fallback if render type not supported for this record type
                yield record.to_string()
    else:
        # Default: output as list (format: type:file:line:name)
        for record in records:
            yield record.to_string()

def _build_context_args(self, args):
    """Build context arguments from -A/-B/-C flags."""
    if hasattr(args, 'C') and args.C:
        return {'before': args.C, 'after': args.C}
    else:
        before = getattr(args, 'B', 0)
        after = getattr(args, 'A', 0)
        return {'before': before, 'after': after}
```

### Phase 2: Implement `--via` Detection and Pipeline Parsing

**Changes to `via/__main__.py`**:
1. Detect `--via` flag in sys.argv
2. If `--via` present: split into stages, execute pipeline
3. If no `--via`: execute single stage

```python
def main():
    # Check for --via flag (pipeline mode)
    if '--via' in sys.argv:
        stages = split_at_via_flags(sys.argv[1:])
        pipeline_main(stages)
    else:
        # Single-stage mode (match with optional render)
        single_stage_main(sys.argv[1:])

def split_at_via_flags(argv: List[str]) -> List[List[str]]:
    """Split argv into segments at each --via flag."""
    segments = [[]]
    for arg in argv:
        if arg == '--via':
            segments.append([])
        else:
            segments[-1].append(arg)
    return [s for s in segments if s]  # Remove empty segments

def single_stage_main(argv: List[str]):
    """Execute single-stage match command."""
    parser = argparse.ArgumentParser()
    MatchCommand.add_arguments(parser)
    args = parser.parse_args(argv)
    
    # Execute and output
    for output_line in MatchCommand().execute(args):
        print(output_line)

def pipeline_main(stages: List[List[str]]):
    """Execute multi-stage pipeline."""
    parser = argparse.ArgumentParser()
    MatchCommand.add_arguments(parser)
    
    result = None
    
    for i, stage_args in enumerate(stages):
        args = parser.parse_args(stage_args)
        
        if i == 0:
            # First stage: query database
            result = MatchCommand().execute(args, input_records=None)
        else:
            # Subsequent stages: filter previous results
            result = MatchCommand().execute(args, input_records=result)
    
    # Output final results
    for output_line in result:
        print(output_line)
```

### Phase 3: Create Pipeline Parser (Optional, for validation)

**New file**: `via/pipeline/parser.py`
- Parse `--via` separated stages
- Validate each stage syntax
- Support error reporting

### Phase 4: Write Tests

**Test coverage**:
1. Single-stage match
2. Single-stage match + render
3. Multi-stage pipeline (match + filter)
4. Multi-stage pipeline (match + filter + render)
5. Render type support matrix validation
6. Context argument handling

---

## Architecture Comparison

| Scenario | Single Stage | Pipeline | Example |
|----------|--------------|----------|---------|
| **Match only** | ✅ | ❌ | `via -mg -tc '*'` |
| **Match + render** | ✅ | ❌ | `via -mg -tc '*' -oT -fm` |
| **Match + filter** | ❌ | ✅ | `via -mg -tc '*' --via -mr '^__'` |
| **Match + filter + render** | ❌ | ✅ | `via -mg -tc '*' --via -mr '^__' -oD -fm` |
| **Complexity** | Simple | Advanced | - |
| **Use Cases** | ~90% | ~10% | - |

---

## Render Type Support Matrix

Each MatchRecord type declares what render types it supports:

| Record Type | List | Table | Diagram | Usage | Raw |
|-------------|------|-------|---------|-------|-----|
| **Class** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Method** | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Function** | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Import** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Global** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **File** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Header** | ✅ | ✅ | ❌ | ❌ | ❌ |

**Rule**: If unsupported render type requested, fallback to list format.

---

## Files to Create/Modify

| File | Operation | Purpose |
|------|-----------|---------|
| `via/__main__.py` | Modify | Add `--via` detection, pipeline execution |
| `via/commands/match.py` | Modify | Add render flags, update execute() |
| `via/pipeline/parser.py` | Create | Parse and validate pipeline stages |
| Tests | Create | 30+ tests for all scenarios |

**Estimated code**: ~350 lines

---

## Key Design Principles

✅ **Render is integrated** — not a separate command or stage  
✅ **Single command for common case** — `via -mg -tc '*' -oT -fm` (no `--via` needed)  
✅ **Pipeline only for filtering** — use `--via` when you need multiple match stages  
✅ **Backward compatible** — existing `via match ...` syntax still works  
✅ **No Unix pipes needed** — internal pipeline is self-contained  
✅ **User-friendly** — most queries are single-stage, complex ones optional  

---

## Implementation Checklist

- [ ] Add render flags to MatchCommand.add_arguments()
- [ ] Update MatchCommand.execute() to handle rendering
- [ ] Add `--via` detection to __main__.py
- [ ] Implement pipeline parsing (split on `--via`)
- [ ] Implement pipeline execution (multi-stage)
- [ ] Add render type support validation
- [ ] Write unit tests (30+)
- [ ] Write integration tests
- [ ] Update help documentation
- [ ] Test all example commands
- [ ] Verify backward compatibility

