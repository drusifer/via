# Evaluation Report: VIA Tool Usage & Prompt Optimization

**Audit Target**: `via` usage in current session  
**Auditor**: Bob (Prompt Engineer)  
**Date**: 2026-06-21  

---

## 1. Session Activity Analysis

During the current session, the agent (Neo) performed a series of code inspections to understand how relationships and canned queries are handled. 

### Commands & Tools Used:
- **`grep_search`**: Called **15 times** to search for symbols and code patterns.
- **`view_file`**: Called **18 times** to inspect python modules, configurations, and test files.
- **`list_dir`**: Called **5 times** to explore directory contents.
- **`run_command`**: Called **6 times** to run git status, git log, git diff, etc.
- **`via` (CLI / MCP)**: Called **0 times**.

---

## 2. Tool Choice Assessment

While some usages of `grep_search` were appropriate (e.g., searching for SQL schemas, string literals, and log files), several instances represents sub-optimal fallbacks where `via` query capabilities should have been utilized.

### Sub-optimal Tool Fallbacks:
1. **Finding method definitions**: Used `grep_search` for `def query_relationships` in `via/db/store.py`.
   - *Better*: `via -mg '*query_relationships*' -tm` or `via -mg 'query_relationships' -tm`.
2. **Finding function/method calls**: Used `grep_search` for `resolve_pending_relationships` and `expand_canned_query`.
   - *Better*: `via -mg 'resolve_pending_relationships' -tm` and `via -mg 'expand_canned_query' -tf`.
3. **Searching for types/enums**: Used `grep_search` for `ReferenceType` and `get_full_value_map`.
   - *Better*: `via -mg '*ReferenceType*' -tc` and `via -mg 'get_full_value_map' -tm`.
4. **Locating relationship insertions**: Used `grep_search` for `insert_` in `via/services/`.
   - *Better*: `via -mg 'insert_*' -tm` or relationship-calls query.

---

## 3. Root Cause Analysis

Why did the agent fail to use `via` despite `via: enabled` being active in [PROJECT.md](file:///home/drusifer/Projects/via/agents/PROJECT.md)?

1. **Missing MCP Tool**: The `mcp__via__via_query` tool is not registered in the sandbox tool list.
2. **Ambiguity in Prompts**: Specialist prompts instruct: *"If via is not enabled, use Grep/Glob/Read instead."* The agents confuse "tool not present in my MCP toolset" with "via not enabled in project". They fail to realize they can and should fall back to running the `via` CLI command using the `run_command` tool.
3. **Force of Habit**: Without the convenient MCP wrapper, the LLM default-biases to `grep_search` and `view_file` rather than invoking CLI executables.

---

## 4. Trace Effectiveness Score (TES) Rubric

| Category | Max Points | Deductions | Score | Notes |
|---|---|---|---|---|
| **Correctness & Success** | 100 | 0 | 100 | Completed design document successfully. |
| **Resource Waste** | - | -15 | 85 | Deducted for 5 redundant `grep_search` calls for symbol locations instead of `via` queries. |
| **Protocol Adherence** | - | 0 | 85 | SMP context, task updates, summaries, and handoffs followed perfectly. |
| **Final Score** | **100** | **-15** | **85 / 100** | **Sub-optimal (Target is >= 90)** |

---

## 5. Proposed Prompt & Skill Improvements

To improve tool compliance and token efficiency, Bob proposes updating the universal `via` skill and specialist prompts with the following rules:

### A. Clarified CLI Fallback Rule
Modify `agents/skills/via/SKILL.md` and specialist persona docs:
```markdown
> [!IMPORTANT]
> **MCP vs. CLI Fallback**: If `via: enabled` is set in `agents/PROJECT.md` but the `mcp__via__via_query` tool is missing from your toolset, you **MUST** run `via` queries using the CLI (via the `run_command` tool or `make via` targets) instead of falling back to raw `grep_search` or manual file scanning for symbol lookups.
```

### B. Strict Symbol Lookup Constraint
Add to `AGENTS.md` and `GEMINI.md`:
- **Never** use `grep_search` to find class, function, method, global variable, or import definitions.
- **Always** use `via` first to resolve symbol names, types, and locations.
- **Only** use `grep_search` for free-text search inside code (e.g. comments, logs, string constants, SQL queries) or when `via` returns no matches.
