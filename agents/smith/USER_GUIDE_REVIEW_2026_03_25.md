# USER_GUIDE.md Review — Smith
**Date**: 2026-03-25

## Verdict: Needs fixes — 5 bugs, 2 structural issues

---

## Bug 1 — CRITICAL: Prose notes inside a code fence (line 140–146)

**Location**: `## Searching with Pipeline Syntax`, the syntax block.

The markdown is:
```
```
via -m<X> PATTERN [-t<Y>...] [-o<Z>] [-f<W>] [OPTIONS]

**Note on filtering**: The `--via` flag is used to chain additional match filters...

**Note on multiple types**: You can specify multiple type flags...
```
```

Both `**Note on...**` lines are inside the code block. They will render as literal text, not bold markdown. They need to be moved outside the fence.

**Fix**: Close the code fence after the first line, then add the notes as regular paragraphs.

---

## Bug 2 — CRITICAL: `--via` misdescribed as a filter chaining operator (line 143)

The "Note on filtering" says: *"The `--via` flag is used to chain additional match filters."*

This is wrong framing. `--via <rel>` is a **relationship query operator** — it's how you query inheritance, calls, imports, etc. (Section 7 of the guide). Describing it as a "match filter chain" operator in Section 4 will confuse readers who then reach Section 7 and find a completely different mental model.

**Tested**: `via -mg '*' -tc --via -mr 'Test.*' -n 3` — the bare `--via` does work as a separator, but the doc's framing is still harmful.

**Fix**: Remove the "Note on filtering" entirely. The pipeline separator behavior is an implementation detail; relationship queries are the user-facing feature. If pipeline chaining is worth documenting, add a brief note like: *"Use `--via <rel>` to add a relationship stage — see [Relationship Queries](#relationship-queries)."*

---

## Bug 3 — CRITICAL: "Add `--via` followed by output flags" (line 219)

**Location**: `## Output Formats` section, between the `-f<X>` table and the `-o<X>` table.

The text reads: *"Add `--via` followed by output flags to change format:"*

This is incorrect. Output flags (`-oT`, `-oL`, etc.) are added directly to the command — they have nothing to do with `--via`. Example:
```bash
via -mg '*' -tc -oT   # correct
via -mg '*' -tc --via -oT  # wrong / confusing
```

**Fix**: Remove the "Add `--via` followed by output flags" sentence. Just say: *"Output flags control how results are rendered:"* or similar.

---

## Bug 4 — CONFIRMED BROKEN: `--sans has` (lines 382, 394)

**Location**: `### --sans: Negative Relationship` and `### --not` example blocks.

Both examples use `--sans has`:
```bash
via -mg '*' -tF --sans has -mg '*' -tf
via -mg '*/tests/*' -tF --sans has --not -mg 'test_*' -tf
```

**Tested** and confirmed broken:
```
Error: Unknown relationship type 'has'.
Valid: calls, declares, imports, inherits-from, references
```

The correct relationship type is `declares`.

**Fix**: Replace `has` with `declares` in both examples.

---

## Bug 5 — Broken shell one-liner (line 732)

**Location**: `## Practical Examples`, "Find Unique Files with Matches":
```bash
via -mg '*save*' -tm -n 0 | cut -d: -tf2 | sort -u
```

`-tf2` is not valid `cut` syntax. The correct flag is `-f2`.

**Fix**: `cut -d: -f2`

---

## Structural Issue 1 — Output Formats section order is backwards (lines 207–229)

The section leads with `-f<X>` (format modifiers: ASCII/Markdown/HTML/PNG) — these are rarely-used secondary flags. The `-o<X>` flags (List/Table/Raw/etc.) are what 95% of users will use, but they appear second.

**Fix**: Move the `-o<X>` table to the top of the section, and move `-f<X>` below with a note that these are format modifiers for the output.

---

## Structural Issue 2 — List output example shows relative paths (lines 237–241)

The doc shows:
```
class:via/core/types.py:35:MatchOp:@890+120
```

Actual output (tested):
```
class:/home/drusifer/Projects/via/tests/.../TestAC1_GlobPatterns:@8812+1244
```

Paths are **absolute**, not relative. The example is misleading for new users who will wonder why their output looks different.

**Fix**: Either use `...` to indicate paths are truncated, or note that paths are absolute and depend on the indexed directory.

---

---

## Bug 6 — CONFIRMED CRASH: `--sans imports` (not in doc, but tested)

**Tested**: `via -mg 'typing' --sans imports -mg '*' -tF`

**Result**: `ValueError: Unknown symbol type: module` — full traceback crash.

`--via imports` works fine. The negative variant crashes in `query_negative_relationships()` because import symbols have type `module` which the record factory doesn't handle.

**Action**: File `*user bug` → Trin for triage → Neo to fix. Do NOT add `--sans imports` examples to the doc until fixed.

---

## Bug 7 — CONFIRMED CRASH: `--sans declares` (examples exist in doc)

**Tested**: `via -mg '*' -tN --sans declares -tc` and `via -mg '*' -tc --sans declares -tm`

**Both crash** in `_execute_negative_relationship_query`.

This means the current doc examples at lines 382, 394 (Bug 4 above) are doubly wrong: `has` is an invalid type AND `declares` also crashes. The 20 Real-World Queries Q14 example at line 941 (`--sans declares`) is also documenting broken behavior.

**Action**: File `*user bug` → Trin → Neo. Remove all `--sans declares` examples from doc until fixed.

---

## Missing: `--sans` coverage gaps — what works vs. what's broken

| `--sans <rel>` | Works? | In doc? |
|----------------|--------|---------|
| `inherits-from` | ✅ | ✅ (root classes example) |
| `calls` | ✅ | ✅ (functions that call nothing) |
| `references` | ✅ | ❌ **Missing** |
| `imports` | ❌ Crashes | ❌ (good — not in doc) |
| `declares` | ❌ Crashes | ❌ (bad — examples use broken `has`/`declares`) |

**Action**: Add `--sans references` example. Remove `--sans declares`/`--sans has` examples.

---

## What's Good

- Relationship Queries section (§7) is excellent — `--via`/`--sans`/`--not` clearly explained with correct examples
- Container Queries section (`--via declares`) — correct
- Temporal Queries — correct and well-formatted
- Web Interface section — accurate, the 5 screenshots are well-captioned
- 20 Real-World Queries — very strong addition; real-world grounding is exactly what power users need
- `--stale` documentation — semantics clearly explained
- MCP Mode section — accurate and complete

---

## Priority Order

| # | Location | Severity | Fix effort |
|---|----------|----------|------------|
| 4 | `--sans has` → `--sans declares` (×2) | P0 — broken | trivial |
| 5 | `cut -d: -tf2` → `cut -d: -f2` | P0 — broken | trivial |
| 3 | Remove "Add `--via` followed by output flags" | P1 — misleading | trivial |
| 2 | Reframe/remove "Note on filtering" | P1 — misleading | trivial |
| 1 | Move notes out of code fence | P1 — renders wrong | trivial |
| 6 | Output Formats section order | P2 — UX | minor restructure |
| 7 | List output example paths | P2 — inaccurate | trivial |
