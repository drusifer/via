# Sprint 15 — MCP Ergonomics + Index Completeness

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Fix the gaps an expert user found when navigating the project with via's own MCP tool.
**Source**: `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md` + PRD backlog
**Points**: ~11pt
**Baseline**: ~1178 tests (end of Sprint 14)

---

## Sprint Goal

Sprint 14 completed the query surface (JS/TS relationships, `--lang`, `--subtype`, web UI UX). Sprint 15 addresses what an expert user found broken when using via MCP to navigate via's own codebase: results are silently truncated, output format flags do nothing, `--lang` breaks on file path queries, markdown files can't be navigated by structure, and there's no way to scope a query to a directory. These are correctness and discoverability gaps that affect every MCP user daily.

---

## Stories

---

### S15-1: `--slice` Result Windowing + `total_count` in JSON Response (P0, 2pt)

**As a** power user or AI agent using via MCP,
**I want** to know how many total results matched and request a specific window of results,
**so that** I can paginate through large result sets without guessing whether I got everything.

#### Background

`-n`/`--limit N` exists and the CLI already warns when results are capped (`__main__.py:507`). But the MCP tool description doesn't mention it, the JSON response has no `total` field, and there is no offset/pagination mechanism. `parse_line_slice()` in `via/core/utils.py` already handles `start:end` slice syntax — this sprint reuses it for result windowing.

Smith finding: BUG-4 (hard result cap, no pagination, no count).
User directive: "use slice syntax e.g. `--slice 20:30`; we use that for some results already."

#### Acceptance Criteria

1. **`--slice start:end`** is accepted anywhere `-n`/`--limit` is accepted.
   ```
   via -mg '*' -tH --slice 0:20      # first 20 headers
   via -mg '*' -tH --slice 20:40     # next 20 headers
   via -mg '*' -tH --slice 20:       # from result 20 to end
   ```
2. Slice syntax follows `parse_line_slice()` convention: `start:end`, `start:`, `:end`, single integer.
3. **JSON response gains `total` and `shown` fields**:
   ```json
   {"result": [...], "total": 347, "shown": 20}
   ```
   `total` = full match count before slice/limit; `shown` = count in this response.
4. The existing `total` count must not require a second full-table scan — compute it efficiently within the existing query or with a COUNT subquery.
5. **CLI output** (non-JSON): when results are truncated, the existing warning includes the total count:
   ```
   Warning: showing 10 of 347 results. Use --slice 0:50 or -n 0 for all.
   ```
   This warning must be written to **stderr** (not stdout) so it doesn't corrupt piped JSON or text output.
6. **MCP tool description** updated to document `-n`/`--limit` and `--slice`.
7. `--slice` and `-n` are mutually exclusive — using both produces: `"--slice and --limit are mutually exclusive. Use --slice start:end for windowed results."`
8. **Tests**: unit test for `--slice` parsing; integration test verifying `total` and `shown` in JSON output; test that `--slice` and `-n` conflict correctly.

**Files expected to change:**
- `via/core/utils.py` — `parse_line_slice()` already exists; may need a `parse_result_slice()` wrapper
- `via/core/flag_groups.py` — add `--slice` flag definition
- `via/__main__.py` — parse `--slice`, apply to results, emit warning with total
- `via/pipeline/executor.py` or `via/db/store.py` — compute `total` count alongside query results
- `via/mcp/server.py` — update tool description; pass `total`/`shown` in JSON response

---

### S15-2: MCP Output Type Wrapper (P0, 2pt)

**As an** AI agent using via MCP,
**I want** `-oD` and `-oR` to return usable output rather than silently falling back to JSON,
**so that** I can get Mermaid diagrams and raw source from the MCP tool without switching to CLI.

#### Background

All output format flags (`-oD`, `-oR`, `-oF`, `-oT`, `-oL`) are currently ignored via MCP — the tool always returns a JSON array regardless. Users who add `-oD` hoping for a Mermaid diagram get a JSON symbol list with no explanation (BUG-3). User directive: "needs a json wrapper, e.g. `{"output_type": "diagram", "result": "<diagram>"}`. +1 for Mermaid output."

#### Acceptance Criteria

1. **MCP response shape changes** from `{"result": [...]}` to:
   ```json
   {"output_type": "json" | "diagram" | "raw" | "table" | "list" | "usage", "result": <value>}
   ```
   - `"json"` (default): `result` is an array of symbol objects (current behavior, backward compatible)
   - `"diagram"`: `result` is a Mermaid markup string
   - `"raw"`: `result` is a plain-text string of symbol source
   - `"table"`, `"list"`, `"usage"`: `result` is a plain-text string

2. **Backward compatibility**: existing callers that only read `response["result"]` continue to work — in `"json"` mode, `result` is still an array.

3. **`-oD` (diagram)**: Returns valid Mermaid markup in `result`. Agents can render it directly.

4. **`-oR` (raw source)**: Returns concatenated source text for matched symbols.

5. **`-oF` (formatted)**: Returns syntax-highlighted text (ANSI stripped for MCP).

6. **MCP tool description** updated to document all output format flags and the `output_type` response field.

7. **`--slice`/`total`/`shown`** fields are still included in the response regardless of `output_type`.

8. **Tests**: MCP unit tests asserting correct `output_type` for each `-o<X>` flag; backward-compat test asserting `result` is still a list in default mode.

**Files expected to change:**
- `via/mcp/server.py` — wrap response with `output_type`; pass `-o<X>` flags through to renderer
- `via/mcp/schema.py` — update tool schema

---

### S15-3: Fix `--lang` Filter for File Path Queries (`-tF`) (P0, 1pt)

**As a** developer,
**I want** `via -mg '*' -tF --lang py` to return Python files,
**so that** `--lang` works consistently across all symbol types, not just functions and classes.

#### Background

`--lang py` works correctly for `-tc`, `-tf`, `-tm` (symbol queries). It silently returns nothing for `-tF` (file path queries) because the language filter joins `symbols.language` which isn't set for `filepath` pseudo-symbols (BUG-1). Smith workaround: use `*.py -tF` — non-obvious and inconsistent.

#### Acceptance Criteria

1. `via -mg '*' -tF --lang py` returns all indexed Python files.
2. `via -mg '*' -tF --lang md` returns all indexed Markdown files.
3. `via -mg '*' -tF --lang js` returns all JS/TS files.
4. The `--lang` + `-tF` combination applies the filter against `files.language` (not `symbols.language`) for filepath queries.
5. Existing `--lang` behavior for symbol types (`-tc`, `-tf`, etc.) is unchanged.
6. **Tests**: integration test: `--lang py -tF` on a mixed-language fixture returns only `.py` files; same for `--lang js`.

**Files expected to change:**
- `via/db/store.py` or `via/pipeline/executor.py` — fix language filter application for `-tF` queries

---

### S15-4: `declares` Relationship for Markdown Files → Headers (P1, 2pt)

**As a** developer using via to navigate project documentation,
**I want** `via -mg 'USER_GUIDE.md' -tF -Q --via declares -mg '*' -tH` to return the sections of USER_GUIDE.md,
**so that** I can navigate markdown structure the same way I navigate Python class methods.

#### Background

`declares` works for Python: `store.py -tF -Q --via declares -mg '*'` returns all symbols in `store.py`. The same query for a markdown file returns nothing because the indexer doesn't write `symbol_references` rows linking files to their header symbols (BUG-2). Headers exist in the index; the relationship record is just never written.

User directive: "AGREED, and the string index [string constants feature] can be used to find sections that contain specific string values."

#### Acceptance Criteria

1. `via -mg 'README.md' -tF -Q --via declares -mg '*' -tH` returns all headers in `README.md`.
2. `via -mg 'USER_GUIDE.md' -tF -Q --via declares -mg 'Installation*' -tH` returns only Installation-related headers from `USER_GUIDE.md`.
3. The `declares` relationship is written for all markdown headers at index time, using the same `symbol_references` mechanism as Python.
4. **`--sans declares`** works: `via -mg '*.md' -tF --sans declares -mg '*' -tH` returns markdown files with no headers (empty docs).
5. Watch mode: when a `.md` file is re-indexed after header additions/removals, the `declares` rows are updated correctly.
6. **Tests**: unit test — index a markdown file with 3 headers → 3 `declares` rows in DB; integration test — `--via declares` on a `.md` file returns correct headers; regression test — existing Python `declares` behavior unchanged.

**Files expected to change:**
- `via/parsers/markdown_parser.py` — emit `relationship` records for each header
- `via/services/indexing.py` — process markdown relationships (mirror Python/JS flow)
- `via/db/store.py` — confirm `store_references()` handles markdown file path anchors

---

### S15-5: Extend `-Q` to Full Relative-Path Pattern Matching (P1, 1pt)

**As a** developer,
**I want** `via -mg 'via/pipeline/*' -tF -Q` to return all files in the `via/pipeline/` directory,
**so that** I can scope any query to a subdirectory without needing a new flag.

#### Background

`-Q` currently enables full-path matching in the `-tF` type anchor stage — it was designed for `README.md -tF -Q` to disambiguate `docs/README.md` from `README.md`. But `-Q` with a path-segment glob (`via/pipeline/*`) doesn't work because the pattern is matched against filenames only, not the full relative path (CONCERN-5). User directive: "-Q should match against the full path; maybe needs better docs."

#### Acceptance Criteria

1. `via -mg 'via/pipeline/*' -tF -Q` returns all files whose relative path matches `via/pipeline/*`.
2. `via -mg 'tests/**/test_*.py' -tF -Q` returns all test files recursively under `tests/`.
3. `via -mg '*/pipeline/*' -tF -Q` returns files containing `/pipeline/` anywhere in their path.
4. Without `-Q`, `-tF` pattern matching continues to match filenames only (no behavior change for existing users).
5. **`-Q` on symbol types** (`-tc`, `-tf`, etc.): `-Q` continues to match against the fully-qualified symbol name (existing behavior unchanged).
6. **MCP tool description** updated: document `-Q` with a full-path example.
7. **`--help`**: `-Q` description updated to say "match against full relative path for -tF, or fully-qualified name for symbol types."
8. **Tests**: integration test — `via/pipeline/* -tF -Q` on this project returns parser.py, executor.py, relationship_filter.py; test that without `-Q`, the same pattern returns no results (no file named `via/pipeline/*`).

**Files expected to change:**
- `via/db/store.py` or `via/pipeline/executor.py` — apply full-path matching when `-Q` + `-tF`
- `via/__main__.py` — update `-Q` help text
- `via/mcp/schema.py` or `via/mcp/server.py` — update MCP tool description

---

### S15-6: Improve `--help` — Relationship Query Examples Section (P1, 1pt)

**As a** first-time via user,
**I want** `via --help` to show two or three annotated relationship query examples with the direction convention explained,
**so that** I can write a relationship query correctly without reading the full docs.

#### Background

Smith's review found that the "anchor left, wildcard right" rule for `--via`/`--sans` is the hardest thing to learn from `--help` alone (HCI heuristic #6: Recognition over Recall). The current `--help` lists the flags but provides no examples of composed queries. User directive: "improve help output — could make 'learning' easier."

#### Acceptance Criteria

1. `via --help` contains a **"Relationship Queries"** section (after the flag list) with:
   - One-liner rule: *"KNOWN anchor LEFT `--via`/`--sans` wildcard RIGHT."*
   - Valid `<rel>` values listed inline: `inherits-from`, `calls`, `imports`, `references`, `declares`
   - Three annotated examples:
     ```
     # Subclasses of Base:
     via -mg 'Base' -tc --via inherits-from -mg '*' -tc

     # Functions never called (potentially unused):
     via -mg '*' -tf --sans calls -mg '*' -tf

     # All symbols declared in a file:
     via -mg 'myfile.py' -tF -Q --via declares -mg '*'
     ```

2. The section is produced by `_build_pipeline_help()` in `__main__.py` and appears after the flag tables.

3. Total `--help` length increases by at most 20 lines — no bloat.

4. **Tests**: `via --help` output contains the strings `"Relationship Queries"`, `"anchor LEFT"`, and all five relationship type names.

**Files expected to change:**
- `via/__main__.py` — update `_build_pipeline_help()` to add the examples section

---

## Sprint Summary

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| S15-1 | `--slice` windowing + `total`/`shown` in JSON + MCP docs | 2 | P0 |
| S15-2 | MCP output type wrapper (`output_type` in response) | 2 | P0 |
| S15-3 | Fix `--lang` filter for `-tF` file path queries | 1 | P0 |
| S15-4 | `declares` relationship for markdown files → headers | 2 | P1 |
| S15-5 | Extend `-Q` to full relative-path pattern matching | 1 | P1 |
| S15-6 | Improve `--help` with relationship query examples | 1 | P1 |
| **Total** | | **9pt** | |

---

## Backlog Items Deferred to Sprint 16+

These came from Smith's review but require more design work or are lower urgency:

| Item | Source | Notes |
|------|--------|-------|
| String constants as `-ts` symbol type | WISH-4 | Index string literals as queryable symbols. High value; needs Morpheus design (can't use SQL index for arbitrary text). First design decision: what to index (log strings? all string literals? only exported constants?). Assign to Morpheus for Sprint 16 arch spike. |
| Coverage report import (`covered-by` relationship) | WISH-6 | Index `.coverage`/`coverage.xml` as `covered-by` relationships. Enables "find uncovered functions." Strong sprint story once design is settled. |
| URL/link indexing (`link` symbol type) | User feedback | Index hyperlinks in markdown as a `link` symbol type. Enables "which docs reference this URL?" queries. Pairs with string constants sprint. |
| Canned queries (`via --canned "name"`) | WISH-7 | Named query templates stored in `.via/canned/`. Ship with built-in starters (`unused`, `callers`, `inheritors`). |
| Cross-language HTTP bridge (string-constant URL matching) | WISH-5 | Depends on string constants being indexed first. |

---

## Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S15-3 + S15-5 + S15-6 | Small fixes + --help: all touch executor/DB/CLI, no new schema |
| 2 | S15-1 | --slice + total_count: touches flag parsing, executor, JSON output, MCP |
| 3 | S15-2 + S15-4 | MCP wrapper + markdown declares: both are isolated subsystems |

---

## Key Files

| File | Stories |
|------|---------|
| `via/db/store.py` / `via/pipeline/executor.py` | S15-1, S15-3, S15-5 |
| `via/__main__.py` | S15-1, S15-5, S15-6 |
| `via/core/flag_groups.py` | S15-1 |
| `via/core/utils.py` | S15-1 (reuse `parse_line_slice`) |
| `via/mcp/server.py` | S15-1, S15-2 |
| `via/mcp/schema.py` | S15-2, S15-5 |
| `via/parsers/markdown_parser.py` | S15-4 |
| `via/services/indexing.py` | S15-4 |

---

## Open Questions for Smith (Gate 1)

1. **S15-1**: Should `total` include results excluded by `--lang`/`--subtype` filters, or only the final filtered count? Recommend: filtered count (what the user asked for).

2. **S15-2**: When `-oD` returns a Mermaid string and there are no relationships to diagram (e.g., flat symbol list), should via return an empty string, an empty graph `graph TD`, or fall back to `output_type: "json"`? Recommend: empty graph `graph TD\n` with a comment.

3. **S15-4**: Should `declares` for markdown write one row per header (flat), or use the parent header hierarchy (nested `declares`)? Recommend: flat (one row per header, `parent_name` already tracks hierarchy in the symbols table).

4. **S15-6**: Three examples in `--help` or two? Recommend three — the "potentially unused" example is the most compelling real-world case.

@Smith: Please review these stories at Gate 1 before Morpheus begins architecture.
