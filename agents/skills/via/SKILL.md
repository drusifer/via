---
name: via
description: Guidelines for writing efficient via relationship queries.
triggers: ["*via", "*via help", "*via query"]
requires: ["bob-protocol", "chat", "make"]
---

# Via — Guidelines for Efficient Relationship Queries

This skill outlines guidelines for writing efficient `via` relationship queries within the project workspace, ensuring optimal token usage, performance, and developer efficiency.

## 1. Declare Direction Properly
When constructing relationship queries with `via`, always declare the query direction properly based on the result-first convention:
- The **result (what gets returned)** is on the left.
- The **relationship** (e.g., `--via <rel>`, `--sans <rel>`) is in the middle.
- The **filter (the anchor/target)** is on the right.

### Correct Direction Patterns:

- **Inheritance**:
  - Finding children (what inherits from parent): `<ChildClass> --via inherits-from <ParentClass>` (e.g., `via -mg '*' -tc --via inherits-from -mg 'ParserABC' -tc`)
  - Finding parents: `<ParentClass> --via inherited-by <ChildClass>` (e.g., `via -mg 'ParserABC' -tc --via inherited-by -mg '*' -tc`)

- **Calls**:
  - Finding callers (what calls callee): `<Caller> --via calls <Callee>` (e.g., `via -mg '*' -tf --via calls -mg 'helper' -tf`)
  - Finding callees (what callee is called by): `<Callee> --via called-by <Caller>` (e.g., `via -mg 'helper' -tf --via called-by -mg '*' -tf`)

- **Imports**:
  - Finding importing files (transitive imports resolution allows file-level queries): `<ImportingFile> --via imports <ImportedModule>` (e.g., `via -mg '*' -tF --via imports -mg 'sqlite3' -ti`)
  - Finding imported modules: `<ImportedModule> --via imported-by <ImportingFile>` (e.g., `via -mg '*' -ti --via imported-by -mg 'via/db/store.py' -tF`)

- **Declares & Declared-In** (Structural Containment):
  - Finding members of a container: `<Container> --via declares <Member>` (e.g., `via -mg 'via/core/*' -tF --via declares -mg '*' -tf`)
  - Finding container of a member: `<Member> --via declared-in <Container>` (e.g., `via -mg 'my_function' -tf --via declared-in -mg '*' -tF`)

## 2. Use Qualified Matching
To refine results and avoid unnecessary matching across large codebases, use qualified matching:
- Use `-Q` or `--qualified` to match symbols against their fully qualified names (such as `Package.Module.ClassName.MethodName`).
- This prevents name collisions, minimizes result sets, and reduces token overhead.

### Example:
```bash
via -mg 'DatabaseStore.connect' -tf -Q --via calls -mg '*' -tf
```

## 3. Prohibited Query Methods & Fallback Rules
To maintain the integrity of the tool and the consistency of the indexing system:
- **MCP vs. CLI Fallback**: If `via: enabled` is set in `agents/PROJECT.md` but the `mcp__via__via_query` tool is missing from your toolset, you **MUST** run `via` queries using the CLI (via the `run_command` tool or `make via` targets) instead of falling back to raw `grep_search` or manual file scanning for symbol lookups.
- **Direct SQLite DB Queries are Forbidden**: DO NOT write direct SQL queries (e.g., `sqlite3 .via/index.db "SELECT ..."` or using Python's `sqlite3` client directly in commands) to fetch relationship or symbol details, except under explicitly authorized gauntlet benchmarks. Always use the `via` command-line interface.
- **Raw File-Reads and Grep Fallbacks are Forbidden for Symbols**: All specialist personas MUST NEVER perform fallback file-reading (e.g., `view_file` or `cat`) or `grep_search` to locate symbol definitions, trace imports, map call sites, or analyze inheritance structures. The `via` query tool is the exclusive and mandatory interface for retrieving code symbols and relationship details.
- **Grep Scope Restriction**: Use `grep_search` ONLY for free-text search inside code (e.g., string literals, comments, logs, or raw SQL queries) or when `via` returns no results.

