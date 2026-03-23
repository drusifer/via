Complete reference for indexing, searching, and navigating Python, JavaScript, and TypeScript codebases with VIA.

TLDR:
    Covers every aspect of VIA usage: installation, incremental indexing, the
    pipeline query syntax (`via -m<X> PATTERN -t<Y> -o<Z>`), all output formats
    (list, table, raw, formatted, usage/docstring, JSON via -oJ), context-line
    flags (-A/-B/-C), relationship queries (inheritance, calls, imports, references,
    container membership -Vhas, `--ref-type` alternative specifier, `--stale`
    cross-stage temporal filter, with --invert), temporal filtering (--newerthan /
    --olderthan with human-friendly durations), watch mode (`via index . -w`),
    and MCP server mode (`via mcp serve` / `via install mcp`) for AI agent integration.
    All pattern matching is case-sensitive by default; use -I to ignore case.
    Includes a practical examples section and a troubleshooting guide for common
    errors (missing database, no REGEXP support, slow indexing).
    Intended for end-users and AI agents; complements the README and the
    architecture document at agents/morpheus.docs/VIA_ARCHITECTURE.md.

# VIA User Guide

A complete guide to using VIA for indexing and searching Python, JavaScript, and TypeScript codebases.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Indexing](#indexing)
4. [Searching with Pipeline Syntax](#searching-with-pipeline-syntax)
5. [Output Formats](#output-formats)
6. [Context Lines](#context-lines)
7. [Relationship Queries](#relationship-queries)
8. [Container Queries (-Vhas)](#container-queries--vhas)
9. [Temporal Queries](#temporal-queries)
10. [Watch Mode](#watch-mode)
11. [MCP Mode (AI Agent Integration)](#mcp-mode-ai-agent-integration)
12. [Legacy Subcommand Syntax](#legacy-subcommand-syntax)
13. [Practical Examples](#practical-examples)
14. [Troubleshooting](#troubleshooting)

---

## Installation

```bash
# Clone and install
git clone https://github.com/your-org/via.git
cd via
python -tm venv .venv
source .venv/bin/activate
pip install -e .

# Verify
via --version
```

---

## Quick Start

```bash
# 1. Index your codebase
cd /path/to/your/python/project
via index .

# 2. Search for symbols
via -mg '*' -tc              # All classes
via -mg 'test_*' -tf         # Test functions
via -mg '*save*' -tm         # Methods containing "save"

# 3. View source code
via -mg 'User' -tc -oF    # Class with syntax highlighting
via -mg 'main' -tf -oR    # Function as raw source
```

---

## Indexing

### Basic Usage

```bash
# Index current directory
via index .

# Index specific directory
via index /path/to/project

# Force full re-index (ignore timestamps)
via index . --force

# Verbose output
via index . -v
via index . -vv    # More detail
via index . -vvv   # Even more detail
```

### Supported Languages

| Language | Extensions | Symbols Extracted |
|----------|-----------|-------------------|
| Python | `.py`, `.pyx`, `.pyi` | classes, methods, functions, imports, globals |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | classes, methods, functions, imports, globals |
| TypeScript | `.ts`, `.tsx` | classes, interfaces, enums, methods, functions, imports, globals, type aliases |
| Markdown | `.md`, `.markdown` | headers |

**Default excluded directories**: `node_modules/`, `dist/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `.turbo/`, `__pycache__/`, `.git/`. Add more with `--exclude`.

### What Gets Indexed

| Symbol Type | Example | Description |
|-------------|---------|-------------|
| class | `class User:` / `class Server extends Base {}` | Class definitions (Python + JS/TS) |
| method | `def save(self):` / `render() {}` | Methods inside classes |
| function | `def main():` / `function main() {}` / `const fn = () => {}` | Top-level functions |
| import | `import json` / `import { X } from 'y'` | Import statements |
| global | `MAX_SIZE = 100` / `const PORT = 3000` | Module-level variables |
| header | `## Section` | Markdown headers |

### Incremental Updates

VIA tracks file modification times. Only changed files are re-indexed:

```bash
$ via index .
Files indexed: 50

# Make changes to 2 files...

$ via index .
Files indexed: 2, Files skipped: 48
```

---

## Searching with Pipeline Syntax

The recommended way to search uses **pipeline syntax**:

```
via -m<X> PATTERN [-t<Y>...] [-o<Z>] [-f<W>] [OPTIONS]

**Note on filtering**: The `--via` flag is used to chain additional match filters. For example, `via -mg '*' -tc --via -mr 'Test.*'` will first find all classes, and then filter those results to classes matching the regex 'Test.*'.

**Note on multiple types**: You can specify multiple type flags to search for symbols of different types. For example, `via -mg '*' -tc -tf` will search for all classes and functions.
```

### Pattern Flags

| Flag | Type | Wildcards | Example |
|------|------|-----------|---------|
| `-mg` | Glob (default) | `*` any, `?` single | `-g '*save*'` |
| `-ms` | SQL LIKE | `%` any, `_` single | `-s '%save%'` |
| `-mr` | Regex | Full regex | `-r '^test_.*'` |

### Type Flags

| Flag | Type | Description |
|------|------|-------------|
| `-tc` | class | Class definitions |
| `-tm` | method | Class methods |
| `-tf` | function | Top-level functions |
| `-ti` | import | Import statements |
| `-tg` | global | Module-level variables |
| `-tF` | filepath | Full file paths |
| `-tN` | filename | File names only |
| `-tH` | header | Markdown headers |

**Omit type flags to search all symbol types.**

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n N` | Limit results | 10 |
| `-n 0` | Unlimited results | - |
| `-I` | Case-insensitive matching (all patterns are case-sensitive by default) | Off |
| `-Q` | Match against qualified name (useful with `-tF` for full-path matching) | Off |
| `--newerthan DURATION` | Only symbols from files modified within duration (e.g. `1h`, `2d`, `1w`) | Off |
| `--olderthan DURATION` | Only symbols from files NOT modified within duration | Off |

### Examples

```bash
# All classes
via -mg '*' -tc

# Classes ending with "Manager"
via -mg '*Manager' -tc

# Test functions (first 5)
via -mg 'test_*' -tf -n 5

# Methods containing "save" (case-insensitive)
via -mg '*save*' -tm -I

# All symbols matching "main"
via -mg '*main*'

# Unlimited results
via -mg '*' -tf -n 0
```

---

## Output Formats


### Format Flags (-f<X>)

| Flag | Format |
|------|--------|
| `-fa` | ASCII (terminal colors) |
| `-fm` | Markdown |
| `-fh` | HTML |
| `-fp` | PNG image |


Add `--via` followed by output flags to change format:

| Flag | Format | Description |
|------|--------|-------------|
| `-oL` | List | One result per line (default) |
| `-oT` | Table | ASCII table format |
| `-oR` | Raw | Source code extraction |
| `-oF` | Formatted | Syntax-highlighted source |
| `-oU` | Usage | Renders the docstring of the matched symbol |
| `-oJ` | JSON | JSON array of symbol objects (AI agents / MCP) |

### List Output (Default)

```bash
via -mg '*' -tc -n 3
```

Output:
```
class:via/core/types.py:35:MatchOp:@890+120
class:via/core/types.py:58:MatchResult:@1234+340
class:via/db/store.py:42:DatabaseStore:@1456+8900
```

### Table Output

```bash
via -mg '*Record' -tc -oT
```

Output:
```
| Type  | Name               | File                    | Line | Qualified Name       |
|-------|--------------------|-------------------------|------|----------------------|
| class | MatchRecord        | via/core/match_record.py | 41  | MatchRecord          |
| class | ClassMatchRecord   | via/core/match_record.py | 89  | ClassMatchRecord     |
| class | MethodMatchRecord  | via/core/match_record.py | 112 | MethodMatchRecord    |
```

### Raw Source Output

```bash
via -mg 'extract_source' -tf -oR
```

Output:
```
############################################################
# via/renderers/utils/source_extraction.py:21-67
#     function *extract_source*
############################################################
def extract_source(
    file_path: str,
    byte_offset: Optional[int],
    byte_length: Optional[int],
    before_context: int = 0,
    after_context: int = 0,
    read_full_file: bool = False
) -> str:
    """Extract source code from file."""
    ...
```

### Formatted Output (Syntax Highlighting)

```bash
via -mg 'Renderer' -tc -oF -n 1
```

Output shows syntax-highlighted Python code with ANSI colors.

---


### Usage Output (Docstrings)

```bash
via -mg 'MyClassName' -tc -oU
```

Output:
```
############################################################
# via/my_module.py:123
#     class *MyClassName*
############################################################
This is the docstring for MyClassName.
It can be multiple lines.
```

## Context Lines

Show surrounding code with raw (`-oR`) or formatted (`-oF`) output:

| Flag | Description |
|------|-------------|
| `-B N` | N lines before match |
| `-A N` | N lines after match |
| `-C N` | N lines before AND after |

### Examples

```bash
# Show 3 lines before the match
via -mg 'main' -tf -oR -B 3

# Show 5 lines after the match
via -mg 'User' -tc -oF -A 5

# Show 2 lines on each side
via -mg 'save' -tm -oR -C 2
```

### Disable Headers

Use `--nodelims` to remove the delimiter headers between matches:

```bash
via -mg '*' -tf -oR --nodelims
```

---

## Relationship Queries

VIA can trace relationships between symbols: inheritance, function calls, imports, and references. This lets you navigate code structure, not just search for names.

### Syntax

```
via -m<X> SUBJECT -t<Y> -V<rel> -m<X> OBJECT -t<Y> [--invert]
```

- **SUBJECT** (before `-V`): The symbol you're querying about (the "known" thing)
- **OBJECT** (after `-V`): Filter the results (defaults to `*` = all matches)
- **`--invert` / `-iv`**: Flip the relationship direction

### Relationship Flags

| Relationship | Long Form | Short Form | Default Direction | With `--invert` |
|---|---|---|---|---|
| Inheritance | `--via inherits-from` | `-Vinh` | Find children of X | Find parents of X |
| Calls | `--via calls` | `-Vca` | Find callers of X | Find callees of X |
| Imports | `--via imports` | `-Vimp` | Find importers of X | Find imports by X |
| References | `--via references` | `-Vr` | Find referencers of X | Find references by X |
| Container membership | `--via-has` | `-Vhas` | Find members of container X | (not supported) |

### `--ref-type`: Alternative Relationship Specifier

`--ref-type <value>` is a third way to specify relationship type — equivalent to `-V<X>` short flags and `--via <type>` long forms. Useful when scripting or when you prefer explicit column names.

Valid values: `inherits-from`, `calls`, `imports`, `references`, `declares`

```bash
# These three are exactly equivalent:
via -mg 'BaseClass' -tc -Vinh -mg '*' -tc
via -mg 'BaseClass' -tc --via inherits-from -mg '*' -tc
via -mg 'BaseClass' -tc --ref-type inherits-from -mg '*' -tc

# --ref-type with --invert
via -mg 'MyClass' -tc --ref-type inherits-from -iv -mg '*' -tc

# --ref-type declares (same as -Vhas)
via -mg 'MyClass' -tc --ref-type declares -mg '*' -tm
```

> **Note**: If both `--via` and `--ref-type` appear in the same stage, `--via` wins (scan order). An invalid value exits with an error listing valid choices.

### `--stale`: Cross-Stage Temporal Filter

`--stale` filters relationship results to those where the **result symbol's file is older than the anchor's file**. Use it to find stale dependencies — code that was last touched *before* the thing it depends on.

```bash
# Find test files that haven't been updated since the classes they test changed
via -mg '*' -tc -Vinh -mg 'test_*' -tf --stale

# Find subclasses older than their base class (may need to catch up with parent changes)
via -mg 'Base*' -tc -Vinh -mg '*' -tc --stale

# Find callers that pre-date the function they call (stale call sites)
via -mg 'my_func' -tf -Vca -mg '*' -tf --stale
```

> **Note**: `--stale` only applies to relationship queries (stages separated by `-V*` or `--via`). On a plain match query with no relationship it is a no-op. If mtime data is missing, rebuild the index with `via index --force`.

### Inheritance Examples

```bash
# Find all classes that inherit from BaseClass
via -mg 'BaseClass' -tc -Vinh -mg '*' -tc

# Find what MyClass inherits from (parents)
via -mg 'MyClass' -tc -Vinh -mg '*' -tc --invert

# Find children of any class matching *Base*
via -mg '*Base*' -tc -Vinh -mg '*' -tc

# Filter: only show children matching "Child*"
via -mg 'BaseClass' -tc -Vinh -mg 'Child*' -tc
```

### Import Examples

```bash
# Find all files that import typing
via -mg 'typing' -Vimp -mg '*' -tF

# Find what a specific file imports
via -mg 'my_service.py' -tF -Vimp -mg '*' --invert

# Find all files importing dataclasses, show as table
via -mg 'dataclasses' -Vimp -mg '*' -tF --via -oT
```

### Call Examples

```bash
# Find all functions that call helper_func
via -mg 'helper_func' -tf -Vca -mg '*' -tf

# Find what main() calls (callees)
via -mg 'main' -tf -Vca -mg '*' -tf --invert

# Find all callers of a method
via -mg 'save' -tm -Vca -mg '*' -tm
```

### Reference Examples

```bash
# Find all functions that reference a constant
via -mg 'MAX_RETRIES' -tG -Vr -mg '*' -tf

# Find what external symbols a function references
via -mg 'process_data' -tf -Vr -mg '*' --invert
```

### Combining with Output Formats

```bash
# Inheritance tree as table
via -mg 'BaseClass' -tc -Vinh -mg '*' -tc --via -oT

# Show source of all callers
via -mg 'validate' -tf -Vca -mg '*' -tf --via -oR
```

---

## Container Queries (`-Vhas`)

`-Vhas` queries "what lives inside this container?" — file→symbols, class→methods, function→nested functions. It replaces awkward qualified-name workarounds.

### Syntax

```
via -m<X> CONTAINER_PATTERN -t<container> -Vhas -t<member>
```

Valid container types: `-tF` (filepath), `-tN` (filename), `-tc` (class), `-tf` (function)

### Examples

```bash
# All classes defined in store.py
via -mg 'store.py' -tN -Vhas -tc

# All methods of DatabaseStore
via -mg 'DatabaseStore' -tc -Vhas -tm

# All functions in service files
via -mg '*service*' -tF -Vhas -tf -n 0

# All methods in executor.py, as table
via -mg 'executor.py' -tN -Vhas -tm -oT -n 0

# All test functions across all test files
via -mg 'test_*.py' -tN -Vhas -tf -n 0
```

> **Note**: All patterns are case-sensitive. Use `-I` for case-insensitive matching.
> `--invert` is not supported with `-Vhas`.

---

## Temporal Queries

Filter symbols by when their source file was last modified. Useful for finding recently changed code or stale symbols.

### Syntax

```
via -m<X> PATTERN -t<Y> --newerthan DURATION
via -m<X> PATTERN -t<Y> --olderthan DURATION
```

### Duration Format

Human-friendly durations: `30s`, `5m`, `2h`, `1d`, `1w`

| Unit | Example | Meaning |
|------|---------|---------|
| `s` | `30s` | 30 seconds |
| `m` | `5m` | 5 minutes |
| `h` | `2h` | 2 hours |
| `d` | `1d` | 1 day |
| `w` | `1w` | 1 week |

### Examples

```bash
# Classes in files modified in the last hour
via -mg '*' -tc --newerthan 1h

# All symbols changed today
via -mg '*' --newerthan 1d -n 0

# Functions in files not touched in over a week (stale code)
via -mg '*' -tf --olderthan 1w

# Recently changed test functions
via -mg 'test_*' -tf --newerthan 2d
```

> **Note**: Timestamps are per-symbol. Watch mode updates symbol mtimes as files change — only modified symbols get new timestamps, not all symbols in the file.

---

## Watch Mode

Keep the index automatically up-to-date as you edit files.

```bash
via index . -w     # Index then watch — re-indexes on every save
```

VIA detects file changes using watchdog with a 1-second debounce. Changed files are re-indexed automatically; deleted files are fully removed (symbols and relationships). Press Ctrl-C to stop.

---

## MCP Mode (AI Agent Integration)

VIA can run as an MCP (Model Context Protocol) server, exposing a `via_query` tool to Claude Code and other MCP clients over JSON-RPC 2.0 via stdio. The index is always current — watch mode starts automatically when the server starts.

### Setup

```bash
# Register via as an MCP server in the current project
via install mcp

# Check registration status
via status mcp

# Remove registration
via uninstall mcp
```

`via install mcp` writes `.mcp.json` in the project root (next to `.via/`). Claude Code reads this at session startup and calls `tools/list` to discover the `via_query` tool.

### Starting the Server

```bash
via mcp serve              # Serve from current directory
via mcp serve /path/to/project   # Serve a specific project
```

The server starts WatchService in a background thread (index stays current) and listens for JSON-RPC 2.0 on stdin/stdout. Exit by closing stdin (Claude Code does this automatically on session end).

### Calling via_query

Claude Code can call the tool with the same CLI args you would use on the command line:

```json
{"args": ["-mg", "*Parser*", "-tc"]}         // All Parser classes
{"args": ["-mg", "*", "-tf", "-n", "20"]}   // First 20 functions
{"args": ["stats"]}                           // Database statistics
```

Results are returned as a JSON array of symbol objects with fields: `symbol_name`, `symbol_type`, `file_path`, `line_number`, `byte_offset`, `byte_length`, `qualified_name`, `parent_name`.

### Inspecting the Schema

```bash
via mcp schema             # Print the via_query tool schema as JSON
```

This shows exactly what Claude Code sees when it calls `tools/list`.

---

## Legacy Subcommand Syntax

The older subcommand syntax still works:

```bash
# Index
via index .
via index /path/to/project --force

# Match
via match '*save*' -t method
via match 'test_*' -t function -g
via match '%User%' -t class -s -I
```

**Note:** Pipeline syntax is recommended for new usage.

---

## Practical Examples

### Find All Test Functions

```bash
via -mg 'test_*' -tf
```

### Find Classes in a Module Pattern

```bash
via -mg '*Handler' -tc -oT
```

### View a Specific Class Implementation

```bash
via -mg 'DatabaseStore' -tc -oF
```

### Find Methods and Show Context

```bash
via -mg '*save*' -tm -oR -C 5
```

### Count Symbols

```bash
# Count all classes
via -mg '*' -tc -n 0 | wc -l

# Count all methods
via -mg '*' -tm -n 0 | wc -l

# Count test functions
via -mg 'test_*' -tf -n 0 | wc -l
```

### Find Unique Files with Matches

```bash
via -mg '*save*' -tm -n 0 | cut -d: -tf2 | sort -u
```

### Search Imports

```bash
# Find all typing imports
via -mg '*typing*' -ti

# Find json imports
via -mg 'json' -ti
```

### Find Global Constants

```bash
# Find all globals
via -mg '*' -tg

# Find uppercase constants
via -mg '*_*' -tg
```

### Find Files by Name or Path

```bash
# Find test files (by filename)
via -mg '*test*' -tN

# Find files in a directory (by full path — requires -Q)
via -mg 'via/core/*' -tF -Q

# Find all Python files under a subdirectory
via -mg '*/pipeline/*' -tF -Q -n 0
```

### Complex Pipeline: Search and Format

```bash
# Find all Renderer classes with syntax highlighting
via -mg '*Renderer' -tc -oF

# Find save methods, show as table
via -mg '*save*' -tm -oT

# Find functions, show raw source with 3 lines context
via -mg 'main' -tf -oR -C 3
```

---

## Troubleshooting

### "Database not found"

Run `via index .` first:

```bash
$ via -mg '*' -tc
Error: Database not found

$ via index .
$ via -mg '*' -tc
# Now works
```

### No Results

1. **Case sensitivity**: Patterns are case-sensitive by default. `*store*` won't match `DatabaseStore` — use `*Store*` or add `-I` for case-insensitive matching.
2. **Broaden pattern**: Try `via -mg '*' -tc` to see if anything matches
3. **Check type**: Try different type flags (`-tc`, `-tm`, `-tf`)
4. **File path matching**: Use `-Q` with `-tF` to match by full directory path: `via -mg 'via/core/*' -tF -Q`
5. **Re-index**: Run `via index . --force`

### REGEXP Not Available

SQLite REGEXP requires an extension that may not be installed:

```bash
$ via -mr '^test_.*' -tf
Error: no such function: REGEXP

# Use glob instead
$ via -mg 'test_*' -tf
```

### Slow Indexing

- Use incremental indexing (default)
- Add patterns to `.gitignore`
- Use `--exclude` for generated directories

---

## Quick Reference

### Index Commands

```bash
via index .                  # Index current directory
via index /path --force      # Force re-index
via index . -vvv             # Very verbose
```

### Search Commands

```bash
via -mg PATTERN               # Search all types
via -mg PATTERN -tc            # Search classes
via -mg PATTERN -tm            # Search methods
via -mg PATTERN -tf            # Search functions
via -mg PATTERN -ti            # Search imports
via -mg PATTERN -tg            # Search globals
via -mg PATTERN -tF            # Search filepaths
via -mg PATTERN -tN            # Search filenames
```

### Output Commands

```bash
via ... -oL            # List output
via ... -oT            # Table output
via ... -oR            # Raw source
via ... -oF            # Formatted source
via ... -oR -C 3       # With context lines
```

### Relationship Commands

```bash
via ... -Vinh ...              # Inheritance (inherits-from)
via ... -Vca ...               # Calls
via ... -Vimp ...              # Imports
via ... -Vr ...                # References
via ... -Vhas ...              # Container membership (file/class has member)
via ... --invert               # Flip direction (or -iv)
```

### Temporal Commands

```bash
via ... --newerthan 1d         # Symbols from files changed in last day
via ... --olderthan 1w         # Symbols from files not changed in last week
```

### Pattern Types

```bash
-mg 'pattern'                 # Glob: * ?  (case-sensitive; add -I to ignore case)
-ms 'pattern'                 # SQL LIKE: % _
-mr 'pattern'                 # Regex (if available)
-Q                            # Match qualified name (full path for -tF)
```
