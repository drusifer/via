# Artifact Templates and Checks

This catalog identifies the canonical template, author, and review/check owner for project artifacts.
Template source lives in `bobp/templates/agents/templates/`; installed or dogfooding copies live in
`agents/templates/`. Changes to a template must update both copies together.

## Artifact Catalog

| Artifact | Template | Owner | Check / reviewer |
|---|---|---|---|
| Architecture/design proposal | `_template_ARCH.md` | Morpheus | ARCH / Smith at planning gate |
| Decision record (ADR) | `_template_DECISION.md` | Morpheus / Oracle | DECISION / Oracle or Smith |
| Domain model | `_template_DOMAIN.md` | Cypher / Morpheus | DOMAIN / planning review |
| Research finding or spike | `_template_finding.md` | Any | FINDING / Oracle or Morpheus |
| Security review | `_template_SECURITY_REVIEW.md` | Switch | SECURITY REVIEW / Switch, reviewed by Trin or Morpheus |
| Security finding | `_template_SECURITY_FINDING.md` | Switch | SECURITY FINDING / Switch, reviewed by Trin or Morpheus |
| Lesson | `_template_LESSON.md` | Oracle | LESSON / Smith at sprint close |
| SDLC guide | `_template_SDLC.md` and language profiles | Tank | SDLC / Oracle when changed |
| Sprint task board | `_template_task.md` | Mouse | PLAN / Morpheus at plan review |
| Quality and test strategy | `_template_TEST_STRATEGY.md` | Trin | STRATEGY / Morpheus and Smith |
| UAT plan and results | `_template_UAT_PLAN.md` | Trin | UAT / Smith or Morpheus |
| User stories | `_template_USER_STORIES.md` | Cypher | STORIES / Smith at planning gate |
| Persona skill | `_template_PERSONA_SKILL.md` | Bob | PERSONA / Bob at creation or material revision |
| Agent working memory | `_template_state.md` | Each persona | STATE / mechanical handoff check |
| Chat instructions | `_template_CHAT.md` | All | CHAT / `bobp chat` format check |
| TLDR summaries | `_template_tldr.md` | All | TLDR / `bobp tldr` visibility check |
| This catalog | `ARTIFACTS.md` | Bob | CATALOG / template inventory check |

Loop effectiveness rubrics are defined by their owning workflow skills. They evaluate execution,
not the content of these artifact templates.

## Check Convention

Every template ends with a check that applies to the finished artifact. Checks use binary results:
`PASS` when the stated evidence is present and consistent; otherwise `FAIL`, with the missing or
contradictory evidence and the smallest correction named. Use `N/A` only when the criterion truly
does not apply, and state why. A check must be specific enough that two reviewers can reach the
same result from the artifact and linked evidence.

For a checklist, every required item must pass. Remove template checks when creating a real artifact;
keep the check instructions here and in the template. Workflow, ownership, and lifecycle instructions
belong in the relevant skill and should be linked rather than copied into every artifact.

<!-- RUBRIC-START -->
## Check — CATALOG

- [ ] **PASS** — Every file in `agents/templates/` is listed here with its purpose and applicable check.
- [ ] **PASS** — Each listed packaged template exists in `bobp/templates/agents/templates/` and matches its live counterpart.
- [ ] **PASS** — Every content template has a named human or mechanical reviewer/check in this catalog.
- [ ] **FAIL** — A template is missing, unlisted, out of sync, or has no usable check; update the catalog and both copies.
<!-- RUBRIC-END -->
