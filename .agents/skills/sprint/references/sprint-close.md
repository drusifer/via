## Stage 3: Sprint Close

### Step 6a — Tank: SDLC Conformance Check
```
Tank *devops sdlc-check
```
- Rebuild from clean and confirm the project still matches `docs/SDLC.md` (full checklist in the
  `build-env` skill): manifest matches imports, documented targets exist, no installs or
  instructions that bypass `make`
- Conforms → update the "Last verified" line. Legitimate mechanism change → update the SDLC
- Runs before Oracle so any SDLC correction is included in the documentation pass

**Handoff (conforms):**
```bash
bobp chat "SDLC check passed. @Oracle *ora groom" --persona Tank --cmd "devops handoff" --to Oracle
```

**Handoff (regression):**
```bash
bobp chat "SDLC check FAILED: <drift>. @Neo *swe fix <issue>" --persona Tank --cmd "devops reject" --to Neo
```
→ fix → Tank re-checks. The sprint does not close on a failed check.

### Step 7 — Oracle: Groom
```
Oracle *ora groom
```
- Update docs, record decisions, archive sprint artifacts
- If `docs/SDLC.md` changed this sprint, apply the SDLC rubric and report its verdict line; any Weak goes back to Tank before the handoff
- If any research spikes or findings were added, apply the FINDING rubric (`agents/templates/_template_finding.md`) and report its verdict line
- If any decision records were added, apply the DECISION rubric (`agents/templates/_template_DECISION.md`) and report its verdict line
- Write new lessons from the lesson template, self-checked against the LESSON rubric
- Ensure CHAT.md is archived if over 50-100 messages (rolling `*ora archive`)
- **Per-phase report:** `bobp chat-report` splits the archived diagram into one section per phase when Mouse has posted `*phase <N>*` markers (sprint summary first, then each phase's description and its own diagram). Run it after Cypher's launch if the SDLC says so, so the report covers the whole sprint.
- **Sprint-close chat report:** write a short summary of the sprint's CHAT.md conversation, then run
  `bobp chat-report --moniker <SPRINT_MONIKER> --summary "<summary>"` (`*ora report <SPRINT_MONIKER>`).
  This archives CHAT.md + CHAT.diagram.md to `agents/chat_archive/CHAT_<SPRINT_MONIKER>.md`/`.diagram.md`
  and resets CHAT.md for the next sprint — all file I/O is handled by the command; Oracle supplies only
  the summary text. Run `bobp chat-report --combine` afterward if a consolidated `CHAT_FULL.md` is needed.

**Handoff:**
```bash
bobp chat "Docs groomed. @Smith *user test <sprint>" --persona Oracle --cmd "ora handoff" --to Smith
```

### Step 8 — Smith: End-to-End User Testing
```
Smith *user test <sprint>
Smith *user feedback
```
- Test all delivered features from the user's perspective against the sprint UAT plan (`docs/sprints/UAT_PLAN_SPRINT<N>.md`)
- Apply the UAT rubric (`agents/templates/_template_UAT_PLAN.md`) and report its verdict line (`rubric UAT: COVER=A STEPS=A FAIL=A DATA=A EVID=A`)
- Apply the LESSON rubric to each lesson Oracle added this sprint and report a verdict line per lesson; any Weak goes back to Oracle
- Apply HCI heuristics — flag rough edges, inconsistencies, confusing interfaces

**Handoff (pass):**
```bash
bobp chat "User testing passed. @all *sprint retro" --persona Smith --cmd "user approve" --to all
```

**Handoff (bug found):**
```bash
bobp chat "*user bug CMD: <cmd> | EXPECTED: <x> | ACTUAL: <y> | UX ISSUE: <z>. @Trin triage." --persona Smith --cmd "user bug" --to Trin
```
→ Trin triages → fix loop → re-test before retro

### Step 9 — All Personas: Sprint Retrospective
```
*sprint retro
```
Each persona posts their domain retrospective to CHAT.md:

| Persona | Retrospective focus |
|---------|-------------------|
| Neo | Code quality, tech debt, implementation friction |
| Trin | Test coverage, regressions caught, test suite health |
| Morpheus | Architecture decisions made, anything to revisit |
| Oracle | Documentation gaps, decisions not recorded |
| Mouse | Phase sizing, blockers, velocity |
| Cypher | Story quality, acceptance criteria accuracy |
| Smith | UX issues, HCI gaps, user feedback themes |

Output feeds Cypher's backlog before launch.

```bash
# Each persona posts:
bobp chat "<persona> retro: <findings>. Backlog items: <items>" --persona <Name> --cmd retro --to Cypher
```

### Step 10 — Cypher: Launch
```
Cypher *pm launch <sprint>
```
- Announce release
- Add retro feedback to backlog
- Update changelog
- Close sprint

**Handoff:**
```bash
bobp chat "*pm launch <sprint>. Sprint complete." --persona Cypher --cmd "pm launch" --to all
```

**Sprint is complete** when Cypher posts `*pm launch`.

---

