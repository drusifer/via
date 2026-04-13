# Sprint 22-24 — HCI/UX Focused Backlog

**Author**: Cypher (PM)  
**Date**: 2026-04-12  
**Theme**: Make VIA easier to understand, recover from, and use efficiently through MCP/CLI.  
**Primary Source**: `agents/smith.docs/VIA_MCP_Usability_Summary_2026-04-12T13:25.md`  
**Oracle Constraints Consulted**: `agents/oracle.docs/context.md`

---

## Product Direction

The next few sprints should focus on HCI and UX rather than adding broad query power. Smith's latest MCP testing shows VIA already has useful token-saving primitives: narrow symbol lookup, targeted raw output, relationship queries, markdown header triage, multi-type queries, and result paging.

The current product gap is not capability. It is confidence. Users cannot always tell the difference between a valid empty result, invalid syntax, unsupported query composition, or a documented pattern that does not work. The HCI focus is therefore:

1. make errors diagnostic;
2. make query semantics explicit;
3. reduce recall burden for common workflows;
4. document token-saving recipes where users already work: MCP schema, CLI help, and user guide.

The user-facing command model for documentation should be:

> The first stage defines the candidate result set: what symbols/files/headers VIA will return. Later `--via` / `--sans` stages filter that result set by requiring, or excluding, a relationship to another matched set.

This should replace "known anchor left, wildcard right" as the primary teaching model. Relationship direction still needs examples, but the first concept users should learn is result stage first, relationship stages as filters.

---

## Prior Decisions That Constrain Scope

- Relationship syntax is `--via` / `--sans`; old `-Vxxx` flags remain removed.
- `--not` negates the immediately following pattern flag only.
- Pattern matching is case-sensitive by default; `-I` is the opt-in case-insensitive path.
- `-tH` is the markdown header type flag; lowercase `-th` is invalid by design.
- `-Q` means full relative path for `-tF` and fully qualified name for symbol types.
- Error messages project-wide should state what happened, why, and valid alternatives.

---

## Sprint 22 — Query Confidence And Error Recovery

**Theme**: Stop silent empty results from masquerading as successful queries.  
**Points**: ~8pts  
**Goal**: Users and agents can distinguish valid empty results from invalid syntax, unsupported matcher combinations, and known unsupported relationship patterns.

### S22-1: Structured MCP Errors For Invalid Query Arguments (P0, 3pts)

**As an** agent using VIA MCP,  
**I want** invalid query arguments to return a structured error,  
**so that** I can correct the query instead of assuming the index is empty.

#### Background

Smith observed `["--definitely-not-a-real-flag"]` returning `result: [], total: 0, shown: 0`. That violates HCI heuristic #9: help users recognize, diagnose, and recover from errors.

#### Acceptance Criteria

- [ ] Invalid MCP query args return a structured error response, not an empty success result.
- [ ] Error response includes:
  - `output_type: "error"`
  - `error.code`, e.g. `invalid_argument`
  - `error.message` naming the bad argument
  - `error.hint` with a valid alternative or where to look
- [ ] CLI behavior remains compatible, but CLI parse errors should also avoid raw tracebacks.
- [ ] Unknown flags, malformed `--slice`, invalid relationship names, and invalid output flags are covered.
- [ ] Tests cover MCP and CLI invalid-argument paths.

#### Expected Files

- `via/mcp/server.py`
- `via/pipeline/parser.py`
- `via/__main__.py`
- `tests/unit/test_sprint22_*.py`

---

### S22-2: Define And Enforce Multi-Match Semantics (P0, 2pts)

**As a** user narrowing a query,  
**I want** multiple match flags to be either clearly supported or clearly rejected,  
**so that** I do not misread ambiguous empty results.

#### Background

Smith tested repeated and mixed matcher combinations:

```json
["-mg", "*mcp*", "-mg", "*schema*", "-tf", "-tm", "-tc"]
["-mg", "*schema*", "-mr", "^test_.*mcp", "-tf", "-tm"]
["-mg", "*schema*", "-ms", "%mcp%", "-tf", "-tm"]
```

The behavior was ambiguous. Product recommendation for Sprint 22: reject multiple match flags in one match stage until intentional AND/OR composition is designed.

#### Acceptance Criteria

- [ ] A single match stage accepts exactly one of `-mg`, `-mr`, or `-ms`.
- [ ] Repeated match flags in one stage return a structured error.
- [ ] Mixed matcher types in one stage return a structured error.
- [ ] The error message states: "Use one match flag per stage. Compose with relationship stages or rerun a narrower query."
- [ ] MCP schema and CLI help mention the one-matcher-per-stage rule.
- [ ] Documentation defines a "stage" in user terms: the first stage returns candidate results; `--via` / `--sans` introduce filter stages.
- [ ] Tests cover repeated `-mg`, mixed `-mg` + `-mr`, and valid relationship-stage queries that use separate matchers on each side.

---

### S22-3: Regex Search UX And Error Handling (P1, 1pt)

**As a** power user searching naming conventions,  
**I want** regex searches to work predictably and fail clearly,  
**so that** I can use `-mr` for precise token-saving queries.

#### Background

Smith's first report under-covered `-mr`. Follow-up review identified regex as a valuable power-user workflow for names like `^test_.*mcp` and `.*_command$`.

#### Acceptance Criteria

- [ ] MCP and CLI docs include at least one `-mr` naming-convention example.
- [ ] Invalid regex patterns return a structured error with the regex parser message.
- [ ] Valid regex searches continue to return normal results.
- [ ] Tests cover a valid regex, an invalid regex, and a regex with no matches.

---

### S22-4: Correct Or Remove Documented File `declares` Pattern (P0, 2pts)

**As a** user following project quick-reference docs,  
**I want** documented VIA MCP examples to work exactly as written,  
**so that** I can trust the tool guidance.

#### Background

`agents/PROJECT.md` recommends:

```json
["-mg", "path/to/file.py", "-tF", "-Q", "--via", "declares", "-mg", "*"]
```

Smith tested the pattern against `via/mcp/server.py` and received an empty result. If the pattern is unsupported, the doc is wrong. If it is intended, the implementation is incomplete.

#### Acceptance Criteria

- [ ] Decide implementation vs documentation correction during architecture review.
- [ ] If implemented: file-to-symbol `declares` works for Python source files and markdown headers.
- [ ] If corrected: `agents/PROJECT.md`, MCP schema examples, and user guide stop recommending unsupported syntax.
- [ ] Empty result for an unsupported `declares` composition is not allowed; users receive a structured unsupported-composition error.
- [ ] Tests cover the chosen behavior.

---

## Sprint 23 — Recognition Over Recall

**Theme**: Make common workflows visible so users do not memorize relationship direction, output flags, or token-saving sequences.  
**Points**: ~7pts  
**Goal**: A first-time user can discover common tasks from help/schema/docs without asking another agent.

### S23-1: Canned Relationship Shortcuts For Common Questions (P0, 3pts)

**As a** user asking common code-navigation questions,  
**I want** shortcut flags or canned query names for callers/callees/declared symbols,  
**so that** I do not have to remember relationship direction.

#### Acceptance Criteria

- [ ] Add a product-approved design for at least:
  - callers of symbol
  - callees from symbol
  - symbols declared in file
- [ ] Shortcuts expand into existing `--via` / `--sans` semantics; no new relationship model.
- [ ] Existing explicit relationship syntax remains supported.
- [ ] Help text explains both the shortcut and expanded equivalent.
- [ ] Tests confirm shortcuts and expanded queries return the same result sets.

---

### S23-2: Task-Oriented MCP Schema Examples (P0, 2pts)

**As an** AI agent using VIA MCP,  
**I want** the schema examples grouped by task,  
**so that** I can choose a low-token workflow without remembering flags.

#### Acceptance Criteria

- [ ] MCP description includes examples for:
  - find symbol
  - read one symbol body with `-oR`
  - find callers
  - search docs headers
  - regex naming search
  - multi-type search
  - paged broad scan
- [ ] Examples are short enough to stay useful in tool descriptions.
- [ ] Examples avoid unsupported multi-match composition.
- [ ] Tests assert key examples appear in `via mcp schema`.

---

### S23-3: Preserve Useful Data On Diagram Fallback (P1, 1pt)

**As a** user requesting `-oD`,  
**I want** non-renderable diagram responses to preserve useful query results,  
**so that** I do not have to rerun the query blindly.

#### Acceptance Criteria

- [ ] If diagram rendering cannot produce edges, the MCP response includes a clear note and fallback data.
- [ ] Fallback response keeps `output_type`, `result`, `total`, and `shown` coherent.
- [ ] Users are told whether the issue is no relationships found or unsupported diagram shape.
- [ ] Tests cover no-edge and valid-edge diagram requests.

---

### S23-4: CLI Help HCI Pass (P1, 1pt)

**As a** CLI user,  
**I want** `via --help` to expose examples and constraints without becoming bloated,  
**so that** I can self-serve common query syntax.

#### Acceptance Criteria

- [ ] Help includes concise sections for pattern flags, type flags, relationship direction, match-stage constraints, and output formats.
- [ ] Help teaches the command model: `via <result stage> [--via|--sans <relationship> <filter stage>]`.
- [ ] Relationship examples are phrased as "return X, filtered by relationship to Y" rather than "known anchor left, wildcard right."
- [ ] Help explicitly says `-tH` is uppercase and `-th` is invalid.
- [ ] Help length increases by no more than 25 lines.
- [ ] Tests assert the presence of the high-value guidance strings.

---

## Sprint 24 — UX Polish And Learning Loops

**Theme**: Close the loop between actual tool behavior, user documentation, and agent workflows.  
**Points**: ~6pts  
**Goal**: Documentation and UAT catch HCI regressions before users do.

### S24-1: End-To-End HCI UAT Suite For MCP Query Workflows (P0, 2pts)

**As Smith**,  
**I want** a repeatable UAT script for MCP query workflows,  
**so that** future regressions in usability are caught before release.

#### Acceptance Criteria

- [ ] UAT covers happy path, bad args, invalid regex, multi-match rejection, relationship shortcut, raw output, diagram fallback, and pagination.
- [ ] UAT output is readable and maps failures to HCI heuristics.
- [ ] UAT can be run through the project Makefile.

---

### S24-2: User Guide Token-Saving Recipes (P0, 2pts)

**As an** agent author or human maintainer,  
**I want** documented recipes for low-token VIA usage,  
**so that** I can use the tool effectively without reverse-engineering examples.

#### Acceptance Criteria

- [ ] `docs/USER_GUIDE.md` gains a "Token-Saving Query Recipes" section.
- [ ] Recipes include symbol lookup, raw body fetch, callers, docs headers, regex search, multi-type query, and paged scan.
- [ ] Each recipe states when not to use it.
- [ ] Recipes match MCP schema examples.

---

### S24-3: Error Message Style Guide And Regression Tests (P1, 1pt)

**As a** maintainer,  
**I want** a small style guide for VIA user-facing errors,  
**so that** future errors stay actionable and consistent.

#### Acceptance Criteria

- [ ] Document standard shape: what happened, why, valid alternatives.
- [ ] Include MCP and CLI examples.
- [ ] Add regression tests for at least five representative error messages.

---

### S24-4: UX Debt Closeout Review (P1, 1pt)

**As a** product team,  
**I want** Smith and Trin to review remaining UX debt after S22-S24,  
**so that** we intentionally decide what to fix next.

#### Acceptance Criteria

- [ ] Smith writes a post-sprint UX review.
- [ ] Trin confirms correctness coverage for UX-critical paths.
- [ ] Cypher updates the backlog with explicit keep/defer/drop decisions.

---

## Recommended Sequence

1. **Sprint 22 first** because silent empty results break trust and make every other feature harder to use.
2. **Sprint 23 second** because shortcut and example work depends on clear semantics from Sprint 22.
3. **Sprint 24 third** because documentation and UAT should lock in the improved behavior after the interface stabilizes.

---

## Gate Handoff

@Smith: Please review this HCI/UX sprint batch before it proceeds to Morpheus. Pay special attention to whether Sprint 22 is narrow enough and whether Sprint 23 shortcut wording matches actual user mental models.
