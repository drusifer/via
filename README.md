# VIA - Python Codebase Indexing and Query Tool

VIA is a command-line tool for indexing and searching Python codebases. It parses your Python files, extracts code entities (classes, methods, functions, imports, globals), and stores them in a SQLite database for fast pattern-based searching.

## Features

- **Fast Indexing**: Indexes Python files with AST parsing, capturing classes, methods, functions, imports, and globals
- **Pattern Matching**: Search using glob patterns (`*`, `?`), SQL LIKE (`%`, `_`), or regex
- **Entity Type Filtering**: Filter by method, class, function, import, global, filename, or filepath
- **Incremental Updates**: Only re-indexes changed files (based on mtime)
- **Streaming Output**: Results stream to stdout for piping to `grep`, `less`, `wc`, etc.
- **Byte Positions**: Includes byte offset and length for editor integration

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/via.git
cd via

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .
```

## Quick Start

### 1. Index Your Codebase

```bash
# Index the current directory
via index

# Index a specific directory
via index /path/to/project

# Force re-index all files
via index --force
```

### 2. Search Your Code

```bash
# Find all methods ending with "save"
via match -t method -g "*save"

# Find classes named "User" (case-insensitive)
via match -t class -g "user" -I

# Find functions starting with "test_"
via match -t function -g "test_*"

# Find imports containing "json"
via match -t import -s "%json%"

# Limit results to 10
via match -t method -g "*" -n 10
```

## Commands

### `via index`

Index Python files in a directory tree.

```bash
via index [DIRECTORY] [OPTIONS]

Options:
  DIRECTORY          Directory to index (default: current directory)
  -w, --watch        Watch for file changes (NOT IMPLEMENTED YET)
  --force            Force re-index all files (ignore mtime)
  --exclude PATTERN  Additional patterns to exclude
  --db PATH          Custom database path
  -v, -vv, -vvv      Increase verbosity level
```

**Examples:**

```bash
via index                    # Index current directory
via index src/               # Index src/ directory
via index --force            # Re-index everything
via index -vv                # Verbose output
```

### `via match` (alias: `via m`)

Search indexed code using pattern matching.

```bash
via match PATTERN [OPTIONS]

Required:
  PATTERN            Pattern to match
  -t, --type TYPE    Symbol type to match

Options:
  -g, --glob         Use glob pattern matching (default)
  -r, --regex        Use regex pattern matching
  -s, --sql          Use SQL LIKE pattern matching
  -I, --case-insensitive  Case-insensitive matching
  -n, --limit N      Limit results to N matches
  -d, --directory    Directory containing the index
  --db PATH          Custom database path
```

**Symbol Types:**

| Type | Description | Example |
|------|-------------|---------|
| `method` | Class methods | `User.save()` |
| `class` | Classes | `class User` |
| `function` | Top-level functions | `def calculate()` |
| `import` | Import statements | `import json` |
| `global` | Global variables | `MAX_SIZE = 100` |
| `filename` | File names | `user.py` |
| `filepath` | Full file paths | `src/models/user.py` |

**Pattern Syntax:**

| Flag | Syntax | Wildcards | Example |
|------|--------|-----------|---------|
| `-g` (default) | Glob | `*` (any), `?` (single) | `*ToString`, `sav?` |
| `-s` | SQL LIKE | `%` (any), `_` (single) | `%save%`, `sav_` |
| `-r` | Regex | Full regex | `^test_.*$` |

## Output Format

Results are printed one per line in the format:

```
type:file_path:line_number:qualified_name:@byte_offset+byte_length
```

**Example Output:**

```
method:src/models/user.py:45:models.user.User.save:@1234+56
method:src/models/post.py:78:models.post.Post.save:@2345+48
function:src/utils/helpers.py:12:utils.helpers.calculate_hash:@456+120
```

For symbols without byte positions (filename, filepath):

```
filename:src/models/user.py:0:src/models/user.py
```

## Usage Examples

### Find Methods

```bash
# All methods
via match -t method -g "*"

# Methods ending with "ToString"
via match -t method -g "*ToString"

# Methods in a specific pattern
via match -t method -s "%init%"
```

### Find Classes

```bash
# All classes
via match -t class -g "*"

# Classes starting with "Base"
via match -t class -g "Base*"

# Case-insensitive search for "manager"
via match -t class -g "*manager*" -I
```

### Find Functions

```bash
# All test functions
via match -t function -g "test_*"

# Functions containing "calculate"
via match -t function -s "%calculate%"
```

### Find Imports

```bash
# All imports
via match -t import -g "*"

# Find json imports
via match -t import -g "json"

# Find typing imports
via match -t import -s "%typing%"
```

### Find Globals

```bash
# All globals
via match -t global -g "*"

# Find constants (UPPER_CASE pattern)
via match -t global -g "*_*"
```

### Pipeline Examples

```bash
# Count matching results
via match -t method -g "*" | wc -l

# Filter results with grep
via match -t function -g "*" | grep "test_"

# Browse results with less
via match -t class -g "*" | less

# Extract just file paths
via match -t method -g "*save*" | cut -d: -f2 | sort -u
```

## Configuration

### Database Location

By default, VIA stores its index in `.via/index.db` within the indexed directory:

```
project/
  .via/
    index.db
  src/
    ...
```

Use `--db` to specify a custom path:

```bash
via index --db /tmp/myproject.db
via match -t method -g "*" --db /tmp/myproject.db
```

### Ignored Files

VIA respects `.gitignore` files and automatically excludes:
- `__pycache__/` directories
- `*.pyc` files
- `.via/` directory
- Files over 10MB

## Requirements

- Python 3.9+
- SQLite 3.x (included with Python)

## Development

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=via

# Type checking
mypy via/
```

## License

GPL-3.0

## Author

Drew Gutstein
