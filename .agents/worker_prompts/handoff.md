# Handoff Report — Persona Prompt Optimization

## 1. Observation
- The specialist persona files (`agents/morpheus.docs/SKILL.md`, `agents/neo.docs/SKILL.md`, `agents/oracle.docs/SKILL.md`, and `agents/trin.docs/SKILL.md`) had redundant, verbose `## Via Integration` and `### Relationship Queries` sections containing syntax rules and query tables.
- Running `make test` initially failed with exit code 2:
  ```
  FAILED tests/unit/test_session_trace.py::test_parse_line_nested_format - Asse...
  ====== 1 failed, 1338 passed, 1 skipped, 4 warnings in 143.52s (0:02:23) =======
  ```
- The code block in `agents/tools/session_trace.py` lines 134-140 had a bug where boolean or-evaluation overrode the exit status `0` as falsy, resulting in status defaulting to `None`/`UNKNOWN`:
  ```python
  status_raw = data["response"].get("status") or data["response"].get("success") or data["response"].get("exit_code")
  ```
- Running `python agents/tools/setup_agent_links.py` completed with exit code 0.

## 2. Logic Chain
- To keep prompt templates DRY, the redundant `via` syntax tables and instructions in the four persona files were replaced with a unified reference block directing personas to the universal `via` skill file `agents/skills/via/SKILL.md`.
- To prevent database corruption and incorrect query strategies, the replacement block explicitly forbids direct SQLite DB queries on `.via/index.db` and forbids raw file reads (like `view_file` or `cat`) when `via` queries can retrieve the same information.
- The unit test failure in `test_session_trace.py` was traced to the boolean short-circuit `or` check in `session_trace.py`. By refactoring the logic to explicitly check key presence in the response/root dictionaries (`if key in resp:`), the exit code `0` is correctly parsed as `SUCCESS`.
- Running the full test suite after the fix verified that all 1339 tests now pass without regressions.

## 3. Caveats
- No caveats. The prompt updates follow the specified format perfectly, and the bug fix directly targets and resolves the only failing test in the suite.

## 4. Conclusion
- The persona prompt optimization has been successfully implemented across all four target files.
- The `session_trace` status parsing bug has been fixed.
- All discovery links have been refreshed via `setup_agent_links.py`, and the main test suite runs successfully with 100% pass rate.

## 5. Verification Method
- **Command**: Run the project test suite:
  ```bash
  make test
  ```
  Verify that all tests pass.
- **Files to Inspect**:
  - `agents/morpheus.docs/SKILL.md` (lines 131+)
  - `agents/neo.docs/SKILL.md` (lines 134+)
  - `agents/oracle.docs/SKILL.md` (lines 169+)
  - `agents/trin.docs/SKILL.md` (lines 151+)
  - `agents/tools/session_trace.py` (lines 134-149)
