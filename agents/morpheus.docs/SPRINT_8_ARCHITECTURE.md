# Sprint 8 Architecture Design — Line Number Index

**Author**: Morpheus (Tech Lead)
**Date**: 2026-03-20
**Status**: ✅ APPROVED — all decisions resolved. Neo cleared to implement.

---

## Context

Sprint 8 adds line-level byte offset indexing so that `via -mL 1:5` can extract
specific lines from any matched symbol or file using the pre-built index — no
file scanning needed for offset lookup.

### What already exists

| Item | Location | Note |
|------|----------|------|
| `files.id` FK anchor | `via/db/schema.py` | All line data will foreign-key here |
| `symbols.byte_offset / byte_length` | `via/db/schema.py` | Per-symbol ranges — same model extended to lines |
| `MATCH_FLAGS (-mg/-mr/-ms)` | `via/core/flag_groups.py` | `-mL` follows same prefix convention |
| `PipelineParser` match parser | `via/pipeline/parser.py` | Will add `-mL` as optional argument |
| `PipelineExecutor.execute()` | `via/pipeline/executor.py` | Will add post-match line slice step |
| `RawRenderer` / `FormattedRenderer` | `via/renderers/` | Already seek to byte_offset — no change needed |
| `SCHEMA_VERSION = 3` | `via/db/schema.py` | Bump to 4 |

---

## Open Questions (need Drew sign-off)

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| **OQ-1** | Are line number slice values **relative to the matched symbol** or **absolute file line numbers**? | ✅ **RELATIVE** — line 1 = first line of the matched thing. For a file, symbol start = line 1 = file line 1, so relative and absolute coincide. For a class at file line 50, `-mL 1:5` = file lines 50-54. |
| **OQ-2** | Index line offsets for ALL indexed files, or only parsed files? | ✅ **ALL text-indexed files** — same gate as symbol indexing (`parsed=True`). Binary/oversized files skipped. |

---

## Design 1: `line_offsets` Table

New table in `via/db/schema.py`. Every indexed line gets one row.

```sql
CREATE TABLE line_offsets (
    file_id     INTEGER NOT NULL,
    line_number INTEGER NOT NULL,   -- 1-based
    byte_offset INTEGER NOT NULL,   -- file byte offset of line start
    byte_length INTEGER NOT NULL,   -- bytes in this line (incl. newline)
    PRIMARY KEY (file_id, line_number),
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_line_offsets_file ON line_offsets(file_id);
```

**FK cascade**: `files ON DELETE CASCADE` — no manual cleanup needed in `delete_file_completely()`.
The FK handles it automatically, matching the existing `symbol_references` pattern.

**Why not store in `files` BLOB?** SQL queries by line number would be impossible.
Clean separate table is consistent with `symbol_references` design.

### Storage estimate

| File size | Lines | Rows | Row size | Total |
|-----------|-------|------|----------|-------|
| 1K lines | 1,000 | 1,000 | ~20 bytes | 20 KB |
| 10K lines | 10,000 | 10,000 | ~20 bytes | 200 KB |
| 100K lines | 100,000 | 100,000 | ~20 bytes | 2 MB |

Acceptable for any reasonably-sized codebase.

### Schema migration

Bump `SCHEMA_VERSION = 3 → 4`. Add migration in `initialize_schema()`:
```python
if current_version < 4:
    conn.execute(CREATE_LINE_OFFSETS_TABLE)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_line_offsets_file ON line_offsets(file_id)")
```

---

## Design 2: Indexing Pass

Add `_index_line_offsets(file_id, content: bytes)` to `IndexingService`.
Called immediately after symbol indexing for a file (same content bytes already in memory).

```python
def _index_line_offsets(self, file_id: int, content: bytes) -> None:
    """Record byte offset of each line start."""
    offsets = []
    pos = 0
    for line_num, line in enumerate(content.splitlines(keepends=True), start=1):
        offsets.append((file_id, line_num, pos, len(line)))
        pos += len(line)
    self._db_store.upsert_line_offsets(file_id, offsets)
```

`splitlines(keepends=True)` handles `\n`, `\r\n`, `\r` correctly. O(file_size) — same as parsing.

### `DatabaseStore` additions

```python
def upsert_line_offsets(self, file_id: int,
                         offsets: list[tuple[int,int,int,int]]) -> None:
    """Insert/replace line offsets for a file (atomic)."""
    with self.transaction():
        self.conn.execute(
            "DELETE FROM line_offsets WHERE file_id = ?", (file_id,)
        )
        self.conn.executemany(
            "INSERT INTO line_offsets (file_id,line_number,byte_offset,byte_length)"
            " VALUES (?,?,?,?)",
            offsets,
        )

def get_line_byte_range(self, file_path: str,
                         abs_start: int, abs_end: int
                         ) -> tuple[int, int]:
    """Return (byte_offset, byte_length) for lines abs_start..abs_end (inclusive, 1-based).

    Returns (0, 0) if file or lines not found.
    """
    row = self.conn.execute("""
        SELECT
            MIN(lo.byte_offset)                                    AS start_off,
            MAX(lo.byte_offset) + MAX(lo.byte_length) -
            MIN(lo.byte_offset)                                    AS length
        FROM line_offsets lo
        JOIN files f ON lo.file_id = f.id
        WHERE f.path = ?
          AND lo.line_number BETWEEN ? AND ?
    """, (file_path, abs_start, abs_end)).fetchone()
    if not row or row[0] is None:
        return (0, 0)
    return (row[0], row[1])

def get_line_count(self, file_path: str) -> int:
    """Return total line count for a file (for negative slice resolution)."""
    row = self.conn.execute("""
        SELECT MAX(lo.line_number)
        FROM line_offsets lo
        JOIN files f ON lo.file_id = f.id
        WHERE f.path = ?
    """, (file_path,)).fetchone()
    return row[0] if row and row[0] else 0
```

**Note**: `delete_file_completely()` does NOT need to change — FK cascade in the DDL
handles `line_offsets` deletion automatically when the `files` row is deleted.

---

## Design 3: `-mL` Flag and Pipeline Integration

### Flag placement

`-mL SLICE` is **not** added to `MATCH_FLAGS` (which is for mutually-exclusive primary
match syntax). Instead it is added directly to `PipelineParser._create_match_parser()` as
an optional standalone argument, similar to `-I`, `-n`, `-Q`:

```python
# in _create_match_parser()
parser.add_argument(
    '-mL', '--match-lines',
    dest='line_slice',
    metavar='SLICE',
    default=None,
    help='Line slice (Python-style): 5:10, 1:, -10:, :20'
)
```

This means `-mL` is always combined with `-mg/-tF` etc.; it does not trigger a new
stage on its own. `_is_match_stage()` requires no change (the `-mg` or `-tF` will
still trigger match detection).

### Slice syntax

```python
# via/core/utils.py — add parse_line_slice()
def parse_line_slice(s: str) -> tuple[Optional[int], Optional[int]]:
    """Parse Python-style slice string into (start, end).

    '5:10'  → (5, 10)    lines 5 through 10 (inclusive, 1-based relative)
    '1:'    → (1, None)   from line 1 to end
    ':5'    → (None, 5)   from start through line 5
    '-10:'  → (-10, None) last 10 lines
    '7'     → (7, 7)      single line 7
    """
    if ':' not in s:
        n = int(s)
        return (n, n)
    left, right = s.split(':', 1)
    start = int(left) if left else None
    end = int(right) if right else None
    return (start, end)
```

### Absolute line resolution

Given a MatchRecord with `line_number = symbol_line` (absolute, 1-based), and a
parsed slice `(rel_start, rel_end)` (1-based relative):

```python
def resolve_abs_lines(symbol_line: int, total_lines: int,
                       rel_start: Optional[int], rel_end: Optional[int],
                       symbol_length_lines: int
                       ) -> tuple[int, int]:
    """Resolve relative slice to absolute file line numbers."""
    # symbol_length_lines = approx lines in symbol (from byte_length + line_offsets)
    # For a file: symbol_line=1, symbol_length_lines=total_lines
    sym_end = symbol_line + symbol_length_lines - 1

    start = (symbol_line + rel_start - 1) if rel_start and rel_start > 0 \
            else (sym_end + rel_start + 1) if rel_start and rel_start < 0 \
            else symbol_line
    end = (symbol_line + rel_end - 1) if rel_end and rel_end > 0 \
          else (sym_end + rel_end + 1) if rel_end and rel_end < 0 \
          else sym_end

    return (max(start, symbol_line), min(end, sym_end))
```

**Simplification**: For the initial implementation, restrict to non-negative slices only.
Negative-index support (last N lines) can be added iteratively. Flag as OQ-3 below.

### PipelineExecutor changes

Add post-match step in `execute()` after MATCH stages:

```python
# in PipelineExecutor.execute()
if last_match_stage and getattr(last_match_stage.args, 'line_slice', None):
    result_iter = self._apply_line_slice(result_iter, last_match_stage.args)
```

```python
def _apply_line_slice(self, records: Iterator[MatchRecord],
                       args: Namespace) -> Iterator[MatchRecord]:
    """Update byte_offset/byte_length on each record to cover the requested lines."""
    slice_str = args.line_slice
    rel_start, rel_end = parse_line_slice(slice_str)

    for record in records:
        # Resolve relative lines to absolute file lines
        abs_start = record.line_number + (rel_start - 1 if rel_start else 0)
        abs_end = record.line_number + (rel_end - 1 if rel_end else 9999)

        new_offset, new_length = self.db.get_line_byte_range(
            record.file_path, abs_start, abs_end
        )
        if new_length > 0:
            record.byte_offset = new_offset
            record.byte_length = new_length
            record.line_number = abs_start
        yield record
```

The updated `byte_offset` / `byte_length` flow straight into `RawRenderer` and
`FormattedRenderer` with **zero changes** to those renderers.

---

## Design 4: Open Questions for Drew

| # | Question | Morpheus recommendation |
|---|----------|------------------------|
| OQ-1 | Relative vs absolute slice? | Relative to symbol start (see above) |
| OQ-2 | Which files to line-index? | All `parsed=True` files |
| **OQ-3** | Negative slice support (last N lines) in Sprint 8 or defer? | **Defer negative indices to Sprint 9 / post-MVP** — requires `get_line_count()` per record, adds DB round-trip. Positive slices cover 95% of use cases. |

---

## Updated File Change Summary

| File | Change |
|------|--------|
| `via/db/schema.py` | Add `CREATE_LINE_OFFSETS_TABLE`, bump `SCHEMA_VERSION` to 4, add to `ALL_TABLES`, add index |
| `via/db/store.py` | Add `upsert_line_offsets()`, `get_line_byte_range()`, `get_line_count()` |
| `via/services/indexing.py` | Add `_index_line_offsets(file_id, content)` called after symbol indexing |
| `via/pipeline/parser.py` | Add `-mL` / `--match-lines` optional arg to `_create_match_parser()` |
| `via/pipeline/executor.py` | Add `_apply_line_slice()`, call after last MATCH stage if `line_slice` present |
| `via/core/utils.py` | Add `parse_line_slice()` |
| `tests/unit/test_line_index.py` | New — schema, store, indexer, slice parser, executor |
| `tests/uat/test_sprint8_uat.py` | New — E2E UAT |

**No new files in `via/`** — all changes slot into existing modules.

---

## Implementation Order for Neo

```
P1 — DB Schema + Indexing (Story 1 prerequisite)
  P1-1  Add CREATE_LINE_OFFSETS_TABLE to schema.py; bump SCHEMA_VERSION → 4
  P1-2  Add migration in DatabaseStore.initialize_schema()
  P1-3  Add upsert_line_offsets() + get_line_byte_range() to store.py
  P1-4  Add _index_line_offsets() to IndexingService._index_file()
  P1-5  Unit tests: schema created, offsets stored, range lookup returns correct bytes
  P1-6  Regression: make test (existing suite green)

P2 — Pipeline Integration (Story 2)
  P2-1  Add parse_line_slice() to via/core/utils.py
  P2-2  Add -mL argument to PipelineParser._create_match_parser()
  P2-3  Add _apply_line_slice() to PipelineExecutor; wire into execute()
  P2-4  Unit tests: slice parsing, round-trip via -mL flag, byte range accuracy
  P2-5  Integration smoke: via -mg 'store.py' -tF -mL 1:5 -oR extracts correct lines

P3 — UAT (Trin)
  P3-1  UAT: file line extraction
  P3-2  UAT: symbol line extraction
  P3-3  UAT: open-ended slices (5:, :10)
  P3-4  Regression: make test full suite
```

---

## Sprint 8 Tech Debt Created

| ID | Item |
|----|------|
| TD-S8-1 | Negative line indices (last N lines) — deferred per OQ-3 |
| TD-S8-2 | Line offset coverage for non-parsed files (binary metadata) — deferred |
