# Sprint 11 — End-to-End User Test Report

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Test method**: Live `via index` + `via -mg` queries on real JS/TS fixture files + DB inspection

---

## Test Scenarios

### Scenario 1: node_modules + dist exclusion (S11-5)

**Setup**: Created `/tmp/via_jstest/` with `src/` (3 files) + `node_modules/react/index.js` + `dist/built/app.js`

**Result**: `via index .` reports 3 files discovered — `node_modules/` and `dist/` both excluded. ✅

**Note 4 from Gate 1** (trailing slash `dist/`): CONFIRMED — `dist/` excluded as directory, not file glob. ✅

---

### Scenario 2: JS/TS file discovery (S11-1)

**Files**: `app.js`, `types.ts`, `Component.jsx`

**Result**: All 3 files indexed. `.jsx` included as JavaScript. `.ts` included as TypeScript. ✅

---

### Scenario 3: Symbol extraction (S11-2)

**Functions** (`via -mg '*' -tf`): `greet`, `fetchData`, `fetchUser`, `MyComponent` — all correct ✅

**Imports** (`via -mg '*' -ti`): `React`, `useState`, `useEffect`, `* as utils`, `Observable` — all correct ✅

**Globals** (`via -mg '*' -tg`): `API_URL`, `UserId` — correct ✅

**Classes** (`via -mg '*' -tc`): `UserService`, `User`, `ApiResponse`, `Status`, `UserRepository` — present ✅

**Language column**: `javascript` for `.js`/`.jsx`, `typescript` for `.ts`/`.tsx` ✅

---

## Defect: symbol_subtype NOT populated (BUG-S11-01)

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
# symbol_subtype='interface' populated in store phase via metadata
```
No such mechanism exists. This comment should be removed or replaced with the actual fix.

**Fix required**:
- Add `symbol_subtype: Optional[str] = None` to `ClassEntity` and `FunctionEntity` in `base.py`
- Set it in `javascript_parser.py` for interfaces (`'interface'`), enums (`'enum'`), arrow functions (`'arrow_function'`)
- Pass `symbol_subtype=cls.symbol_subtype` (or `fn.symbol_subtype`) in `indexing.py`
- Update table renderer to display `symbol_subtype` when set (if not already done)

---

## Summary

| Story | Test | Result |
|-------|------|--------|
| S11-5 | node_modules + dist excluded | ✅ PASS |
| S11-1 | JS/TS file discovery | ✅ PASS |
| S11-2 | Functions, classes, imports, globals extracted | ✅ PASS |
| S11-2 | `language` column populated | ✅ PASS |
| S11-2 (OQ-2) | `symbol_subtype` for interface/enum/arrow | ❌ BUG — NULL for all |

---

## Gate Decision

**HOLD** — Sprint 11 cannot launch until BUG-S11-01 is fixed.

`symbol_subtype` was a committed deliverable (arch OQ-2, resolving Smith Note 1). Shipping with
all subtypes NULL means users see `interface` and `enum` types as plain `class` — a regression
against the announced behaviour.

@Neo: Fix `ClassEntity`/`FunctionEntity` + `javascript_parser.py` + `indexing.py`. @Trin: retest after fix.
