Fast, pattern-based symbol search for Python codebases backed by SQLite.

TLDR:
    VIA indexes Python and Markdown files using AST parsing, stores symbols
    (classes, methods, functions, imports, globals, headers) in a local SQLite
    database, and exposes them through a composable pipeline CLI with glob, regex,
    and SQL LIKE matching. Supports multiple output formats (list, table, raw,
    syntax-highlighted, Mermaid diagram, JSON), relationship queries (inheritance,
    calls, imports, references), watch mode (auto re-index on change), and MCP
    server mode (`via mcp serve`) for AI agent integration via JSON-RPC 2.0.
    Run `via index .` to build the database, then query with `via -mg PATTERN -t<type>`.
    Consumed by developers and AI agents; depends on Python 3.9+, Pygments, watchdog, mcp.

# VIA - Python Codebase Indexing and Query Tool

VIA is a command-line tool for indexing and searching Python codebases. It parses Python and Markdown files, extracts code entities (classes, methods, functions, imports, globals, headers), and stores them in a SQLite database for fast pattern-based searching with multiple output formats.

## Features

- **Fast Indexing**: AST-based parsing of Python files with incremental updates
- **Pattern Matching**: Search using glob (`*`), SQL LIKE (`%`), or regex patterns
- **Multiple Output Formats**: List, table, raw source, or syntax-highlighted
- **Context Lines**: Show surrounding code with `-A`, `-B`, `-C` flags
- **Relationship Queries**: Inheritance, calls, imports, references
- **Watch Mode**: Auto re-index on file changes (`via index -w`)
- **Streaming Architecture**: O(1) memory usage for large result sets
- **Result Cap Warning**: Notifies when results hit `--limit` with total match count

## Quick Start

```bash
# Install
git clone https://github.com/your-org/via.git && cd via
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Index current directory
via index .

# Search
via -mg '*' -tc                        # All classes (default limit: 10)
via -mg '*' -tc -n 0                   # All classes (unlimited)
via -mg 'test_*' -tf -n 5             # First 5 test functions
via -mg '*Manager*' -tc -oT -n 0      # Manager classes as table
via -mg 'MyClass' -tc -oF             # Class source with syntax highlighting
```

## Usage

### Pipeline Syntax

```
via -m<X> PATTERN -t<Y> [OPTIONS] [-o<Z>] [-f<W>]
```

### Match Syntax Flags

| Flag | Description |
|------|-------------|
| `-mg`, `--match-glob` | Glob pattern (`*`, `?`) |
| `-mr`, `--match-regex` | Regex pattern |
| `-ms`, `--match-sql` | SQL LIKE pattern (`%`, `_`) |

### Symbol Type Flags

| Flag | Description |
|------|-------------|
| `-tc` | Classes |
| `-tf` | Functions |
| `-tm` | Methods |
| `-ti` | Imports |
| `-tg` | Globals |
| `-tF` | File paths |
| `-tN` | File names |
| `-tH` | Markdown headers |

### Output Flags

| Flag | Description |
|------|-------------|
| `-oL` | List format (default) |
| `-oT` | Table format |
| `-oD` | Mermaid diagram |
| `-oU` | Usage references |
| `-oR` | Raw source code |
| `-oF` | Syntax highlighted source |
| `-oJ` | JSON array (for AI agents / MCP) |

### Options

| Flag | Description |
|------|-------------|
| `-n N`, `--limit N` | Limit results (default: 10, use `-n 0` for all) |
| `-I` | Case-insensitive matching |
| `-Q` | Match against qualified name |

### Relationship Queries

`--via` flags query relationships between symbols:

| Flag | Description |
|------|-------------|
| `-Vinh` | Inheritance |
| `-Vca` | Function/method calls |
| `-Vimp` | Import relationships |
| `-Vr` | Symbol references |
| `--invert` | Invert relationship direction |

```bash
via -mg 'Base' -tc -Vinh -mg '*' -tc              # Who inherits from Base?
via -mg 'MyClass' -tc -Vinh -mg '*' -tc --invert  # What does MyClass inherit?
via -mg 'helper' -tf -Vca -mg '*' -tf             # Who calls helper()?
via -mg 'main' -tf -Vca -mg '*' -tf --invert      # What does main() call?
via -mg 'typing' -Vimp -mg '*' -tF                # Files importing typing
```

### Result Limit and Cap Warning

Results default to 10. When more matches exist than the limit, via prints a warning to stderr:

```
results 1-10 of 106 matches returned (--limit=10) use -n 0 for all results
```

Use `-n 0` for unlimited results:

```bash
via -mg '*.py' -tF -n 0        # All Python files
via -mg '*' -tc -oT -n 0       # All classes as table
```

### Watch Mode

```bash
via index . -w     # Index then watch for file changes, auto re-indexing
```

### MCP Mode (AI Agent Integration)

VIA can run as an MCP (Model Context Protocol) server, exposing the `via_query` tool to Claude Code and other MCP clients over JSON-RPC 2.0 via stdio.

```bash
# Register via as an MCP server in the current project
via install mcp

# Start the MCP server (watch mode always on)
via mcp serve

# Inspect the tool schema
via mcp schema

# Show registration status
via status mcp

# Remove registration
via uninstall mcp
```

The server auto-starts watch mode so the index is always current. Claude Code can then call `via_query` with CLI args:

```json
{"args": ["-mg", "*Parser*", "-tc"]}
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage examples and reference
- **[Architecture](agents/morpheus.docs/VIA_ARCHITECTURE.md)** - System design

## Development

### Setup

```bash
git clone https://github.com/your-org/via.git
cd via
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

All targets run through `make`. Do not invoke `pytest` directly — use `make test` so output is captured and build status is posted correctly.

```bash
make test              # Run full test suite
make test V=-vv        # Show failures/errors live
make test V=-vvv       # Show all output live
```

To run a specific test file or subset, pass pytest args via `ARGS=`:

```bash
# Check build/build.out for full output after any run
cat build/build.out
```

### Linting and Code Quality

```bash
make lint-fast     # Ruff only (fast)
make lint          # Ruff + Bandit
make lint-slow     # Full lint suite
make fix           # Auto-fix lint issues
make duplicates    # Detect duplicate code
make security      # Security scan
```

### Project Structure

```
via/
├── via/                    # Main package
│   ├── __main__.py         # CLI entry point
│   ├── core/               # Core types and utilities
│   │   ├── types.py        # SymbolType, MatchOp enums
│   │   ├── match_record.py # Polymorphic MatchRecord classes
│   │   ├── discovery.py    # File discovery with .gitignore support
│   │   └── flag_groups.py  # CLI flag definitions
│   ├── db/                 # Database layer
│   │   ├── store.py        # SQLite operations
│   │   └── schema.py       # Schema definitions
│   ├── parsers/            # File parsers
│   │   ├── python_parser.py  # AST-based Python parser
│   │   ├── markdown_parser.py
│   │   └── registry.py     # Parser registry
│   ├── pipeline/           # Pipeline system
│   │   ├── parser.py       # Argparse-based pipeline parser
│   │   ├── executor.py     # Stage execution + limit warning
│   │   └── types.py        # StageType, PipelineStage
│   ├── renderers/          # Output renderers
│   │   ├── list.py         # ListRenderer (default)
│   │   ├── table.py        # TableRenderer
│   │   ├── raw.py          # RawRenderer (source extraction)
│   │   ├── formatted.py    # FormattedRenderer (Pygments)
│   │   ├── diagram.py      # DiagramRenderer (Mermaid)
│   │   ├── json_renderer.py # JsonRenderer (-oJ, MCP)
│   │   └── factory.py      # RendererFactory
│   ├── mcp/                # MCP server (Sprint 7)
│   │   ├── server.py       # FastMCP stdio server
│   │   └── schema.py       # via_query tool schema builder
│   ├── commands/           # CLI command implementations
│   │   ├── index.py        # Index command
│   │   ├── stats.py        # Stats command
│   │   └── install.py      # Install/uninstall/status (MCP)
│   └── services/           # Business logic
│       ├── indexing.py     # Indexing service
│       └── watch.py        # Watch mode (watchdog)
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── acceptance/         # Sprint UAT tests
│   └── uat/                # UAT test projects
└── agents/                 # Bob Protocol (AI agents)
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI                                  │
│                    (__main__.py)                             │
├─────────────────────────────────────────────────────────────┤
│  Pipeline Parser          │       Pipeline Executor          │
│  (argparse stages)        │       (match → filter → render)  │
├─────────────────────────────────────────────────────────────┤
│  MatchRecord System                                          │
│  (ClassMatchRecord, MethodMatchRecord, FunctionMatchRecord,  │
│   FileMatchRecord, ImportMatchRecord, GlobalMatchRecord)     │
├─────────────────────────────────────────────────────────────┤
│  Renderers                │       Database Store             │
│  (List, Table, Raw,       │       (SQLite + WAL mode)        │
│   Formatted, Diagram,     │                                  │
│   JSON, Usage)            │  WatchService (watchdog)         │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (FastMCP / stdio JSON-RPC 2.0)                  │
│  via_query tool → PipelineExecutor → JsonRenderer           │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Streaming Architecture**: Renderers process `Iterator[MatchRecord]`, not `List`
2. **Metadata-First**: Column widths and total count computed before streaming
3. **Polymorphic Records**: Each symbol type has its own `MatchRecord` subclass
4. **Pipeline Syntax**: `via -m<X> PATTERN -t<Y> [-o<Z>] [-f<W>] [OPTIONS]`
5. **`--via` is for relationships**: Output flags (`-oT`, `-oL`, etc.) are standalone — do not prefix with `--via`

## Requirements

- Python 3.9+
- SQLite 3.x (included with Python)
- Pygments (for syntax highlighting)
- watchdog (for watch mode)
- mcp>=1.26 (for MCP server mode)

## License

GPL-3.0

## Author

Drew Gutstein
