# Handoff Report — Smith closed-loop judge workflow Step 2

## 1. Observation
- Gauntlet trace log records the execution of 14 query scenarios, where Scenarios 3, 7, and 14 returned `(empty output)`.
- Verbatim trace log snippet showing Scenario 3:
  ```
  --- Scenario 3: File Exclusions ---
  Intended Question: What functions are in via/core/ but not in test files?
  Command: via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5
  Exit Status: SUCCESS (exit 0)
  Output:
  (empty output)
  ```
- Verbatim trace log snippet showing Scenario 7:
  ```
  --- Scenario 7: Import Check ---
  Intended Question: Which files import sqlite3?
  Command: via -mg '*' -tF --via imports -mg 'sqlite3' -ti
  Exit Status: SUCCESS (exit 0)
  Output:
  (empty output)
  ```
- Verbatim trace log snippet showing Scenario 14:
  ```
  --- Scenario 14: Test Coverage Mapping ---
  Intended Question: What tests cover or reference code in via/pipeline/executor.py?
  Command: via -mg '*' -tF --via imports -mg '*executor*' -tF -Q
  Exit Status: SUCCESS (exit 0)
  Output:
  (empty output)
  ```

## 2. Logic Chain
- **BUG-1**: qualified_name of class and function symbols is stored as absolute (e.g. starting with `.home.drusifer...`) because `_calculate_qualified_name` is passed the absolute `file_info.path` instead of relative path during indexing. Also, inversion logic overrides in `_get_actual_inverted` map types/joins incorrectly for declares relationships. This causes Scenario 3 to fail and return an empty output.
- **BUG-2**: The query engine fails to resolve file-level imports (`-tF --via imports -mg 'sqlite3' -ti`) and file-to-file imports (`-tF --via imports -mg '*executor*' -tF -Q`) because external module symbols are stored with `file_path = '<external>'` and lack `declares` relationships in the database, causing the `declares` join constraint to fail on the filter side of imports queries. This causes Scenarios 7 and 14 to fail and return empty outputs.
- **TES Score Calculation**: Since Scenarios 3, 7, and 14 failed to return correct answers (returned empty), 3 correctness failures occurred. With a penalty of -5 points per correctness failure (-15 points total) and no fallback penalties or efficiency bonuses, the final TES is 100 - 15 = 85.
- **Handoff Decision**: Since the TES score is 85 (< 90 target) and query engine bugs exist, the closed-loop judge workflow dictates handing off to Neo (`*swe fix judge`) to resolve the parser and query engine defects.

## 3. Caveats
- No caveats. The codebase details match the bug descriptions exactly.

## 4. Conclusion
- The final TES is **85 / 100**.
- The closed-loop judge workflow is routed to **Neo** (`*swe fix judge`) to fix BUG-1 and BUG-2.
- Smith's context, current task, and next steps state files have been updated to reflect the 2026-06-20 evaluation session.

## 5. Verification Method
- **Command to run**: `make test` to verify the synthetic codebase test suite continues to pass.
- **Files to inspect**: 
  - `agents/smith.docs/bugs.md` for the bug catalog.
  - `agents/smith.docs/trace_eval.md` for the scoring breakdown.
  - `agents/smith.docs/TraceEval_Summary_2026-06-20.md` for the task summary.
  - `agents/smith.docs/context.md`, `current_task.md`, and `next_steps.md` for Smith's state.
  - `agents/CHAT.md` for the handoff message to Neo.
