TLDR: Fast, pattern-based symbol indexing and search for Python, JS, TS, Dart, Flutter, and Markdown codebases with a composable pipeline CLI and web UI.

# VIA - Multi-Language Codebase Indexing and Query Tool

VIA is a command-line tool for indexing and searching Python, JavaScript, TypeScript, Dart, Flutter, and Markdown codebases. It parses source files using AST parsing (Python's built-in `ast` module for Python, tree-sitter for JS/TS/Dart), extracts code entities (classes, methods, functions, imports, globals, headers), and stores them in a SQLite database for fast pattern-based searching with multiple output formats.

## Features

- **Multi-Language Indexing**: Python, JavaScript, TypeScript, Dart, Flutter, and Markdown — tree-sitter for JS/TS/Dart, built-in AST for Python
- **Fast Indexing**: AST-based parsing with incremental updates (only changed files re-indexed)
- **Pattern Matching**: Glob (`*`), SQL LIKE (`%`), or regex — case-sensitive by default, `-I` to ignore case
- **Multiple Output Formats**: List, table, raw source, syntax-highlighted, JSON, Mermaid diagram
- **Context Lines**: Show surrounding code with `-A`, `-B`, `-C` flags
- **Relationship Queries**: `--via <rel>` (positive), `--sans <rel>` (not-exists), `--not` (negate pattern) — inheritance, calls, imports, references, declares
- **Stale Detection**: `--stale` flag finds results older than their anchor (e.g. test files not updated since their classes changed)
- **Temporal Queries**: Filter by symbol age with `--newerthan` / `--olderthan` (e.g. `1h`, `2d`, `1w`)
- **Per-Symbol Timestamps**: Watch mode tracks mtime per symbol, not just per file
- **Full-Path Matching**: `-Q` flag enables path-based file queries (`via -mg 'via/core/*' -tF -Q`)
- **Watch Mode**: Auto re-index on file changes (`via index . -w`)
- **MCP Server**: Expose `via_query` to Claude Code and other MCP clients via JSON-RPC 2.0
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
via -mg '*Screen' -tc --lang dart     # Dart/Flutter screen classes
via -mg 'build' -tm --lang dart -oR   # Flutter build methods as raw source
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

Relationship queries use a two-stage pipeline: `<anchor> --via <rel> <result>`.

| Flag | Description |
|------|-------------|
| `--via inherits-from` / `-V inherits-from` | Find subclasses of anchor |
| `--via calls` / `-V calls` | Find callers of anchor |
| `--via imports` / `-V imports` | Find importers of anchor |
| `--via references` / `-V references` | Find referencers of anchor |
| `--via declares` / `-V declares` | Container membership (file/class has member) |
| `--sans <rel>` / `-S <rel>` | Negative: subjects with NO relationship to matching objects |
| `--not` | Negate the immediately following pattern flag |
| `--stale` | Filter results older than their anchor (cross-stage temporal filter) |

```bash
via -mg 'Base' -tc --via inherits-from -mg '*' -tc         # Who inherits from Base?
via -mg '*' -tc --sans inherits-from -mg '*' -tc           # Root classes (no parent)
via -mg 'helper' -tf --via calls -mg '*' -tf               # Who calls helper()?
via -mg 'typing' --via imports -mg '*' -tF                 # Files importing typing
via -mg '*' -tc --lang dart --via inherits-from -mg 'StatefulWidget' -tc  # Flutter widgets
```

For Dart/Flutter, VIA indexes source structure only. It can find Dart files, classes, methods, constructors, directives, explicit inheritance/mixin/interface names, and best-effort calls. It does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics.

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

# Start the MCP server (initial index, watch mode, and web UI in one process)
via mcp serve

# Inspect the tool schema
via mcp schema

# Show registration status
via status mcp

# Remove registration
via uninstall mcp
```

The server creates or refreshes the index on startup, auto-starts watch mode so the index stays current, and serves the web UI on `http://localhost:7891` by default. Claude Code can then call `via_query` with CLI args:

```json
{"args": ["-mg", "*Parser*", "-tc"]}
```

## Python API

`ViaQueryBuilder` and `ViaRunner` are the supported Python query-construction path. They preserve normal via semantics rather than introducing a separate query language.

```python
from via import ViaQueryBuilder, ViaRunner

query = (
    ViaQueryBuilder()
    .glob("*Controller")
    .classes()
    .contains("rate_limit")
    .limit(20)
    .build()
)

records = list(ViaRunner(db_store).run(query))
```

Relationship example:

```python
from via import ViaQueryBuilder, ViaRunner

query = (
    ViaQueryBuilder()
    .glob("Base")
    .classes()
    .via("inherits-from")
        .glob("*")
        .classes()
    .done()
    .build()
)

records = list(ViaRunner(db_store).run(query))
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage reference, web UI guide, and 20 real-world queries
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

## Sprint History

| Sprint | Theme | Tests | Key Features |
|--------|-------|-------|--------------|
| Sprint 1-4 | Core indexing + output formats | — | AST parsing, glob/regex/SQL matching, list/table/diagram/usage/raw/highlighted output |
| Sprint 5 | Relationship queries | — | Inheritance, calls, imports, references relationships |
| Sprint 6 | Incremental indexing + globals | — | Watch triggers, globals type, cascade deletion fix |
| Sprint 7 | MCP server mode | — | `via mcp serve`, JSON output (`-oJ`), MCP install/uninstall |
| Sprint 8 | Headers + container queries | — | `-tH` (markdown headers), container membership, references |
| Sprint 9 | Temporal + stale + `-Q` path matching | 908 | `--newerthan`/`--olderthan`, per-symbol mtime, `DECLARES`, `-Q`, case-sensitivity docs |
| Sprint 10 | `--stale` + incremental `prep_tldr` | 968 | `--stale` (cross-stage temporal filter), `prep_tldr` incremental mode, `PathFilter` extraction |
| Sprint 11–12 | Web UI + UX polish | — | `via web` SPA, JS/TS Vitest suite (74 tests), Playwright E2E (22 tests), UX fixes |
| **Sprint 13** | CLI relationship redesign | **1121** | `--via <rel>` / `--sans <rel>` / `--not` — unified relationship syntax |

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
