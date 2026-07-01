# Sprint 11 Consolidated Documentation

This document consolidates all documentation for Sprint 11.

## Table of Contents

- [SPRINT_11_GATE1_REVIEW.md](#sprint-11-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_11_GATE1_REVIEW.md`)

- [SPRINT_11_USER_TEST.md](#sprint-11-user-testmd) (originally `agents/smith.docs/SPRINT_11_USER_TEST.md`)

- [SPRINT_11_TASKS.md](#sprint-11-tasksmd) (originally `agents/mouse.docs/SPRINT_11_TASKS.md`)


---


## SPRINT_11_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_11_GATE1_REVIEW.md`


## Sprint 11 — Gate 1 User Story Review

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Stories**: `agents/cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md`
**Verdict**: **APPROVED WITH NOTES**

---

### Overall Assessment

The scope is well-chosen. JS/TS is the obvious next language, the architecture fit is clean (ParserABC seam from Sprint 1), and the out-of-scope decisions are sensible (`.vue`/`.svelte`, CommonJS resolution, JSDoc). The stories are testable and the acceptance criteria are specific.

Three targeted notes that Morpheus must address in the architecture, or Cypher must amend before implementation begins.

---

### Story Verdicts

#### S11-1: JS/TS File Discovery — APPROVED
Clean. Uses existing `parseable_extensions` mechanism. No UX concerns.

#### S11-2: JavaScript/TypeScript AST Parser — APPROVED WITH NOTE

**Note 1 — `interface` as `class` type**: A user searching `via -mg '*' -tc` expecting only classes will get TypeScript interfaces in results. This is surprising unless filtered. Two options for Morpheus:
- Option A: Add a `-tc --subtype interface` filter flag (future, not now)
- Option B: `--help` text for `-tc` notes that TS interfaces are included
- **Minimum requirement**: `--help` for `-tc` must mention TS interfaces, or the type column output must show `interface` (not `class`) so users can distinguish. Lock this down in arch.

**No block** — this is a display/labeling concern, not a correctness problem. Just needs a decision.

#### S11-3: JS/TS Relationship Extraction — APPROVED WITH NOTE

**Note 2 — `imports` relationship target**: AC2 says "from the file's module to the imported module name." Clarify whether the target of an `imports` relationship is a **string module path** (e.g. `'react'`, `'../utils'`) or a resolved symbol ID. If it's a string path (like Python's import handling), this is fine — but the user needs to know that `via -mg 'react' -ti -Vimp -mg '*' -tc` may not resolve to actual classes in the index if `react` isn't indexed. Add a note to the AC that targets are string module names (unresolved) and this is consistent with Python behavior.

**No block** — just needs AC clarification.

#### S11-4: `--lang` Filter Flag — APPROVED WITH NOTE

**Note 3 — JSX/TSX extension mapping**: AC2 lists values as `py`, `js`, `ts`, `md` but does not state what extensions each covers. A user will expect:
- `--lang js` → matches `.js`, `.mjs`, `.cjs`, **and `.jsx`**
- `--lang ts` → matches `.ts` **and `.tsx`**

If `--lang js` silently excludes `.jsx` files, users will be confused when React component files don't show up. This must be explicit in AC2 — add the extension mapping table:

| `--lang` value | Extensions matched |
|----------------|-------------------|
| `py` | `.py`, `.pyx`, `.pyi` |
| `js` | `.js`, `.mjs`, `.cjs`, `.jsx` |
| `ts` | `.ts`, `.tsx` |
| `md` | `.md`, `.markdown` |

**This is a blocker on S11-4 only** — AC2 must be updated before Neo implements `--lang`.

#### S11-5: `node_modules` / `.gitignore` Exclusion — APPROVED WITH NOTE

**Note 4 — `dist/` in defaults**: `dist/` is a Python packaging artifact directory (created by `python -m build`). Adding `dist/` to `DEFAULT_EXCLUDES` will hide Python source files in `dist/` for users who index a project root that contains a built distribution. This is a minor edge case but real for library maintainers.

**Recommendation**: Replace `dist` with `dist/` in the pattern (trailing slash = directory only) AND add a note to `--help` that `dist/` is excluded by default with `--exclude` override available.

**No block** — `.gitignore` typically handles `dist/` anyway; this is defense-in-depth. Just needs the trailing slash precision.

---

### Summary of Notes

| # | Story | Note | Block? |
|---|-------|------|--------|
| 1 | S11-2 | `interface` type visibility in `-tc` results — needs labeling decision | No |
| 2 | S11-3 | `imports` target is string module name (not resolved symbol) — clarify AC | No |
| 3 | S11-4 | `--lang js` must cover `.jsx`; `--lang ts` must cover `.tsx` — add extension table to AC2 | **Yes — S11-4 only** |
| 4 | S11-5 | `dist` → `dist/` (dir-only pattern); document in `--help` | No |

---

### Gate 1 Decision

**APPROVED** — sprint proceeds to Morpheus architecture.

Notes 1, 2, 4 are Morpheus/Neo concerns to resolve in arch + implementation.
Note 3 (S11-4 `--lang` extension mapping) must be fixed in the requirements before Neo implements that story. Cypher can amend inline or Morpheus can resolve in arch.


---


## SPRINT_11_USER_TEST.md

**Original Location**: `agents/smith.docs/SPRINT_11_USER_TEST.md`


## Sprint 11 — End-to-End User Test Report

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Test method**: Live `via index` + `via -mg` queries on real JS/TS fixture files + DB inspection

---

### Test Scenarios

#### Scenario 1: node_modules + dist exclusion (S11-5)

**Setup**: Created `/tmp/via_jstest/` with `src/` (3 files) + `node_modules/react/index.js` + `dist/built/app.js`

**Result**: `via index .` reports 3 files discovered — `node_modules/` and `dist/` both excluded. ✅

**Note 4 from Gate 1** (trailing slash `dist/`): CONFIRMED — `dist/` excluded as directory, not file glob. ✅

---

#### Scenario 2: JS/TS file discovery (S11-1)

**Files**: `app.js`, `types.ts`, `Component.jsx`

**Result**: All 3 files indexed. `.jsx` included as JavaScript. `.ts` included as TypeScript. ✅

---

#### Scenario 3: Symbol extraction (S11-2)

**Functions** (`via -mg '*' -tf`): `greet`, `fetchData`, `fetchUser`, `MyComponent` — all correct ✅

**Imports** (`via -mg '*' -ti`): `React`, `useState`, `useEffect`, `* as utils`, `Observable` — all correct ✅

**Globals** (`via -mg '*' -tg`): `API_URL`, `UserId` — correct ✅

**Classes** (`via -mg '*' -tc`): `UserService`, `User`, `ApiResponse`, `Status`, `UserRepository` — present ✅

**Language column**: `javascript` for `.js`/`.jsx`, `typescript` for `.ts`/`.tsx` ✅

---

### Defect: symbol_subtype NOT populated (BUG-S11-01)

**Severity**: Medium — UX regression vs. arch spec

**Description**: TypeScript interfaces (`User`, `ApiResponse`) and enums (`Status`) all show TYPE=`class`
in query output. Arrow functions (`MyComponent`) show no subtype either.

**Expected** (from arch doc OQ-2): TYPE column should show `interface`, `enum`, `arrow_function`
when `symbol_subtype` is set.

**Actual**: `symbol_subtype` is NULL for ALL symbols in the DB.

**Root cause** (two missing pieces):
1. `ClassEntity` and `FunctionEntity` in `via/parsers/base.py` have no `symbol_subtype` field
   — the parser cannot carry this information.
2. `indexing.py:_store_class_symbols()` (line 370) never passes `symbol_subtype` to `insert_symbol()`.

**Dead comment in `javascript_parser.py`** (interface_declaration handler):
```python
## symbol_subtype='interface' populated in store phase via metadata
```
No such mechanism exists. This comment should be removed or replaced with the actual fix.

**Fix required**:
- Add `symbol_subtype: Optional[str] = None` to `ClassEntity` and `FunctionEntity` in `base.py`
- Set it in `javascript_parser.py` for interfaces (`'interface'`), enums (`'enum'`), arrow functions (`'arrow_function'`)
- Pass `symbol_subtype=cls.symbol_subtype` (or `fn.symbol_subtype`) in `indexing.py`
- Update table renderer to display `symbol_subtype` when set (if not already done)

---

### Summary

| Story | Test | Result |
|-------|------|--------|
| S11-5 | node_modules + dist excluded | ✅ PASS |
| S11-1 | JS/TS file discovery | ✅ PASS |
| S11-2 | Functions, classes, imports, globals extracted | ✅ PASS |
| S11-2 | `language` column populated | ✅ PASS |
| S11-2 (OQ-2) | `symbol_subtype` for interface/enum/arrow | ❌ BUG — NULL for all |

---

### Gate Decision

**HOLD** — Sprint 11 cannot launch until BUG-S11-01 is fixed.

`symbol_subtype` was a committed deliverable (arch OQ-2, resolving Smith Note 1). Shipping with
all subtypes NULL means users see `interface` and `enum` types as plain `class` — a regression
against the announced behaviour.

@Neo: Fix `ClassEntity`/`FunctionEntity` + `javascript_parser.py` + `indexing.py`. @Trin: retest after fix.


---


## SPRINT_11_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_11_TASKS.md`


## Sprint 11 — JavaScript/TypeScript Parser Foundation

**Scrum Master**: Mouse
**Date**: 2026-03-22
**Theme**: JS/TS parser foundation — file discovery, default excludes, JavaScriptParser (tree-sitter)
**Points**: ~10pts | **Cycles**: 2

**Source**: `cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md` (S11-1, S11-5, S11-2)
**Architecture**: `morpheus.docs/JAVASCRIPT_SUPPORT_ARCHITECTURE.md`

---

### Cycle 1 — Quick Wins: Discovery + Excludes (2pts)

#### Tasks

| ID | Story | Task | Owner | Status |
|----|-------|------|-------|--------|
| S11-5a | S11-5 | Add JS default excludes to `FileDiscovery.DEFAULT_EXCLUDES` (`node_modules/`, `dist/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `.turbo/`) — use trailing slash (dir-only) | Neo | [ ] |
| S11-5b | S11-5 | Unit test: `node_modules/` files not returned by `FileDiscovery.discover()` | Neo | [ ] |
| S11-1a | S11-1 | Register `JavaScriptParser` in global parser registry (`via/parsers/__init__.py`) — stub parser OK for Cycle 1 | Neo | [ ] |
| S11-1b | S11-1 | Integration test: `.ts` and `.jsx` files appear in `via -mf '*.ts'` after `via index` | Neo | [ ] |

**Cycle 1 exit criteria**: Trin UAT passes, Morpheus review passes → Cycle 2.

---

### Cycle 2 — JavaScriptParser + Schema Migrations (8pts)

#### Phase 2a: Schema Migrations

| ID | Task | Owner | Status |
|----|------|-------|--------|
| S11-2a | Add `symbol_subtype TEXT` nullable column to `symbols` via new migration version | Neo | [ ] |
| S11-2b | Add `language TEXT` column to `symbols` via same migration; backfill existing rows from `files.language` JOIN | Neo | [ ] |
| S11-2c | Add indexes: `idx_symbols_subtype`, `idx_symbols_language` | Neo | [ ] |
| S11-2d | Populate `language` on every symbol INSERT in `store.py` | Neo | [ ] |

#### Phase 2b: `JavaScriptParser` Implementation

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

#### Phase 2c: Tests

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

### Sprint 11 Burndown

| Cycle | Points | Status |
|-------|--------|--------|
| Cycle 1: S11-5 + S11-1 | 2 | [ ] Pending |
| Cycle 2: S11-2 + schema | 8 | [ ] Pending Cycle 1 |
| **Total** | **10** | |

---

### Handoff Note

@Neo: Start Cycle 1. Read arch doc first: `morpheus.docs/JAVASCRIPT_SUPPORT_ARCHITECTURE.md`.
Key constraints:
- `DEFAULT_EXCLUDES` dirs use trailing slash (dir-only pattern)
- Stub parser acceptable for Cycle 1 (just needs `get_supported_extensions()` + auto-register)
- Full tree-sitter implementation is Cycle 2

@Trin: UAT criteria in each cycle's exit row above. Full fixture list TBD by Neo.


---
