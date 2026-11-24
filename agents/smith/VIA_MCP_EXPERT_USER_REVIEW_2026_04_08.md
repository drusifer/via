# Via MCP: Expert User Review

**Date**: 2026-04-08  
**Reviewer**: Smith (HCI Expert)  
**Method**: Live exploration using `mcp__via__via_query` — all findings are from actual MCP calls, not speculation.  
**Scope**: Via as navigated through its MCP tool by an AI agent acting as a power user.

---

## Summary

Via's MCP integration works well for its core use case — finding symbols by name and navigating code relationships. The query model is expressive and consistent. The main frustrations are a **hard result cap with no pagination**, **output format flags that silently do nothing via MCP**, and **file-path filtering that doesn't work the way the docs suggest**. The wishlist items are genuinely exciting: path-scoped queries and cross-language relationship tracing would make via a tier above anything else for codebase navigation.

*Feedback: there's an arg for result size is it not documented?*  
**Smith:** Confirmed — `-n` / `--limit N` exists and the CLI even warns when results are capped (line 507 of `__main__.py`). But the MCP tool description doesn't mention it, so agents using the MCP have no way to discover it. BUG-4 is a **documentation bug**, not a missing feature. Still needs: (1) expose `-n` in MCP docs, (2) add `total_count` to JSON response so callers know truncation happened, (3) add `--slice` for offset access.

---

## What Works Well

### 1. Symbol discovery is fast and precise
Finding a class, method, or function by name works exactly as expected. The glob patterns (`*`, `?`) are intuitive, and combining them with type filters gives tight, relevant results.

```
# Find all service classes in Python
["-mg", "*Service", "-tc", "--lang", "py"]
→ IndexingService, WatchService, MyService, TestIndexingService  ✓

*Feedback: Why not use relationship query not all classes implementing "Service" are call *Service.*  
**Smith:** Fair — name pattern is a proxy. The right query is `--via inherits-from` on a base class, but this project has no common `Service` base class. The real limitation is that duck-typed Python services can't be found structurally without a shared ancestor. The name-pattern example is demonstrating glob syntax, not recommending this as the canonical approach. **Action**: Add a `--via inherits-from` example as the preferred service-discovery pattern in help/docs.

# Find a specific class and its methods
["-mg", "DatabaseStore", "-tc", "--via", "declares", "-mg", "*"]
→ All methods on DatabaseStore  ✓
```

**HCI Assessment**: Matches user mental model. You think "find things named X" and that's what you get.

### 2. Relationship navigation is powerful and learnable
The `--via` / `--sans` syntax is unusual at first but has a clear rule (known anchor left, wildcard right). Once learned, it enables queries that grep simply cannot:


```
# Who calls DatabaseStore?
["-mg", "DatabaseStore", "-tc", "--via", "calls", "-mg", "*", "-tf"]
→ rel_db, _run_index_watch, _run_index_command, _run_stats_command  ✓

# What does __main__.py export?
["-mg", "__main__.py", "-tF", "-Q", "--via", "declares", "-mg", "*", "-tf"]
→ All top-level functions in __main__.py  ✓
```

**HCI Assessment**: The "anchor left, wildcard right" rule is learnable but not obvious without docs. `--via` (positive) vs `--sans` (negative) naming is clean.

*Feedback: Let's improve Help output could make "learning" easier*  
**Smith:** Agreed. The anchor-left/wildcard-right rule for `--via`/`--sans` is the hardest thing to learn from `--help` alone. Recommending a sprint story: improve `--help` with (1) a dedicated "Relationship Queries" section showing 2-3 annotated examples, (2) a one-liner rule ("KNOWN anchor LEFT, wildcard RIGHT"), (3) the valid `REL` values listed inline. This addresses Nielsen #6 (Recognition over Recall) and #10 (Help and Documentation).

### 3. Language filtering works for symbols
`--lang py` and `--lang js` correctly scope results to the right language files:

```
["-mg", "*", "-tf", "--lang", "js"]  → JS functions only  ✓
["-mg", "*Service", "-tc", "--lang", "py"]  → Python classes only  ✓
```

### 4. Case-insensitive search works
`-I` flag applies correctly to all pattern types.

### 5. Subtype filtering works for JS
`--subtype arrow_function` successfully filters to arrow functions in JS files. This is a useful escape hatch for language-specific symbol distinctions.

### 6. Multi-type queries with `--not`
Negation of a match stage works:
```
["-mg", "*", "-tc", "--lang", "py", "--not", "-mg", "Test*", "-tc"]
→ Non-test Python classes  ✓
```

### 7. Empty results are clean
When a query matches nothing, via returns `{"result": []}` — no stack traces, no error codes. This is correct behavior.

### 8. Markdown header indexing works (via name search)
Headers across the entire project are indexed and findable by name:
```
["-mg", "via*", "-tH", "-I"]  → Headers from README.md, ARCH.md, PRD.md, SKILL.md files  ✓
["-mg", "install*", "-tH", "-I"]  → Installation sections across docs  ✓
```

---

## What Doesn't Work

### BUG-1: `--lang` filter does not apply to file path queries (`-tF`)

**Severity**: Medium  
**HCI Heuristic**: #4 Consistency and Standards

```
["-mg", "*", "-tF", "--lang", "py"]  →  {"result": []}  ✗
["-mg", "*", "-tF"]  →  returns only markdown files (not Python)  ✗
```

A user who wants "all Python files" reaches for `--lang py -tF`. They get nothing. The `--lang` filter silently doesn't apply to the file type, and `-tF` without `--lang` only returns markdown files anyway (no `.py` files appear in a bare `*` `-tF` search).

Workaround: `["-mg", "*.py", "-tF"]` matches by filename extension — but this is non-obvious and inconsistent with using `--lang` elsewhere.

### BUG-2: `declares` relationship does not work for markdown files → headers

**Severity**: Medium  
**HCI Heuristic**: #4 Consistency and Standards

```
# Works for Python:
["-mg", "store.py", "-tF", "-Q", "--via", "declares", "-mg", "*"]  →  imports, classes ✓

# Does NOT work for Markdown:
["-mg", "README.md", "-tF", "-Q", "--via", "declares", "-mg", "*", "-tH"]  →  [] ✗
["-mg", "ARCH.md", "-tN", "--via", "declares", "-mg", "*", "-tH"]  →  [] ✗
```

You can't ask "what sections does README.md declare?" — you have to know the section name already and search for it directly. This breaks the mental model that `declares` means "symbols contained in this file."


*Feedback: We should also index links (urls) too we can do references queries*  
**Smith:** Strong +1. Indexing hyperlinks as a `link` symbol type would unlock: "which docs reference this URL?", "which files link to the API guide?", "are there broken internal links?". This fits naturally into the `--via references` relationship. Especially valuable for agent context navigation — an agent could traverse doc cross-references the same way it traverses code call graphs. Recommend as a Sprint 15+ story.

### BUG-3: Output format flags are silently ignored via MCP

**Severity**: Low–Medium  
**HCI Heuristic**: #1 Visibility of System Status, #9 Help Recover from Errors

All output format flags (`-oD`, `-oR`, `-oF`, `-oT`, `-oL`) are silently ignored. The MCP always returns JSON regardless:

```
["-mg", "IndexingService", "-tc", "--via", "calls", "-mg", "*", "-tf", "-oD"]
→  Returns JSON, not a Mermaid diagram  ✗

["-mg", "*Service", "-tc", "--lang", "py", "-oR"]
→  Returns JSON, not raw source  ✗
```

The user has no way to know this. The MCP tool description doesn't document "output flags are ignored." A user who adds `-oD` hoping for a diagram silently gets JSON with no explanation.


*FEEDBACK: Let's add this - but needs a json wrapper for mcp to function eg: `{"output_type": "diagram", "result": "<diagram>"}`*  
**Smith:** Agreed on the wrapper shape. Proposal: MCP response becomes `{"output_type": "json"|"diagram"|"raw"|"table", "result": <data>}` where `result` is an array for JSON mode and a string for all other modes. This is a clean, backward-compatible change — callers that only check `result` continue to work in JSON mode. The output format flags (`-oD`, `-oT`, `-oR`) become meaningful via MCP instead of silently doing nothing. Upgrade BUG-3 from low to **actionable sprint story**.

### BUG-4: Default result cap with no pagination and no count

**Severity**: High (for power users navigating large codebases)  
**HCI Heuristic**: #1 Visibility of System Status, #7 Flexibility and Efficiency

```
["-mg", "*", "-tH"]  →  10 results (only from 2 files)
```

*FEEDBACK: Let's add result counts and include x of y info in the output. we do have a limit flag so maybe we need to fix docs*  
**Smith:** Confirmed via code — `-n`/`--limit N` exists and `__main__.py:507` already warns "use -n 0 for all results" when capped. This is **documentation debt**, not a missing feature. Three-part fix: (1) add `-n`/`--limit` to the MCP tool description, (2) add `"total": N, "shown": M` fields to JSON response, (3) the CLI warning text should print to stderr so it doesn't corrupt piped output.

There are clearly hundreds of markdown headers in this project, but only 10 come back. There is:
- No `--limit` flag exposed
- No `--offset` or `--page` for pagination
- No `total_count` in the JSON response
- No indication that results were truncated

A user has no way to know whether they got all results or just the first page.

### CONCERN-5: File path queries only match filename, not path segments

**Severity**: Low  
**HCI Heuristic**: #2 Match Between System and Real World

```
["-mg", "via*", "-tF"]  →  []  (no results — "via" matches no filenames)
```

The `-tF` pattern matches against the *filename only*, not the path. A user who wants "all files under `via/pipeline/`" has no native way to express this. They must use a filename extension glob (`*.py`) or the full qualified name.


*FEEDBACK: -Q should match against the full path. maybe needs better docs?*  
**Smith:** `-Q` as the path-scoping mechanism makes sense — the model is already there. The gap is that `-Q` currently enables full-path matching only for the `-tF` type's *anchor* stage (e.g., `README.md -tF -Q` to match `docs/README.md`), but doesn't let you say "scope the whole query to files under `via/pipeline/`". Two things needed: (1) docs clarifying what `-Q` does and doesn't do, (2) decide if `-Q` with a glob like `-mg "via/pipeline/*" -tF -Q` should do directory scoping. If yes, that closes WISH-2 entirely without a new flag.

---

## What Would Be Awesome

### WISH-1: Pagination / `--limit` / `--offset` in MCP responses

The single biggest quality-of-life improvement. Add a `total_count` field to all JSON responses and support `--limit N --offset N` args. This makes via genuinely usable for full codebase traversal:

```
["-mg", "*", "-tH", "--limit", "50", "--offset", "0"]
→ {"result": [...], "total": 347, "limit": 50, "offset": 0}
```

*FEEDBACK: +1 we have limit but not offset - let's add but have it use slice syntax eg: --slice 20:30. We use that for some of the results already i think*  
**Smith:** `--slice` syntax confirmed in the codebase — `parse_line_slice` in `via/core/utils.py` already handles `start:end`, open-ended (`20:`), and single values. Reusing this syntax for result pagination is idiomatic with the rest of via. Proposed: `--slice 20:30` returns results 20-29 of the full result set. Combine with `"total": N` in JSON response. This makes BUG-4 a sprint-ready story with minimal new API surface.

### WISH-2: Path-segment filtering (`--path-contains` or `--path-glob`)

A `--path-contains pipeline` or `--path-glob "via/pipeline/**"` flag would allow scoping any query to a subdirectory. This is the single most common thing you want when navigating a large project:

*FEEDBACK: see -Q*  
**Smith:** Understood — `-Q` with full-path glob matching is the intended mechanism. If `-Q` is extended to match against the full relative path (not just filename), then `["-mg", "via/pipeline/*", "-tF", "-Q"]` would close this wish. WISH-2 becomes: "extend `-Q` semantics + doc it clearly." No new flag needed.

```
# All classes in the pipeline module
["-mg", "*", "-tc", "--path-glob", "via/pipeline/**"]

# All functions called by pipeline code (not tests)
["-mg", "*", "-tf", "--path-contains", "via/", "--path-not-contains", "tests/"]
```

This alone would make via the best codebase navigation tool for complex monorepos.

### WISH-3: Mermaid diagram output via MCP

Even if it can't render as an image, returning Mermaid markup via MCP would let LLMs (and tools like Claude) render the graph in the response. A `--mermaid` or `-oM` flag that outputs Mermaid text would unlock:

```
# Inheritance diagram of all pipeline classes
["-mg", "*", "-tc", "--path-glob", "via/pipeline/**", "-oM"]
→ {"result": "graph TD\n  Executor --> BaseExecutor\n  ..."}
```

*FEEDBACK: +1 (and include output type in mcp json result)*  
**Smith:** Tied to BUG-3 response above — same `{"output_type": "diagram", "result": "..."}` wrapper. Once that wrapper exists, Mermaid output via MCP becomes just passing `-oD` and reading `result` as a string.

### WISH-4: Full-text search within symbol source (`--contains`)

Find all methods whose source code contains a specific string (not just by name):

```
# Find all methods that reference 'check_same_thread'
["-mg", "*", "-tm", "--contains", "check_same_thread"]

# Find all functions that import from specific modules
["-mg", "*", "-tf", "--contains", "from via.db"]
```

This bridges the gap between semantic symbol search and grep-style text search.

*FEEDBACK: Yes but I don't think we can use the sql index for "any string" queries. have morph consider an alternate approach and use a "string" symbol type to fit the --via/--sans model.*  
*FEEDBACK2: We should index actual string constants in source code as a symbol type. Common use case is looking for code that produces some log message. This is distinct from the 'grep for any string' semantics.*  
**Smith:** This is a sharp distinction. Two separate things: (a) "find symbols whose source code contains X" — not feasible with the SQL index, needs Morpheus to design an alternate approach; (b) "find string constants matching pattern X" — feasible as a new `-ts` (type: string_constant) symbol type, indexed like any other symbol. Use case clarity: `["-mg", "User not found", "-ts"]` finds the exact error string and then `--via references` chains to which methods produce it. The log-message lookup case is the killer app. **Recommendation for Morpheus**: design `string_constant` as a new symbol type before attempting full-text search — it's 90% of the value at 20% of the cost.

### WISH-5: Cross-language relationship tracing

Currently, Python→Python and JS→JS relationship queries work. But the most interesting questions cross languages:

```
# Which JS frontend functions call which Python API routes?
# Which Python functions are tested by which JS tests?
```

Even partial support — e.g., tracking `fetch()` calls in JS to Python endpoint function names — would be uniquely powerful.

*FEEDBACK: I like this but this goes beyond language semantics and depends on specific frameworks. Indexing fetch might be a good option. Combined with string constants would help bridge the gap.*  
**Smith:** Agree on the framework dependency problem — full cross-language tracing is a research project. The pragmatic path: (1) index `fetch()`/`axios()`/`XMLHttpRequest` calls in JS as their own relationship type (e.g., `http-calls`), (2) index string constants for URL paths in both Python routes and JS fetch calls, (3) a user can then match them manually via pattern: `["-mg", "/api/query", "-ts"] --via references ["-mg", "*", "-tf"]`. Not automatic, but workable. Frame as "HTTP bridge" not "cross-language tracing."

### WISH-6: Symbol health / dead code detection

A `--unreferenced` or `--unused` filter would identify symbols that are declared but never called or imported anywhere in the codebase:

```
["-mg", "*", "-tf", "--sans", "calls", "-mg", "*", "-tm", "--lang", "py"]
→ Python functions never called by any method
```

The current `--sans` already supports the core idea. An ergonomic shorthand for "find dead code" would make via a linting tool, not just a search tool.

*FEEDBACK: +1 but will only be accurate with respect to the current project. A library might not use its interfaces directly so they might appear unused. Call it "potentially unused" and use --sans to ignore usage in tests only.*  
*FEEDBACK2: Coverage is an important concept here. Let's include code coverage reports in the index. Then we have real data to explore what tests cover which code segments.*  
**Smith:** "Potentially unused" is the right framing — this must be surfaced with a caveat, not as fact. Updated recommendation: add a `--potentially-unused` helper (sugar over `--sans calls`) with a warning in output: "Results are potentially unused within this project; library public APIs may appear here." For coverage: indexing `.coverage` / `coverage.xml` as relationships (`covered-by`) would let you query `["-mg", "*", "-tf", "--sans", "covered-by", "-mg", "*"]` to find untested functions. This is genuinely powerful and fits the `--via`/`--sans` model perfectly. Coverage import is a strong sprint story.


### WISH-7: Saved queries / named query patterns

Power users build up a small repertoire of useful queries. A way to save them:

```bash
via alias class-callers '"-mg", "$1", "-tc", "--via", "calls", "-mg", "*", "-tf"'
```

Or a `.viarc` / `via.config.json` that stores named query templates. This is especially valuable for the MCP use case where agents reuse the same patterns constantly.

*FEEDBACK: I like the idea of custom "canned" queries, keep a local list of named queries that can be customized and invoked like `via --canned "unused"`. Perhaps needs --args (template style). We can provide some useful ones out of the box.*  
**Smith:** `via --canned "unused" --args class=Foo` is a clean mental model. Suggested built-ins to ship: `unused` (potentially unused symbols), `callers` (who calls X), `inheritors` (subclasses of X), `dead-docs` (markdown files with no incoming references). Stored in `.via/canned/` as JSON or TOML — user-customizable, team-shareable. Strong sprint story, low implementation cost once the query engine is stable.

### WISH-8: `declares` relationship for markdown files

Fix BUG-2 as a feature: if `via/pipeline/parser.py` "declares" its functions, then `docs/USER_GUIDE.md` should "declare" its sections. This symmetry would make documentation as navigable as code:

```
["-mg", "USER_GUIDE.md", "-tF", "-Q", "--via", "declares", "-mg", "Installation*", "-tH"]
→ The Installation section of the user guide
```

*FEEDBACK: AGREED, and the string index can be used to find sections that contain specific string values.*  
**Smith:** Agreed — once `string_constant` symbol type exists, you could do: `["-mg", "USER_GUIDE.md", "-tF", "-Q", "--via", "declares", "-mg", "check_same_thread", "-ts"]` to find sections of a doc that reference a specific string. This is documentation search that actually understands structure. Promotes WISH-8 to high priority — it unblocks both code and doc navigation symmetry.

---

## HCI Verdict

| Area | Rating | Notes |
|------|--------|-------|
| Core symbol search | ★★★★★ | Precise, consistent, fast |
| Relationship navigation | ★★★★☆ | Powerful; `--via`/`--sans` syntax takes one read to learn |
| Language filtering | ★★★☆☆ | Works for symbols; broken for file paths |
| Documentation navigation | ★★★☆☆ | Works by header name; `declares` gap breaks discoverability |
| MCP ergonomics | ★★★☆☆ | Always-JSON is fine; silent flag ignore and no pagination hurt |
| Error experience | ★★★★★ | Empty results, never crashes, no raw tracebacks |
| Power user ceiling | ★★★☆☆ | Result cap + no pagination creates a hard wall |

**Overall**: Via is genuinely excellent for what it does. The relationship query model is the best thing about it — `--via calls` and `--sans inherits-from` are powerful primitives that grep cannot replicate. The path-filtering and pagination gaps are the main things that would take it from "very useful" to "irreplaceable."
