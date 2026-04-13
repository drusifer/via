# Sprint 23 User Stories — Recognition Over Recall

**Author**: Cypher  
**Date**: 2026-04-12  
**Theme**: Recognition over recall for common VIA query workflows  
**Source Backlog**: `agents/cypher.docs/SPRINT_22_24_HCI_UX_USER_STORIES.md`  
**Sprint 22 Closeout**: `agents/mouse.docs/SPRINT_22_CLOSEOUT.md`

---

## Sprint Goal

Make common VIA workflows discoverable without requiring users or agents to memorize relationship direction, output flags, or multi-step token-saving sequences.

Sprint 22 stabilized the command model:

```text
via <result stage> [--via|--sans REL <filter stage>]
```

Sprint 23 should build recognition affordances on top of that model. Shortcuts and examples must be transparent: users should be able to see the ordinary VIA query they expand to.

---

## Product Constraints

- Do not introduce a new relationship model.
- Do not hide semantics behind magic behavior.
- Shortcuts must expand into existing parser/executor paths where possible.
- Existing explicit `--via` / `--sans` syntax remains supported.
- Documentation must keep the result-stage-first model as the primary teaching model.
- If "symbols declared in file" needs special handling, it must be named as a task-language shortcut and not documented as ordinary inverse `declares` behavior.

---

## S23-1: Task-Language Shortcuts For Common Relationship Questions

**Priority**: P0  
**Estimate**: 3 pts  

**As a** user asking common code-navigation questions,  
**I want** task-language shortcuts for callers, callees, and symbols declared in a file,  
**so that** I do not have to remember relationship direction.

### Required Shortcut Concepts

The final syntax is a Morpheus architecture decision, but the product vocabulary is:

- `callers`: return functions/methods that call a named symbol.
- `callees`: return symbols called by a named function/method.
- `declared-in-file`: return symbols declared in a named file.

### Acceptance Criteria

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

## S23-2: Task-Oriented MCP Schema Examples

**Priority**: P0  
**Estimate**: 2 pts  

**As an** AI agent using VIA MCP,  
**I want** schema examples grouped by task,  
**so that** I can choose a low-token workflow without remembering flags.

### Acceptance Criteria

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

## S23-3: Preserve Useful Data On Diagram Fallback

**Priority**: P1  
**Estimate**: 1 pt  

**As a** user requesting diagram output,  
**I want** non-renderable diagram responses to preserve useful query results,  
**so that** I do not have to rerun the query blindly.

### Acceptance Criteria

- [ ] If `-oD` cannot produce edges, the MCP response includes a clear `note`.
- [ ] Fallback response keeps `output_type`, `result`, `total`, and `shown` coherent.
- [ ] The note distinguishes:
  - no relationships found
  - unsupported diagram shape
- [ ] If useful non-diagram query results exist, they remain available in `result`.
- [ ] Tests cover no-edge and valid-edge diagram requests.

---

## S23-4: CLI Help HCI Pass

**Priority**: P1  
**Estimate**: 1 pt  

**As a** CLI user,  
**I want** `via --help` to expose common tasks and constraints without becoming bloated,  
**so that** I can self-serve common syntax.

### Acceptance Criteria

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

## Definition Of Done

- [ ] Smith approves the Sprint 23 user stories.
- [ ] Morpheus approves architecture without adding a new relationship model.
- [ ] Mouse breaks work into short cycles with one HCI surface per cycle where possible.
- [ ] Shortcuts and examples are discoverable from MCP schema and CLI help.
- [ ] Unsupported shortcut behavior is explicit, structured, and recoverable.

---

## Gate Handoff

@Smith: Please review Sprint 23 stories for HCI fit. Focus on whether the shortcut vocabulary is user-facing enough and whether the scope avoids creating hidden semantics.
