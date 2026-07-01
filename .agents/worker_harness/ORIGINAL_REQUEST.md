## 2026-06-19T20:16:21Z
Implement a standalone evaluation script at `/home/drusifer/Projects/via/scripts/via_eval.py` that runs the 14 gauntlet scenarios against the `via` command-line tool.
The script must run `via index .` to build/refresh the database first.
For each of the 14 scenarios, execute the correct `via` CLI command (using the corrected commands based on the inverted relationship and import bug fixes identified in `/home/drusifer/Projects/via/.agents/explorer_exploration/handoff.md`):
- Scenario 1 (Simple Class Lookup): `via -mg PipelineParser -tc`
- Scenario 2 (Inverse Relationships): `via -mg '*' -tc --via inherits-from -mg 'ParserABC' -tc`
- Scenario 3 (File Exclusions): `via -mg '*' -tf --via declared-in -mg 'via/core/*' -tF -Q --sans declared-in -mg '*test*' -tF`
- Scenario 4 (Negative Relationships): `via -mg '*' -tc --sans declares -mg '*' -tm`
- Scenario 5 (SQL Pattern Match): `via -ms '%reindex%' -I`
- Scenario 6 (Direct SQLite Query): Run SQLite query `SELECT COUNT(*) FROM symbols;` on `.via/index.db`
- Scenario 7 (Import Check): `via -mg '*' -tF --via imports -mg 'sqlite3'`
- Scenario 8 (Markdown Header Search): `via -mg '*' -tH --via declared-in -mg '*USER_GUIDE.md' -tF`
- Scenario 9 (Line Slicing): `via -mg '*/executor.py' -tF -Q -mL '50:70' -oR`
- Scenario 10 (Complex Multi-Filter): `via -mg 'parse' -tm --via declared-in -mg 'PythonParser' -tc`
- Scenario 11 (Call Sites): `via -mg '*' -tm --via calls -mg 'connect' -tm`
- Scenario 12 (Declaration Site): `via -mg 'PipelineParseError' -tc`
- Scenario 13 (Type Hierarchy Expansion): `via -mg '*' -tc --via inherits-from -mg 'ParserABC' -tc -oD`
- Scenario 14 (Test Coverage Mapping): `via -mg '*' -tF --via imports -mg '*via.pipeline.executor*'`

Audit the execution trace and efficiency of each query:
- Check that the command succeeded (exit code 0) and didn't crash.
- Verify that output contains the expected results and doesn't fall back to empty or missing data (which would force user/agent fallback to raw file reading or pattern grepping).
- Document any specific fallback check or db hit count check you perform to audit token efficiency.
Print a beautifully formatted Markdown table of evaluation results to `stdout` containing columns for Scenario ID, Question, Command, Status, Execution Time, and Trace Efficiency Verdict.

Run python tests/linter/etc to verify the script is clean. Expose running instructions in your handoff report.
Once done, write `/home/drusifer/Projects/via/.agents/worker_harness/handoff.md` following the Handoff Protocol, and send a completion message to the Project Orchestrator (96da455b-67e7-4672-9d43-b25b6dcadda9).
