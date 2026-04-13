# Sprint 23 Architecture — Recognition Over Recall

**Author**: Morpheus  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`  
**Theme**: Make common VIA workflows discoverable without changing query semantics.

---

## Sprint Goal

Sprint 23 should reduce recall burden by making common workflows visible through one shortcut surface, task-oriented MCP examples, diagram fallback clarity, and compact CLI help.

Sprint 22 established the command model:

```text
via <result stage> [--via|--sans REL <filter stage>]
```

Sprint 23 must build on that model, not replace it.

---

## Non-Goals

- No new relationship model.
- No hidden inverse `declares` behavior.
- No direct shortcut flags in this sprint.
- No executor strategy refactor.
- No broad CLI parser replacement.

---

## Architecture Decisions

### Decision 1: Use `--canned` As The Single Shortcut Surface

Sprint 23 should use the existing `--canned` mechanism for task-language shortcuts.

Rationale:

- `--canned` already exists.
- It expands into ordinary VIA argv.
- It avoids adding a competing direct-flag system.
- It is customizable through `.via/canned/*.json`.
- It matches Smith's requirement that shortcuts show their expansion and do not hide semantics.

Do not add `--callers`, `--callees`, or `--declared-in-file` direct flags in Sprint 23. If direct aliases are desired later, they should be a thin layer over `--canned`, not a separate execution path.

### Decision 2: Correct Built-In Canned Queries To Result-Stage-First

Existing built-ins predate Sprint 22's clarified teaching model. Sprint 23 should audit and correct them.

Required built-ins:

| Name | Status | Expansion |
|------|--------|-----------|
| `callers` | support | `["-mg", "*", "-tf", "--via", "calls", "-mg", "{symbol}", "-tf"]` |
| `methods-calling` | support | `["-mg", "*", "-tm", "--via", "calls", "-mg", "{symbol}"]` |
| `inheritors` | support | `["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "{class}", "-tc"]` |
| `docs-headers` | support | `["-mg", "{pattern}", "-tH"]` |
| `symbol-body` | support | `["-mg", "{symbol}", "-tf", "-tm", "-tc", "-oR"]` |
| `paged-scan` | support | `["-mg", "{pattern}", "--slice", "{slice}"]` |

Keep `unused`, `potentially-unused`, and `dead-docs` only if their descriptions and expansions match result-stage-first semantics.

### Decision 3: Defer `callees` And `declared-in-file` As Shipped Shortcuts Unless A Clean Expansion Exists

Smith's Gate 1 note is binding: do not ship fake support.

Current VIA relationship semantics support result-stage records filtered by a relationship to filter-stage records. That cleanly supports `callers` and `inheritors`. It does not currently provide a general inverse "what does this symbol call?" or "what symbols are declared by this file?" surface through ordinary `--via` syntax.

Therefore:

- `callees` is not a Sprint 23 supported built-in unless Neo identifies an existing tested expansion that returns callees without changing relationship semantics.
- `declared-in-file` is not a Sprint 23 supported built-in unless implemented as an explicit task helper with tests and docs that explain it is task-language behavior.
- If either name appears in docs before support exists, it must appear in a "deferred shortcuts" section, not as a runnable command.

Do not add a canned query name that always errors. A command users can invoke is interpreted as support.

### Decision 4: Add Shortcut Expansion Visibility

Users need to learn from shortcuts. Add a transparent expansion display path.

Recommended CLI behavior:

```bash
via --canned callers --args symbol=parse_args --show-expanded
```

Output:

```text
via -mg '*' -tf --via calls -mg 'parse_args' -tf
```

Implementation options:

- Add `--show-expanded` beside `--canned` in `via/__main__.py`.
- Or add `via --canned callers --args symbol=parse_args --dry-run`.

Prefer `--show-expanded`: it names the user goal directly and avoids implying execution side effects.

For MCP, schema examples should include both task labels and expanded argv arrays. MCP does not need a separate dry-run tool in Sprint 23.

### Decision 5: Task-Oriented MCP Schema Examples Stay In `via/mcp/schema.py`

Add a compact "Common tasks" section to the schema description.

Required labels:

- Find symbol
- Read symbol body
- Find callers
- Search docs headers
- Regex naming search
- Multi-type search
- Paged broad scan

Keep examples as argv arrays. Do not add long prose recipes to the schema; longer recipes belong in `docs/USER_GUIDE.md` or Sprint 24.

### Decision 6: Diagram Fallback Is A Response-Shape Fix, Not A Renderer Rewrite

`-oD` fallback behavior should preserve useful data when the diagram renderer cannot produce edges.

MCP response rules:

- If a valid diagram is produced:

```json
{"output_type": "diagram", "result": "graph TD...", "total": N, "shown": N}
```

- If no relationships exist:

```json
{
  "output_type": "json",
  "result": [],
  "total": 0,
  "shown": 0,
  "note": "No relationships found for diagram output; falling back to JSON."
}
```

- If records exist but the diagram shape is unsupported:

```json
{
  "output_type": "json",
  "result": [...],
  "total": N,
  "shown": M,
  "note": "Diagram output is unsupported for this result shape; returning JSON results."
}
```

Do not alter the renderer API unless needed to distinguish no-edge from unsupported-shape. Prefer a small MCP wrapper change around renderer output and record metadata.

### Decision 7: CLI Help Adds Compact Task Examples Only

Sprint 22 help is already dense. Sprint 23 help may grow by at most 25 lines.

Add concise examples for:

- `--canned callers`
- docs headers
- regex search
- multi-type search
- paged scan
- uppercase `-tH` note

Do not add long recipe blocks; defer full recipes to Sprint 24.

---

## Implementation Plan By Story

### S23-1 Shortcut Surface

Files:

- `via/canned.py`
- `via/__main__.py`
- `via/mcp/schema.py`
- `docs/USER_GUIDE.md`
- `tests/unit/test_sprint23_c1.py`

Work:

- Audit existing built-ins.
- Correct result-stage-first expansions.
- Add supported task-language built-ins.
- Add `--show-expanded` for `--canned`.
- Document deferred shortcut names without making them executable.

### S23-2 MCP Task Examples

Files:

- `via/mcp/schema.py`
- `tests/unit/test_sprint23_c2.py`

Work:

- Add compact "Common tasks" schema section.
- Assert labels and representative argv appear.
- Keep schema concise.

### S23-3 Diagram Fallback

Files:

- `via/mcp/server.py`
- renderer-adjacent code only if needed
- `tests/unit/test_sprint23_c3.py`

Work:

- Preserve useful records when `-oD` cannot render edges.
- Add clear `note` field.
- Distinguish no relationships from unsupported shape.

### S23-4 CLI Help HCI Pass

Files:

- `via/__main__.py`
- `tests/unit/test_sprint23_c4.py`

Work:

- Add compact task examples.
- Add uppercase `-tH` / invalid lowercase `-th` guidance.
- Enforce help length growth limit.

---

## Cycle Recommendation

| Cycle | Scope | Reason |
|-------|-------|--------|
| 1 | `--canned` shortcut audit + expansion visibility | Highest HCI value and lowest architectural risk |
| 2 | MCP task examples + CLI help pass | Documentation surfaces should follow the final shortcut names |
| 3 | Diagram fallback preservation | Independent response-shape fix, easy to isolate |

---

## Risks

1. **Shortcut proliferation**: adding flags and canned names together creates competing concepts. Use `--canned` only.
2. **Hidden inverse semantics**: `declared-in-file` can recreate the Sprint 22 docs bug if treated as ordinary `--via declares`. Defer unless implemented explicitly.
3. **Help bloat**: examples help discovery but can bury core syntax. Enforce line budget.
4. **MCP schema bloat**: tool descriptions are token-sensitive. Use task labels plus short argv arrays.

---

## Smith Gate 2 Questions

1. Is `--canned` acceptable as the single Sprint 23 shortcut surface?
2. Is `--show-expanded` the clearest name for displaying shortcut expansion?
3. Should `declared-in-file` be deferred unless implemented as an explicit task helper?
