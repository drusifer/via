# VIA - Python Codebase Indexing and Query Tool

VIA is a command-line tool for indexing and searching Python codebases. It parses Python files using AST, extracts code entities (classes, methods, functions, imports, globals), and stores them in a SQLite database for fast pattern-based searching with multiple output formats.

## Features

- **Fast Indexing**: AST-based parsing of Python files with incremental updates
- **Pattern Matching**: Search using glob (`*`), SQL LIKE (`%`), or regex patterns
- **Multiple Output Formats**: List, table, raw source, or syntax-highlighted
- **Context Lines**: Show surrounding code with `-A`, `-B`, `-C` flags
- **Streaming Architecture**: O(1) memory usage for large result sets
- **Pipeline Syntax**: Chain match and render stages with `--via`

## Quick Start

```bash
# Install
git clone https://github.com/your-org/via.git && cd via
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Index and search
via index .
via -g '*' -c                    # All classes
via -g 'test_*' -f -n 5          # First 5 test functions
via -g '*Manager' -c --via -oT   # Manager classes as table
via -mg 'User' -tc -oF       # User class with syntax highlighting
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Complete usage examples and reference
- **[Architecture](agents/morpheus.docs/VIA_ARCHITECTURE.md)** - System design
- **[Sprint 3 Architecture](agents/morpheus.docs/SPRINT_3_ARCHITECTURE.md)** - Pipeline & renderer system

## Development

### Setup

```bash
git clone https://github.com/your-org/via.git
cd via
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=via --cov-report=html

# Run specific test file
pytest tests/unit/test_pipeline_parser.py -v

# Linting
make lint-fast    # Ruff only
make lint         # Ruff + Bandit
```

### Project Structure

```
via/
├── via/                    # Main package
│   ├── __main__.py         # CLI entry point
│   ├── core/               # Core types and records
│   │   ├── types.py        # SymbolType, MatchOp, MatchResult
│   │   ├── match_record.py # Polymorphic MatchRecord classes
│   │   └── discovery.py    # File discovery
│   ├── db/                 # Database layer
│   │   └── store.py        # SQLite operations
│   ├── parsers/            # AST parsing
│   │   └── python_parser.py
│   ├── pipeline/           # Pipeline system (Sprint 3)
│   │   ├── parser.py       # Argparse-based pipeline parser
│   │   ├── executor.py     # Stage execution
│   │   └── types.py        # StageType, PipelineStage
│   ├── renderers/          # Output renderers
│   │   ├── base.py         # Renderer ABC
│   │   ├── list.py         # ListRenderer
│   │   ├── table.py        # TableRenderer
│   │   ├── raw.py          # RawRenderer (source extraction)
│   │   ├── formatted.py    # FormattedRenderer (Pygments)
│   │   └── factory.py      # RendererFactory
│   └── services/           # Business logic
│       └── indexing.py     # Indexing service
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── acceptance/         # UAT tests
└── agents/                 # Bob System (AI agents)
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
│  (List, Table, Raw,       │       (SQLite + metadata)        │
│   Formatted, Diagram)     │                                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Streaming Architecture**: Renderers process Iterator[MatchRecord], not List
2. **Metadata-First**: Column widths computed before streaming for consistent tables
3. **Polymorphic Records**: Each symbol type has its own MatchRecord subclass
4. **Pipeline Syntax**: `via -m<X> PATTERN -t<Y> [-o<Z>] [-f<W>] [OPTIONS]`

### Running Specific Test Suites

```bash
# Pipeline tests
pytest tests/unit/test_pipeline_parser.py tests/unit/test_pipeline_executor.py -v

# Renderer tests
pytest tests/unit/test_renderers.py tests/unit/test_raw_renderer.py tests/unit/test_formatted_renderer.py -v

# Integration tests
pytest tests/integration/ -v

# UAT tests
pytest tests/acceptance/ -v
```

### Code Quality

```bash
# Check for issues
ruff check via/

# Auto-fix
ruff check via/ --fix

# Security scan
bandit -r via/ -ll
```

## Requirements

- Python 3.9+
- SQLite 3.x (included with Python)
- Pygments (for syntax highlighting)

## License

GPL-3.0

## Author

Drew Gutstein
