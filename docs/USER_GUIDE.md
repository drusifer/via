# VIA User Guide

This guide provides detailed documentation for using VIA, a command-line tool for indexing and searching Python codebases.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Indexing Your Codebase](#indexing-your-codebase)
3. [Searching with Match](#searching-with-match)
4. [Pattern Matching Reference](#pattern-matching-reference)
5. [Symbol Types](#symbol-types)
6. [Output Format](#output-format)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/via.git
cd via

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# Windows: venv\Scripts\activate

# Install VIA
pip install -e .

# Verify installation
via --version
```

### Your First Search

```bash
# Navigate to your Python project
cd /path/to/your/project

# Index the codebase
via index

# Search for methods
via match -t method -g "*"
```

---

## Indexing Your Codebase

The `via index` command scans your Python files and builds a searchable database.

### Basic Usage

```bash
# Index current directory
via index

# Index a specific directory
via index /path/to/project

# Index with verbose output
via index -v
```

### Options

| Option | Description |
|--------|-------------|
| `DIRECTORY` | Directory to index (default: `.`) |
| `--force` | Re-index all files, ignoring mtime |
| `--exclude PATTERN` | Exclude files matching pattern |
| `--db PATH` | Custom database path |
| `-v`, `-vv`, `-vvv`, `-vvvv` | Increase verbosity |

### What Gets Indexed

VIA parses Python files and extracts:

| Entity | Description | Example |
|--------|-------------|---------|
| **Classes** | Class definitions | `class User:` |
| **Methods** | Class methods | `def save(self):` |
| **Functions** | Top-level functions | `def calculate():` |
| **Imports** | Import statements | `import json` |
| **Globals** | Module-level variables | `MAX_SIZE = 100` |

### Incremental Indexing

By default, VIA only re-indexes files that have changed since the last index:

```bash
# First index - processes all files
via index
# Output: Files indexed: 50

# Second index - only changed files
via index
# Output: Files indexed: 2, Files skipped: 48

# Force full re-index
via index --force
# Output: Files indexed: 50
```

### Ignored Files

VIA automatically excludes:
- Files/directories in `.gitignore`
- `__pycache__/` directories
- `*.pyc` files
- `.via/` directory
- Files larger than 10MB

---

## Searching with Match

The `via match` command searches your indexed codebase using pattern matching.

### Basic Syntax

```bash
via match PATTERN -t TYPE [OPTIONS]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `PATTERN` | The pattern to search for |
| `-t`, `--type` | Symbol type to match |

### Examples

```bash
# Find all save methods
via match -t method -g "*save*"

# Find User class
via match -t class -g "User"

# Find test functions
via match -t function -g "test_*"

# Find json imports
via match -t import -g "json"

# Find constants
via match -t global -g "MAX_*"
```

### Match Options

| Option | Description |
|--------|-------------|
| `-g`, `--glob` | Glob pattern (default) |
| `-s`, `--sql` | SQL LIKE pattern |
| `-r`, `--regex` | Regular expression |
| `-I`, `--case-insensitive` | Ignore case |
| `-n`, `--limit N` | Limit results |
| `-d`, `--directory` | Directory with index |

---

## Pattern Matching Reference

### Glob Patterns (`-g`, default)

Glob patterns use shell-style wildcards:

| Wildcard | Meaning | Example | Matches |
|----------|---------|---------|---------|
| `*` | Any characters | `*save*` | `save`, `auto_save`, `save_all` |
| `?` | Single character | `sav?` | `save`, `savx` |
| `[abc]` | Character set | `[gs]et` | `get`, `set` |

**Examples:**

```bash
# Suffix matching
via match -t method -g "*ToString"

# Prefix matching
via match -t function -g "get_*"

# Contains
via match -t class -g "*Manager*"

# Single character
via match -t method -g "sav?"
```

### SQL LIKE Patterns (`-s`)

SQL LIKE patterns use database wildcards:

| Wildcard | Meaning | Example | Matches |
|----------|---------|---------|---------|
| `%` | Any characters | `%save%` | `save`, `auto_save` |
| `_` | Single character | `sav_` | `save`, `savx` |

**Examples:**

```bash
# Contains "user"
via match -t class -s "%user%"

# Starts with "get"
via match -t method -s "get%"

# Exactly 4 chars starting with "sav"
via match -t method -s "sav_"
```

### Regular Expressions (`-r`)

Full Python regex support (requires SQLite REGEXP extension):

```bash
# Methods starting with underscore
via match -t method -r "^_[^_].*"

# Test methods
via match -t function -r "^test_.*"

# Magic methods
via match -t method -r "^__.*__$"
```

> **Note:** Regex requires SQLite REGEXP extension which may not be available on all systems.

---

## Symbol Types

### method

Class methods - functions defined inside a class.

```bash
# Find all methods
via match -t method -g "*"

# Find save methods
via match -t method -g "*save*"

# Find __init__ methods
via match -t method -g "__init__"
```

### class

Class definitions.

```bash
# Find all classes
via match -t class -g "*"

# Find Manager classes
via match -t class -g "*Manager"

# Case-insensitive search
via match -t class -g "user" -I
```

### function

Top-level functions (not inside a class).

```bash
# Find all functions
via match -t function -g "*"

# Find test functions
via match -t function -g "test_*"

# Find helper functions
via match -t function -s "%helper%"
```

### import

Import statements.

```bash
# Find all imports
via match -t import -g "*"

# Find typing imports
via match -t import -s "%typing%"

# Find json import
via match -t import -g "json"
```

### global

Module-level variable assignments.

```bash
# Find all globals
via match -t global -g "*"

# Find constants (UPPER_CASE)
via match -t global -g "*_*"

# Find DEBUG flags
via match -t global -g "DEBUG*"
```

### filename

File names (basename only).

```bash
# Find all .py files
via match -t filename -g "*.py"

# Find test files
via match -t filename -g "test_*"
```

### filepath

Full relative file paths.

```bash
# Find files in models/
via match -t filepath -g "*/models/*"

# Find files in tests/
via match -t filepath -s "%tests%"
```

---

## Output Format

### Standard Format

Each result is printed on one line:

```
type:file_path:line_number:qualified_name:@byte_offset+byte_length
```

**Fields:**

| Field | Description |
|-------|-------------|
| `type` | Symbol type (method, class, etc.) |
| `file_path` | Path to the file |
| `line_number` | Starting line number |
| `qualified_name` | Fully qualified name |
| `byte_offset` | Byte position in file |
| `byte_length` | Length in bytes |

**Example:**

```
method:src/models/user.py:45:models.user.User.save:@1234+56
```

### Parsing Output

Extract specific fields using standard Unix tools:

```bash
# Get just file paths
via match -t method -g "*save*" | cut -d: -f2

# Get unique files
via match -t method -g "*" | cut -d: -f2 | sort -u

# Get line numbers
via match -t function -g "test_*" | cut -d: -f3

# Get qualified names
via match -t class -g "*" | cut -d: -f4
```

---

## Advanced Usage

### Pipeline Integration

VIA output is designed for Unix pipelines:

```bash
# Count methods
via match -t method -g "*" | wc -l

# Filter with grep
via match -t function -g "*" | grep "test_"

# Browse with less
via match -t class -g "*" | less

# Find unique files with matching methods
via match -t method -g "*save*" | cut -d: -f2 | sort -u
```

### Multiple Searches

Combine multiple searches:

```bash
# Find both save and delete methods
via match -t method -g "*save*"
via match -t method -g "*delete*"

# Or use grep
via match -t method -g "*" | grep -E "(save|delete)"
```

### Custom Database Location

```bash
# Store index in custom location
via index --db /tmp/myproject.db

# Search custom database
via match -t method -g "*" --db /tmp/myproject.db
```

### Searching Different Directories

```bash
# Index one directory
via index /path/to/project

# Search from anywhere
via match -t method -g "*" -d /path/to/project
```

---

## Troubleshooting

### "Database not found"

The index database doesn't exist. Run `via index` first:

```bash
$ via match -t method -g "*"
Error: Database not found: .via/index.db
Run 'via index' first to create the index.

$ via index
$ via match -t method -g "*"
# Now works
```

### "Directory does not exist"

The specified directory doesn't exist:

```bash
$ via match -t method -g "*" -d /nonexistent
Error: Directory does not exist: /nonexistent

$ via match -t method -g "*" -d /path/to/actual/project
# Use correct path
```

### No Results

If no results are returned:

1. **Check the pattern**: Try a broader pattern like `*`
2. **Check case sensitivity**: Add `-I` for case-insensitive
3. **Check symbol type**: Try a different `-t` type
4. **Re-index**: Run `via index --force`

```bash
# Broad search to verify data exists
via match -t method -g "*" -n 5

# Case-insensitive
via match -t class -g "user" -I
```

### Regex Not Working

SQLite REGEXP requires an extension that may not be installed:

```bash
$ via match -t method -r "^test_.*"
Error: no such function: REGEXP

# Use glob instead
$ via match -t method -g "test_*"
```

### Slow Indexing

For large codebases:

1. Use incremental indexing (default)
2. Exclude unnecessary directories with `--exclude`
3. Add patterns to `.gitignore`

```bash
# Exclude generated directories
via index --exclude "build/*" --exclude "dist/*"
```

---

## Quick Reference

### Index Commands

```bash
via index                  # Index current directory
via index /path            # Index specific directory
via index --force          # Force full re-index
via index -vvv             # Very verbose output
```

### Match Commands

```bash
via match PATTERN -t TYPE  # Basic search
via match -t method -g "*" # All methods
via match -t class -g "User" -I  # Case-insensitive
via match -t function -g "test_*" -n 10  # Limit results
```

### Pattern Types

```bash
-g  # Glob (default): *, ?
-s  # SQL LIKE: %, _
-r  # Regex (if available)
```

### Symbol Types

```bash
-t method    # Class methods
-t class     # Classes
-t function  # Functions
-t import    # Imports
-t global    # Globals
-t filename  # File names
-t filepath  # File paths
```
