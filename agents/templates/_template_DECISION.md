<!--
Architecture Decision Record (ADR) template. Based on the Markdown Architectural Decision Records (MADR) standard.
Owned by Oracle (recording) and Morpheus (deciding) — see .agents/skills/oracle/SKILL.md and .agents/skills/morpheus/SKILL.md.
Instantiated in `docs/DECISIONS.md` or `docs/decisions/ADR-{NNNN}-{title}.md`.
Remove this note and the check block when creating a real artifact; checks belong to templates.
Oracle reviews this at groom (or Smith at Gate 2) using the DECISION rubric.
-->
# ADR-{NNNN}: {Short Title of Decision}

*   **Status**: {Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-{NNNN}}
*   **Deciders**: {Morpheus, Cypher, Smith, etc.}
*   **Date**: {YYYY-MM-DD}
*   **Consulted** (optional): {People or roles, or omit}
*   **Related** (optional): `{story, finding, or ADR links}`

---

## 1. Context and Problem Statement

{What is the context and architectural challenge being addressed? What forces are pushing us in certain directions (functional, non-functional, business, UX constraints)?}

## 2. Decision Drivers

* {Driver 1: e.g., Must maintain sub-50ms query response time}
* {Driver 2: e.g., Must avoid introducing external C-extensions to preserve portability}
* {Driver 3: e.g., Must comply with docs/SDLC.md build and packaging constraints}

## 3. Considered Options (when alternatives exist)

| Option | Benefits | Costs / risks | Reason selected or rejected |
|---|---|---|---|
| `{Option}` | {Evidence or benefit} | {Cost or risk} | {Relationship to decision drivers} |

## 4. Decision Outcome & Justification

* **Chosen Option:** **{Option X}**
* **Justification:** {Why this option best satisfies the decision drivers; link supporting evidence where available.}

### Consequences
- **Expected benefit:** {What improves}
- **Costs or risks:** {What becomes harder or remains unresolved, and mitigation if needed}

The option table records comparative trade-offs; use this section only for consequences of the chosen decision.

<!-- RUBRIC-START -->
## Check — DECISION

- [ ] **PASS** — `WHY` (Does it state the context, problem, and decision drivers?): States architectural context, problem statement, and concrete decision drivers (forces, constraints, requirements).
- [ ] **PASS** — `OPTS` (Were genuine alternative options evaluated?): Details at least two viable options (including "do nothing" if applicable) with balanced pros and cons.
- [ ] **PASS** — `CONS` (Are trade-offs, consequences, and technical debt acknowledged?): Documents both positive outcomes (what is gained) and negative consequences (what is lost, technical debt accepted).
- [ ] **PASS** — `STATE` (Is the lifecycle state and relationship to other decisions clear?): Has a clear status (Proposed, Accepted, Deprecated, Superseded) and date; links to decisions it supersedes or depends on when applicable. If there are no related decisions, omitting the optional Related field or stating "None" is valid.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
