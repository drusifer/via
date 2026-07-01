# Sprint 23 Consolidated Documentation

This document consolidates all documentation for Sprint 23.

## Table of Contents

- [SPRINT_23_USER_STORIES.md](#sprint-23-user-storiesmd) (originally `agents/cypher.docs/SPRINT_23_USER_STORIES.md`)

- [SPRINT_23_ARCHITECTURE.md](#sprint-23-architecturemd) (originally `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`)

- [SPRINT_23_CYCLE_1_REVIEW.md](#sprint-23-cycle-1-reviewmd) (originally `agents/morpheus.docs/SPRINT_23_CYCLE_1_REVIEW.md`)

- [SPRINT_23_CYCLE_2_REVIEW.md](#sprint-23-cycle-2-reviewmd) (originally `agents/morpheus.docs/SPRINT_23_CYCLE_2_REVIEW.md`)

- [SPRINT_23_CYCLE_3_REVIEW.md](#sprint-23-cycle-3-reviewmd) (originally `agents/morpheus.docs/SPRINT_23_CYCLE_3_REVIEW.md`)

- [SPRINT_23_PLAN_REVIEW.md](#sprint-23-plan-reviewmd) (originally `agents/morpheus.docs/SPRINT_23_PLAN_REVIEW.md`)

- [SPRINT_23_CYCLE_2_HCI_REVIEW.md](#sprint-23-cycle-2-hci-reviewmd) (originally `agents/smith.docs/SPRINT_23_CYCLE_2_HCI_REVIEW.md`)

- [SPRINT_23_GATE1_REVIEW.md](#sprint-23-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`)

- [SPRINT_23_GATE2_REVIEW.md](#sprint-23-gate2-reviewmd) (originally `agents/smith.docs/SPRINT_23_GATE2_REVIEW.md`)

- [SPRINT_23_CLOSEOUT.md](#sprint-23-closeoutmd) (originally `agents/mouse.docs/SPRINT_23_CLOSEOUT.md`)

- [SPRINT_23_TASKS.md](#sprint-23-tasksmd) (originally `agents/mouse.docs/SPRINT_23_TASKS.md`)

- [SPRINT_23_CYCLE_1_SUMMARY_2026-04-12T18-18.md](#sprint-23-cycle-1-summary-2026-04-12t18-18md) (originally `agents/neo.docs/SPRINT_23_CYCLE_1_SUMMARY_2026-04-12T18-18.md`)

- [SPRINT_23_CYCLE_2_SUMMARY_2026-04-12T18-24.md](#sprint-23-cycle-2-summary-2026-04-12t18-24md) (originally `agents/neo.docs/SPRINT_23_CYCLE_2_SUMMARY_2026-04-12T18-24.md`)

- [SPRINT_23_CYCLE_3_SUMMARY_2026-04-12T18-31.md](#sprint-23-cycle-3-summary-2026-04-12t18-31md) (originally `agents/neo.docs/SPRINT_23_CYCLE_3_SUMMARY_2026-04-12T18-31.md`)

- [SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md](#sprint-23-cycle-1-uat-summary-2026-04-12t18-21md) (originally `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md`)

- [SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md](#sprint-23-cycle-2-uat-summary-2026-04-12t18-27md) (originally `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md`)

- [SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md](#sprint-23-cycle-3-uat-summary-2026-04-12t18-32md) (originally `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md`)


---


## SPRINT_23_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`


## Sprint 23 User Stories — Recognition Over Recall

**Author**: Cypher  
**Date**: 2026-04-12  
**Theme**: Recognition over recall for common VIA query workflows  
**Source Backlog**: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`  
**Sprint 22 Closeout**: `agents/mouse.docs/SPRINT_22_CLOSEOUT.md`

---

### Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or multi-step token-saving sequences.

Sprint 22 stabilized the command model:

```text
via <result stage> [--via|--sans REL <filter stage>]
```

Sprint 23 should build recognition affordances on top of that model. Shortcuts and examples must be transparent: users should be able to see the ordinary VIA query they expand to.

---

### Product Constraints

- Do not introduce a new relationship model.
- Do not hide semantics behind magic behavior.
- Shortcuts must expand into existing parser/executor paths where possible.
- Existing explicit `--via` / `--sans` syntax remains supported.
- Documentation must keep the result-stage-first model as the primary teaching model.
- If "symbols declared in file" needs special handling, it must be named as a task-language shortcut and not documented as ordinary inverse `declares` behavior.

---

### S23-1: Task-Language Shortcuts For Common Relationship Questions

**Priority**: P0  
**Estimate**: 3 pts  

**As a** user asking common code-navigation questions,  
**I want** task-language shortcuts for callers, callees, and symbols declared in a file,  
**so that** I do not have to remember relationship direction.

#### Required Shortcut Concepts

The final syntax is a Morpheus architecture decision, but the product vocabulary is:

- `callers`: return functions/methods that call a named symbol.
- `callees`: return symbols called by a named function/method.
- `declared-in-file`: return symbols declared in a named file.

#### Acceptance Criteria

- [ ] Architecture selects one explicit shortcut surface:
  - built-in `--canned` names, or
  - direct task-language CLI flags, or
  - a thin dedicated helper API used by MCP examples.
- [ ] Shortcuts are named in user language, not parser-language.
- [ ] `callers` expands to ordinary `--via calls` semantics.
- [ ] `callees` either expands through a supported existing path or is deferred with a clear structured unsupported shortcut error.
- [ ] `declared-in-file` either expands through a supported existing path or is implemented as an explicit task shortcut; it must not be documented as ordinary inverse `declares`.
- [ ] Help/schema/docs show the expanded equivalent query for each supported shortcut.
- [ ] Existing explicit relationship syntax remains supported.
- [ ] Tests prove shortcut and expanded query result sets match for supported shortcuts.
- [ ] Unsupported shortcut paths return `output_type: "error"` through MCP with a recovery hint.

---

### S23-2: Task-Oriented MCP Schema Examples

**Priority**: P0  
**Estimate**: 2 pts  

**As an** AI agent using VIA MCP,  
**I want** schema examples grouped by task,  
**so that** I can choose a low-token workflow without remembering flags.

#### Acceptance Criteria

- [ ] MCP schema description includes a compact "Common tasks" section.
- [ ] Common tasks include:
  - find a symbol by name
  - read one symbol body with `-oR`
  - find callers
  - search docs headers with `-tH`
  - regex naming search with `-mr`
  - multi-type search with `-tf -tm -tc`
  - paged broad scan with `--slice`
- [ ] Examples are short and copyable as `args` arrays.
- [ ] Examples avoid unsupported multi-match composition.
- [ ] Examples use result-stage-first relationship wording.
- [ ] Tests assert the key task labels and representative args appear in `via mcp schema`.

---

### S23-3: Preserve Useful Data On Diagram Fallback

**Priority**: P1  
**Estimate**: 1 pt  

**As a** user requesting diagram output,  
**I want** non-renderable diagram responses to preserve useful query results,  
**so that** I do not have to rerun the query blindly.

#### Acceptance Criteria

- [ ] If `-oD` cannot produce edges, the MCP response includes a clear `note`.
- [ ] Fallback response keeps `output_type`, `result`, `total`, and `shown` coherent.
- [ ] The note distinguishes:
  - no relationships found
  - unsupported diagram shape
- [ ] If useful non-diagram query results exist, they remain available in `result`.
- [ ] Tests cover no-edge and valid-edge diagram requests.

---

### S23-4: CLI Help HCI Pass

**Priority**: P1  
**Estimate**: 1 pt  

**As a** CLI user,  
**I want** `via --help` to expose common tasks and constraints without becoming bloated,  
**so that** I can self-serve common syntax.

#### Acceptance Criteria

- [ ] Help keeps the Sprint 22 command model visible:

  ```text
  via <result stage> [--via|--sans REL <filter stage>]
  ```

- [ ] Help includes concise task-language examples for:
  - callers
  - docs headers
  - regex search
  - multi-type search
  - paged scan
- [ ] Help explicitly says `-tH` is uppercase and `-th` is invalid.
- [ ] Help keeps one-matcher-per-stage guidance.
- [ ] Relationship examples are phrased as "return X, filtered by relationship to Y."
- [ ] Help length increases by no more than 25 lines from Sprint 22 baseline.
- [ ] Tests assert the high-value guidance strings and help length limit.

---

### Definition Of Done

- [ ] Smith approves the Sprint 23 user stories.
- [ ] Morpheus approves architecture without adding a new relationship model.
- [ ] Mouse breaks work into short cycles with one HCI surface per cycle where possible.
- [ ] Shortcuts and examples are discoverable from MCP schema and CLI help.
- [ ] Unsupported shortcut behavior is explicit, structured, and recoverable.

---

### Gate Handoff

@Smith: Please review Sprint 23 stories for HCI fit. Focus on whether the shortcut vocabulary is user-facing enough and whether the scope avoids creating hidden semantics.


---


## SPRINT_23_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`


## Sprint 23 Architecture — Recognition Over Recall

**Author**: Morpheus  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`  
**Theme**: Make common VIA workflows discoverable without changing query semantics.

---

### Sprint Goal

Sprint 23 should reduce recall burden by making common workflows visible through one shortcut surface, task-oriented MCP examples, diagram fallback clarity, and compact CLI help.

Sprint 22 established the command model:

```text
via <result stage> [--via|--sans REL <filter stage>]
```

Sprint 23 must build on that model, not replace it.

---

### Non-Goals

- No new relationship model.
- No hidden inverse `declares` behavior.
- No direct shortcut flags in this sprint.
- No executor strategy refactor.
- No broad CLI parser replacement.

---

### Architecture Decisions

#### Decision 1: Use `--canned` As The Single Shortcut Surface

Sprint 23 should use the existing `--canned` mechanism for task-language shortcuts.

Rationale:

- `--canned` already exists.
- It expands into ordinary VIA argv.
- It avoids adding a competing direct-flag system.
- It is customizable through `.via/canned/*.json`.
- It matches Smith's requirement that shortcuts show their expansion and do not hide semantics.

Do not add `--callers`, `--callees`, or `--declared-in-file` direct flags in Sprint 23. If direct aliases are desired later, they should be a thin layer over `--canned`, not a separate execution path.

#### Decision 2: Correct Built-In Canned Queries To Result-Stage-First

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

#### Decision 3: Defer `callees` And `declared-in-file` As Shipped Shortcuts Unless A Clean Expansion Exists

Smith's Gate 1 note is binding: do not ship fake support.

Current VIA relationship semantics support result-stage records filtered by a relationship to filter-stage records. That cleanly supports `callers` and `inheritors`. It does not currently provide a general inverse "what does this symbol call?" or "what symbols are declared by this file?" surface through ordinary `--via` syntax.

Therefore:

- `callees` is not a Sprint 23 supported built-in unless Neo identifies an existing tested expansion that returns callees without changing relationship semantics.
- `declared-in-file` is not a Sprint 23 supported built-in unless implemented as an explicit task helper with tests and docs that explain it is task-language behavior.
- If either name appears in docs before support exists, it must appear in a "deferred shortcuts" section, not as a runnable command.

Do not add a canned query name that always errors. A command users can invoke is interpreted as support.

#### Decision 4: Add Shortcut Expansion Visibility

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

#### Decision 5: Task-Oriented MCP Schema Examples Stay In `via/mcp/schema.py`

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

#### Decision 6: Diagram Fallback Is A Response-Shape Fix, Not A Renderer Rewrite

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

#### Decision 7: CLI Help Adds Compact Task Examples Only

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

### Implementation Plan By Story

#### S23-1 Shortcut Surface

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

#### S23-2 MCP Task Examples

Files:

- `via/mcp/schema.py`
- `tests/unit/test_sprint23_c2.py`

Work:

- Add compact "Common tasks" schema section.
- Assert labels and representative argv appear.
- Keep schema concise.

#### S23-3 Diagram Fallback

Files:

- `via/mcp/server.py`
- renderer-adjacent code only if needed
- `tests/unit/test_sprint23_c3.py`

Work:

- Preserve useful records when `-oD` cannot render edges.
- Add clear `note` field.
- Distinguish no relationships from unsupported shape.

#### S23-4 CLI Help HCI Pass

Files:

- `via/__main__.py`
- `tests/unit/test_sprint23_c4.py`

Work:

- Add compact task examples.
- Add uppercase `-tH` / invalid lowercase `-th` guidance.
- Enforce help length growth limit.

---

### Cycle Recommendation

| Cycle | Scope | Reason |
|-------|-------|--------|
| 1 | `--canned` shortcut audit + expansion visibility | Highest HCI value and lowest architectural risk |
| 2 | MCP task examples + CLI help pass | Documentation surfaces should follow the final shortcut names |
| 3 | Diagram fallback preservation | Independent response-shape fix, easy to isolate |

---

### Risks

1. **Shortcut proliferation**: adding flags and canned names together creates competing concepts. Use `--canned` only.
2. **Hidden inverse semantics**: `declared-in-file` can recreate the Sprint 22 docs bug if treated as ordinary `--via declares`. Defer unless implemented explicitly.
3. **Help bloat**: examples help discovery but can bury core syntax. Enforce line budget.
4. **MCP schema bloat**: tool descriptions are token-sensitive. Use task labels plus short argv arrays.

---

### Smith Gate 2 Questions

1. Is `--canned` acceptable as the single Sprint 23 shortcut surface?
2. Is `--show-expanded` the clearest name for displaying shortcut expansion?
3. Should `declared-in-file` be deferred unless implemented as an explicit task helper?


---


## SPRINT_23_CYCLE_1_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_23_CYCLE_1_REVIEW.md`


## Sprint 23 Cycle 1 Review — Canned Shortcut Surface

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Verdict**: APPROVED

### Scope Reviewed

- `via/canned.py`
- `via/__main__.py`
- `tests/unit/test_sprint23_c1.py`
- Trin UAT: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md`

### Findings

#### Approved: `--canned` Remains A Template Expander

The implementation keeps canned queries as static argv templates expanded through the existing pipeline path. It does not add a second query engine, strategy branch, or custom executor path.

#### Approved: `--show-expanded` Is Transparent And Non-Executing

`--show-expanded` is handled at the canned-command boundary, prints a copyable `via ...` command, and returns success without calling the pipeline executor. This matches the Sprint 23 transparency goal.

#### Approved: No Unsupported Shortcut Surface

No direct flags such as `--callers` were added. Deferred names `callees` and `declared-in-file` were not shipped as runnable built-ins.

#### Architecture Note: Relationship Orientation Mismatch

Cycle 1 exposed an existing mismatch between Sprint 22 user-facing docs and the runtime executor:

- Sprint 22 docs teach result-stage-first relationship syntax.
- The current executor still evaluates positive relationship queries with the older anchor-left/object-first orientation.

Neo correctly chose task-correct canned expansions against the current runtime. Forcing result-stage-first text into canned shortcuts without changing the executor would have shipped broken shortcuts. This is approved as a bounded implementation exception, not a new relationship design.

### Follow-Up Requirement

Cycle 2 must treat the docs/runtime mismatch carefully when adding help and MCP examples. It should not add examples that promise result-stage-first behavior unless the runtime actually supports that behavior. The long-term fix is a separate relationship-orientation reconciliation task, not part of Cycle 1.

### Verification Reviewed

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

### Decision

Cycle 1 is approved. Proceed to Sprint 23 Cycle 2: task-oriented MCP schema and CLI help examples, followed by Smith HCI review.


---


## SPRINT_23_CYCLE_2_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_23_CYCLE_2_REVIEW.md`


## Sprint 23 Cycle 2 Review — Task Examples And CLI Help

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Verdict**: APPROVED

### Scope Reviewed

- `via/__main__.py`
- `via/mcp/schema.py`
- `tests/unit/test_sprint23_c2.py`
- Updated help/schema regression tests
- Trin UAT: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md`

### Findings

#### Approved: Task-First Recognition Surface

CLI help and MCP schema now lead with common tasks instead of forcing users to recall low-level relationship direction. The examples cover the planned task set: symbol lookup, body reading, callers, docs headers, regex, multi-type search, and paged scans.

#### Approved: Bounded Help Growth

Help remains compact:

- Sprint 22 baseline: 112 lines
- Sprint 23 actual: 121 lines
- Budget maximum: 137 lines

#### Approved: Runtime-Correct Relationship Wording

Cycle 2 correctly handles the Cycle 1 finding that executor behavior still uses current-runtime relationship orientation. The help/schema now frame raw relationship syntax as advanced and point common tasks to `--canned`, avoiding examples that look nice but do not work.

#### Approved: No Unsupported Shortcut Advertising

No unsupported direct flags or deferred shortcut names are advertised. `-tH` guidance is explicit, including the lowercase `-th` trap in MCP schema.

### Review Note

This review accepts a deliberate correction from the Sprint 22 documentation direction: user-facing examples must be executable against the current runtime. The broader relationship-orientation reconciliation remains a future architecture task.

### Verification Reviewed

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `via --help` — 121 lines.
- `via mcp schema` — 121 lines.

### Decision

Cycle 2 is approved for Smith HCI wording review.


---


## SPRINT_23_CYCLE_3_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_23_CYCLE_3_REVIEW.md`


## Sprint 23 Cycle 3 Review — Diagram Fallback Preservation

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Verdict**: APPROVED

### Scope Reviewed

- `via/mcp/server.py`
- `tests/unit/test_sprint23_c3.py`
- Trin UAT: `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md`

### Findings

#### Approved: Wrapper-Layer Response Fix

The implementation keeps fallback handling in the MCP wrapper. Renderer APIs are unchanged, which matches the Sprint 23 architecture boundary.

#### Approved: Data Preservation

When diagram output cannot render for a non-class result shape, MCP now returns JSON with the matching records and a note. This directly addresses the original usability defect where useful data could be discarded.

#### Approved: Existing Diagram Contract Preserved

Valid diagram output still returns `output_type: "diagram"` and rendered Mermaid content.

#### Approved: Regression Coverage

Tests cover unsupported-shape fallback, empty fallback, and valid diagram output. Existing Sprint 15 MCP output-wrapper and Sprint 22 structured-error regressions stayed green.

### Decision

Cycle 3 is approved. Sprint 23 implementation is complete and ready for Mouse closeout.


---


## SPRINT_23_PLAN_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_23_PLAN_REVIEW.md`


## Sprint 23 Plan Review

**Persona**: Morpheus  
**Date**: 2026-04-12  
**Reviewed**: `agents/mouse.docs/SPRINT_23_TASKS.md`  
**Verdict**: APPROVED

### Review Criteria

- Plan follows `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`.
- Work is split into short cycles.
- Smith HCI gate is placed where wording and discoverability are user-facing.
- No direct shortcut flags are planned.
- No hidden inverse `declares` behavior is planned.

### Findings

No blockers found.

The cycle sequence is correct:

1. `--canned` shortcut surface and `--show-expanded`
2. MCP schema and CLI help examples, with Smith HCI wording gate
3. Diagram fallback preservation

This order minimizes churn. Shortcut names and expansions are stabilized before documentation examples are updated, and diagram fallback stays isolated from shortcut work.

### Decision

Sprint 23 task plan is approved. Neo can start Cycle 1: canned shortcut surface.


---


## SPRINT_23_CYCLE_2_HCI_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_23_CYCLE_2_HCI_REVIEW.md`


## Sprint 23 Cycle 2 HCI Review — Help And Schema Wording

**Persona**: Smith  
**Date**: 2026-04-12  
**Verdict**: APPROVED WITH NOTES

### Surfaces Tested

- `.venv/bin/python -m via --help`
- `.venv/bin/python -m via mcp schema`
- `via/mcp/schema.py`

### HCI Findings

#### Approved: Recognition Over Recall

The new `Common Tasks` section gives users task-language commands before exposing low-level relationship syntax. This directly supports Nielsen #6, recognition rather than recall.

#### Approved: Error Prevention

The schema explicitly calls out uppercase `-tH` and invalid lowercase `-th`. This prevents a known command-entry mistake before the user makes it.

#### Approved: Progressive Disclosure

The help now separates common tasks from `Advanced Relationship Queries`. This is the right HCI shape: novice users can copy common tasks, while expert users still have access to raw relationship primitives.

#### Approved: Minimalism

The help remains compact at 121 lines, within the 137-line budget. The new content adds high-value examples without turning `--help` into a manual.

### Note For Future Work

The phrase "Current runtime positive relationship lookups" is technically accurate but still somewhat implementation-facing. It is acceptable in the advanced section for this sprint because it prevents misleading users. A later relationship-orientation reconciliation should replace this with a simpler stable command model.

### Decision

Cycle 2 passes the HCI gate. Proceed to Cycle 3.


---


## SPRINT_23_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`


## Sprint 23 Gate 1 Review

**Persona**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Verdict**: APPROVED WITH NOTES

### HCI Assessment

Sprint 23 correctly follows Sprint 22. The stories shift from "make the query system trustworthy" to "make common workflows discoverable," which fits Nielsen #6 Recognition Rather Than Recall and #7 Flexibility and Efficiency.

### Approved Scope

- Task-language shortcuts for common questions.
- Task-oriented MCP examples.
- Diagram fallback that preserves useful data.
- CLI help HCI pass.

### Notes For Morpheus

1. **Shortcut surface must be one coherent path.** Do not ship both direct flags and `--canned` names unless one is explicitly an alias of the other. Multiple shortcut systems create a new recall burden.
2. **Do not ship fake support for `callees` or `declared-in-file`.** If the architecture cannot support one cleanly in Sprint 23, defer that shortcut visibly instead of returning a placeholder error from a command users think exists.
3. **Every shortcut must show its expansion.** This is the main safety rail against hidden semantics.
4. **MCP examples should be task-grouped, not flag-grouped.** Agents ask "find callers" or "read symbol body"; they do not think "compose output flag plus relationship filter."
5. **Help length limit matters.** The Sprint 22 help is already dense. Favor compact examples and point to user guide for longer recipes.

### Gate Decision

Approved to proceed to Morpheus architecture.


---


## SPRINT_23_GATE2_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_23_GATE2_REVIEW.md`


## Sprint 23 Gate 2 Architecture Review

**Persona**: Smith  
**Date**: 2026-04-12  
**Reviewed**: `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`  
**Verdict**: APPROVED

### HCI Assessment

The architecture preserves Sprint 22's mental model while adding recognition affordances. It correctly chooses one shortcut surface, `--canned`, instead of adding competing direct flags.

### Gate Answers

1. **Is `--canned` acceptable as the single Sprint 23 shortcut surface?**  
   Yes. It is already established, transparent, customizable, and avoids another flag family.

2. **Is `--show-expanded` the clearest name for displaying shortcut expansion?**  
   Yes. It is more direct than `--dry-run` because the user goal is learning the expansion, not simulating execution.

3. **Should `declared-in-file` be deferred unless implemented as an explicit task helper?**  
   Yes. This prevents the Sprint 22 inverse `declares` confusion from reappearing.

### Approval Notes

- Keep `--show-expanded` output copyable as a complete `via ...` command.
- Do not list deferred shortcuts in the primary examples table. Put them in a clearly labeled "Deferred" note if mentioned at all.
- MCP schema examples should remain compact; full recipes belong in Sprint 24.
- `callees` should not appear as a runnable built-in unless tests prove it returns callees.

### Gate Decision

Approved to proceed to Mouse sprint task planning.


---


## SPRINT_23_CLOSEOUT.md

**Original Location**: `agents/mouse.docs/SPRINT_23_CLOSEOUT.md`


## Sprint 23 Closeout — Recognition Over Recall

**Persona**: Mouse  
**Date**: 2026-04-12  
**Status**: COMPLETE

### Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or token-saving sequences.

### Delivered

#### Cycle 1 — Canned Shortcut Surface

- Added/verified Sprint 23 canned shortcuts: `methods-calling`, `docs-headers`, `symbol-body`, `paged-scan`.
- Added `--show-expanded`.
- Kept unsupported `callees` and `declared-in-file` out of built-ins.
- Morpheus approved the template-expander architecture.

#### Cycle 2 — Task Examples And CLI Help

- Added compact CLI `Common Tasks`.
- Added task-oriented MCP schema examples.
- Added `--show-expanded` help discoverability.
- Added uppercase `-tH` guidance.
- Kept unsupported shortcut names out of help/schema.
- Smith approved the HCI wording gate with a future wording note.

#### Cycle 3 — Diagram Fallback Preservation

- MCP diagram fallback now preserves useful JSON result records when diagram output cannot render.
- Empty diagram fallback returns JSON with a clear note.
- Valid diagram output remains `output_type: "diagram"`.
- Renderer API was not broadened.

### Verification Baseline

Targeted Makefile verification passed:

- Cycle 1: 9 tests
- Cycle 2: 30 tests
- Cycle 3: 28 tests

Total targeted Sprint 23 verification baseline: **67 passing tests**.

### Reviews And Gates

- Cycle 1 UAT: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md`
- Cycle 1 review: `agents/morpheus.docs/SPRINT_23_CYCLE_1_REVIEW.md`
- Cycle 2 UAT: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md`
- Cycle 2 review: `agents/morpheus.docs/SPRINT_23_CYCLE_2_REVIEW.md`
- Cycle 2 HCI review: `agents/smith.docs/SPRINT_23_CYCLE_2_HCI_REVIEW.md`
- Cycle 3 UAT: `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md`
- Cycle 3 review: `agents/morpheus.docs/SPRINT_23_CYCLE_3_REVIEW.md`

### Follow-Up Risk

Sprint 23 exposed that runtime relationship orientation still differs from the Sprint 22 result-stage-first documentation direction. Sprint 23 handled this by leading users toward canned task shortcuts and labeling raw relationship syntax as advanced current-runtime behavior. A future sprint should reconcile the runtime and documentation model so the command structure can be simplified again.


---


## SPRINT_23_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_23_TASKS.md`


## Sprint 23 Task Plan — Recognition Over Recall

**Author**: Mouse  
**Date**: 2026-04-12  
**Stories**: `agents/cypher.docs/SPRINT_23_USER_STORIES.md`  
**Architecture**: `agents/morpheus.docs/SPRINT_23_ARCHITECTURE.md`  
**Smith Gate 1**: `agents/smith.docs/SPRINT_23_GATE1_REVIEW.md`  
**Smith Gate 2**: `agents/smith.docs/SPRINT_23_GATE2_REVIEW.md`

---

### Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or token-saving sequences.

### Scope

#### In Scope

- `--canned` built-in audit and result-stage-first corrections
- `--show-expanded` for shortcut transparency
- Compact task-oriented MCP schema examples
- Compact CLI help HCI pass
- Diagram fallback response preservation

#### Out Of Scope

- Direct shortcut flags like `--callers`
- New relationship model
- Hidden inverse `declares`
- Executor strategy refactor
- Full recipe section (Sprint 24)

---

### Cycle Plan

| Cycle | Phase | Stories | Owner Flow | Status |
|-------|-------|---------|------------|--------|
| 1 | Canned Shortcut Surface | S23-1 | Neo → Trin → Morpheus | Approved |
| 2 | Task Examples And CLI Help | S23-2, S23-4 | Neo → Trin → Morpheus → Smith | Approved |
| 3 | Diagram Fallback Preservation | S23-3 | Neo → Trin → Morpheus | Approved |

---

### Cycle 1 — Canned Shortcut Surface

**Goal**: Make `--canned` the transparent recognition shortcut path.

#### Neo Tasks

- [x] Audit existing built-in canned queries in `via/canned.py`.
- [x] Correct built-ins to current task-correct runtime semantics.
- [x] Add supported built-ins from architecture:
  - `callers`
  - `methods-calling`
  - `inheritors`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- [x] Keep or remove existing built-ins based on whether their semantics remain correct.
- [x] Add `--show-expanded` for `--canned`.
- [x] Ensure `--show-expanded` prints a copyable full `via ...` command.
- [x] Do not add runnable `callees` or `declared-in-file` unless cleanly implemented and tested.
- [x] Add focused unit tests in `tests/unit/test_sprint23_c1.py`.

#### Trin Verification

- [x] Verify supported canned shortcuts return same results as expanded queries.
- [x] Verify `--show-expanded` does not execute the query.
- [x] Verify missing canned args still produce actionable errors.
- [x] Verify deferred shortcut names are not advertised as runnable built-ins.

#### Morpheus Review Focus

- [x] `--canned` remains a template expander, not a second query engine.
- [x] No new relationship semantics shipped.

---

### Cycle 2 — Task Examples And CLI Help

**Goal**: Make common tasks discoverable in MCP schema and CLI help without bloat.

#### Neo Tasks

- [x] Add compact "Common tasks" section to `via/mcp/schema.py`.
- [x] Include examples for:
  - find symbol
  - read symbol body
  - find callers
  - docs headers
  - regex naming search
  - multi-type search
  - paged broad scan
- [x] Update `via --help` with compact task examples.
- [x] Add uppercase `-tH` / invalid lowercase `-th` guidance.
- [x] Preserve one-matcher-per-stage guidance and use runtime-correct relationship examples.
- [x] Add tests in `tests/unit/test_sprint23_c2.py`.

#### Trin Verification

- [x] Run schema/help tests through Makefile.
- [x] Smoke-check `.venv/bin/python -m via --help`.
- [x] Smoke-check `.venv/bin/python -m via mcp schema`.
- [x] Confirm help growth is at most 25 lines from Sprint 22 baseline.

#### Morpheus Review Focus

- [x] Help/schema examples match approved shortcut names and expansions.
- [x] No unsupported shortcut appears as runnable.

#### Smith Review Focus

- [x] Final HCI wording gate for examples and help density.

---

### Cycle 3 — Diagram Fallback Preservation

**Goal**: Preserve useful MCP data when diagram output cannot render edges.

#### Neo Tasks

- [x] Update MCP output handling in `via/mcp/server.py`.
- [x] Preserve useful JSON result data for unsupported diagram shapes.
- [x] Add a clear `note` for no-relationship and unsupported-shape fallbacks.
- [x] Keep valid diagram responses as `output_type: "diagram"`.
- [x] Add tests in `tests/unit/test_sprint23_c3.py`.

#### Trin Verification

- [x] Verify no-edge diagram fallback.
- [x] Verify unsupported-shape fallback preserves results.
- [x] Verify valid-edge diagram response remains diagram output.
- [x] Run existing MCP output regression tests.

#### Morpheus Review Focus

- [x] Response-shape fix stays in MCP wrapper layer where possible.
- [x] Renderer API is not broadened unless necessary.

---

### Definition Of Done

- [x] All Sprint 23 acceptance criteria are met.
- [x] All cycle-level targeted tests pass through Makefile.
- [x] Smith approves Cycle 2 HCI wording.
- [x] No direct shortcut flags added.
- [x] No hidden inverse `declares` shipped.
- [ ] Sprint closeout records final targeted baseline.

---

### First Handoff

@Neo: Start Cycle 1, canned shortcut surface.


---


## SPRINT_23_CYCLE_1_SUMMARY_2026-04-12T18-18.md

**Original Location**: `agents/neo.docs/SPRINT_23_CYCLE_1_SUMMARY_2026-04-12T18-18.md`


## Sprint 23 Cycle 1 Summary — Canned Shortcut Surface

**Persona**: Neo  
**Date**: 2026-04-12T18:18  
**Status**: Implementation complete; QA pending

### Delivered

- Added Sprint 23 canned shortcuts in `via/canned.py`:
  - `methods-calling`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- Preserved existing task-useful shortcuts:
  - `unused`
  - `potentially-unused`
  - `callers`
  - `inheritors`
  - `dead-docs`
- Added `--show-expanded` handling for `--canned` in `via/__main__.py`.
- `--show-expanded` prints a copyable `via ...` command and exits without running the query.
- Deferred unsupported shortcut names are not added as built-ins:
  - `callees`
  - `declared-in-file`
- Added focused tests in `tests/unit/test_sprint23_c1.py`.

### Important Finding

The current executor relationship implementation still uses the older runtime orientation:

```text
before --via = known anchor / object
after --via = returned subject filter
```

Sprint 22 documentation moved toward a result-stage-first mental model, but the executor was not changed in that sprint. Cycle 1 therefore keeps `callers` and `inheritors` expanded in the orientation that returns correct runtime results today. This avoids shipping a shortcut that looks correct in documentation but returns the wrong symbols.

### Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed after QA added coverage for `methods-calling` and `inheritors`.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

### QA Notes

- Verify shortcut output against explicit expanded queries, not only against template text.
- Confirm `--show-expanded` does not require an index and does not execute.
- Confirm deferred names remain absent from `load_canned_queries()`.
- Morpheus should review the docs/runtime orientation mismatch as a follow-up risk, but no new relationship semantics were added in Cycle 1.


---


## SPRINT_23_CYCLE_2_SUMMARY_2026-04-12T18-24.md

**Original Location**: `agents/neo.docs/SPRINT_23_CYCLE_2_SUMMARY_2026-04-12T18-24.md`


## Sprint 23 Cycle 2 Summary — Task Examples And CLI Help

**Persona**: Neo  
**Date**: 2026-04-12T18:24  
**Status**: Implementation complete; QA pending

### Delivered

- Added compact `Common Tasks` examples to CLI help.
- Added `--show-expanded` to the CLI help options list.
- Added task-oriented MCP schema examples for:
  - find symbol
  - read symbol body
  - find callers
  - docs headers
  - regex naming search
  - multi-type search
  - paged broad scan
- Added explicit uppercase `-tH` guidance and noted lowercase `-th` is invalid in MCP schema.
- Kept unsupported shortcut names out of help/schema:
  - `--callers`
  - `--callees`
  - `--declared-in-file`
- Updated raw relationship examples to be labeled advanced and current-runtime oriented.

### Design Note

Cycle 1 confirmed that runtime relationship orientation still differs from the Sprint 22 result-stage-first documentation model. Cycle 2 therefore leads users toward `--canned` task shortcuts and only shows raw relationship forms as advanced current-runtime examples. This avoids documenting commands that do not work against the current executor.

### Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `.venv/bin/python -m via --help | wc -l` — 121 lines.
- `.venv/bin/python -m via mcp schema | wc -l` — 121 lines.

### QA Notes

- Verify the schema output contains the common-task examples and no unsupported shortcut names.
- Verify `via --help` remains under the Sprint 23 growth budget: baseline 112 lines; limit 137 lines.
- Verify Smith HCI review focuses on whether users can pick a task without memorizing relationship direction.


---


## SPRINT_23_CYCLE_3_SUMMARY_2026-04-12T18-31.md

**Original Location**: `agents/neo.docs/SPRINT_23_CYCLE_3_SUMMARY_2026-04-12T18-31.md`


## Sprint 23 Cycle 3 Summary — Diagram Fallback Preservation

**Persona**: Neo  
**Date**: 2026-04-12T18:31  
**Status**: Implementation complete; QA pending

### Delivered

- Added a shared JSON payload helper for MCP query responses.
- Updated MCP diagram fallback handling to preserve matching records as JSON when diagram output cannot render.
- Added a clear fallback note for:
  - unsupported diagram shapes with matching records
  - empty diagram results
- Kept valid diagram responses as `output_type: "diagram"`.
- Kept the change in `via/mcp/server.py`; renderer APIs were not broadened.

### Verification

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c3.py` — 3 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c3.py` — 19 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.

### QA Notes

- Verify unsupported diagram shape fallback preserves matching symbol rows.
- Verify empty diagram fallback remains JSON with an empty result and note.
- Verify valid class diagram output remains `output_type: "diagram"`.


---


## SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md

**Original Location**: `agents/trin.docs/SPRINT_23_CYCLE_1_UAT_Summary_2026-04-12T18-21.md`


## Sprint 23 Cycle 1 UAT Summary — Canned Shortcut Surface

**Persona**: Trin  
**Date**: 2026-04-12T18:21  
**Status**: PASS

### Verification

- Confirmed Sprint 23 canned built-ins are registered:
  - `callers`
  - `methods-calling`
  - `inheritors`
  - `docs-headers`
  - `symbol-body`
  - `paged-scan`
- Confirmed deferred shortcuts are not advertised as runnable built-ins:
  - `callees`
  - `declared-in-file`
- Confirmed `callers`, `methods-calling`, and `inheritors` return the same result as their explicit expanded queries.
- Confirmed `--show-expanded` prints a copyable `via ...` command without executing.
- Confirmed missing canned args remain actionable.
- Confirmed docs-header and paged-scan templates expand to normal argv.

### Tests

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c1.py` — 6 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint16_c3.py` — 3 passed.

### QA Note

The shortcut expansions are verified against current runtime behavior. There remains a known product/architecture follow-up: Sprint 22 result-stage-first documentation and the executor's actual relationship orientation are divergent. Cycle 1 does not introduce new relationship semantics.


---


## SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md

**Original Location**: `agents/trin.docs/SPRINT_23_CYCLE_2_UAT_Summary_2026-04-12T18-27.md`


## Sprint 23 Cycle 2 UAT Summary — Task Examples And CLI Help

**Persona**: Trin  
**Date**: 2026-04-12T18:27  
**Status**: PASS

### Verification

- CLI help includes compact common-task examples.
- CLI help documents `--show-expanded`.
- MCP schema includes task-oriented examples for symbol lookup, body reading, callers, docs headers, regex, multi-type, and paged scans.
- Uppercase `-tH` guidance is present; lowercase `-th` is identified as invalid in schema guidance.
- Unsupported shortcut names are not advertised:
  - `--callers`
  - `--callees`
  - `--declared-in-file`
- Raw relationship examples are labeled advanced and use current-runtime behavior.
- Help growth stays within Sprint 23 budget:
  - Sprint 22 baseline: 112 lines
  - Budget: <=137 lines
  - Actual: 121 lines

### Tests

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c2.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c3.py` — 4 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c1.py` — 22 passed.
- `.venv/bin/python -m via --help | wc -l` — 121.
- `.venv/bin/python -m via mcp schema | wc -l` — 121.

### QA Note

This is ready for Morpheus review and then Smith HCI wording review. The remaining risk is product-facing wording around the known relationship-orientation mismatch; QA confirms examples are runtime-correct.


---


## SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md

**Original Location**: `agents/trin.docs/SPRINT_23_CYCLE_3_UAT_Summary_2026-04-12T18-32.md`


## Sprint 23 Cycle 3 UAT Summary — Diagram Fallback Preservation

**Persona**: Trin  
**Date**: 2026-04-12T18:32  
**Status**: PASS

### Verification

- Unsupported diagram-shape fallback preserves matching JSON records.
- Empty diagram fallback returns JSON with an empty result and clear note.
- Valid class diagram output remains `output_type: "diagram"`.
- Existing MCP output wrapper behavior stayed green.
- Existing structured MCP error behavior stayed green.

### Tests

- `make -f Makefile.prj test FILE=tests/unit/test_sprint23_c3.py` — 3 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint15_c3.py` — 19 passed.
- `make -f Makefile.prj test FILE=tests/unit/test_sprint22_c1.py` — 6 passed.

### QA Note

An initial parallel run of multiple Makefile test targets produced a coverage SQLite combine error after the Cycle 3 tests had passed. The Cycle 3 test file was rerun alone and passed cleanly, so this is not a product regression.


---
