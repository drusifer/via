# VIA User Guide

A complete guide to using VIA for indexing and searching Python codebases.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Indexing](#indexing)
4. [Searching with Pipeline Syntax](#searching-with-pipeline-syntax)
5. [Output Formats](#output-formats)
6. [Context Lines](#context-lines)
7. [Legacy Subcommand Syntax](#legacy-subcommand-syntax)
8. [Practical Examples](#practical-examples)
9. [Troubleshooting](#troubleshooting)

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

### Pattern Types

```bash
-mg 'pattern'                 # Glob: * ?
-ms 'pattern'                 # SQL LIKE: % _
-mr 'pattern'                 # Regex (if available)
```
