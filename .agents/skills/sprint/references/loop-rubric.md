## Loop Effectiveness Rubric (`LOOP_SPRINT`)

Reviewed by Morpheus (at Step 3a Plan Review) or Smith/Oracle (at Sprint Close) or during `*judge sprint`.  
Verdict line in `agents/CHAT.md`: `rubric LOOP_SPRINT: SDLC=L DECOMP=L GATES=L CADENCE=L RETRO=L`

| Code | Criterion | Weak (W) | Acceptable (A) | Strong (S) |
|---|---|---|---|---|
| `SDLC` | **SDLC Governance** | Proceeded without `docs/SDLC.md`; ignored project build rules, linters, or git workflow conventions; skipped close audit. | Stage 0 SDLC gate verified before planning; drift check executed at sprint close by Tank. | 100% adherence to documented SDLC tooling and quality gates; proactive updates proposed to SDLC if tooling evolved. |
| `DECOMP` | **Work-Loop Decomposition** | Task board contains vague, unstructured notes or giant multi-day lumps; tasks do not specify work-loop type (`*impl`, `*fix`, etc.). | Mouse structured `task.md` into phased tasks, each explicitly mapped to a typed Work Loop with clear dependencies. | Bounded phases (1-3 tasks each); typed loops assigned to specialist personas; clear acceptance references; passes PLAN rubric. |
| `GATES` | **Gate & Rubric Enforcement** | Gates rubber-stamped without rubric verdicts; Weak findings ignored; handoffs proceeded despite unapproved gates. | Smith, Switch, and Morpheus posted explicit verdict lines (`rubric STORIES:...`, `security gate:...`); rejections required fixes before approval. | Thorough, formative critique on every gate; concrete tells identified; clean progression from rejection to revision to approval. |
| `CADENCE` | **Cadence & Context Budget** | Personas hopped erratically across tasks; context bloated past 70-80% without checkpoints; unlogged handoffs. | Sequential execution of task board; state files updated; `*prep-clear` run before clearing when context exceeded 60%. | Smooth, rhythmic handoffs in CHAT.md; zero lost context across clear boundaries; anti-loop guard protected against thrashing. |
| `RETRO` | **Knowledge & Retro Harvest** | Sprint ended without retro; lessons lost; CHAT.md ungroomed; changelog unmaintained. | Tank verified SDLC; Oracle groomed docs and archived chat; team held retrospective feeding backlog; Cypher launched. | Rich engineering lessons logged in `docs/LESSONS.md`; meaningful retrospective insights; comprehensive release notes published. |
