# VIA MCP Usability Evaluation

**Persona**: Smith  
**Date**: 2026-04-12T13:25  
**Task**: Play with VIA MCP, evaluate usefulness/ease of use, identify token-saving use cases and edge cases.

## Verdict

**Approved with usability concerns.** VIA MCP is immediately useful for token-efficient codebase exploration when the user already knows the query vocabulary. The strongest workflow is:

1. Use a narrow symbol query to find the exact file, line, and symbol.
2. Use `-oR` only for the one symbol body that matters.
3. Use `--via calls` to answer dependency/caller questions without reading whole files.
4. Use `--slice` to page large result sets.

This reduces token use sharply compared with opening full files or recursive grep output. The main UX risk is that several invalid or unsupported inputs return empty results without saying what went wrong, which can make users doubt the index instead of correcting the query.

## Useful Token-Saving Use Cases

### 1. Symbol Reconnaissance

**Command**: `["-mg", "*mcp*", "-tf", "-tm", "--slice", "0:20"]`

**Observed**: Returned 20 of 27 matching functions/methods with file paths and line numbers.

**Value**: Good first-pass discovery. It lets an agent decide which file or symbol matters before spending tokens on source.

**HCI**: Pass for #7 Flexibility and Efficiency.

### 2. Read One Relevant Function, Not the File

**Command**: `["-mg", "_run_mcp_command", "-tf", "-oR"]`

**Observed**: Returned only the `_run_mcp_command` function body from `via/__main__.py`.

**Value**: Excellent token control. This is the best workflow for agents: locate with JSON/list/table, then fetch raw only for the target symbol.

**HCI**: Pass for #8 Aesthetic and Minimalist Design.

### 3. Caller Discovery Without Grep Noise

**Command**: `["-mg", "build_tool_schema", "-tf", "--via", "calls", "-mg", "*", "--slice", "0:10"]`

**Observed**: Returned `_run_mcp_command` and `run_mcp_server`.

**Value**: Very strong for impact analysis. This answers "who calls this?" without reading every file that mentions the string.

**HCI**: Pass with a terminology caveat: relationship direction is still hard to remember.

### 4. Documentation Navigation

**Command**: `["-mg", "*MCP*", "-tH", "--slice", "0:10"]`

**Observed**: Returned markdown headers with parent context and line numbers.

**Value**: Good way to locate relevant documentation sections without loading large markdown files.

**HCI**: Pass for #6 Recognition Rather Than Recall when used through examples.

### 5. Result Paging

**Commands**:
- `["-mg", "*", "-tf", "--slice", "0:3"]`
- `["-mg", "*", "-tf", "--slice", "3:6"]`

**Observed**: Returned stable windows with `total: 366` and `shown: 3`.

**Value**: Good token budget control. The `total` field helps users decide whether to refine or page.

**HCI**: Pass for #1 Visibility of System Status.

### 6. Output Format Selection

**Commands**:
- `["-mg", "build_tool_schema", "-tf", "-oL"]`
- `["-mg", "build_tool_schema", "-tf", "-oT"]`
- `["-mg", "build_tool_schema", "-tf", "-oU"]`
- `["-mg", "build_tool_schema", "-tf", "-oR"]`

**Observed**: List, table, usage, and raw output all worked.

**Value**: `-oL` is lowest-token for references, `-oT` is human-readable, `-oU` is compact context, and `-oR` is best for targeted code reading.

**HCI**: Pass, with a discoverability concern because agents must know which output shape to request.

### 7. Regex Search For Naming Conventions

**Command**: `["-mr", "^test_.*mcp", "-tm", "--slice", "0:10"]`

**Observed**: Regex search is available through `-mr` and should be treated as a distinct power-user workflow. It was not covered in the initial pass and needs explicit regression coverage.

**Value**: High for convention-heavy codebases. Regex lets agents target prefixes, suffixes, and naming families more precisely than broad glob matches.

**HCI**: Concern for #9 Help Users Recognize, Diagnose, and Recover from Errors. Regex is powerful, but invalid patterns need clear structured errors because users cannot reliably distinguish "no matches" from "bad pattern" if both return empty results.

### 8. Multi-Type Queries

**Command**: `["-mg", "*mcp*", "-tf", "-tm", "-tc", "--slice", "0:8"]`

**Observed**: Multi-type queries worked and returned mixed functions, methods, and classes with `total: 27`.

**Value**: Strong. This is one of the best exploratory patterns because agents can search one concept across symbol kinds without multiple tool calls.

**HCI**: Pass for #7 Flexibility and Efficiency.

## Edge Cases And Usability Findings

### Finding 1: Invalid Flags Silently Return Empty Results

**Command**: `["--definitely-not-a-real-flag"]`

**Expected**: Clear error explaining the unknown argument and showing valid examples.

**Actual**: Empty result object: `result: [], total: 0, shown: 0`.

**HCI heuristic**: #9 Help Users Recognize, Diagnose, and Recover from Errors.

**Impact**: High. A user may conclude the index is empty or broken rather than recognizing a query syntax error.

**Fix**: Return structured MCP errors for invalid flags, including the bad flag and a short hint.

### Finding 2: Unsupported Relationship Query Fails Like A Legitimate Empty Result

**Command**: `["-mg", "via/mcp/server.py", "-tF", "-Q", "--via", "declares", "-mg", "*", "--slice", "0:20"]`

**Expected**: Either symbols declared in `via/mcp/server.py` or an explicit message that file-to-symbol `declares` is unsupported.

**Actual**: Empty result object.

**HCI heuristic**: #1 Visibility of System Status and #9 Error Recovery.

**Impact**: Medium-high. This exact use case appears in `agents/PROJECT.md` as a quick reference, so failure is especially confusing.

**Fix**: Either implement the documented pattern or remove/correct the quick reference.

### Finding 3: Regex/Glob Mistakes Are Not Diagnosed

**Command**: `["-mg", "[", "-tf"]`

**Expected**: For glob mode, the literal behavior should be made clear; for regex mode, invalid patterns should produce an explicit error.

**Actual**: Empty result object.

**HCI heuristic**: #5 Error Prevention and #9 Error Recovery.

**Impact**: Medium. Empty results are valid sometimes, so the tool needs to distinguish "valid query, no matches" from "query could not mean what the user likely intended."

**Fix**: Add validation and return warnings where feasible.

### Finding 4: Relationship Direction Remains Cognitively Heavy

**Command**: `["-mg", "_run_mcp_command", "-tf", "--via", "calls", "-mg", "*", "-tf", "-tm"]`

**Observed**: Returned the caller `_dispatch_subcommand`, which is useful, but the syntax requires remembering that the known anchor goes left and the results go right.

**HCI heuristic**: #6 Recognition Rather Than Recall.

**Impact**: Medium. Power users can learn it, but it is easy to invert when under context pressure.

**Fix**: Add canned aliases such as `--callers SYMBOL`, `--callees SYMBOL`, or documented examples in the MCP tool description grouped by user question.

### Finding 5: Diagram Output Fallback Is Understandable But Not Helpful

**Command**: `["-mg", "_run_mcp_command", "-tf", "--via", "calls", "-mg", "*", "-tf", "-tm", "-oD"]`

**Expected**: Diagram if possible, or a fallback preserving the relationship result.

**Actual**: Empty JSON with note: no diagram content produced.

**HCI heuristic**: #1 Visibility of System Status.

**Impact**: Low-medium. The note helps, but the relationship result disappears, so the user must retry.

**Fix**: When diagram generation has no content, include the non-diagram relationship result or explain why the relationship query produced no drawable edges.

### Finding 6: Multi-Match Semantics Are Ambiguous

**Commands**:
- `["-mg", "*mcp*", "-mg", "*schema*", "-tf", "-tm", "-tc", "--slice", "0:12"]`
- `["-mg", "*schema*", "-mr", "^test_.*mcp", "-tf", "-tm", "--slice", "0:12"]`
- `["-mg", "*schema*", "-ms", "%mcp%", "-tf", "-tm", "--slice", "0:12"]`

**Expected**: The tool should document whether multiple match flags are unsupported, last-one-wins, AND, or OR.

**Actual**: Repeated `-mg` appears to behave like one matcher overriding the other rather than composing them. Mixed matcher types returned empty results without explaining whether the syntax was invalid or simply had no matches.

**HCI heuristic**: #4 Consistency and Standards and #9 Error Recovery.

**Impact**: Medium-high. Multi-match queries are a natural way for agents to reduce token use by narrowing results server-side. Ambiguous semantics make agents either over-fetch or trust misleading empty results.

**Fix**: Define the rule explicitly. Recommended: reject multiple match flags in a single match stage with a structured error until AND/OR composition is intentionally designed.

## Recommended Agent Workflows

### Workflow A: Lowest Token Symbol Lookup

1. `["-mg", "*Name*", "-tf", "-tm", "-tc", "--slice", "0:10"]`
2. If one result matters, fetch it with `-oR`.
3. If many results return, refine by type or use `--slice`.

### Workflow B: Impact Analysis

1. Find the exact symbol with `-mg`.
2. Query callers with `--via calls`.
3. Fetch raw bodies only for callers that look relevant.

### Workflow C: Documentation Triage

1. Search headers with `-tH`.
2. Use returned file path and line number to read only the relevant section if needed.

### Workflow D: File Discovery

1. Use `-tF` for basename searches, e.g. `["-mg", "*server*", "-tF"]`.
2. Use `-Q` for full-path searches, e.g. `["-mg", "via/mcp/*", "-tF", "-Q"]`.

## Priority Recommendations

1. **P1**: Return structured errors for invalid flags instead of empty results.
2. **P1**: Fix or remove the documented file `declares` quick-reference pattern.
3. **P1**: Define and enforce multi-match semantics; reject ambiguous combinations until composition is supported.
4. **P2**: Add canned relationship shortcuts for common user questions.
5. **P2**: Preserve fallback data when `-oD` cannot render a diagram.
6. **P3**: Add short examples to the MCP description for token-saving workflows: symbol lookup, raw function body, callers, docs headers, regex search, multi-type search, and paged results.

## Final Assessment

VIA MCP is useful today as an agent-facing token reducer. It is strongest for indexed symbol discovery, targeted source extraction, and caller lookup. It is less easy for first-time users because invalid inputs and unsupported documented patterns can look identical to valid empty searches. The next usability improvement should be error clarity, not more query power.
