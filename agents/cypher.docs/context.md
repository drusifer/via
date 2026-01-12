# Cypher Context - VIA Project

**Last Updated**: 2026-01-10 19:24:32

## Current Project
Via - Python codebase indexing and querying CLI tool

## Key Decisions Made

### Index Command Specification
- **Storage**: SQLite database at `.via/index.db`
- **No AST caching**: Parse on-demand using byte offsets
- **Universal file indexing**: Index ALL files (metadata), parse only `.py`, `.pyx`, `.pyi`, `.md`
- **Nested architecture**: Directory-scoped indexes with `.via/watch` signaling
- **Parallelization**: 1 worker per subfolder
- **Incremental by default**: Skip unchanged files unless `--force`
- **10MB parse limit**: Track oversized files separately
- **Multi-language ready**: Pluggable parsers (JS in Phase 2)

### Command Syntax Finalized
```bash
via index [-w] [-v|-vv|-vvv|-vvvv] [--force] [--exclude PATTERN] [<dir>]
```

## Next Commands (Future Sessions)
- `via query` - Querying the index
- `via render` - Rendering results
- `via filter` - Filtering results

## Blockers
None - spec is complete for Phase 1 index command

## Notes
- User wants query/render specs in next session
- Filter command after that
- Architecture needs to support future n-gram duplicate detection
