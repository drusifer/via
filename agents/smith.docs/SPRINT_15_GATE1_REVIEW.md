# Sprint 15 — Smith Gate 1 Review

**Date**: 2026-04-08
**Reviewer**: Smith (HCI Expert)
**Stories reviewed**: `agents/cypher.docs/SPRINT_15_USER_STORIES.md`
**Verdict**: **APPROVED**

---

## Story-by-Story Review

### S15-1: `--slice` windowing + `total`/`shown` — APPROVED

Strong story. The `total`/`shown` fields in JSON directly fix the #1 power-user frustration from the MCP review.

**Notes:**
- AC7 (mutual exclusion of `--slice` and `-n`) is good error prevention. The error message text is clear and actionable.
- Reusing `parse_line_slice()` syntax is the right call — consistency with existing slice behavior (Nielsen #4).
- The CLI warning text in AC5 should go to stderr, not stdout, so piped JSON isn't corrupted. Add this to the AC.

**HCI assessment:** Directly addresses Nielsen #1 (Visibility of System Status) — users will always know "10 of 347."

### S15-2: MCP output type wrapper — APPROVED

The `output_type` envelope is a clean, backward-compatible design.

**Notes:**
- The ANSI-stripping for `-oF` via MCP (AC5) is the right call — raw ANSI in JSON is unusable.
- Consider: should the MCP tool description list the valid `output_type` values so agents know what to expect? Recommend yes.

**HCI assessment:** Fixes silent flag-ignore (Nielsen #1), makes MCP a first-class output surface.

### S15-3: Fix `--lang` + `-tF` — APPROVED

Smallest, cleanest story. The diagnosis is correct: `files.language` is the right column for filepath queries.

**No notes.** Ship it.

### S15-4: `declares` for markdown → headers — APPROVED

This is the symmetry fix that makes documentation navigable as code.

**Notes:**
- Watch mode AC (AC5) is important — headers change frequently during doc editing. Good that it's explicitly called out.

**HCI assessment:** Restores the mental model that `declares` means "things contained in this file" regardless of file type (Nielsen #4).

### S15-5: Extend `-Q` to full-path matching — APPROVED

**Notes:**
- AC2 (`tests/**/test_*.py`) is the key test — recursive glob via `**` must work. If the existing glob library doesn't support `**`, this could be more than 1pt. Flag for Morpheus.
- The distinction in AC4 (without `-Q`, behavior unchanged) is critical for backward compat.

**HCI assessment:** Makes `-Q` do what users already expect it to do (Nielsen #2, match real-world mental model).

### S15-6: `--help` relationship examples — APPROVED

**Notes:**
- Three examples is the right number. The "potentially unused" example (`--sans calls`) is the most compelling real-world case — it demonstrates the unique value of via over grep.
- The one-liner rule ("KNOWN anchor LEFT, wildcard RIGHT") should be visually set apart (e.g., indented or in a box-drawing frame) so it's scannable.

**HCI assessment:** Directly addresses Nielsen #6 (Recognition over Recall) and #10 (Help and Documentation).

---

## Open Question Answers

### Q1: S15-1 — Should `total` include results excluded by `--lang`/`--subtype`?

**Answer: No — `total` should be the filtered count.** Users ask "how many Python classes match?" — they want 47, not "47 of 312 across all languages." The `total` field answers "how many results exist for my query?" not "how many symbols are in the index." Cypher's recommendation is correct.

### Q2: S15-2 — Empty `-oD` diagram behavior?

**Answer: Return `output_type: "json"` with empty result array.** An empty `graph TD\n` is misleading — it implies there's a graph with no edges, when really there's nothing to diagram. Falling back to JSON with `[]` is honest. Add a `"note": "No relationships found for diagram output; falling back to JSON."` field.

### Q3: S15-4 — Flat or nested `declares` for markdown headers?

**Answer: Flat.** One `declares` row per header, using the existing `parent_name` column in symbols for hierarchy. This is how Python `declares` works (class→method is flat, parent tracked in `parent_name`). Nesting `declares` (file→h1→h2→h3) would create a different relationship model that doesn't exist for code. Consistency wins. Cypher's recommendation is correct.

### Q4: S15-6 — Two or three examples?

**Answer: Three.** The `--sans calls` "potentially unused" example is the most compelling demo of via's unique value. Cutting it would remove the strongest argument for why relationship queries matter. Keep all three.

---

## Sprint-Level Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Story quality | ★★★★★ | All stories traceable to specific bugs/findings from the MCP review |
| Acceptance criteria | ★★★★★ | Specific, testable, with exact CLI examples |
| Scope | ★★★★★ | 9pt is tight and achievable; no scope creep |
| User value | ★★★★★ | Every story directly improves the MCP user experience |
| Backlog management | ★★★★☆ | String constants correctly deferred; could have included link indexing as a stretch goal |

**Overall: APPROVED. Proceed to Morpheus architecture.**

---

## One Amendment (add to S15-1 AC)

> AC5 amendment: The CLI warning ("Warning: showing 10 of 347 results...") must be written to **stderr**, not stdout, so it doesn't corrupt piped JSON or text output.

@Cypher: Please add this stderr constraint to S15-1 AC5 before handing to Morpheus.
