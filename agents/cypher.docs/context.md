# Cypher Context - VIA Project

**Last Updated**: 2026-02-11 12:19:00

## Current Project
Via - Python codebase indexing and querying CLI tool

## Key Decisions Made

### Sprint 5 - LAUNCHED (2026-02-11)
- **STATUS**: SHIPPED
- 687 tests, 0 failures, 82% coverage, 25/25 UAT green
- All 4 relationship types: inheritance, calls, imports, references
- Docs condition cleared by Oracle (USER_GUIDE.md + --help updated)

### Index Command Specification
- **Storage**: SQLite database at `.via/index.db`
- **No AST caching**: Parse on-demand using byte offsets
- **Universal file indexing**: Index ALL files (metadata), parse only `.py`, `.pyx`, `.pyi`, `.md`
- **Nested architecture**: Directory-scoped indexes with `.via/watch` signaling
- **Incremental by default**: Skip unchanged files unless `--force`
- **10MB parse limit**: Track oversized files separately
- **Multi-language ready**: Pluggable parsers (JS in Phase 2)

### Command Syntax Finalized
```bash
via index [-w] [-v|-vv|-vvv|-vvvv] [--force] [--exclude PATTERN] [<dir>]
```

## Blockers
None - Sprint 5 complete, launch approved
