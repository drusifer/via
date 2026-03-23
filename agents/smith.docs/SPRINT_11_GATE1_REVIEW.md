# Sprint 11 — Gate 1 User Story Review

**Reviewer**: Smith (Expert User)
**Date**: 2026-03-22
**Stories**: `agents/cypher.docs/JAVASCRIPT_SUPPORT_REQUIREMENTS.md`
**Verdict**: **APPROVED WITH NOTES**

---

## Overall Assessment

The scope is well-chosen. JS/TS is the obvious next language, the architecture fit is clean (ParserABC seam from Sprint 1), and the out-of-scope decisions are sensible (`.vue`/`.svelte`, CommonJS resolution, JSDoc). The stories are testable and the acceptance criteria are specific.

Three targeted notes that Morpheus must address in the architecture, or Cypher must amend before implementation begins.

---

## Story Verdicts

### S11-1: JS/TS File Discovery — APPROVED
Clean. Uses existing `parseable_extensions` mechanism. No UX concerns.

### S11-2: JavaScript/TypeScript AST Parser — APPROVED WITH NOTE

**Note 1 — `interface` as `class` type**: A user searching `via -mg '*' -tc` expecting only classes will get TypeScript interfaces in results. This is surprising unless filtered. Two options for Morpheus:
- Option A: Add a `-tc --subtype interface` filter flag (future, not now)
- Option B: `--help` text for `-tc` notes that TS interfaces are included
- **Minimum requirement**: `--help` for `-tc` must mention TS interfaces, or the type column output must show `interface` (not `class`) so users can distinguish. Lock this down in arch.

**No block** — this is a display/labeling concern, not a correctness problem. Just needs a decision.

### S11-3: JS/TS Relationship Extraction — APPROVED WITH NOTE

**Note 2 — `imports` relationship target**: AC2 says "from the file's module to the imported module name." Clarify whether the target of an `imports` relationship is a **string module path** (e.g. `'react'`, `'../utils'`) or a resolved symbol ID. If it's a string path (like Python's import handling), this is fine — but the user needs to know that `via -mg 'react' -ti -Vimp -mg '*' -tc` may not resolve to actual classes in the index if `react` isn't indexed. Add a note to the AC that targets are string module names (unresolved) and this is consistent with Python behavior.

**No block** — just needs AC clarification.

### S11-4: `--lang` Filter Flag — APPROVED WITH NOTE

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

### S11-5: `node_modules` / `.gitignore` Exclusion — APPROVED WITH NOTE

**Note 4 — `dist/` in defaults**: `dist/` is a Python packaging artifact directory (created by `python -m build`). Adding `dist/` to `DEFAULT_EXCLUDES` will hide Python source files in `dist/` for users who index a project root that contains a built distribution. This is a minor edge case but real for library maintainers.

**Recommendation**: Replace `dist` with `dist/` in the pattern (trailing slash = directory only) AND add a note to `--help` that `dist/` is excluded by default with `--exclude` override available.

**No block** — `.gitignore` typically handles `dist/` anyway; this is defense-in-depth. Just needs the trailing slash precision.

---

## Summary of Notes

| # | Story | Note | Block? |
|---|-------|------|--------|
| 1 | S11-2 | `interface` type visibility in `-tc` results — needs labeling decision | No |
| 2 | S11-3 | `imports` target is string module name (not resolved symbol) — clarify AC | No |
| 3 | S11-4 | `--lang js` must cover `.jsx`; `--lang ts` must cover `.tsx` — add extension table to AC2 | **Yes — S11-4 only** |
| 4 | S11-5 | `dist` → `dist/` (dir-only pattern); document in `--help` | No |

---

## Gate 1 Decision

**APPROVED** — sprint proceeds to Morpheus architecture.

Notes 1, 2, 4 are Morpheus/Neo concerns to resolve in arch + implementation.
Note 3 (S11-4 `--lang` extension mapping) must be fixed in the requirements before Neo implements that story. Cypher can amend inline or Morpheus can resolve in arch.
