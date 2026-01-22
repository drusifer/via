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
python -m venv .venv
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
via -g '*' -c              # All classes
via -g 'test_*' -f         # Test functions
via -g '*save*' -m         # Methods containing "save"

# 3. View source code
via -g 'User' -c --via -oF    # Class with syntax highlighting
via -g 'main' -f --via -oR    # Function as raw source
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
via -g PATTERN [TYPE_FLAGS] [OPTIONS] [--via OUTPUT_FLAGS]
```

### Pattern Flags

| Flag | Type | Wildcards | Example |
|------|------|-----------|---------|
| `-g` | Glob (default) | `*` any, `?` single | `-g '*save*'` |
| `-s` | SQL LIKE | `%` any, `_` single | `-s '%save%'` |
| `-r` | Regex | Full regex | `-r '^test_.*'` |

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
via -g '*' -c

# Classes ending with "Manager"
via -g '*Manager' -c

# Test functions (first 5)
via -g 'test_*' -f -n 5

# Methods containing "save" (case-insensitive)
via -g '*save*' -m -I

# All symbols matching "main"
via -g '*main*'

# Unlimited results
via -g '*' -f -n 0
```

---

## Output Formats

Add `--via` followed by output flags to change format:

| Flag | Format | Description |
|------|--------|-------------|
| `-oL` | List | One result per line (default) |
| `-oT` | Table | ASCII table format |
| `-oR` | Raw | Source code extraction |
| `-oF` | Formatted | Syntax-highlighted source |

### List Output (Default)

```bash
via -g '*' -c -n 3
```

Output:
```
class:via/core/types.py:35:MatchOp:@890+120
class:via/core/types.py:58:MatchResult:@1234+340
class:via/db/store.py:42:DatabaseStore:@1456+8900
```

### Table Output

```bash
via -g '*Record' -c --via -oT
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
via -g 'extract_source' -f --via -oR
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
via -g 'Renderer' -c --via -oF -n 1
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
via -g 'main' -f --via -oR -B 3

# Show 5 lines after the match
via -g 'User' -c --via -oF -A 5

# Show 2 lines on each side
via -g 'save' -m --via -oR -C 2
```

### Disable Headers

Use `--nodelims` to remove the delimiter headers between matches:

```bash
via -g '*' -f --via -oR --nodelims
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
via -g 'test_*' -f
```

### Find Classes in a Module Pattern

```bash
via -g '*Handler' -c --via -oT
```

### View a Specific Class Implementation

```bash
via -g 'DatabaseStore' -c --via -oF
```

### Find Methods and Show Context

```bash
via -g '*save*' -m --via -oR -C 5
```

### Count Symbols

```bash
# Count all classes
via -g '*' -c -n 0 | wc -l

# Count all methods
via -g '*' -m -n 0 | wc -l

# Count test functions
via -g 'test_*' -f -n 0 | wc -l
```

### Find Unique Files with Matches

```bash
via -g '*save*' -m -n 0 | cut -d: -f2 | sort -u
```

### Search Imports

```bash
# Find all typing imports
via -g '*typing*' -i

# Find json imports
via -g 'json' -i
```

### Find Global Constants

```bash
# Find all globals
via -g '*' -G

# Find uppercase constants
via -g '*_*' -G
```

### Find Files by Name

```bash
# Find test files
via -g '*test*' -N

# Find files in tests directory
via -g '*tests*' -F
```

### Complex Pipeline: Search and Format

```bash
# Find all Renderer classes with syntax highlighting
via -g '*Renderer' -c --via -oF

# Find save methods, show as table
via -g '*save*' -m --via -oT

# Find functions, show raw source with 3 lines context
via -g 'main' -f --via -oR -C 3
```

---

## Troubleshooting

### "Database not found"

Run `via index .` first:

```bash
$ via -g '*' -c
Error: Database not found

$ via index .
$ via -g '*' -c
# Now works
```

### No Results

1. **Broaden pattern**: Try `via -g '*' -c` to see if anything matches
2. **Check type**: Try different type flags (`-c`, `-m`, `-f`)
3. **Case sensitivity**: Add `-I` for case-insensitive
4. **Re-index**: Run `via index . --force`

### REGEXP Not Available

SQLite REGEXP requires an extension that may not be installed:

```bash
$ via -r '^test_.*' -f
Error: no such function: REGEXP

# Use glob instead
$ via -g 'test_*' -f
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
via -g PATTERN               # Search all types
via -g PATTERN -c            # Search classes
via -g PATTERN -m            # Search methods
via -g PATTERN -f            # Search functions
via -g PATTERN -i            # Search imports
via -g PATTERN -G            # Search globals
via -g PATTERN -F            # Search filepaths
via -g PATTERN -N            # Search filenames
```

### Output Commands

```bash
via ... --via -oL            # List output
via ... --via -oT            # Table output
via ... --via -oR            # Raw source
via ... --via -oF            # Formatted source
via ... --via -oR -C 3       # With context lines
```

### Pattern Types

```bash
-g 'pattern'                 # Glob: * ?
-s 'pattern'                 # SQL LIKE: % _
-r 'pattern'                 # Regex (if available)
```
