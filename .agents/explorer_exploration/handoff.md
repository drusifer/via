# Handoff Report — Codebase Exploration and Requirements Analysis for VIA Evaluation Harness

## 1. Observation

### CLI Entry Point and Invocation
In `/home/drusifer/Projects/via/pyproject.toml` (lines 34-36):
```toml
[project.scripts]
via = "via.__main__:main"
```
The CLI entry point for the `via` tool is defined as `via.__main__:main`.
The virtual environment is created at `/home/drusifer/Projects/via/.venv/`.
In `/home/drusifer/Projects/via/Makefile.prj` (lines 44-45):
```makefile
via: install-dev ## Run via command in the virtual environment (usage: make via ARGS="...")
	$(VENV_DIR)/bin/via $(ARGS)
```
The tool can be executed via:
1. Activating the virtual environment: `source .venv/bin/activate` and running `via [args]`
2. Direct invocation: `.venv/bin/via [args]`
3. Python module invocation: `python -m via [args]` (or `.venv/bin/python -m via [args]`)
4. Makefile proxy: `make via ARGS="[args]"`

### The 14 Gauntlet Scenarios
The scenarios are defined in `/home/drusifer/Projects/via/agents/skills/judge/SKILL.md` (lines 113-184).
Traces of their prior executions are recorded in `/home/drusifer/Projects/via/agents/trin.docs/via_gauntlet_trace.log` (lines 1-181).
Below is the verbatim mapping of the scenarios and their CLI commands from the trace log:

*   **Scenario 1 (Simple Class Lookup)**:
    *   *Question*: What is the location of the `PipelineParser` class?
    *   *Command in trace*: `via -mg PipelineParser -tc`
    *   *Expected output*: `class:/home/drusifer/Projects/via/via/pipeline/parser.py:58:.home.drusifer.Projects.via.via.pipeline.parser.PipelineParser:@1835+21364`
*   **Scenario 2 (Inverse Relationships)**:
    *   *Question*: Which classes inherit from `ParserABC`?
    *   *Command in trace*: `via -mg '*' -tc --via inherits-from -mg 'ParserABC' -tc`
    *   *Expected output*: Lists of classes inheriting from `ParserABC` (e.g. `PythonParser`, `MarkdownParser`, `JavaScriptParser`, `DartParser`).
*   **Scenario 3 (File Exclusions)**:
    *   *Question*: What functions are in `via/core/` but not in test files?
    *   *Command in trace*: `via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5`
*   **Scenario 4 (Negative Relationships)**:
    *   *Question*: Which classes do not declare any methods?
    *   *Command in trace*: `via -mg '*' -tc --sans declares -mg '*' -tm`
    *   *Expected output*: List of classes declaring no methods (e.g. config classes, dataclasses).
*   **Scenario 5 (SQL Pattern Match)**:
    *   *Question*: What indexed symbols contain "reindex" (case-insensitive)?
    *   *Command in trace*: `via -ms '%reindex%' -I`
    *   *Expected output*: List of symbols containing "reindex" (case-insensitive).
*   **Scenario 6 (Direct SQLite Query)**:
    *   *Question*: How many total symbols are currently indexed in the SQLite database?
    *   *Command in trace*: Run direct SQL query `SELECT COUNT(*) FROM symbols;` on `.via/index.db`.
    *   *Expected output*: Total symbol count as an integer (e.g., `13169`).
*   **Scenario 7 (Import Check)**:
    *   *Question*: Which files import `sqlite3`?
    *   *Command in trace*: `via -mg '*' -tF --via imports -mg 'sqlite3' -ti`
*   **Scenario 8 (Markdown Header Search)**:
    *   *Question*: What are the section headers in `docs/USER_GUIDE.md`?
    *   *Command in trace*: `via -mg '*' -tH --via declares -mg '*USER_GUIDE.md' -tF`
*   **Scenario 9 (Line Slicing)**:
    *   *Question*: What are lines 50-70 of `via/pipeline/executor.py`?
    *   *Command in trace*: `via -mg '*/executor.py' -tF -Q -mL '50:70' -oR`
    *   *Expected output*: Raw text snippet showing lines 50 to 70 of the file.
*   **Scenario 10 (Complex Multi-Filter)**:
    *   *Question*: Find functions named `parse` declared inside a class named `PythonParser`.
    *   *Command in trace*: `via -mg 'parse' -tm --via declares -mg 'PythonParser' -tc`
*   **Scenario 11 (Call Sites)**:
    *   *Question*: Where is `DatabaseStore.connect` called?
    *   *Command in trace*: `via -mg '*' -tm --via calls -mg 'connect' -tm`
    *   *Expected output*: List of methods calling `connect`.
*   **Scenario 12 (Declaration Site)**:
    *   *Question*: Where is `PipelineParseError` declared (exact line)?
    *   *Command in trace*: `via -mg 'PipelineParseError' -tc`
    *   *Expected output*: `class:/home/drusifer/Projects/via/via/pipeline/errors.py:36:.home.drusifer.Projects.via.via.pipeline.errors.PipelineParseError:@758+724`
*   **Scenario 13 (Type Hierarchy Expansion)**:
    *   *Question*: What is the inheritance hierarchy of `ParserABC`?
    *   *Command in trace*: `via -mg '*' -tc --via inherits-from -mg 'ParserABC' -tc -oD`
    *   *Expected output*: Mermaid class diagram of the inheritance hierarchy.
*   **Scenario 14 (Test Coverage Mapping)**:
    *   *Question*: What tests cover or reference code in `via/pipeline/executor.py`?
    *   *Command in trace*: `via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`

### Execution Trace Logging and Auditing
*   **Production Logging**: In `/home/drusifer/Projects/via/via/core/logging.py`, `setup_logging(verbosity: int = 0, log_file: Optional[str] = None)` sets up logging formats based on verbosity (0 to 4) mapping to `WARNING`, `INFO`, and `DEBUG`. An optional `log_file` parameter pipes logs to a file.
*   **Watch and MCP logs**: MCP-mode logging is routed to `~/.via/mcp.log` as defined in `via/mcp/server.py` (lines 60-66).
*   **Auditing Strategy**:
    *   *Concept*: "Token waste" or "Efficiency metrics" are defined conceptually in `agents/skills/judge/SKILL.md` rather than measured via production telemetry. If the agent falls back to full file reads (`view_file`) or pattern matching (`grep_search`) because a `via` query was incorrect/empty, it wastefully consumes large context sizes.
    *   *Programmatic Auditing*: In the evaluation script, we can audit queries by:
        1. Executing the `via` CLI command under `.venv/` and ensuring it completes with exit code 0.
        2. Validating the query output contains the expected target content (preventing empty/incorrect results).
        3. Auditing the database hits: the SQLite database matches can be cross-verified using direct SQLite checks (like Scenario 6).
        4. Verifying that the query does not require opening/scanning source files directly (which is the core value of `via` indexing).

### Makefile Structure
*   **Interception Layer**: The project Makefile uses a custom build capture script `agents/tools/mkf.py` to route all commands to the background, pipe outputs to `build/build.out`, and post notifications to `agents/CHAT.md`.
*   **Project Targets**: The actual recipes are contained in `Makefile.prj`, which is conditionally included using `MKF_ACTIVE`.

---

## 2. Logic Chain

### Swapped Relationships and Command Corrections
Based on `/home/drusifer/Projects/via/agents/neo.docs/context.md` (lines 280-287), Neo implemented critical bug fixes in Sprint 25 Cycle 3:
1.  **`declares` Validation Direction**: Swap `declares` to `inverted=True` and `declared-in` to `inverted=False` in `ReferenceType.get_full_value_map()`.
    *   *Reasoning*: `declares` indicates `container --via declares member`. The DB stores relations as `member -> container`. Hence, filtering containers that declare members requires `inverted=True`.
    *   *Reasoning*: `declared-in` indicates `member --via declared-in container`. This maps directly to the DB relation direction, hence `inverted=False`.
2.  **`-Q` Qualified Path Filtering**: Enabled `DatabaseStore.query_relationships` to filter on the `qualified_name` column when `-Q` is active.

Because of these fixes, several queries run in Trin's trace log returned empty results and must be corrected in the evaluation harness:
*   **Scenario 3 (File Exclusions)**:
    *   *Old command*: `via -mg '*' -tf --via declares -mg 'via/core/*' -tF -Q -n 5`
    *   *Correction*: Since `declares` is container -> member, a left-hand side of functions (`-tf`) is a member, which cannot declare files. To query members by their container, use `declared-in`. In addition, to exclude tests, chain with `--sans declared-in -mg '*test*' -tF`:
        `via -mg '*' -tf --via declared-in -mg 'via/core/*' -tF -Q --sans declared-in -mg '*test*' -tF`
*   **Scenario 7 (Import Check)**:
    *   *Old command*: `via -mg '*' -tF --via imports -mg 'sqlite3' -ti`
    *   *Correction*: When imports are resolved in `/home/drusifer/Projects/via/via/db/store.py` (lines 1070-1075), they are linked to symbols of type `module`, not `import`. Adding `-ti` restricts the target to an `import` symbol, which returns empty. Removing `-ti` allows it to match the imported module:
        `via -mg '*' -tF --via imports -mg 'sqlite3'`
*   **Scenario 8 (Markdown Header Search)**:
    *   *Old command*: `via -mg '*' -tH --via declares -mg '*USER_GUIDE.md' -tF`
    *   *Correction*: Since `declares` is now inverted (`container --via declares member`), querying member headers (`-tH`) by their container files requires `declared-in` (or swapping the result and filter stages):
        `via -mg '*' -tH --via declared-in -mg '*USER_GUIDE.md' -tF`
*   **Scenario 10 (Complex Multi-Filter)**:
    *   *Old command*: `via -mg 'parse' -tm --via declares -mg 'PythonParser' -tc`
    *   *Correction*: Querying method member (`-tm`) by container class requires `declared-in`:
        `via -mg 'parse' -tm --via declared-in -mg 'PythonParser' -tc`
*   **Scenario 14 (Test Coverage Mapping)**:
    *   *Old command*: `via -mg '*' -tF --via imports -mg '*executor*' -tF -Q`
    *   *Correction*: The imported target resolves to a module symbol named `via.pipeline.executor` (type `module`), not a file path symbol (type `filepath`/`file`). Restricting the filter stage to `-tF -Q` causes it to return empty. Removing `-tF -Q` enables matching the module import:
        `via -mg '*' -tF --via imports -mg '*via.pipeline.executor*'`

---

## 3. Caveats

*   **Venv Path Dependency**: The scripts assume the virtual environment is named `.venv` at the project root. If a user runs the script in a custom-named venv (e.g. `venv`), they must explicitly invoke it using their virtualenv python.
*   **SQLite Database State**: The symbol count verification (Scenario 6) depends on the index being freshly built and containing all files. If the index is empty or stale, Scenario 6 and other queries will return incorrect results or fail. Therefore, the evaluation harness must ensure `via index .` runs before running the scenarios.
*   **Terminal Execution Permission**: Because this agent operates in a read-only investigation mode and the terminal command execution timed out during permission checks, the correct CLI outputs have been inferred by analyzing the codebase source, the database schemas, and UAT tests.

---

## 4. Conclusion

To implement the automated verification and evaluation harness, the following plan is recommended:

### 1. Place the Script at `scripts/via_eval.py`
Create the `scripts/` directory at the project root and implement the script to:
1. Re-build the index to ensure it is fresh: runs `via index .`.
2. Define a list of dictionaries for all 14 scenarios containing:
   * `id`: 1 to 14
   * `question`: The intended question text
   * `command`: The list of command arguments (e.g., `['.venv/bin/via', '-mg', 'PipelineParser', '-tc']`)
   * `verifier`: A function taking the stdout string and returning a boolean (e.g. checking for specific output lines/substrings)
3. For Scenario 6 (direct database query), run python SQLite query directly using `sqlite3` on `.via/index.db`.
4. Capture execution time and verify outputs.
5. Print a beautifully formatted Markdown table of results to `stdout`.

### 2. Update the Makefile
Add a `via-eval` target to both `Makefile` and `Makefile.prj`:
In `Makefile`:
```makefile
via-eval: ## Run all 14 gauntlet scenarios and print markdown evaluation table
	@./agents/tools/mkf.py ${V} $@
```
In `Makefile.prj`:
```makefile
via-eval: install-dev
	. ${VENV_ACTIVATE} && python scripts/via_eval.py
```

### 3. Exact Commands for the 14 Scenarios in the Script
```python
scenarios = [
    {
        "id": 1,
        "question": "What is the location of the PipelineParser class?",
        "command": ["via", "-mg", "PipelineParser", "-tc"],
        "verify": lambda out: "via/pipeline/parser.py" in out and "PipelineParser" in out
    },
    {
        "id": 2,
        "question": "Which classes inherit from ParserABC?",
        "command": ["via", "-mg", "*", "-tc", "--via", "inherits-from", "-mg", "ParserABC", "-tc"],
        "verify": lambda out: all(x in out for x in ["PythonParser", "MarkdownParser", "JavaScriptParser", "DartParser"])
    },
    {
        "id": 3,
        "question": "What functions are in via/core/ but not in test files?",
        "command": ["via", "-mg", "*", "-tf", "--via", "declared-in", "-mg", "via/core/*", "-tF", "-Q", "--sans", "declared-in", "-mg", "*test*", "-tF"],
        "verify": lambda out: "setup_logging" in out or "discover_files" in out
    },
    {
        "id": 4,
        "question": "Which classes do not declare any methods?",
        "command": ["via", "-mg", "*", "-tc", "--sans", "declares", "-mg", "*", "-tm"],
        "verify": lambda out: "DiscoveredFile" in out and "FlagGroup" in out
    },
    {
        "id": 5,
        "question": "What indexed symbols contain 'reindex' (case-insensitive)?",
        "command": ["via", "-ms", "%reindex%", "-I"],
        "verify": lambda out: "reindex" in out.lower()
    },
    {
        "id": 6,
        "question": "How many total symbols are currently indexed in the SQLite database?",
        "type": "sql",
        "query": "SELECT COUNT(*) FROM symbols;",
        "verify": lambda val: val > 0
    },
    {
        "id": 7,
        "question": "Which files import sqlite3?",
        "command": ["via", "-mg", "*", "-tF", "--via", "imports", "-mg", "sqlite3"],
        "verify": lambda out: "via/db/store.py" in out
    },
    {
        "id": 8,
        "question": "What are the section headers in docs/USER_GUIDE.md?",
        "command": ["via", "-mg", "*", "-tH", "--via", "declared-in", "-mg", "*USER_GUIDE.md", "-tF"],
        "verify": lambda out: "Table of Contents" in out and "Installation" in out
    },
    {
        "id": 9,
        "question": "What are lines 50-70 of via/pipeline/executor.py?",
        "command": ["via", "-mg", "*/executor.py", "-tF", "-Q", "-mL", "50:70", "-oR"],
        "verify": lambda out: "PipelineStage" in out
    },
    {
        "id": 10,
        "question": "Find functions named parse declared inside a class named PythonParser.",
        "command": ["via", "-mg", "parse", "-tm", "--via", "declared-in", "-mg", "PythonParser", "-tc"],
        "verify": lambda out: "python_parser.py" in out and "PythonParser.parse" in out
    },
    {
        "id": 11,
        "question": "Where is DatabaseStore.connect called?",
        "command": ["via", "-mg", "*", "-tm", "--via", "calls", "-mg", "connect", "-tm"],
        "verify": lambda out: "test_database.py" in out or "test_relationships.py" in out
    },
    {
        "id": 12,
        "question": "Where is PipelineParseError declared (exact line)?",
        "command": ["via", "-mg", "PipelineParseError", "-tc"],
        "verify": lambda out: "via/pipeline/errors.py" in out and "PipelineParseError" in out
    },
    {
        "id": 13,
        "question": "What is the inheritance hierarchy of ParserABC?",
        "command": ["via", "-mg", "*", "-tc", "--via", "inherits-from", "-mg", "ParserABC", "-tc", "-oD"],
        "verify": lambda out: "ParserABC <|--" in out
    },
    {
        "id": 14,
        "question": "What tests cover or reference code in via/pipeline/executor.py?",
        "command": ["via", "-mg", "*", "-tF", "--via", "imports", "-mg", "*via.pipeline.executor*"],
        "verify": lambda out: "test_relationship_executor.py" in out or "test_documented_queries_uat.py" in out
    }
]
```

---

## 5. Verification Method

To independently verify this plan:
1. Inspect the relationship definitions in `via/core/relationship_types.py` (lines 44-67) to confirm that `declares` is indeed inverted and `declared-in` is forward.
2. Run `make test` to ensure that all 1333 tests are green, which confirms the Cycle 3 bug fixes are stable and integrated.
3. Review the proposed corrections against the database schema mapping to verify that `sqlite3` imports map to `module` type, and `executor` imports map to `module` type.
