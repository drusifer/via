# Web UI UX Review — 2026-03-23
**Reviewer:** Smith
**Screenshots:** tests/e2e/screenshots/ux-01 through ux-05

---

## P1 — Must Fix Before Launch

### UX-WEB-001: Grammar bug — "1 results"
**Screen:** ux-02-list-results
**Issue:** Result count reads "1 results (1ms)". Should be "1 result" (singular).
**Fix:** Pluralise the counter string: `${count} result${count === 1 ? '' : 's'}`.

### UX-WEB-002: Placeholder text looks like real values
**Screen:** ux-01-initial-load (FILTERS section)
**Issue:** "Newer than" shows `1h` and "Older than" shows `2d` as placeholder text. These look like real set values — a user will think temporal filters are already active. This is a silent correctness trap: they run a query expecting all symbols but unknowingly get a filtered set.
**Fix:** Change placeholders to something clearly non-value, e.g. `e.g. 1h, 2d` (which the label already says) — or just leave the input blank with no placeholder.

---

## P2 — Should Fix

### UX-WEB-003: Run Query button buried below fold
**Screen:** ux-01-initial-load, ux-02-list-results
**Issue:** The controls panel is tall. "Run Query" and "Reset" only appear at the very bottom, requiring the user to scroll down to run a query. On typical monitor heights this is the very last thing on the page. The primary action should always be reachable without scrolling.
**Fix:** Make the Run Query / Reset button row sticky at the bottom of the left panel, or move it to the top (below the Pattern field).

### UX-WEB-004: Full absolute paths — unreadable in results
**Screen:** ux-02-list-results, ux-03-table-format
**Issue:** File paths display as full absolute paths: `/home/drusifer/Projects/via/tests/e2e/fixture/example.py:4`. In real projects this will be 60–80 chars. Cards and table cells will overflow.
**Fix:** Display the path relative to the indexed root (which the server already knows). The status bar already shows the root dir — strip it from result paths.

### UX-WEB-005: Empty results panel — no call to action
**Screen:** ux-01-initial-load
**Issue:** The right panel just says "Results" with blank space underneath on first load. A new user has no indication they need to run a query.
**Fix:** Show a subtle hint in the empty state, e.g. "Enter a pattern and click Run Query." Could reuse the existing `#empty-state` element.

---

## P3 — Polish / Nice to Have

### UX-WEB-006: Diagram left-anchored in large canvas
**Screen:** ux-04-diagram-format
**Issue:** The Mermaid diagram renders top-left in a wide empty canvas. For small diagrams (2–3 nodes) this looks sparse and unfinished.
**Fix:** Center the diagram container or add `mermaid.initialize({ startOnLoad: false, theme: 'default' })` with a `diagramPadding` option. Alternatively wrap the diagram area with `display:flex; justify-content:center`.

### UX-WEB-007: Watch dot is very small
**Screen:** ux-01-initial-load (status bar)
**Issue:** The green watch dot in the top-left status bar is a tiny 6–8px circle. Easy to miss, especially for users who aren't looking for it.
**Fix:** Increase to 10–12px and add a subtle CSS pulse animation when actively watching — gives live feedback that the server is running.

### UX-WEB-008: Table column widths unbalanced
**Screen:** ux-03-table-format
**Issue:** File path column dominates the table width. Name and Type columns get squeezed.
**Fix:** Set `max-width` on the File column with `overflow: hidden; text-overflow: ellipsis`, and fix Name/Type to a minimum width.

---

## What's Working Well

- **Status bar** (ux-01): Clean, readable. Directory + file count + symbol count + time-ago all useful at a glance.
- **List result card** (ux-02): Badge colour, bold name, monospace path — clear visual hierarchy.
- **Diagram** (ux-04): Mermaid rendering works. Inheritance arrow and class boxes correct.
- **Error state** (ux-05): Red warning icon + message is immediately visible and clear.
- **Empty state** (no-match): "No results. Try broadening your pattern." — good helpful copy.
- **Output format toggle**: List/Table/Diagram buttons — clear active state highlighting.

---

## Priority Summary

| ID | Severity | Fix |
|----|----------|-----|
| UX-WEB-001 | P1 | Pluralise result count |
| UX-WEB-002 | P1 | Fix misleading placeholders on temporal filters |
| UX-WEB-003 | P2 | Sticky or elevated Run Query button |
| UX-WEB-004 | P2 | Relative file paths in results |
| UX-WEB-005 | P2 | Empty panel call-to-action |
| UX-WEB-006 | P3 | Centre diagram in canvas |
| UX-WEB-007 | P3 | Larger watch dot + pulse |
| UX-WEB-008 | P3 | Table column width balancing |
