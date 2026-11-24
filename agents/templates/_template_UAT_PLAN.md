<!--
UAT plan for specific acceptance scenarios and observed results. Owned by Trin; see the UAT and
sprint skills for workflow and handoffs. Remove this note and the check block when instantiated.
-->
# UAT Plan: {Feature or Sprint}

- **Stories / criteria:** {IDs and links}
- **Environment and build:** {version, URL/device, build or commit as useful}
- **Date / tester:** {date and persona}
- **Entry conditions:** {deployed build, test account/data, required approvals}
- **Exit conditions:** {acceptance criteria pass; unresolved issues listed}

## Scenarios

Create one case for each important acceptance outcome. Use commands for scripted checks and a task
prompt for participant usability sessions; record what actually happened rather than assuming success.

### UAT-{ID}: {User goal and scenario}

- **Linked criterion:** {story and acceptance criterion}
- **User / task:** {target user and task prompt, or omit for scripted check}
- **Preconditions and data:** {state, account, fixture; use isolated/non-production data}
- **Steps:** {numbered actions or exact command; omit unsafe/destructive production actions}
- **Expected observable outcome:** {behavior, message, output, and relevant state change}
- **Actual outcome:** {what occurred}
- **Verdict:** {PASS | FAIL | BLOCKED}
- **Evidence / issue:** {brief observation, screenshot/log reference, or issue ID}

{Repeat the same case shape as needed. Include negative paths when the feature accepts input or can reject an action.}

## Results and Handoff

- **Passed / failed / blocked:** {counts and case IDs}
- **Open issues and impact:** {issue IDs, severity if project defines it, owner}
- **Overall verdict:** {PASS | FAIL | BLOCKED, with reason}
- **Handoff evidence:** {review message or report link}

<!-- RUBRIC-START -->
## Check — UAT

- [ ] **PASS** — Every in-scope acceptance criterion links to at least one scenario with explicit preconditions, steps/task, and an observable expected outcome.
- [ ] **PASS** — Each executed scenario records its actual outcome, PASS/FAIL/BLOCKED verdict, and evidence or issue reference.
- [ ] **PASS** — Input/rejection paths are covered when applicable; test data and environment avoid unintended production or user-data changes.
- [ ] **PASS** — Overall verdict follows the recorded cases, and unresolved failures/blockers are named with impact and owner.
- [ ] **FAIL** — Coverage, reproducibility, evidence, or verdict consistency is missing; add the specific case or result needed to resolve it.
<!-- RUBRIC-END -->
