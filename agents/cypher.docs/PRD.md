# VIA — Master Product Requirements Document

**Version**: 2.0
**Author**: Cypher (PM)
**Last Updated**: 2026-05-06
**Status**: Living Document — updated each sprint

---

## Executive Summary

VIA is a fast, pattern-based symbol search and indexing tool for Python, JavaScript, and TypeScript codebases. It indexes Python, JS/TS, and Markdown files using AST parsing (tree-sitter for JS/TS), stores symbols in a local SQLite database, and exposes them through a composable pipeline CLI with glob, regex, and SQL LIKE matching.

**Primary users**: Developers and AI agents who need fast, precise code navigation without spinning up a language server.

**Core value proposition**:
- Sub-second symbol lookup by name, type, or relationship
- Composable pipeline syntax: `via -m<X> PATTERN -t<Y> [OPTIONS]`
- Relationship queries (inheritance, calls, imports, references, container membership)
- Lightweight: one SQLite file, no daemon, no server

---

## Design Principles

1. **Composable pipeline**: Match → filter → output stages chain naturally
2. **Streaming architecture**: O(1) memory — renderers process iterators, not lists
3. **Metadata-first**: column widths and totals computed before streaming
4. **Polymorphic records**: each symbol type has its own `MatchRecord` subclass
5. **CLI consistency**: all flags follow established shorthand conventions

---

## All User Stories by Sprint

### Sprint 1 — Core Indexing MVP ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S1-1 | Database schema setup (`.via/index.db`, tables, indexes) | 3 | ✅ |
| S1-2 | File discovery with `.gitignore` support | 5 | ✅ |
| S1-3 | Python AST parser (functions, classes, imports, globals, methods) | 8 | ✅ |
| S1-4 | Parser registry (pluggable `ParserABC` interface) | 3 | ✅ |
| S1-5 | Indexing service (orchestrate discovery → parse → store) | 5 | ✅ |
| S1-6 | Multiprocessing worker pool (CPU-bound AST parsing) | 5 | ✅ |
| S1-7 | CLI: `via index <dir>` with argparse | 3 | ✅ |
| S1-8 | Progress feedback (X/Y files, final summary) | 2 | ✅ |
| S1-9 | Incremental indexing (mtime check, `--force` flag) | 3 | ✅ |
| S1-10 | Auto-add `.via/` to `.gitignore` | 2 | ✅ |

**Total**: 39pts

---

### Sprint 2 — Pattern Matching & Query CLI ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S2-1 | Pattern matcher foundation (glob via `pathspec`, interface for future matchers) | 3 | ✅ |
| S2-2 | Query service layer (search symbols by name + type) | 5 | ✅ |
| S2-3 | CLI: pipeline syntax `via -mg PATTERN -t<Y>` | 3 | ✅ |
| S2-4 | Regex matcher (`-mr`) | 3 | ✅ |
| S2-5 | SQL LIKE matcher (`-ms`) | 2 | ✅ |
| S2-6 | Type flags (`-tc`, `-tf`, `-tm`, `-ti`, `-tg`) | 2 | ✅ |

**Key decisions** (from SPRINT_2_PRD.md):
- No default result limit; use `--limit N` / `-n N` (default 10 in later sprints)
- Syntax highlighting via pygments (must-have)
- No interactive pagination — pipe to `less`
- Multiple output formats via interface (JSON, CSV, table, etc.)
- Grep-style glob as default (`-mg`)
- Fully-qualified names for disambiguation

**Total**: 18pts

---

### Sprint 3 — Render Pipeline & Output Formats ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S3-1 | Render symbol source code (`-oR` raw, `-oF` formatted) | 3 | ✅ |
| S3-2 | Context line control (`-A`, `-B`, `-C` flags) | 3 | ✅ |
| S3-3 | List command / browse entities (streaming iterator) | 3 | ✅ |
| S3-4 | Stats command (`via stats`) | 2 | ✅ |
| S3-5 | Multiple output formats (`-oL` list, `-oT` table, `-oD` diagram, `-oU` usage) | 4 | ✅ |
| S3-6 | Internal pipeline architecture with `--via` flag | 3 | ✅ |

**Total**: 18pts

---

### Sprint 4 — Markdown Indexing ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S4-1 | Markdown parser (`-tH` headers indexed as symbols) | 3 | ✅ |
| S4-2 | Markdown integration with existing pipeline | 2 | ✅ |

**Total**: 5pts

---

### Sprint 5 — Relationship Queries ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S5-1 | Inheritance queries (`-Vinh` / `--via inherits-from`) | 3 | ✅ |
| S5-2 | Call queries (`-Vca` / `--via calls`) | 3 | ✅ |
| S5-3 | Import queries (`-Vimp` / `--via imports`) | 3 | ✅ |
| S5-4 | `--invert` flag (reverse relationship direction) | 1 | ✅ |
| S5-5 | Symbol reference tracking (`-Vr`) — class bases, decorators, annotations, body | 3 | ✅ |

**Total**: 13pts

---

### Sprint 6 — Watch Mode ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S6-1 | Basic watch mode (`via index -w`) — watchdog, auto re-index on change | 5 | ✅ |
| S6-2 | Watch mode feedback (startup/change/delete/stop messages) | 2 | ✅ |
| S6-3 | Globals type (`-tg`) symbol support | 2 | ✅ |
| S6-4 | Symbol cascade deletion fix (symbols removed when file deleted) | 2 | ✅ |
| S6-5 | SQLite thread safety (`check_same_thread=False`) | 1 | ✅ |

**Total**: 12pts

---

### Sprint 7 — MCP Server Mode ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S7-1 | MCP server (`via mcp serve`) — watch + JSON-RPC 2.0 + `via_query` tool | 5 | ✅ |
| S7-2 | Auto-config for Claude Code (`via install mcp` / `via uninstall mcp` / `via status mcp`) | 3 | ✅ |
| S7-3 | Tool schema inspection (`via mcp schema`) | 2 | ✅ |
| S7-4 | JSON output format (`-oJ`) for AI agent integration | 2 | ✅ |

**Total**: 12pts

---

### Sprint 8 — Line-Level Indexing ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S8-1 | Line number indexing (byte offsets stored per symbol) | 3 | ✅ |
| S8-2 | Line slice queries (`-mL` match type with slice syntax) | 3 | ✅ |

**Total**: 6pts

---

### Sprint 9 — Temporal Queries + Container Membership + `-Q` Path Matching ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S9-1 | `-Vhas` container membership (`file/class/function has member`) | 3 | ✅ |
| S9-2a | Temporal matcher — `--newerthan` / `--olderthan` with human-friendly durations (`1h`, `2d`, `1w`) | 3 | ✅ |
| S9-2b | Per-symbol `mtime` timestamps (watch mode updates per symbol, not per file) | 2 | ✅ |
| S9-3 | Expanded `-Vr` reference tracking (class bases, decorators, annotations, body) | 3 | ✅ |
| S9-4 | Fix class anchor bug for `-Vca` | 1 | ✅ |
| S9-5 | `-Q` full-path matching for `-tF` file queries | 1 | ✅ |
| S9-6 | `DECLARES` reference type (renamed from `HAS`, maps to `-Vhas`) | 1 | ✅ |
| S9-7 | Case-sensitivity docs + `-I` flag documentation | 1 | ✅ |

**Total**: 15pts

---

### Sprint 10 — `--ref-type` + `--stale` + Incremental `prep_tldr` + PathFilter ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S10-1 | `--ref-type <type>` alternative relationship specifier (inherits-from, calls, imports, references, declares) | 3 | ✅ |
| S10-2 | `--stale` cross-stage temporal filter (result.mtime < anchor.mtime) | 2 | ✅ |
| S10-3 | `prep_tldr.py` incremental mode (argparse, `--force`, `.via/prep_tldr_last_run`) | 2 | ✅ |
| TD-W1 | `PathFilter` extraction from `FileDiscovery` into `via/core/path_filter.py` | 1 | ✅ |

**Total**: 8pts

### Sprint 11 — JavaScript/TypeScript Parser Foundation ✅ SHIPPED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S11-1 | JS/TS file discovery (`.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.tsx`) | 1 | ✅ |
| S11-5 | `node_modules/`, `dist/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `.turbo/` default excludes | 1 | ✅ |
| S11-2 | `JavaScriptParser` via tree-sitter — functions, classes (with inheritance), imports, globals, TS interfaces/enums/type aliases | 8 | ✅ |

**Total**: 10pts | **Tests**: 1022 (+52 from Sprint 10) | **Schema**: v6 (language + symbol_subtype columns)

---

## Feature Summary (all shipped)

| Feature Area | Flags / Commands | Sprint |
|---|---|---|
| **Indexing** | `via index .`, `--force`, incremental mtime | 1 |
| **Multi-language** | Python, JavaScript (`.js`/`.jsx`/`.mjs`/`.cjs`), TypeScript (`.ts`/`.tsx`), Markdown | 11 |
| **Pattern matching** | `-mg`, `-mr`, `-ms`, `-I` (case-insensitive), `-Q` (full-path) | 2, 9 |
| **Symbol types** | `-tc`, `-tf`, `-tm`, `-ti`, `-tg`, `-tF`, `-tN`, `-tH` | 2, 4 |
| **Output formats** | `-oL`, `-oT`, `-oR`, `-oF`, `-oD`, `-oU`, `-oJ` | 3, 7 |
| **Context lines** | `-A`, `-B`, `-C` | 3 |
| **Result control** | `-n N` / `--limit N`, cap warning | 2 |
| **Relationships** | `-Vinh`, `-Vca`, `-Vimp`, `-Vr`, `-Vhas`, `--via <type>`, `--ref-type <type>`, `--invert` | 5, 8, 10 |
| **Temporal** | `--newerthan`, `--olderthan` (per-symbol mtime), `--stale` | 9, 10 |
| **Watch mode** | `via index -w` (watchdog, debounce 500ms) | 6 |
| **MCP server** | `via mcp serve`, `via install mcp`, `via mcp schema`, `-oJ` | 7 |

---

## Cumulative Test Count

| Sprint | Tests End | Delta |
|--------|-----------|-------|
| Sprint 1–5 | ~450 | — |
| Sprint 6 | 709 | +~260 |
| Sprint 7 | 794 | +85 |
| Sprint 8 | 837 | +43 |
| Sprint 9 | 908 | +71 |
| Sprint 10 | 968 | +60 |
| Sprint 11 | 1022 | +54 |

---

### Sprint 25 — Dart / Flutter Support 📝 PLANNED

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| S25-1 | Dart file discovery and `--lang dart` filtering | 2 | Draft |
| S25-2 | Dart parser foundation for classes, methods, functions, imports, globals | 5 | Draft |
| S25-3 | Flutter-aware query value for widgets and `build` methods | 2 | Draft |
| S25-4 | Dart relationships: declares, imports, inherits-from, calls | 3 | Draft |
| S25-5 | Flutter project hygiene and docs/MCP examples | 1 | Draft |

**Total**: 13pts | **Source**: `agents/cypher.docs/SPRINT_25_DART_FLUTTER_USER_STORIES.md`

---

## Open Questions / Future Backlog

- **Dart parser engine**: Morpheus to confirm a maintained Dart AST/tree-sitter parser dependency or choose another robust parsing strategy.
- **Boolean operators in queries**: `AND`, `OR`, `NOT` across pipeline stages
- **Cross-project queries**: multiple `.via/index.db` sources
- **Interactive TUI**: browsable results (deferred since Sprint 2)
- **Git integration**: `git blame`, history-aware queries
- **Language support beyond current scope**: Go, Rust, Java/Kotlin, Swift

---

## Source Documents

Per-sprint stories and architecture decisions:
- `agents/cypher.docs/SPRINT_1_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_2_USER_STORIES.md` + `SPRINT_2_PRD.md`
- `agents/cypher.docs/SPRINT_3_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_5_RELATIONSHIPS_SCOPE.md`
- `agents/cypher.docs/SPRINT_6_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_7_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_8_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_9_USER_STORIES.md`
- `agents/cypher.docs/SPRINT_10_USER_STORIES.md`
- `agents/morpheus.docs/SPRINT_10_ARCHITECTURE.md`
- `docs/USER_GUIDE.md` — end-user reference
- `README.md` — project overview
