# Sprint 11 — JavaScript/TypeScript Parser Foundation

**Scrum Master**: Mouse
**Date**: 2026-03-22
**Theme**: JS/TS parser foundation — file discovery, default excludes, JavaScriptParser (tree-sitter)
**Points**: ~10pts | **Cycles**: 2

**Source**: `cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md` (S11-1, S11-5, S11-2)
**Architecture**: `morpheus.docs/JAVASCRIPT_SUPPORT_ARCHITECTURE.md`

---

## Cycle 1 — Quick Wins: Discovery + Excludes (2pts)

### Tasks

| ID | Story | Task | Owner | Status |
|----|-------|------|-------|--------|
| S11-5a | S11-5 | Add JS default excludes to `FileDiscovery.DEFAULT_EXCLUDES` (`node_modules/`, `dist/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `.turbo/`) — use trailing slash (dir-only) | Neo | [ ] |
| S11-5b | S11-5 | Unit test: `node_modules/` files not returned by `FileDiscovery.discover()` | Neo | [ ] |
| S11-1a | S11-1 | Register `JavaScriptParser` in global parser registry (`via/parsers/__init__.py`) — stub parser OK for Cycle 1 | Neo | [ ] |
| S11-1b | S11-1 | Integration test: `.ts` and `.jsx` files appear in `via -mf '*.ts'` after `via index` | Neo | [ ] |

**Cycle 1 exit criteria**: Trin UAT passes, Morpheus review passes → Cycle 2.

---

## Cycle 2 — JavaScriptParser + Schema Migrations (8pts)

### Phase 2a: Schema Migrations

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S11-2a | Add `symbol_subtype TEXT` nullable column to `symbols` via new migration version | Neo | [ ] |
| S11-2b | Add `language TEXT` column to `symbols` via same migration; backfill existing rows from `files.language` JOIN | Neo | [ ] |
| S11-2c | Add indexes: `idx_symbols_subtype`, `idx_symbols_language` | Neo | [ ] |
| S11-2d | Populate `language` on every symbol INSERT in `store.py` | Neo | [ ] |

### Phase 2b: `JavaScriptParser` Implementation

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S11-2e | Add tree-sitter deps to `pyproject.toml`: `tree-sitter>=0.23`, `tree-sitter-javascript>=0.23`, `tree-sitter-typescript>=0.23` | Neo | [ ] |
| S11-2f | Implement `JavaScriptParser` in `via/parsers/javascript_parser.py` — lazy per-process parser init, JS grammar | Neo | [ ] |
| S11-2g | Extend to TypeScript grammar in same class — detect by extension | Neo | [ ] |
| S11-2h | Extract: `FunctionEntity` (named functions + arrow consts, subtype='arrow_function') | Neo | [ ] |
| S11-2i | Extract: `ClassEntity` (classes + TS interfaces subtype='interface' + TS enums subtype='enum') | Neo | [ ] |
| S11-2j | Extract: `ImportEntity` (ES module imports, one per named specifier) | Neo | [ ] |
| S11-2k | Extract: `GlobalEntity` (module-level const/let/var that are not arrow functions) | Neo | [ ] |
| S11-2l | Partial parse on ERROR nodes: set `parse_error`, continue walking | Neo | [ ] |
| S11-2m | Respect 10MB size limit | Neo | [ ] |

### Phase 2c: Tests

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S11-2n | Unit tests: FunctionEntity extraction (`.js` named + arrow, `.ts` async) | Neo | [ ] |
| S11-2o | Unit tests: ClassEntity extraction (`class Foo extends Bar`, TS interface, TS enum) | Neo | [ ] |
| S11-2p | Unit tests: ImportEntity (`default`, `named {X,Y}`, `* as X`) | Neo | [ ] |
| S11-2q | Unit tests: GlobalEntity (module-level const/let/var, not arrow) | Neo | [ ] |
| S11-2r | Unit test: syntax error file → `parse_error` set, other symbols returned | Neo | [ ] |
| S11-2s | Integration test: `via index` on JS fixture dir → symbols queryable with `-tf`, `-tc`, `-ti` | Neo | [ ] |
| S11-2t | Integration test: schema migration runs on existing Python-only DB (no crash, backfill works) | Neo | [ ] |

**Cycle 2 exit criteria**: All tests pass, Trin UAT passes, Morpheus review passes → Sprint 11 complete.

---

## Sprint 11 Burndown

| Cycle | Points | Status |
|-------|--------|--------|
| Cycle 1: S11-5 + S11-1 | 2 | [ ] Pending |
| Cycle 2: S11-2 + schema | 8 | [ ] Pending Cycle 1 |
| **Total** | **10** | |

---

## Handoff Note

@Neo: Start Cycle 1. Read arch doc first: `morpheus.docs/JAVASCRIPT_SUPPORT_ARCHITECTURE.md`.
Key constraints:
- `DEFAULT_EXCLUDES` dirs use trailing slash (dir-only pattern)
- Stub parser acceptable for Cycle 1 (just needs `get_supported_extensions()` + auto-register)
- Full tree-sitter implementation is Cycle 2

@Trin: UAT criteria in each cycle's exit row above. Full fixture list TBD by Neo.
