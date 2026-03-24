# JS Unit Test Plan — via Web UI
_Author: Trin | Date: 2026-03-23_

## Context

All Web UI JS lives inline in `via/web/template.py` as a single Python string.
No JS tooling exists. Zero JS unit test coverage.

## Test Pyramid Approach

```
        ▲  Playwright E2E (Trin — after Neo ships JS units)
       ▲▲▲  Integration: DOM interactions (Vitest + jsdom)
     ▲▲▲▲▲  Unit: Pure functions (Vitest — fast, no DOM needed)
```

---

## Step 1 — Extract JS from template.py

Extract the `<script type="module">` block from `via/web/template.py` into a
separate file: **`via/web/static/app.js`**

The template then loads it:
```html
<script type="module" src="/static/app.js"></script>
```

Add a `/static/<file>` route to `via/web/server.py` that serves files from
`via/web/static/`.

**Why:** You cannot import inline string JS in any test runner. Extraction is the
prerequisite for all JS testing.

---

## Step 2 — Export testable symbols

Add explicit exports at the bottom of `app.js` (only used by tests; tree-shaken
in prod):

```js
// test-only exports
export { esc, relTime, badgeClass, selectedChips, buildQueryBody,
         displayResults, renderList, renderTable, showLoading, showError };
```

For `buildQueryBody` — refactor `runQuery()` to extract the body-building logic
into a pure function that reads DOM values and returns a plain object. This makes
it testable without fetch.

---

## Step 3 — JS tooling (minimal package.json)

```json
{
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "jsdom": "^24.0.0",
    "@testing-library/jest-dom": "^6.0.0"
  }
}
```

`vitest.config.js`:
```js
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
```

Makefile target to add:
```makefile
test-js: ## Run JavaScript unit tests
    npm test
```

---

## Step 4 — Test file: `tests/js/app.test.js`

### Priority 1: Pure functions (no DOM — fast)

| Function | What to test |
|----------|-------------|
| `esc(s)` | `&`, `<`, `>` escaping; null/undefined input; numbers |
| `relTime(iso)` | "just now" (<5s), seconds, minutes, hours boundaries |
| `badgeClass(type)` | all 8 known types return correct class; unknown → 'badge-global' |

### Priority 2: DOM unit tests (jsdom)

| Function | What to test |
|----------|-------------|
| `showLoading()` | loading visible, result-list cleared, table/diagram hidden |
| `showError(msg)` | error-state visible with correct text, loading hidden |
| `renderList(results)` | correct number of result-cards; name/path/badge rendered; esc applied |
| `renderTable(results)` | table body has correct rows; sorting by column works (asc/desc toggle) |
| `buildQueryBody()` | reads all form fields correctly; rel fields only included when relationship set |
| `selectedChips(groupId)` | returns correct types for selected chips |
| Output format toggle | clicking Table/Diagram updates `outputFormat` and active class |
| Reset button | all fields back to defaults; chips deselected; outputFormat = 'list' |

### Priority 3: Async / fetch (mocked)

| Scenario | What to test |
|----------|-------------|
| `runQuery()` success | fetch called with correct body; `displayResults` called with response |
| `runQuery()` API error | `showError` called with error message |
| `updateStatus()` success | status bar fields updated; watch-dot class set correctly |
| Toast on reindex | toast shown when `last_reindex_count` increases |

Use `vi.stubGlobal('fetch', ...)` for fetch mocking — no external libs needed.

---

## Step 5 — Makefile integration

```makefile
test-all: test test-js  ## Run Python + JS tests
```

---

## Handoff to Playwright (Trin)

Once `make test-js` passes with coverage on all Priority 1 + 2 items, Trin
takes over for Playwright E2E:
- Full query flow (fill form → run → results displayed)
- Status bar updates
- Diagram rendering
- Reset flow
- Error states

---

## Files Neo needs to create/modify

| File | Action |
|------|--------|
| `via/web/static/app.js` | New — extracted JS |
| `via/web/template.py` | Modify — replace inline script with `<script src="/static/app.js">` |
| `via/web/server.py` | Modify — add `/static/` route |
| `package.json` | New |
| `vitest.config.js` | New |
| `tests/js/app.test.js` | New |
| `Makefile` | Add `test-js` target |
