# VIA - Agent Instructions

> This file provides context for AI coding agents (Codex, Cursor, Copilot, Gemini, Claude).

## Project Overview

VIA is a Python codebase indexing and query tool. It parses Python files, extracts code entities (classes, methods, functions, imports, globals), and stores them in SQLite for fast pattern-based searching.

## Tech Stack

- **Language**: Python 3.9+
- **Database**: SQLite
- **Parsing**: Python AST
- **CLI**: Click
- **Testing**: pytest

## Project Structure

```
via/
├── via/                    # Main package
│   ├── cli/                # CLI commands (index, match)
│   ├── db/                 # Database layer (SQLite)
│   ├── indexer/            # AST parsing and indexing
│   └── pipeline/           # Query pipeline (WIP)
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── agents/                 # Bob System multi-persona protocol
│   ├── CHAT.md             # Team communication log
│   ├── *.docs/             # Persona working directories
│   └── tools/              # Agent utilities
└── .via/                   # Index database (gitignored)
```

## Build & Test Commands

```bash
# Setup environment and install dependencies
make install

# Run all tests
make test

# Install + test (default target)
make

# Run specific test file
.venv/bin/pytest tests/unit/test_store.py -v

# Clean build artifacts
make clean
```

## Code Conventions

1. **Imports**: Use absolute imports (full package paths)
2. **Style**: PEP-8, enforced with pylint
3. **Types**: Use type hints throughout
4. **Docstrings**: Google style docstrings
5. **Tests**: Every feature needs tests; "if it's not tested, it doesn't exist"

## Key Files

| File | Purpose |
|------|---------|
| `via/cli/match.py` | Match command implementation |
| `via/cli/index.py` | Index command implementation |
| `via/db/store.py` | Database operations |
| `via/indexer/parser.py` | AST parsing |
| `via/db/models.py` | Data models |

## Working with This Codebase

### Adding a New Command
1. Create command in `via/cli/`
2. Register in `via/cli/__init__.py`
3. Add tests in `tests/unit/`

### Database Schema
- `files`: Indexed file metadata (path, mtime, hash)
- `symbols`: Code symbols (name, type, location, byte positions)

### Pattern Matching
Three modes supported:
- `-g` (glob): `*save*` matches any symbol containing "save"
- `-s` (SQL LIKE): `%save%` same as glob
- `-r` (regex): `^test_.*$` full regex support

## Bob System (Multi-Persona Protocol)

This project uses the Bob System for AI-assisted development. See `agents/bob.docs/BOB_SYSTEM_PROTOCOL.md`.

**Available Personas:**
- **Bob** - Prompt Engineering Expert
- **Neo** - Senior Software Engineer
- **Morpheus** - Tech Lead / Architect
- **Trin** - QA / Guardian
- **Oracle** - Knowledge Officer
- **Mouse** - Scrum Master
- **Cypher** - Product Manager

**Quick Start:**
```
*chat              # Activate multi-persona workflow
*help              # Show all commands
@Neo *swe impl X   # Request Neo implement something
@Trin *qa test     # Request Trin run tests
```
