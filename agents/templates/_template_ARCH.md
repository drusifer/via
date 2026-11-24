<!--
Architecture document template. Owned by Morpheus — see .agents/skills/morpheus/SKILL.md and the sprint skill.
Can be instantiated as `docs/ARCH.md` (standing project architecture) or appended to the sprint
stories document during Sprint Planning Step 2.
Remove this note and the check block when creating a real artifact; checks belong to templates.
Smith reviews this at Gate 2 using the ARCH rubric.
-->
# Architecture Document: {System or Feature Name}

*   **Status**: Draft — awaiting Smith Gate 2
*   **Author**: Morpheus
*   **Last Updated**: {YYYY-MM-DD}
*   **Scope**: {Project-wide ARCH.md | Sprint {N} Architecture}

---

## 1. Executive Summary & System Overview

{State the design scope, key drivers, and intended outcome. Include goals and non-goals when they clarify boundaries.}

## 2. System Context & Boundaries

{Describe the system boundary: who interacts with it (users, external services, upstream/downstream pipelines), network boundaries, and trust domains.}

{Optional: add a context diagram when it clarifies actors, dependencies, or trust boundaries. A short description is sufficient for a small change.}

## 3. Component & Container Architecture

{Decompose the system into cohesive components or containers. Describe the single responsibility of each block.}

{Optional: show containers or components at the level needed to explain the design. Do not add lower-level diagrams without a decision they help explain.}

### Component Inventory
| Component | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `{Component A}` | {Single clear responsibility} | {Call / Event / Data} | {Response / State change} |
| `{Component B}` | {Single clear responsibility} | {Call / Event / Data} | {Response / State change} |

## 4. Runtime Interaction & Critical Flows

{Describe the important user or system flows that change state or cross boundaries. Use a sequence diagram only when it is clearer than concise steps.}

{Optional example: describe one critical flow as ordered steps with actor, action, and result.}

## 5. Interface & Contract Specifications

{Define observable interfaces: CLI commands, flags, exit codes, API endpoints, schemas, or key data structures.}

* **Command / Endpoint:** `{command name or route}`
* **Parameters / Flags:**
  * `--{flag}`: {Type, default, validation constraints}
* **Output Format:** {JSON schema, stdout table, exit codes on success/failure}

## 6. Cross-Cutting Concepts & Resilience

### Failure Modes & Error Handling (when relevant)
| Failure Mode | Trigger / Condition | System Behavior | User / Client Impact | Blast Radius |
|---|---|---|---|---|
| `{Dependency Timeout}` | {Network partition or slow remote} | {Timeout after Ns, retry with backoff, abort} | {Clear error message, exit code X} | {Isolated to calling command} |
| `{Invalid Input}` | {Malformed file or invalid flag} | {Validation fails before execution} | {Helpful fix suggestion, state unmodified} | {None (zero state change)} |

### Security & Privacy (when relevant)
* **Trust / access boundaries:** {Relevant controls or None — reason}.
* **Sensitive data:** {Relevant handling or None — reason}.

## 7. Technical Stack & SDLC / Build Impact

* **Languages & Runtime:** `{e.g. Python 3.13, Node 20}`
* **Core Libraries & Tools:** `{e.g. pytest, pydantic}`
* **Build-Environment Check (CRITICAL):**
  * Does this design add a new language, package manager, runtime version, or external tool? **{Yes | No}**
  * *If Yes:* Explicitly flag for Mouse to schedule a **Tank Phase 0** (`*devops bootstrap` or `*devops sdlc`) before implementation.
  * All dependencies follow `docs/SDLC.md` change classes.

## 8. Architectural Decisions (ADRs) & Technical Debt

### Decision Records
* `{ADR-001}`: {Short title and decision outcome — link to record}

### Acknowledged Technical Debt & Trade-offs
* `{Debt Item}`: {What compromise was made, why it was accepted now, and when it will be repaid}

<!-- RUBRIC-START -->
## Check — ARCH

- [ ] **PASS** — `BOUND` (Does it clearly delimit system boundaries and responsibilities?): System boundary is explicit; each component has a single responsibility; external systems and communication protocols are identified.
- [ ] **PASS** — `FLOW` (Can an engineer trace data and execution through critical paths?): Important state-changing or boundary-crossing flows are described as concise steps or diagrams; irrelevant flows are marked N/A with a reason.
- [ ] **PASS** — `FAIL` (Does it define behavior when dependencies fail or input is invalid?): Identifies relevant failure modes and their behavior, or marks the section N/A with a reason when the design adds no failure-sensitive behavior.
- [ ] **PASS** — `USER` (Does it preserve HCI standards and protect the user mental model?): The design identifies user-visible interfaces and their observable behavior; user-facing changes have a linked acceptance criterion or review.
- [ ] **PASS** — `DECS` (Are technical choices defended with context and tradeoffs?): Explains consequential choices against their drivers and links an ADR or alternative when needed; otherwise records N/A with a reason.
- [ ] **PASS** — `FEAS` (Does it account for build-environment and operational feasibility?): All dependencies adhere to SDLC change classes; flags any new runtime, language, or package manager as a Tank Phase 0.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
