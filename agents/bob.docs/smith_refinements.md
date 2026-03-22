# Smith Persona — Refinement Suggestions from Each Persona

After reading `agents/smith.docs/SKILL.md`, here's what each persona flagged:

---

## From Cypher (PM)
Smith's story review is clear. One addition: **Smith should be able to co-author acceptance criteria** when a story's user perspective is unclear. If Cypher writes a story and the "what does done look like to a user?" is ambiguous, Smith should be able to add or amend the acceptance criteria directly (not just approve/reject).
- **Suggested command**: `*user story <criteria>` — append user-perspective acceptance criteria to a story.

---

## From Morpheus (Tech Lead)
The `*user feedback` command is good for full gate reviews, but Morpheus needs something lighter for quick async questions during architecture. "Is this flag name confusing?" or "Should this default to table or list?" doesn't need a full review cycle.
- **Suggested command**: `*user consult <question>` — quick, non-blocking UX input on an open question. No approve/reject — just an opinion.

---

## From Neo (SWE)
Smith's `*user test` is only mentioned at the gate level. Neo wants to be able to invoke it **mid-phase** during implementation — "I just wired up the new flag, can Smith do a quick sanity check before I write all the tests?"
- **Clarification needed**: Explicitly state in SKILL.md that `*user test` is available at any time (not just sprint gates), and that Neo can invoke it directly with `@Smith *user test <feature>`.

---

## From Trin (QA)
The boundary between Smith's usability testing and Trin's correctness testing is undefined. Trin catches bugs; Smith catches UX issues — but what happens when Smith finds a defect?
- **Suggested command**: `*user bug <description>` — Smith files a usability defect. This goes to Trin to triage (correctness issue → Neo; UX issue → Neo with Trin verification).
- **Routing rule**: Smith's `*user bug` always routes through Trin, not directly to Neo.

---

## From Mouse (Scrum Master)
Sprint gates can become bottlenecks. Mouse needs `*user reject` to always include:
1. The specific blocking reason
2. What would need to change for approval
- **Required format for `*user reject`**: `*user reject REASON: <what's wrong> | FIX: <what's needed>`
- Also: if Smith cannot review within a sprint cycle, Smith must post `*user blocked <reason>` so Mouse can flag it and escalate.

---

## From Oracle (Knowledge Officer)
Smith's `*user research` sessions will produce valuable domain knowledge that must be preserved. Currently the SKILL.md doesn't mandate recording research findings.
- **Required exit step for `*user research`**: After completing research, Smith must call `@Oracle *ora record <findings>` before posting results to CHAT.md.
- Oracle will index these under `docs/DOMAIN.md` or equivalent.

---

## From Bob (Prompt Engineer)
Summary of all suggested additions to `agents/smith.docs/SKILL.md`:

| New/Changed | Details |
|-------------|---------|
| `*user consult <question>` | Lightweight async UX opinion — no gate, just input for Morpheus |
| `*user story <criteria>` | Co-author user-perspective acceptance criteria with Cypher |
| `*user bug <description>` | File a usability defect — routed through Trin for triage |
| `*user test` availability | Explicitly available mid-phase (not just at gates) — any persona can invoke |
| `*user reject` format | Must include `REASON:` and `FIX:` fields |
| `*user blocked <reason>` | Signal when Smith cannot complete a gate in time |
| `*user research` exit | Mandatory `@Oracle *ora record` before posting findings |
