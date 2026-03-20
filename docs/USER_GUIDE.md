Complete reference for indexing, searching, and navigating Python codebases with VIA.

TLDR:
    Covers every aspect of VIA usage: installation, incremental indexing, the
    pipeline query syntax (`via -m<X> PATTERN -t<Y> -o<Z>`), all output formats
    (list, table, raw, formatted, usage/docstring, JSON via -oJ), context-line
    flags (-A/-B/-C), relationship queries (inheritance, calls, imports, references
    with --invert), watch mode (`via index . -w`), and MCP server mode
    (`via mcp serve` / `via install mcp`) for AI agent integration.
    Includes a practical examples section and a troubleshooting guide for common
    errors (missing database, no REGEXP support, slow indexing).
    Intended for end-users and AI agents; complements the README and the
    architecture document at agents/morpheus.docs/VIA_ARCHITECTURE.md.

# VIA User Guide

A complete guide to using VIA for indexing and searching Python codebases.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Indexing](#indexing)
4. [Searching with Pipeline Syntax](#searching-with-pipeline-syntax)
5. [Output Formats](#output-formats)
6. [Context Lines](#context-lines)
7. [Relationship Queries](#relationship-queries)
8. [Watch Mode](#watch-mode)
9. [MCP Mode (AI Agent Integration)](#mcp-mode-ai-agent-integration)
10. [Legacy Subcommand Syntax](#legacy-subcommand-syntax)
11. [Practical Examples](#practical-examples)
12. [Troubleshooting](#troubleshooting)

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

### What Gets Indexed

| Symbol Type | Example | Description |
|-------------|---------|-------------|
| class | `class User:` | Class definitions |
| method | `def save(self):` | Methods inside classes |
| function | `def main():` | Top-level functions |
| import | `import json` | Import statements |
| global | `MAX_SIZE = 100` | Module-level variables |

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
| `-c` | class | Class definitions |
| `-m` | method | Class methods |
| `-f` | function | Top-level functions |
| `-i` | import | Import statements |
| `-G` | global | Module-level variables |
| `-F` | filepath | Full file paths |
| `-N` | filename | File names only |

**Omit type flags to search all symbol types.**

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n N` | Limit results | 10 |
| `-n 0` | Unlimited results | - |
| `-I` | Case-insensitive | Off |

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

### Find Files by Name

```bash
# Find test files
via -mg '*test*' -tN

# Find files in tests directory
via -mg '*tests*' -tF
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

1. **Broaden pattern**: Try `via -mg '*' -tc` to see if anything matches
2. **Check type**: Try different type flags (`-c`, `-m`, `-f`)
3. **Case sensitivity**: Add `-I` for case-insensitive
4. **Re-index**: Run `via index . --force`

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
via ... --invert               # Flip direction (or -iv)
```

### Pattern Types

```bash
-mg 'pattern'                 # Glob: * ?
-ms 'pattern'                 # SQL LIKE: % _
-mr 'pattern'                 # Regex (if available)
```
