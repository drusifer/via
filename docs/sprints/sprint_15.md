# Sprint 15 Consolidated Documentation

This document consolidates all documentation for Sprint 15.

## Table of Contents

- [SPRINT_15_CLOSEOUT_2026-04-08T18-24.md](#sprint-15-closeout-2026-04-08t18-24md) (originally `agents/cypher.docs/SPRINT_15_CLOSEOUT_2026-04-08T18-24.md`)

- [SPRINT_15_USER_STORIES.md](#sprint-15-user-storiesmd) (originally `agents/cypher.docs/SPRINT_15_USER_STORIES.md`)

- [SPRINT_15_ARCHITECTURE.md](#sprint-15-architecturemd) (originally `agents/morpheus.docs/SPRINT_15_ARCHITECTURE.md`)

- [SPRINT_15_GATE1_REVIEW.md](#sprint-15-gate1-reviewmd) (originally `agents/smith.docs/SPRINT_15_GATE1_REVIEW.md`)

- [SPRINT_15_SCRUM_CLOSEOUT_Summary_2026-04-08T18-25.md](#sprint-15-scrum-closeout-summary-2026-04-08t18-25md) (originally `agents/mouse.docs/SPRINT_15_SCRUM_CLOSEOUT_Summary_2026-04-08T18-25.md`)

- [SPRINT_15_TASKS.md](#sprint-15-tasksmd) (originally `agents/mouse.docs/SPRINT_15_TASKS.md`)


---


## SPRINT_15_CLOSEOUT_2026-04-08T18-24.md

**Original Location**: `agents/cypher.docs/SPRINT_15_CLOSEOUT_2026-04-08T18-24.md`


## Sprint 15 Closeout

**Author**: Cypher (PM)  
**Date**: 2026-04-08T18:24  
**Sprint**: Sprint 15 — MCP Ergonomics + Index Completeness

### Outcome

Sprint 15 is complete and ready to be marked SHIPPED.

- Delivery completed across 3 implementation cycles.
- QA passed on each cycle.
- Morpheus approved each cycle and declared Sprint 15 complete in `agents/CHAT.md`.
- Latest full test baseline reported in chat: **1235 passed, 1 skipped, 4 warnings**.

### Shipped Stories

| Story | Outcome |
|-------|---------|
| S15-1 | Shipped: `--slice`, `total`, `shown`, mutual exclusion with `-n`, CLI warning fix |
| S15-2 | Shipped: MCP `output_type` wrapper with backward-compatible `result` |
| S15-3 | Shipped: `--lang` works for `-tF` filepath queries |
| S15-4 | Shipped: markdown `declares` returns header structure |
| S15-5 | Closed as docs/help clarification: full-path `-Q` behavior already worked |
| S15-6 | Shipped: relationship-query examples added to `via --help` |

### Product Notes

- Sprint 15 addressed the most important issues from Smith's MCP expert-user review.
- The top user-visible improvements are pagination/windowing, accurate MCP output typing, and markdown structural navigation.
- One implementation note captured by Morpheus remains backlog material: `--slice` is ignored for OR'd type queries and should be treated as a Sprint 16 candidate.

### Deferred / Next Sprint Candidates

- String constants as `-ts`
- Coverage import / `covered-by`
- URL/link indexing
- Canned queries
- OR-query interaction with `--slice`

### Close Recommendation

Sprint 15 should be recorded as SHIPPED and the team should move to:

1. Mouse: archive Sprint 15 board / set Sprint 16 planning entrypoint
2. Oracle: refresh long-lived docs if needed



---


## SPRINT_15_USER_STORIES.md

**Original Location**: `agents/cypher.docs/SPRINT_15_USER_STORIES.md`


## Sprint 15 — MCP Ergonomics + Index Completeness

**Author**: Cypher (PM)
**Date**: 2026-04-08
**Theme**: Fix the gaps an expert user found when navigating the project with via's own MCP tool.
**Source**: `agents/smith.docs/VIA_MCP_EXPERT_USER_REVIEW_2026_04_08.md` + PRD backlog
**Points**: ~11pt
**Baseline**: ~1178 tests (end of Sprint 14)

---

### Sprint Goal

Sprint 14 completed the query surface (JS/TS relationships, `--lang`, `--subtype`, web UI UX). Sprint 15 addresses what an expert user found broken when using via MCP to navigate via's own codebase: results are silently truncated, output format flags do nothing, `--lang` breaks on file path queries, markdown files can't be navigated by structure, and there's no way to scope a query to a directory. These are correctness and discoverability gaps that affect every MCP user daily.

---

### Stories

---

#### S15-1: `--slice` Result Windowing + `total_count` in JSON Response (P0, 2pt)

**As a** power user or AI agent using via MCP,
**I want** to know how many total results matched and request a specific window of results,
**so that** I can paginate through large result sets without guessing whether I got everything.

##### Background

`-n`/`--limit N` exists and the CLI already warns when results are capped (`__main__.py:507`). But the MCP tool description doesn't mention it, the JSON response has no `total` field, and there is no offset/pagination mechanism. `parse_line_slice()` in `via/core/utils.py` already handles `start:end` slice syntax — this sprint reuses it for result windowing.

Smith finding: BUG-4 (hard result cap, no pagination, no count).
User directive: "use slice syntax e.g. `--slice 20:30`; we use that for some results already."

##### Acceptance Criteria

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

#### S15-2: MCP Output Type Wrapper (P0, 2pt)

**As an** AI agent using via MCP,
**I want** `-oD` and `-oR` to return usable output rather than silently falling back to JSON,
**so that** I can get Mermaid diagrams and raw source from the MCP tool without switching to CLI.

##### Background

All output format flags (`-oD`, `-oR`, `-oF`, `-oT`, `-oL`) are currently ignored via MCP — the tool always returns a JSON array regardless. Users who add `-oD` hoping for a Mermaid diagram get a JSON symbol list with no explanation (BUG-3). User directive: "needs a json wrapper, e.g. `{"output_type": "diagram", "result": "<diagram>"}`. +1 for Mermaid output."

##### Acceptance Criteria

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

#### S15-3: Fix `--lang` Filter for File Path Queries (`-tF`) (P0, 1pt)

**As a** developer,
**I want** `via -mg '*' -tF --lang py` to return Python files,
**so that** `--lang` works consistently across all symbol types, not just functions and classes.

##### Background

`--lang py` works correctly for `-tc`, `-tf`, `-tm` (symbol queries). It silently returns nothing for `-tF` (file path queries) because the language filter joins `symbols.language` which isn't set for `filepath` pseudo-symbols (BUG-1). Smith workaround: use `*.py -tF` — non-obvious and inconsistent.

##### Acceptance Criteria

1. `via -mg '*' -tF --lang py` returns all indexed Python files.
2. `via -mg '*' -tF --lang md` returns all indexed Markdown files.
3. `via -mg '*' -tF --lang js` returns all JS/TS files.
4. The `--lang` + `-tF` combination applies the filter against `files.language` (not `symbols.language`) for filepath queries.
5. Existing `--lang` behavior for symbol types (`-tc`, `-tf`, etc.) is unchanged.
6. **Tests**: integration test: `--lang py -tF` on a mixed-language fixture returns only `.py` files; same for `--lang js`.

**Files expected to change:**
- `via/db/store.py` or `via/pipeline/executor.py` — fix language filter application for `-tF` queries

---

#### S15-4: `declares` Relationship for Markdown Files → Headers (P1, 2pt)

**As a** developer using via to navigate project documentation,
**I want** `via -mg 'USER_GUIDE.md' -tF -Q --via declares -mg '*' -tH` to return the sections of USER_GUIDE.md,
**so that** I can navigate markdown structure the same way I navigate Python class methods.

##### Background

`declares` works for Python: `store.py -tF -Q --via declares -mg '*'` returns all symbols in `store.py`. The same query for a markdown file returns nothing because the indexer doesn't write `symbol_references` rows linking files to their header symbols (BUG-2). Headers exist in the index; the relationship record is just never written.

User directive: "AGREED, and the string index [string constants feature] can be used to find sections that contain specific string values."

##### Acceptance Criteria

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

#### S15-5: Extend `-Q` to Full Relative-Path Pattern Matching (P1, 1pt)

**As a** developer,
**I want** `via -mg 'via/pipeline/*' -tF -Q` to return all files in the `via/pipeline/` directory,
**so that** I can scope any query to a subdirectory without needing a new flag.

##### Background

`-Q` currently enables full-path matching in the `-tF` type anchor stage — it was designed for `README.md -tF -Q` to disambiguate `docs/README.md` from `README.md`. But `-Q` with a path-segment glob (`via/pipeline/*`) doesn't work because the pattern is matched against filenames only, not the full relative path (CONCERN-5). User directive: "-Q should match against the full path; maybe needs better docs."

##### Acceptance Criteria

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

#### S15-6: Improve `--help` — Relationship Query Examples Section (P1, 1pt)

**As a** first-time via user,
**I want** `via --help` to show two or three annotated relationship query examples with the direction convention explained,
**so that** I can write a relationship query correctly without reading the full docs.

##### Background

Smith's review found that the "anchor left, wildcard right" rule for `--via`/`--sans` is the hardest thing to learn from `--help` alone (HCI heuristic #6: Recognition over Recall). The current `--help` lists the flags but provides no examples of composed queries. User directive: "improve help output — could make 'learning' easier."

##### Acceptance Criteria

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

### Sprint Summary

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

### Backlog Items Deferred to Sprint 16+

These came from Smith's review but require more design work or are lower urgency:

| Item | Source | Notes |
|------|--------|-------|
| String constants as `-ts` symbol type | WISH-4 | Index string literals as queryable symbols. High value; needs Morpheus design (can't use SQL index for arbitrary text). First design decision: what to index (log strings? all string literals? only exported constants?). Assign to Morpheus for Sprint 16 arch spike. |
| Coverage report import (`covered-by` relationship) | WISH-6 | Index `.coverage`/`coverage.xml` as `covered-by` relationships. Enables "find uncovered functions." Strong sprint story once design is settled. |
| URL/link indexing (`link` symbol type) | User feedback | Index hyperlinks in markdown as a `link` symbol type. Enables "which docs reference this URL?" queries. Pairs with string constants sprint. |
| Canned queries (`via --canned "name"`) | WISH-7 | Named query templates stored in `.via/canned/`. Ship with built-in starters (`unused`, `callers`, `inheritors`). |
| Cross-language HTTP bridge (string-constant URL matching) | WISH-5 | Depends on string constants being indexed first. |

---

### Cycle Plan

| Cycle | Stories | Notes |
|-------|---------|-------|
| 1 | S15-3 + S15-5 + S15-6 | Small fixes + --help: all touch executor/DB/CLI, no new schema |
| 2 | S15-1 | --slice + total_count: touches flag parsing, executor, JSON output, MCP |
| 3 | S15-2 + S15-4 | MCP wrapper + markdown declares: both are isolated subsystems |

---

### Key Files

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

### Open Questions for Smith (Gate 1)

1. **S15-1**: Should `total` include results excluded by `--lang`/`--subtype` filters, or only the final filtered count? Recommend: filtered count (what the user asked for).

2. **S15-2**: When `-oD` returns a Mermaid string and there are no relationships to diagram (e.g., flat symbol list), should via return an empty string, an empty graph `graph TD`, or fall back to `output_type: "json"`? Recommend: empty graph `graph TD\n` with a comment.

3. **S15-4**: Should `declares` for markdown write one row per header (flat), or use the parent header hierarchy (nested `declares`)? Recommend: flat (one row per header, `parent_name` already tracks hierarchy in the symbols table).

4. **S15-6**: Three examples in `--help` or two? Recommend three — the "potentially unused" example is the most compelling real-world case.

@Smith: Please review these stories at Gate 1 before Morpheus begins architecture.


---


## SPRINT_15_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_15_ARCHITECTURE.md`


## Sprint 15 — Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-08
**Stories**: `agents/cypher.docs/SPRINT_15_USER_STORIES.md`
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_15_GATE1_REVIEW.md`)

---

### S15-3: Fix `--lang` + `-tF` (1pt)

#### Root Cause

`_store_file_path_symbols()` in `indexing.py:470` does NOT pass `language=` to `insert_symbol()`. The `filepath` and `filename` rows in the `symbols` table have `language = NULL`. The executor's `match()` method applies `s.language = ?` which never matches NULL.

#### Fix

Pass `parse_result.language` through to `_store_file_path_symbols()`:

```python
## indexing.py _store_symbols():
self._store_file_path_symbols(file_info, parse_result.language)

## indexing.py _store_file_path_symbols():
def _store_file_path_symbols(self, file_info: DiscoveredFile, language: str = None) -> None:
    ...
    self.db_store.insert_symbol(..., language=language)  # for both filename and filepath
```

**No schema change. No new queries. Existing indexes re-populate on next `via index --force`.**

#### Migration

Users with existing indexes will need `via index --force` to backfill language on file path symbols. This is acceptable — `via index` is fast and the `--force` flag is documented.

---

### S15-1: `--slice` + `total`/`shown` in JSON (2pt)

#### Architecture

##### 1. Flag definition

Add to `flag_groups.py` or parse directly in `pipeline/parser.py`. `--slice` takes a string argument parsed by `parse_line_slice()` (already in `core/utils.py`). Reuse the same function — it handles `start:end`, `start:`, `:end`, and single values.

**Decision**: Rename/alias: create `parse_result_slice()` in `core/utils.py` that wraps `parse_line_slice()` with 0-based semantics (result indices are 0-based, not 1-based like line numbers).

**Storage**: `slice_start: Optional[int]` and `slice_end: Optional[int]` on the match stage args namespace.

##### 2. Total count (already exists)

`COUNT(*) OVER ()` window function is already in the `match()` SQL query at `store.py:701`. `total_matches` is already propagated to `MatchRecord.total_matches`. The CLI warning at `__main__.py:507` already uses it and already writes to stderr. **No work needed on the CLI side.**

##### 3. Slice application

Apply `--slice` as SQL `LIMIT n OFFSET m`:

```python
## store.py match():
if slice_start is not None or slice_end is not None:
    offset = slice_start or 0
    limit = (slice_end - offset) if slice_end is not None else None
    query += f"\nLIMIT {limit or -1} OFFSET {offset}"
```

**Decision**: `--slice` is applied in SQL (not Python-side) because the window function `COUNT(*) OVER()` still computes the full total before LIMIT/OFFSET. This means `total_matches` is always the unsliced total.

**Mutual exclusion**: `--slice` and `-n`/`--limit` cannot coexist. Parse-time error in `pipeline/parser.py`.

##### 4. MCP JSON response

The MCP `via_query()` function in `server.py` must include `total` and `shown`:

```python
results = list(executor.execute(stages) or [])
dicts = [JsonRenderer._to_dict(r) for r in results]
total = results[0].total_matches if results else 0
return {"result": dicts, "total": total, "shown": len(dicts)}
```

**Breaking change**: MCP response changes from `list[dict]` to `dict` with `result`, `total`, `shown` keys. Document in MCP schema.

##### 5. MCP tool description

Update `mcp/schema.py` `build_tool_schema()` to document `-n`/`--limit` and `--slice`.

#### Files Changed

| File | Change |
|------|--------|
| `via/core/utils.py` | Add `parse_result_slice()` (0-based wrapper) |
| `via/pipeline/parser.py` | Parse `--slice` into stage args; mutual-exclusion check with `-n` |
| `via/db/store.py` | Apply LIMIT/OFFSET from slice args |
| `via/mcp/server.py` | Wrap response as `{"result": ..., "total": N, "shown": M}` |
| `via/mcp/schema.py` | Document `--slice` and `-n` |
| `via/__main__.py` | Update warning message to mention `--slice` |

---

### S15-2: MCP Output Type Wrapper (2pt)

#### Architecture

##### Current behavior

`server.py:124-134` strips all output flags and always returns JSON via `JsonRenderer._to_dict()`.

##### New behavior

Instead of stripping output flags, detect the requested output type and render accordingly:

```python
@mcp.tool(description=_schema["description"])
def via_query(args: list[str]) -> dict:
    # Detect output format from args
    output_type = _detect_output_type(args)

    if output_type == "json":
        # Current behavior: strip flags, return dicts
        clean_args = [a for a in args if a not in _OUTPUT_FLAGS]
        stages = PipelineParser().parse(clean_args)
        executor = PipelineExecutor(mcp_store)
        results = list(executor.execute(stages) or [])
        dicts = [JsonRenderer._to_dict(r) for r in results]
        total = results[0].total_matches if results else 0
        return {"output_type": "json", "result": dicts, "total": total, "shown": len(dicts)}
    else:
        # Non-JSON: execute with render, capture text output
        stages = PipelineParser().parse(args)
        executor = PipelineExecutor(mcp_store)
        import io
        buf = io.StringIO()
        # Temporarily redirect renderer output to buffer
        rendered = _capture_render(executor, stages, buf)
        return {"output_type": output_type, "result": rendered, "total": 0, "shown": 0}
```

**Key decisions:**

1. **Capture mechanism**: Renderers write to stdout. Use `contextlib.redirect_stdout` + `io.StringIO` to capture. Strip ANSI codes from the captured text.

2. **Output type detection**: Parse `-oX` flags to determine type. Map: `-oD` → `"diagram"`, `-oR` → `"raw"`, `-oF` → `"formatted"` (ANSI stripped), `-oT` → `"table"`, `-oL` → `"list"`, `-oU` → `"usage"`, default → `"json"`.

3. **`total`/`shown` in non-JSON mode**: For rendered output, `total` and `shown` are both 0 (not meaningful for text output).

4. **Empty diagram fallback** (per Smith Gate 1 Q2): Return `{"output_type": "json", "result": [], "note": "No relationships found for diagram output; falling back to JSON."}`.

5. **ANSI stripping**: Use `strip_ansi()` (already in `agents/tools/mkf.py` but we should have a copy in via's core or reuse a simple regex).

#### Files Changed

| File | Change |
|------|--------|
| `via/mcp/server.py` | Rework `via_query()` to detect output type, capture render output |
| `via/mcp/schema.py` | Document `output_type` in response, document all `-oX` flags |
| `via/core/utils.py` | Add `strip_ansi()` utility if not already in via core |

---

### S15-4: `declares` for Markdown Headers (2pt)

#### Root Cause

`_store_declares_relationships()` in `indexing.py:497` iterates over classes, functions, imports, and globals. It does NOT iterate over `parse_result.markdown_headings`. Headers are inserted as symbols but never linked to their file via `declares`.

#### Fix

Add a header loop at the end of `_store_declares_relationships()`:

```python
## After the globals loop:
for heading in parse_result.markdown_headings:
    header_id = self.db_store.get_symbol_id(
        heading.text, 'header', file_info.path, parent_name_for_header
    )
    if header_id:
        _link(header_id)
```

**Design decision (per Smith Gate 1 Q3): Flat, not nested.** Each header gets a `declares` row linking it to the file's filepath and filename symbols. The hierarchy is already captured in `parent_name` on the symbols table. This is consistent with how Python class→method declares works (method→filepath + method→class, but the class→method hierarchy is in `parent_name`).

**Parent name lookup**: Headers use `parent_name` from the hierarchical stack. For `get_symbol_id()`, pass `parent_name` from the header stack context. Since `_store_markdown_headers()` and `_store_declares_relationships()` are called separately, the parent info needs to be accessible. Two options:

- **Option A**: Recompute the header stack in `_store_declares_relationships()`. Simple but duplicates logic.
- **Option B**: Extend `ParseResult.markdown_headings` with a `parent_name` field computed in `_store_markdown_headers()`. Clean but requires touching the data model.

**Decision: Option A** (recompute). The header stack is 5 lines of code. Duplicating it avoids changing `MarkdownHeadingEntity` and `ParseResult`. The declares loop is the only consumer of parent_name for headers.

#### Files Changed

| File | Change |
|------|--------|
| `via/services/indexing.py` | Add header loop in `_store_declares_relationships()` |

---

### S15-5: Extend `-Q` to Full Relative-Path Matching (1pt)

#### Current Behavior

For `-tF` queries:
- Without `-Q`: matches against `symbol_name` (filename only, e.g., `executor.py`)
- With `-Q`: matches against `qualified_name` (relative path, e.g., `via/pipeline/executor.py`)

This already works correctly in `store.py:654`:
```python
base_column = "qualified_name" if match_qualified else "symbol_name"
```

#### The Real Issue

SQLite GLOB `*` does NOT cross `/` in the way some users expect. In SQLite GLOB, `*` matches **any sequence of characters INCLUDING `/`**. So `via/*` DOES match `via/pipeline/executor.py`.

Wait — **verifying this**: SQLite GLOB `*` matches ANY character sequence (including `/`). So `via -mg 'via/*' -tF -Q` SHOULD already return all files under `via/`. If it doesn't, that's a separate bug.

**Action**: Write a test first. If `-Q -mg 'via/*' -tF` already works, then S15-5 is purely a documentation story. If it doesn't, investigate why.

#### Likely Scenario

The issue Smith hit was `via -mg "via*" -tF` WITHOUT `-Q`. That correctly matches nothing because no file is *named* `via*`. With `-Q`, it would match against the qualified_name (relative path). Smith's review didn't test `-mg "via/*" -tF -Q` directly.

#### Architecture

**If already working**: Add integration tests proving `-Q` + `-tF` path matching works. Update `--help` text and MCP schema to document the `-Q` + path glob pattern.

**If broken**: Investigate whether the GLOB pattern is applied correctly against `qualified_name`. Fix in `store.py` if needed.

#### Files Changed

| File | Change |
|------|--------|
| `via/__main__.py` | Update `-Q` help text with path example |
| `via/mcp/schema.py` | Add `-Q` path-matching example to MCP docs |
| Tests | Integration test: `-mg 'via/pipeline/*' -tF -Q` → returns pipeline files |

---

### S15-6: Improve `--help` (1pt)

#### Architecture

Add a `Relationship Queries` section to `_build_pipeline_help()` in `__main__.py`:

```python
help_text += """
  Relationship Queries:
    KNOWN anchor LEFT  --via/--sans  wildcard RIGHT

    # Subclasses of Base:
    via -mg 'Base' -tc --via inherits-from -mg '*' -tc

    # Functions never called (potentially unused):
    via -mg '*' -tf --sans calls -mg '*' -tf

    # All symbols declared in a file:
    via -mg 'myfile.py' -tF -Q --via declares -mg '*'

    Valid relationship types: inherits-from, calls, imports, references, declares
"""
```

Place after the existing flag tables, before the "Format modifiers" section.

#### Files Changed

| File | Change |
|------|--------|
| `via/__main__.py` | Add relationship examples to `_build_pipeline_help()` |

---

### Dependency Graph

```
S15-3 (--lang fix)          ← no dependencies
S15-5 (-Q docs/tests)       ← no dependencies
S15-6 (--help examples)     ← no dependencies
  ↓ (all three can be Cycle 1)
S15-1 (--slice + total)     ← needs S15-3 done (language fix may affect total counts)
  ↓
S15-2 (MCP wrapper)         ← needs S15-1 done (wraps response with total/shown)
S15-4 (md declares)         ← no dependencies, parallel with S15-2
```

---

### Cycle Plan (Morpheus-approved)

| Cycle | Stories | Risk |
|-------|---------|------|
| 1 | S15-3 + S15-5 + S15-6 | Low — small isolated changes, no new architecture |
| 2 | S15-1 | Medium — touches parser, executor, DB, MCP; breaking MCP response change |
| 3 | S15-2 + S15-4 | Medium — MCP output capture + indexing relationship addition |

---

### Open Risks

1. **S15-1 MCP breaking change**: Response changes from `list[dict]` to `dict`. Any callers that do `response[0]` will break. The MCP tool description should document the new shape. Risk is mitigated by the fact that the only known consumer is Claude Code, which reads `response["result"]`.

2. **S15-2 render capture**: Some renderers may write to `sys.stdout` directly (bypassing the file parameter). Need to verify that `contextlib.redirect_stdout` captures all output from all renderer types. If not, may need to add a `render_to_string()` method to the renderer interface.

3. **S15-4 re-index required**: Like S15-3, users need `via index --force` to populate the new `declares` rows for markdown headers. Existing indexes won't have these rows.

---

### Decisions for Oracle

1. `--slice` uses 0-based result indexing (consistent with Python slicing).
2. MCP response changes to `{"output_type": ..., "result": ..., "total": N, "shown": M}`.
3. Markdown `declares` is flat (one row per header → file), not nested.
4. Empty diagram falls back to JSON with a `note` field.


---


## SPRINT_15_GATE1_REVIEW.md

**Original Location**: `agents/smith.docs/SPRINT_15_GATE1_REVIEW.md`


## Sprint 15 — Smith Gate 1 Review

**Date**: 2026-04-08
**Reviewer**: Smith (HCI Expert)
**Stories reviewed**: `agents/cypher.docs/SPRINT_15_USER_STORIES.md`
**Verdict**: **APPROVED**

---

### Story-by-Story Review

#### S15-1: `--slice` windowing + `total`/`shown` — APPROVED

Strong story. The `total`/`shown` fields in JSON directly fix the #1 power-user frustration from the MCP review.

**Notes:**
- AC7 (mutual exclusion of `--slice` and `-n`) is good error prevention. The error message text is clear and actionable.
- Reusing `parse_line_slice()` syntax is the right call — consistency with existing slice behavior (Nielsen #4).
- The CLI warning text in AC5 should go to stderr, not stdout, so piped JSON isn't corrupted. Add this to the AC.

**HCI assessment:** Directly addresses Nielsen #1 (Visibility of System Status) — users will always know "10 of 347."

#### S15-2: MCP output type wrapper — APPROVED

The `output_type` envelope is a clean, backward-compatible design.

**Notes:**
- The ANSI-stripping for `-oF` via MCP (AC5) is the right call — raw ANSI in JSON is unusable.
- Consider: should the MCP tool description list the valid `output_type` values so agents know what to expect? Recommend yes.

**HCI assessment:** Fixes silent flag-ignore (Nielsen #1), makes MCP a first-class output surface.

#### S15-3: Fix `--lang` + `-tF` — APPROVED

Smallest, cleanest story. The diagnosis is correct: `files.language` is the right column for filepath queries.

**No notes.** Ship it.

#### S15-4: `declares` for markdown → headers — APPROVED

This is the symmetry fix that makes documentation navigable as code.

**Notes:**
- Watch mode AC (AC5) is important — headers change frequently during doc editing. Good that it's explicitly called out.

**HCI assessment:** Restores the mental model that `declares` means "things contained in this file" regardless of file type (Nielsen #4).

#### S15-5: Extend `-Q` to full-path matching — APPROVED

**Notes:**
- AC2 (`tests/**/test_*.py`) is the key test — recursive glob via `**` must work. If the existing glob library doesn't support `**`, this could be more than 1pt. Flag for Morpheus.
- The distinction in AC4 (without `-Q`, behavior unchanged) is critical for backward compat.

**HCI assessment:** Makes `-Q` do what users already expect it to do (Nielsen #2, match real-world mental model).

#### S15-6: `--help` relationship examples — APPROVED

**Notes:**
- Three examples is the right number. The "potentially unused" example (`--sans calls`) is the most compelling real-world case — it demonstrates the unique value of via over grep.
- The one-liner rule ("KNOWN anchor LEFT, wildcard RIGHT") should be visually set apart (e.g., indented or in a box-drawing frame) so it's scannable.

**HCI assessment:** Directly addresses Nielsen #6 (Recognition over Recall) and #10 (Help and Documentation).

---

### Open Question Answers

#### Q1: S15-1 — Should `total` include results excluded by `--lang`/`--subtype`?

**Answer: No — `total` should be the filtered count.** Users ask "how many Python classes match?" — they want 47, not "47 of 312 across all languages." The `total` field answers "how many results exist for my query?" not "how many symbols are in the index." Cypher's recommendation is correct.

#### Q2: S15-2 — Empty `-oD` diagram behavior?

**Answer: Return `output_type: "json"` with empty result array.** An empty `graph TD\n` is misleading — it implies there's a graph with no edges, when really there's nothing to diagram. Falling back to JSON with `[]` is honest. Add a `"note": "No relationships found for diagram output; falling back to JSON."` field.

#### Q3: S15-4 — Flat or nested `declares` for markdown headers?

**Answer: Flat.** One `declares` row per header, using the existing `parent_name` column in symbols for hierarchy. This is how Python `declares` works (class→method is flat, parent tracked in `parent_name`). Nesting `declares` (file→h1→h2→h3) would create a different relationship model that doesn't exist for code. Consistency wins. Cypher's recommendation is correct.

#### Q4: S15-6 — Two or three examples?

**Answer: Three.** The `--sans calls` "potentially unused" example is the most compelling demo of via's unique value. Cutting it would remove the strongest argument for why relationship queries matter. Keep all three.

---

### Sprint-Level Assessment

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Story quality | ★★★★★ | All stories traceable to specific bugs/findings from the MCP review |
| Acceptance criteria | ★★★★★ | Specific, testable, with exact CLI examples |
| Scope | ★★★★★ | 9pt is tight and achievable; no scope creep |
| User value | ★★★★★ | Every story directly improves the MCP user experience |
| Backlog management | ★★★★☆ | String constants correctly deferred; could have included link indexing as a stretch goal |

**Overall: APPROVED. Proceed to Morpheus architecture.**

---

### One Amendment (add to S15-1 AC)

> AC5 amendment: The CLI warning ("Warning: showing 10 of 347 results...") must be written to **stderr**, not stdout, so it doesn't corrupt piped JSON or text output.

@Cypher: Please add this stderr constraint to S15-1 AC5 before handing to Morpheus.


---


## SPRINT_15_SCRUM_CLOSEOUT_Summary_2026-04-08T18-25.md

**Original Location**: `agents/mouse.docs/SPRINT_15_SCRUM_CLOSEOUT_Summary_2026-04-08T18-25.md`


## Sprint 15 Scrum Closeout

**Author**: Mouse  
**Date**: 2026-04-08T18:25  
**Sprint**: Sprint 15 — MCP Ergonomics + Index Completeness

### Status

Sprint 15 is complete and archived from the Scrum side.

- Cycle 1 completed, QA passed, lead approved
- Cycle 2 completed, QA passed, lead approved
- Cycle 3 completed, QA passed, lead approved
- PM closeout recorded by Cypher

### Final Delivery Snapshot

- Sprint scope shipped across 3 cycles
- Final reported test baseline in chat: 1235 passed, 1 skipped, 4 warnings
- Remaining note for future planning: `--slice` ignored for OR'd type queries

### Next Coordination Step

- Sprint 16 planning can begin from the current backlog in Cypher/Morpheus docs



---


## SPRINT_15_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_15_TASKS.md`


## Sprint 15 — Task Board

**Sprint**: MCP Ergonomics + Index Completeness
**Points**: 9pt (6 stories)
**Baseline**: 1178 Python + 74 JS + 22 E2E
**Arch**: `morpheus.docs/SPRINT_15_ARCHITECTURE.md`
**Stories**: `cypher.docs/SPRINT_15_USER_STORIES.md`

---

### Cycle 1: Small Fixes (3pt) — S15-3 + S15-5 + S15-6

All independent, no new schema, no new architecture.

#### S15-3: Fix `--lang` + `-tF` (1pt)
- [x] C1-1: Pass `parse_result.language` to `_store_file_path_symbols()` in `indexing.py`
- [x] C1-2: Add integration test: `--lang py -tF` returns only `.py` files
- [x] C1-3: Add integration test: `--lang js -tF` returns only JS/TS files

#### S15-5: Extend `-Q` to Full Path Matching (1pt)
- [x] C1-4: Write test: `-mg 'via/pipeline/*' -tF -Q` → verify current behavior
- [x] C1-5: Fix if broken; if already works, mark as docs-only
- [x] C1-6: Update `-Q` help text in `__main__.py`
- [x] C1-7: Update MCP schema `-Q` description

#### S15-6: `--help` Relationship Examples (1pt)
- [x] C1-8: Add "Relationship Queries" section to `_build_pipeline_help()` in `__main__.py`
- [x] C1-9: Add test: `via --help` output contains `Relationship Queries`, `anchor LEFT`, all 5 rel types

**Exit criteria**: All baseline tests pass + new tests green. Hand to Trin UAT.

---

### Cycle 2: `--slice` + `total`/`shown` (2pt) — S15-1

#### S15-1: `--slice` Result Windowing (2pt)
- [x] C2-1: Add `parse_result_slice()` to `core/utils.py` (0-based wrapper)
- [x] C2-2: Add `--slice` flag to `pipeline/parser.py`; mutual exclusion with `-n`
- [x] C2-3: Apply LIMIT/OFFSET in `store.py` match() from slice args
- [x] C2-4: Wrap MCP response as `{result, total, shown}` in `server.py`
- [x] C2-5: Update CLI warning in `__main__.py` to mention `--slice`
- [x] C2-6: Update MCP tool description in `schema.py`
- [x] C2-7: Tests: slice parsing, total/shown in JSON, --slice + -n conflict

**Exit criteria**: Baseline + new tests pass. MCP response shape verified. Hand to Trin UAT.

---

### Cycle 3: MCP Output Wrapper + Markdown Declares (4pt) — S15-2 + S15-4

#### S15-2: MCP Output Type Wrapper (2pt)
- [x] C3-1: Add `_detect_output_type()` to `server.py`
- [x] C3-2: Implement render capture via `redirect_stdout` + `io.StringIO`
- [x] C3-3: Add `strip_ansi()` to `core/utils.py`
- [x] C3-4: Wrap response with `output_type` field
- [x] C3-5: Handle empty diagram → JSON fallback with `note` field
- [x] C3-6: Update MCP schema to document `output_type` and all `-oX` flags
- [x] C3-7: Tests: each `-oX` flag returns correct `output_type`; backward compat for default

#### S15-4: `declares` for Markdown Headers (2pt)
- [x] C3-8: Add header loop in `_store_declares_relationships()` in `indexing.py`
- [x] C3-9: Unit test: index .md file with 3 headers → 3 `declares` rows
- [x] C3-10: Integration test: `--via declares` on .md file returns headers
- [x] C3-11: Integration test: `--sans declares` on .md returns files with no headers
- [x] C3-12: Regression test: Python `declares` unchanged

**Exit criteria**: All tests pass. MCP output types verified. Markdown declares works end-to-end.

---

### Post-Implementation

- [x] Trin UAT (per cycle)
- [x] Morpheus review (per cycle)
- [ ] Oracle doc groom
- [ ] Smith end-to-end user test
- [x] Cypher launch


---
