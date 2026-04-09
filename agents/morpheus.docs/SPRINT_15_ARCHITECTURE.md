# Sprint 15 — Architecture

**Author**: Morpheus (Tech Lead)
**Date**: 2026-04-08
**Stories**: `agents/cypher.docs/SPRINT_15_USER_STORIES.md`
**Smith Gate 1**: APPROVED (`agents/smith.docs/SPRINT_15_GATE1_REVIEW.md`)

---

## S15-3: Fix `--lang` + `-tF` (1pt)

### Root Cause

`_store_file_path_symbols()` in `indexing.py:470` does NOT pass `language=` to `insert_symbol()`. The `filepath` and `filename` rows in the `symbols` table have `language = NULL`. The executor's `match()` method applies `s.language = ?` which never matches NULL.

### Fix

Pass `parse_result.language` through to `_store_file_path_symbols()`:

```python
# indexing.py _store_symbols():
self._store_file_path_symbols(file_info, parse_result.language)

# indexing.py _store_file_path_symbols():
def _store_file_path_symbols(self, file_info: DiscoveredFile, language: str = None) -> None:
    ...
    self.db_store.insert_symbol(..., language=language)  # for both filename and filepath
```

**No schema change. No new queries. Existing indexes re-populate on next `via index --force`.**

### Migration

Users with existing indexes will need `via index --force` to backfill language on file path symbols. This is acceptable — `via index` is fast and the `--force` flag is documented.

---

## S15-1: `--slice` + `total`/`shown` in JSON (2pt)

### Architecture

#### 1. Flag definition

Add to `flag_groups.py` or parse directly in `pipeline/parser.py`. `--slice` takes a string argument parsed by `parse_line_slice()` (already in `core/utils.py`). Reuse the same function — it handles `start:end`, `start:`, `:end`, and single values.

**Decision**: Rename/alias: create `parse_result_slice()` in `core/utils.py` that wraps `parse_line_slice()` with 0-based semantics (result indices are 0-based, not 1-based like line numbers).

**Storage**: `slice_start: Optional[int]` and `slice_end: Optional[int]` on the match stage args namespace.

#### 2. Total count (already exists)

`COUNT(*) OVER ()` window function is already in the `match()` SQL query at `store.py:701`. `total_matches` is already propagated to `MatchRecord.total_matches`. The CLI warning at `__main__.py:507` already uses it and already writes to stderr. **No work needed on the CLI side.**

#### 3. Slice application

Apply `--slice` as SQL `LIMIT n OFFSET m`:

```python
# store.py match():
if slice_start is not None or slice_end is not None:
    offset = slice_start or 0
    limit = (slice_end - offset) if slice_end is not None else None
    query += f"\nLIMIT {limit or -1} OFFSET {offset}"
```

**Decision**: `--slice` is applied in SQL (not Python-side) because the window function `COUNT(*) OVER()` still computes the full total before LIMIT/OFFSET. This means `total_matches` is always the unsliced total.

**Mutual exclusion**: `--slice` and `-n`/`--limit` cannot coexist. Parse-time error in `pipeline/parser.py`.

#### 4. MCP JSON response

The MCP `via_query()` function in `server.py` must include `total` and `shown`:

```python
results = list(executor.execute(stages) or [])
dicts = [JsonRenderer._to_dict(r) for r in results]
total = results[0].total_matches if results else 0
return {"result": dicts, "total": total, "shown": len(dicts)}
```

**Breaking change**: MCP response changes from `list[dict]` to `dict` with `result`, `total`, `shown` keys. Document in MCP schema.

#### 5. MCP tool description

Update `mcp/schema.py` `build_tool_schema()` to document `-n`/`--limit` and `--slice`.

### Files Changed

| File | Change |
|------|--------|
| `via/core/utils.py` | Add `parse_result_slice()` (0-based wrapper) |
| `via/pipeline/parser.py` | Parse `--slice` into stage args; mutual-exclusion check with `-n` |
| `via/db/store.py` | Apply LIMIT/OFFSET from slice args |
| `via/mcp/server.py` | Wrap response as `{"result": ..., "total": N, "shown": M}` |
| `via/mcp/schema.py` | Document `--slice` and `-n` |
| `via/__main__.py` | Update warning message to mention `--slice` |

---

## S15-2: MCP Output Type Wrapper (2pt)

### Architecture

#### Current behavior

`server.py:124-134` strips all output flags and always returns JSON via `JsonRenderer._to_dict()`.

#### New behavior

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

### Files Changed

| File | Change |
|------|--------|
| `via/mcp/server.py` | Rework `via_query()` to detect output type, capture render output |
| `via/mcp/schema.py` | Document `output_type` in response, document all `-oX` flags |
| `via/core/utils.py` | Add `strip_ansi()` utility if not already in via core |

---

## S15-4: `declares` for Markdown Headers (2pt)

### Root Cause

`_store_declares_relationships()` in `indexing.py:497` iterates over classes, functions, imports, and globals. It does NOT iterate over `parse_result.markdown_headings`. Headers are inserted as symbols but never linked to their file via `declares`.

### Fix

Add a header loop at the end of `_store_declares_relationships()`:

```python
# After the globals loop:
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

### Files Changed

| File | Change |
|------|--------|
| `via/services/indexing.py` | Add header loop in `_store_declares_relationships()` |

---

## S15-5: Extend `-Q` to Full Relative-Path Matching (1pt)

### Current Behavior

For `-tF` queries:
- Without `-Q`: matches against `symbol_name` (filename only, e.g., `executor.py`)
- With `-Q`: matches against `qualified_name` (relative path, e.g., `via/pipeline/executor.py`)

This already works correctly in `store.py:654`:
```python
base_column = "qualified_name" if match_qualified else "symbol_name"
```

### The Real Issue

SQLite GLOB `*` does NOT cross `/` in the way some users expect. In SQLite GLOB, `*` matches **any sequence of characters INCLUDING `/`**. So `via/*` DOES match `via/pipeline/executor.py`.

Wait — **verifying this**: SQLite GLOB `*` matches ANY character sequence (including `/`). So `via -mg 'via/*' -tF -Q` SHOULD already return all files under `via/`. If it doesn't, that's a separate bug.

**Action**: Write a test first. If `-Q -mg 'via/*' -tF` already works, then S15-5 is purely a documentation story. If it doesn't, investigate why.

### Likely Scenario

The issue Smith hit was `via -mg "via*" -tF` WITHOUT `-Q`. That correctly matches nothing because no file is *named* `via*`. With `-Q`, it would match against the qualified_name (relative path). Smith's review didn't test `-mg "via/*" -tF -Q` directly.

### Architecture

**If already working**: Add integration tests proving `-Q` + `-tF` path matching works. Update `--help` text and MCP schema to document the `-Q` + path glob pattern.

**If broken**: Investigate whether the GLOB pattern is applied correctly against `qualified_name`. Fix in `store.py` if needed.

### Files Changed

| File | Change |
|------|--------|
| `via/__main__.py` | Update `-Q` help text with path example |
| `via/mcp/schema.py` | Add `-Q` path-matching example to MCP docs |
| Tests | Integration test: `-mg 'via/pipeline/*' -tF -Q` → returns pipeline files |

---

## S15-6: Improve `--help` (1pt)

### Architecture

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

### Files Changed

| File | Change |
|------|--------|
| `via/__main__.py` | Add relationship examples to `_build_pipeline_help()` |

---

## Dependency Graph

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

## Cycle Plan (Morpheus-approved)

| Cycle | Stories | Risk |
|-------|---------|------|
| 1 | S15-3 + S15-5 + S15-6 | Low — small isolated changes, no new architecture |
| 2 | S15-1 | Medium — touches parser, executor, DB, MCP; breaking MCP response change |
| 3 | S15-2 + S15-4 | Medium — MCP output capture + indexing relationship addition |

---

## Open Risks

1. **S15-1 MCP breaking change**: Response changes from `list[dict]` to `dict`. Any callers that do `response[0]` will break. The MCP tool description should document the new shape. Risk is mitigated by the fact that the only known consumer is Claude Code, which reads `response["result"]`.

2. **S15-2 render capture**: Some renderers may write to `sys.stdout` directly (bypassing the file parameter). Need to verify that `contextlib.redirect_stdout` captures all output from all renderer types. If not, may need to add a `render_to_string()` method to the renderer interface.

3. **S15-4 re-index required**: Like S15-3, users need `via index --force` to populate the new `declares` rows for markdown headers. Existing indexes won't have these rows.

---

## Decisions for Oracle

1. `--slice` uses 0-based result indexing (consistent with Python slicing).
2. MCP response changes to `{"output_type": ..., "result": ..., "total": N, "shown": M}`.
3. Markdown `declares` is flat (one row per header → file), not nested.
4. Empty diagram falls back to JSON with a `note` field.
