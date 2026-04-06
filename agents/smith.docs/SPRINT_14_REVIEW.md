# Sprint 14 Stories — Smith User Review
**Date**: 2026-04-05
**Reviewer**: Smith (HCI Expert)
**Verdict**: APPROVED with 3 notes

---

## Testing Performed

- Confirmed `--lang` and `--subtype` do not exist: `Error: Invalid match stage arguments`
- Confirmed JS/TS files ARE indexed (7 `.js` files, 5+ `.ts` files in index)
- Confirmed JS/TS files have ZERO relationship records (`--via declares`, `--via imports` return nothing for JS files)
- Confirmed USER_GUIDE.md bugs at lines 143, 219, 732 are present

---

## Story Verdicts

### S14-1: JS/TS Relationship Extraction — PASS
- **Heuristic #4 (Consistency)**: Python has relationships, JS/TS doesn't. Users will query `app.js --via imports` and get silence — confusing gap. Filling this is essential for consistency.
- ACs are specific, testable, and correctly scoped to within-file calls only.

### S14-2: `--lang` Filter Flag — PASS with Note
- Flag position (after match stage, like `--newerthan`) is correct UX.
- ACs accept both `py`/`python`, `js`/`javascript`, etc. — good for learnability.
- **Note**: The error message example in the ACs says `"Valid: py, js, ts, md"` but the ACs also accept full names (`python`, `javascript`, `typescript`, `markdown`). Error message should list all accepted forms to prevent confusion:
  ```
  Error: Unknown --lang 'go'. Valid: py/python, js/javascript, ts/typescript, md/markdown.
  ```

### S14-3: `--subtype` Filter Flag — PASS with Note
- **Heuristic #9 (Error Recovery)**: The AC says "unknown values silently return no results." This is an anti-pattern — users who typo `--subtype interfaze` will see 0 results with no feedback.
- **Recommendation**: Keep the open-ended acceptance (no hardcoded list), but add a `--help` note: *"--subtype is case-sensitive; unknown values return no results."* This sets user expectations without requiring us to enumerate all possible subtypes.
- Combinability with `--lang` (AC #4) is the right call — `--lang ts --subtype interface` is a natural query.

### S14-4: Web UI Relationship Card UX — PASS with Clarification
- Segmented control is the right choice over radio buttons for this context. Compact, shows both options simultaneously (recognition over recall, Nielsen #6).
- **Gap in ACs**: Story doesn't specify that the mode selector should only be visible when a relationship type is selected. If the relationship dropdown is "(none)", showing "With / Without" makes no sense.
- **Add AC**: *"Mode selector is only displayed when the relationship type dropdown has a non-empty selection. Clearing the relationship type hides the mode selector and resets mode to 'With'."*

### S14-5: USER_GUIDE.md Fixes — PASS
- All 4 bugs confirmed present. ACs are precise with line numbers and exact fix instructions.

---

## Cypher's Open Questions — Answered

**Q1 (S14-2)**: Are `py`/`js`/`ts`/`md` the right shorthands?
→ **Yes, with full-name aliases.** Accept `py`/`python`, `js`/`javascript`, `ts`/`typescript`, `md`/`markdown`. Show both in error messages.

**Q2 (S14-3)**: Should invalid `--subtype` values error or return empty?
→ **Silent empty is acceptable, but document it.** Add to `--help` text: "case-sensitive; unknown values return no results." Hardcoding a valid-values list is brittle since subtypes are open-ended.

**Q3 (S14-4)**: Segmented control vs radio buttons?
→ **Segmented control.** Two-option mode toggle is cleaner in a card. Plus: make it conditionally visible (only when relationship type is selected).

---

## Summary

All 5 stories are approved. The 3 notes above should be folded into the ACs before Morpheus begins arch:
1. S14-2: Error message should list `py/python, js/javascript, ts/typescript, md/markdown`
2. S14-3: Document in `--help` that `--subtype` is case-sensitive and unknown values return empty
3. S14-4: Add conditional visibility AC for mode selector
