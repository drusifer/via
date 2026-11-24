<!--
Sprint stories template. Owned by Cypher — see .agents/skills/cypher/SKILL.md and the sprint skill.
Copy to docs/sprints/USER_STORIES_SPRINT<N>.md and replace every {placeholder}.
{KEY} is the project's short story-ID key (for example STORY-FING-31 in a project called Fingerling).
Remove this note and the check block when creating a real artifact; checks belong to templates.
Morpheus appends the architecture section after Smith approves the stories.
-->
# Sprint {N} User Stories: {Short Title}

*   **Planning Size** (optional): {points or omit}
*   **Branch**: `sprint-{N}`
*   **Source**: {who asked, when, and where it is recorded}
*   **Status**: Draft — awaiting Smith Gate 1

## Goal

{Two to four sentences: what will be true for a user or the owner when this sprint is done, and
why it matters now. No implementation.}

## Assumptions made for the owner

{Anything decided on the owner's behalf because they did not say. Each one a sentence the owner
can confirm or overturn.} / None — every choice here was the owner's.

---

## STORY-{KEY}-{id}: {Outcome in a few words}
{Optional: **Points:** {n} · **Owner:** {persona}}

**As a** {who benefits},
**I want** {what they will be able to do},
**so that** {why it matters to them}.

### Acceptance Criteria
1. {One observable behaviour, stated so that a tester could say yes or no.}
2. {Failure or rejection behavior when relevant; omit if the story cannot fail or reject input.}
3. {...}

{Repeat the story block for each story.}

---

## Out of Scope
- {Something a reader might reasonably expect to be included, and is not.}

## Open Questions
1. {A question, who can answer it, and what is assumed until they do.} / None.

<!-- RUBRIC-START -->
## Check — STORIES

- [ ] **PASS** — `OUT` (Does each story say who benefits and what they can do afterwards?): Every story has a real beneficiary and an outcome they would recognise.
- [ ] **PASS** — `TEST` (Could a tester answer yes or no to every acceptance criterion?): Each criterion is one observable behaviour with a definite pass condition.
- [ ] **PASS** — `FAIL` (Do the criteria say what the user sees when things go wrong? Report `n/a` for a story that takes no input and cannot be refused.): Each story includes a failure outcome when failure or rejection is a meaningful user-visible behavior; otherwise mark N/A with a reason.
- [ ] **PASS** — `SCOPE` (Is it clear what is not being done, and what was assumed?): Out-of-scope lists what a reader might expect and will not get; assumptions and open questions are stated separately.
- [ ] **PASS** — `SIZE` (Can each story be delivered and verified on its own?): Each story has a bounded outcome that can be accepted independently, or its dependency is stated.
- [ ] **PASS** — `DESIGN` (Do the criteria leave the design to the architecture step?): Criteria describe behaviour; any named technology is something the user or owner explicitly asked for.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
