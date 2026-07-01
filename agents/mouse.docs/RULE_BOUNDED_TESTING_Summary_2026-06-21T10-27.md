# Task Summary: Bounded Testing Instruction Rule

**Scrum Master**: Mouse  
**Date**: 2026-06-21  
**Task**: Add a project-wide instruction rule to prevent redundant testing execution.

---

## 1. Action Taken
- Received user request to enforce a rule preventing redundant test execution to save tokens and context space.
- Added **Bounded Testing (CRITICAL)** rule under the **Operational Guidelines** section in:
  - [AGENTS.md](file:///home/drusifer/Projects/via/AGENTS.md) (Workspace root rule file)
  - [agents/AGENTS.md](file:///home/drusifer/Projects/via/agents/AGENTS.md) (Agent folder rule file)
  - [GEMINI.md](file:///home/drusifer/Projects/via/GEMINI.md) (Workspace root Gemini rule file)

---

## 2. Rule Details
```markdown
2. **Bounded Testing (CRITICAL)**: **Do not run tests for code that has not changed since the last run.**
   - ❌ Never execute full test suites (`make test`) repeatedly without making code modifications.
   - ✅ Only run tests to validate recent code changes or bug fixes.
   - 📋 Use the task board (`task.md`) and persona state files for tracking sprint/task progress instead of triggering test suite execution.
```

---

## 3. Next Steps
- Enforce the Bounded Testing guideline for all team members (Neo, Trin, Morpheus, etc.) in subsequent cycles.
- Use `task.md` status checks for verifying Cycle 2 progress instead of executing pytest.
