# Verification Plan

This plan documents the verification steps for the Victory Audit.

## Verification Steps
1. **Verify Custom Skill Triggers & Registrations**
   - Check `agents/skills/judge/SKILL.md` contains triggers `*judge "via usage"`, `*judge via usage`, and `*judge via`.
   - Check `agents/skills/via/SKILL.md` exists and contains triggers `*via`, `*via help`, and `*via query`.
   - Check symlinks in `.claude/skills/` for both `judge` and `via`.

2. **Verify Session Trace Tool**
   - Review `agents/tools/session_trace.py` implementation.
   - Verify it handles flat, nested, and MCP schemas.
   - Verify unit tests exist at `tests/unit/test_session_trace.py` and are part of the test suite.

3. **Verify Persona Instructions Optimization**
   - Inspect `agents/morpheus.docs/SKILL.md`, `agents/neo.docs/SKILL.md`, `agents/oracle.docs/SKILL.md`, and `agents/trin.docs/SKILL.md` for proper Via integration instructions.
   - Confirm instructions explicitly forbid SQLite queries and raw file-reads.

4. **Verify Walkthrough**
   - Review `.agents/worker_verification/walkthrough.md`.
   - Verify walkthrough documents query scenarios, session trace audit, and test suite verification.

5. **Verify Test Suite Greenness**
   - Audit the test execution logs in `build/build.out`.
   - Check for the total count of tests (1339 passed, 1 skipped, 4 warnings).
   - Check for hardcoded test results, facade patterns, or cheating.
