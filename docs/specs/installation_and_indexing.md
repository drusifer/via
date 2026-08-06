# VIA Installation and Indexing Specification

TL;DR: Instructions for installing VIA, running basic index operations, tracking incremental changes, and using watch mode.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Indexing](#indexing)
- [Watch Mode](#watch-mode)

---

## Installation

VIA requires Python 3.10 or newer. MCP server mode uses the official
`mcp>=2.0` Python SDK.

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
| Dart / Flutter | `.dart` | classes, mixins, enums, extensions, constructors, methods, functions, directives, globals |
| Markdown | `.md`, `.markdown` | headers |

**Default excluded directories**: `node_modules/`, `dist/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `.turbo/`, `.dart_tool/`, `build/`, `android/.gradle/`, `ios/Pods/`, `__pycache__/`, `.git/`. Add more with `--exclude`.

### What Gets Indexed

| Symbol Type | Example | Description |
|-------------|---------|-------------|
| class | `class User:` / `class Server extends Base {}` | Class definitions (Python + JS/TS) |
| method | `def save(self):` / `render() {}` | Methods inside classes |
| function | `def main():` / `function main() {}` / `const fn = () => {}` | Top-level functions |
| import | `import json` / `import { X } from 'y'` | Import statements |
| global | `MAX_SIZE = 100` / `const PORT = 3000` | Module-level variables |
| header | `## Section` | Markdown headers |

### Dart And Flutter

Common Dart class lookup: `via -mg "*Screen" -tc --lang dart`.

```bash
via -mg "*" -tF --lang dart
via -mg "*Screen" -tc --lang dart
via -mg "build" -tm --lang dart -oR
via -mg "*" -tc --lang dart --via inherits-from -mg "StatefulWidget" -tc
```

Dart imports, exports, and parts are directive strings, not resolved package dependencies. VIA indexes Flutter source structure: explicit classes, mixins, enums, extensions, constructors, methods, `build` methods, and explicit inheritance names such as `StatelessWidget`, `StatefulWidget`, and `State<T>`. It does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.

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

---

## Watch Mode

Keep the index automatically up-to-date as you edit files.

```bash
via index . -w     # Index then watch — re-indexes on every save
```

VIA detects file changes using watchdog with a 1-second debounce. Changed files are re-indexed automatically; deleted files are fully removed (symbols and relationships). Press Ctrl-C to stop.

---
