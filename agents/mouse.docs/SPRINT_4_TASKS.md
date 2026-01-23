# Sprint 4 Task Breakdown - Tech Debt & Markdown Indexing

**Version**: 1.0
**Date**: 2026-01-22
**Task Owner**: @Mouse
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 4 is a **tech debt sprint** that completes the renderer set, adds markdown indexing, and fills gaps in format support. Total: 26 story points, ~208 hours.

**Sprint Theme**: Complete the tooling and enable markdown search

**Critical Path**: MarkdownParser (P0) → DiagramRenderer → UsageRenderer → Stats

---

## Current State Assessment

### Renderer Implementation Status

| Render Type | Implemented | ASCII | MD | HTML | PNG |
|-------------|-------------|-------|-----|------|-----|
| LIST (-oL) | ✅ | ✅ | - | - | - |
| TABLE (-oT) | ✅ | ✅ | ✅ | ✅ | - |
| RAW (-oR) | ✅ | ✅ | - | - | - |
| FORMATTED (-oF) | ✅ | ✅ | ✅ | ✅ | - |
| DIAGRAM (-oD) | ❌ | - | - | - | - |
| USAGE (-oU) | ❌ | - | - | - | - |

### Tech Debt Backlog

| Item | Source | Priority | Sprint 4? |
|------|--------|----------|-----------|
| DiagramRenderer not implemented | Sprint 3 P1 | P1 | ✅ |
| UsageRenderer not implemented | Sprint 3 P1 | P1 | ✅ |
| Stats command not implemented | Sprint 3 P1 | P1 | ✅ |
| REGEXP SQLite extension | Sprint 3 Known Issue | P3 | ❌ Defer |
| Theme preview command | Sprint 3 P1 | P2 | ❌ Defer |

---

## Sprint 4 Scope

### Story Points Summary

| Story | Points | Priority | Status |
|-------|--------|----------|--------|
| US-MD1: MarkdownParser | 5 | P0 | Ready |
| US-RD1: DiagramRenderer | 5 | P1 | Ready |
| US-RD2: UsageRenderer | 5 | P1 | Ready |
| US-ST1: Stats Command | 3 | P1 | Ready |
| US-TD1: Delimiter Control | 2 | P2 | Ready |
| US-TD2: HeaderMatchRecord | 2 | P2 | Ready |
| US-TD3: Integration Tests | 2 | P2 | Ready |
| US-TD4: Documentation Update | 2 | P2 | Ready |
| **Total** | **26** | | |

---

## Phase 1: MarkdownParser (US-MD1 - P0, 5pts)

**Dependencies**: None (BLOCKER for markdown search)
**Duration**: 5 days (40h)
**Assignee**: @Neo

### Task 1.1: Create MarkdownParser Class (2 days, 16h)

**Files to Create**:
- `via/parsers/markdown_parser.py`

**Implementation Steps**:
1. Create `MarkdownParser` class extending `ParserABC`:
   ```python
   class MarkdownParser(ParserABC):
       HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)(?:\s*#*)?\s*$', re.MULTILINE)
   ```
2. Implement `language_name` property: return `"markdown"`
3. Implement `get_supported_extensions()`: return `['.md', '.markdown', '.mdown', '.mkd']`
4. Implement `can_parse(file_path)`: check extension
5. Implement `parse(file_path, content)`:
   - Track header hierarchy with stack: `List[tuple[int, str]]`
   - For each header match:
     - Extract level (count of `#`)
     - Extract header text
     - Calculate byte_offset and line_number
     - Build qualified_name from ancestor stack
     - Pop headers at same or higher level from stack
     - Push current header to stack
     - Yield `ParsedSymbol` with `symbol_type='header'`
6. Add `extra={'header_level': level}` to ParsedSymbol

**Acceptance Criteria**:
- AC1: Parses all markdown header levels (# through ######)
- AC2: Builds correct qualified_name with ancestors (e.g., "Guide > Getting Started > Installation")
- AC3: Calculates correct byte_offset and line_number
- AC4: Handles edge cases: trailing hashes, inline formatting, empty headers
- AC5: parent_name set to immediate ancestor header

**Tests**:
- `test_parse_single_header()`
- `test_parse_nested_headers()`
- `test_parse_header_levels_1_to_6()`
- `test_header_qualified_name_with_ancestors()`
- `test_header_with_trailing_hashes()`
- `test_header_byte_offset_correct()`
- `test_header_line_number_correct()`

**Estimated**: 16h

---

### Task 1.2: Register MarkdownParser in Discovery (0.5 days, 4h)

**Files to Modify**:
- `via/core/discovery.py`

**Implementation Steps**:
1. Import `MarkdownParser` from `via.parsers.markdown_parser`
2. Add to parser registry:
   ```python
   PARSERS = [
       PythonParser(),
       MarkdownParser(),  # NEW
   ]
   ```
3. Verify file discovery includes `.md` files

**Acceptance Criteria**:
- AC1: MarkdownParser registered and discoverable
- AC2: `via index .` indexes `.md` files
- AC3: No conflicts with existing parsers

**Tests**:
- `test_discovery_includes_markdown_parser()`
- `test_index_includes_md_files()`

**Estimated**: 4h

---

### Task 1.3: Add header_level Column to Database (0.5 days, 4h)

**Files to Modify**:
- `via/db/store.py` (schema)
- `via/services/indexing.py` (insert logic)

**Implementation Steps**:
1. Add `header_level INTEGER` column to symbols table:
   ```sql
   CREATE TABLE IF NOT EXISTS symbols (
       ...existing columns...
       header_level INTEGER  -- NULL for non-headers, 1-6 for headers
   );
   ```
2. Create index for header queries:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_header_level ON symbols(header_level)
   WHERE header_level IS NOT NULL;
   ```
3. Update `_store_parsed_file()` in indexing.py:
   - Extract `header_level` from `entity.extra` if present
   - Include in INSERT statement

**Acceptance Criteria**:
- AC1: header_level column exists in symbols table
- AC2: Index created for header queries
- AC3: Header level stored correctly (1-6)
- AC4: Non-headers have NULL header_level

**Tests**:
- `test_schema_has_header_level_column()`
- `test_header_level_stored_correctly()`
- `test_non_header_has_null_level()`

**Estimated**: 4h

---

### Task 1.4: Add -h and -H Flags to Parser (1 day, 8h)

**Files to Modify**:
- `via/pipeline/parser.py`
- `via/core/types.py`

**Implementation Steps**:
1. Add `HEADER = 'header'` and `HEADERPATH = 'headerpath'` to `SymbolType` enum in types.py
2. Update `_create_match_parser()` in parser.py:
   ```python
   # Header type flags (mirrors -N/-F pattern)
   parser.add_argument('-h', '--header', dest='symbol_type',
                       action='store_const', const='header')
   parser.add_argument('-H', '--header-path', dest='symbol_type',
                       action='store_const', const='headerpath')
   ```
3. Update `_is_match_stage()` to include `-h` and `-H` in match_flags set
4. Update `--help` epilog with header flag documentation

**Acceptance Criteria**:
- AC1: `-h` flag sets symbol_type to 'header'
- AC2: `-H` flag sets symbol_type to 'headerpath'
- AC3: Flags recognized in match stage detection
- AC4: Help text documents header flags

**Tests**:
- `test_parse_header_flag()`
- `test_parse_header_path_flag()`
- `test_is_match_stage_with_header_flags()`

**Estimated**: 8h

---

### Task 1.5: Update Executor for Header Matching (1 day, 8h)

**Files to Modify**:
- `via/pipeline/executor.py`
- `via/db/store.py`

**Implementation Steps**:
1. Update `_execute_match_stage()` in executor.py:
   ```python
   if symbol_type == 'header':
       # Match against symbol_name only (like -N for filename)
       return self.db.match(
           symbol_type='header',
           match_column='symbol_name',
           ...
       )
   elif symbol_type == 'headerpath':
       # Match against qualified_name (like -F for filepath)
       return self.db.match(
           symbol_type='header',
           match_column='qualified_name',
           ...
       )
   ```
2. Update `DatabaseStore.match()` to accept optional `match_column` parameter:
   - Default: `match_column='symbol_name'` (existing behavior)
   - For headerpath: `match_column='qualified_name'`
3. Adjust SQL query to use specified column for pattern matching

**Acceptance Criteria**:
- AC1: `-h` matches against symbol_name (header text only)
- AC2: `-H` matches against qualified_name (full path)
- AC3: Pattern matching works with glob/sql/regex
- AC4: Results include proper metadata

**Tests**:
- `test_match_header_by_name()`
- `test_match_header_by_path()`
- `test_match_header_glob_pattern()`

**Estimated**: 8h

---

### Task 1.6: Create HeaderMatchRecord (0.5 days, 4h)

**Files to Modify**:
- `via/core/match_record.py`

**Implementation Steps**:
1. Create `HeaderMatchRecord` class:
   ```python
   @dataclass
   class HeaderMatchRecord(MatchRecord):
       """Match record for markdown headers."""
       header_level: int = 1  # 1-6

       def supports_render_type(self, render_type: RenderType) -> bool:
           return render_type in {
               RenderType.LIST,
               RenderType.TABLE,
               RenderType.RAW,
               RenderType.FORMATTED,
           }
   ```
2. Update `MatchRecordFactory._RECORD_TYPES`:
   ```python
   'header': HeaderMatchRecord,
   ```
3. Update factory to pass `header_level` from DB row

**Acceptance Criteria**:
- AC1: HeaderMatchRecord created with header_level field
- AC2: Factory creates HeaderMatchRecord for header symbols
- AC3: Supports LIST, TABLE, RAW, FORMATTED renders

**Tests**:
- `test_header_match_record_creation()`
- `test_header_match_record_supports_render_types()`
- `test_factory_creates_header_record()`

**Estimated**: 4h

---

**Phase 1 Total**: 44h (5.5 days)

---

## Phase 2: DiagramRenderer (US-RD1 - P1, 5pts)

**Dependencies**: None (ClassMatchRecord exists)
**Duration**: 5 days (40h)
**Assignee**: @Neo

### Task 2.1: Create Diagram Formatters (1 day, 8h)

**Files to Create**:
- `via/renderers/formatters/diagram_formatters.py`

**Implementation Steps**:
1. Create `MermaidAsciiFormatter`:
   ```python
   class MermaidAsciiFormatter:
       def format_diagram(self, mermaid: str) -> str:
           return mermaid  # Plain text output
   ```
2. Create `MermaidMarkdownFormatter`:
   ```python
   class MermaidMarkdownFormatter:
       def format_diagram(self, mermaid: str) -> str:
           return f"```mermaid\n{mermaid}\n```"
   ```
3. Create `MermaidHtmlFormatter`:
   ```python
   class MermaidHtmlFormatter:
       def format_diagram(self, mermaid: str) -> str:
           return f'''<!DOCTYPE html>
   <html><head>
   <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
   </head><body>
   <div class="mermaid">{mermaid}</div>
   <script>mermaid.initialize({{startOnLoad:true}});</script>
   </body></html>'''
   ```

**Acceptance Criteria**:
- AC1: ASCII formatter returns plain mermaid text
- AC2: Markdown formatter wraps in code fence
- AC3: HTML formatter includes mermaid.js

**Tests**:
- `test_mermaid_ascii_formatter()`
- `test_mermaid_markdown_formatter()`
- `test_mermaid_html_formatter()`

**Estimated**: 8h

---

### Task 2.2: Implement DiagramRenderer (2 days, 16h)

**Files to Create**:
- `via/renderers/diagram.py`

**Implementation Steps**:
1. Create `DiagramRenderer(Renderer)`:
   ```python
   class DiagramRenderer(Renderer):
       def render(self, records: Iterator[MatchRecord], **options) -> str:
           # MUST materialize - need all classes for relationships
           all_records = list(records)
           classes = [r for r in all_records if isinstance(r, ClassMatchRecord)]

           if not classes:
               return "No classes to diagram"

           mermaid = self._generate_mermaid(classes)
           return self.formatter.format_diagram(mermaid)
   ```
2. Implement `_generate_mermaid(classes)`:
   - Start with `classDiagram`
   - For each class:
     - Output `class ClassName {`
     - Output methods with visibility prefix (+/-)
     - Output `}`
   - For inheritance: `Parent <|-- Child`
3. Build class name set for filtering relationships

**Acceptance Criteria**:
- AC1: DiagramRenderer materializes records (uses list())
- AC2: Filters for ClassMatchRecord only
- AC3: Generates valid mermaid classDiagram syntax
- AC4: Shows inheritance relationships
- AC5: Shows methods with visibility
- AC6: Handles empty result gracefully

**Tests**:
- `test_diagram_renderer_materializes()`
- `test_diagram_renderer_filters_classes()`
- `test_diagram_renderer_mermaid_syntax()`
- `test_diagram_renderer_inheritance()`
- `test_diagram_renderer_methods()`
- `test_diagram_renderer_no_classes()`

**Estimated**: 16h

---

### Task 2.3: Implement Lazy Method Loading (1 day, 8h)

**Files to Modify**:
- `via/core/match_record.py`
- `via/db/store.py`

**Implementation Steps**:
1. Update `ClassMatchRecord`:
   ```python
   def get_methods(self, db: 'DatabaseStore') -> List[str]:
       if self._methods is None:
           self._methods = db.get_methods_for_class(self.qualified_name)
       return self._methods
   ```
2. Add to `DatabaseStore`:
   ```python
   def get_methods_for_class(self, class_qualified_name: str) -> List[str]:
       query = """
       SELECT symbol_name FROM symbols
       WHERE symbol_type = 'method' AND parent_name = ?
       ORDER BY line_number
       """
       return [row[0] for row in self.conn.execute(query, (class_qualified_name,))]
   ```

**Acceptance Criteria**:
- AC1: Methods loaded lazily (only when requested)
- AC2: Methods cached after first load
- AC3: Query uses parent_name for filtering

**Tests**:
- `test_lazy_load_methods()`
- `test_methods_cached()`
- `test_get_methods_for_class()`

**Estimated**: 8h

---

### Task 2.4: Register DiagramRenderer in Factory (0.5 days, 4h)

**Files to Modify**:
- `via/renderers/factory.py`

**Implementation Steps**:
1. Import DiagramRenderer and formatters
2. Add DIAGRAM_FORMATTERS lookup table:
   ```python
   DIAGRAM_FORMATTERS = {
       FormatType.ASCII: MermaidAsciiFormatter,
       FormatType.MD: MermaidMarkdownFormatter,
       FormatType.HTML: MermaidHtmlFormatter,
   }
   ```
3. Update `RendererFactory.create()`:
   ```python
   if render_type == RenderType.DIAGRAM:
       formatter_cls = DIAGRAM_FORMATTERS.get(format_type or FormatType.ASCII)
       return DiagramRenderer(formatter_cls())
   ```

**Acceptance Criteria**:
- AC1: Factory creates DiagramRenderer for DIAGRAM type
- AC2: Correct formatter selected based on format_type
- AC3: Default to ASCII formatter

**Tests**:
- `test_factory_creates_diagram_renderer()`
- `test_factory_diagram_with_formats()`

**Estimated**: 4h

---

### Task 2.5: Integration Tests for DiagramRenderer (0.5 days, 4h)

**Files to Create**:
- `tests/integration/test_diagram_renderer.py`

**Test Cases**:
1. `test_diagram_single_class()`
2. `test_diagram_with_inheritance()`
3. `test_diagram_with_methods()`
4. `test_diagram_multiple_classes()`
5. `test_diagram_md_output()`
6. `test_diagram_html_output()`
7. `test_diagram_via_pipeline()`: `via -g '*Renderer' -c --via -oD -m`

**Estimated**: 4h

---

**Phase 2 Total**: 40h (5 days)

---

## Phase 3: UsageRenderer (US-RD2 - P1, 5pts)

**Dependencies**: None
**Duration**: 5 days (40h)
**Assignee**: @Neo

### Task 3.1: Create Usage Formatters (0.5 days, 4h)

**Files to Create**:
- `via/renderers/formatters/usage_formatters.py`

**Implementation Steps**:
1. Create `AsciiUsageFormatter`:
   - Output: `  file.py:42: context line`
2. Create `MarkdownUsageFormatter`:
   - Output: `- [file.py:42](file.py#L42): context`
3. Create `HtmlUsageFormatter`:
   - Output: `<li><a href="...">file.py:42</a>: context</li>`

**Acceptance Criteria**:
- AC1: ASCII formatter outputs readable text
- AC2: Markdown formatter uses links
- AC3: HTML formatter generates valid HTML

**Tests**:
- `test_ascii_usage_formatter()`
- `test_markdown_usage_formatter()`
- `test_html_usage_formatter()`

**Estimated**: 4h

---

### Task 3.2: Implement UsageRenderer (2.5 days, 20h)

**Files to Create**:
- `via/renderers/usage.py`

**Implementation Steps**:
1. Create `UsageRenderer(Renderer)`:
   ```python
   class UsageRenderer(Renderer):
       def render(self, records: Iterator[MatchRecord], **options) -> str:
           outputs = []
           for record in records:
               usages = self._find_usages(record)
               if usages:
                   header = f"# {record.qualified_name} ({record.file_path}:{record.line_number})"
                   usage_lines = self.formatter.format_usages(usages)
                   outputs.append(f"{header}\nUsed in:\n{usage_lines}")
               else:
                   outputs.append(f"# {record.qualified_name}: No usages found")
           return '\n\n'.join(outputs)
   ```
2. Implement `_find_usages()` using grep/ripgrep:
   ```python
   def _find_usages(self, record: MatchRecord) -> List[dict]:
       result = subprocess.run(
           ['rg', '-n', '--no-heading', record.symbol_name, '.'],
           capture_output=True, text=True, timeout=10
       )
       # Parse output, skip definition line
       # Return list of {file, line, context}
   ```
3. Limit results to 20 usages per symbol

**Acceptance Criteria**:
- AC1: UsageRenderer finds usages via grep
- AC2: Skips definition line
- AC3: Limits to 20 usages per symbol
- AC4: Handles timeout gracefully
- AC5: Works with all symbol types that support USAGE

**Tests**:
- `test_usage_renderer_finds_usages()`
- `test_usage_renderer_skips_definition()`
- `test_usage_renderer_limits_results()`
- `test_usage_renderer_no_usages()`
- `test_usage_renderer_timeout_handling()`

**Estimated**: 20h

---

### Task 3.3: Register UsageRenderer in Factory (0.5 days, 4h)

**Files to Modify**:
- `via/renderers/factory.py`

**Implementation Steps**:
1. Import UsageRenderer and formatters
2. Add USAGE_FORMATTERS lookup table
3. Update factory to create UsageRenderer

**Acceptance Criteria**:
- AC1: Factory creates UsageRenderer for USAGE type
- AC2: Correct formatter selected

**Tests**:
- `test_factory_creates_usage_renderer()`

**Estimated**: 4h

---

### Task 3.4: Integration Tests for UsageRenderer (1 day, 8h)

**Files to Create**:
- `tests/integration/test_usage_renderer.py`

**Test Cases**:
1. `test_usage_for_function()`
2. `test_usage_for_class()`
3. `test_usage_for_method()`
4. `test_usage_no_references()`
5. `test_usage_via_pipeline()`: `via -g 'match' -f --via -oU`

**Estimated**: 8h

---

### Task 3.5: Handle Missing ripgrep (0.5 days, 4h)

**Implementation Steps**:
1. Check if `rg` command available
2. Fallback to `grep` if ripgrep not installed
3. Provide helpful error if neither available

**Estimated**: 4h

---

**Phase 3 Total**: 40h (5 days)

---

## Phase 4: Stats Command (US-ST1 - P1, 3pts)

**Dependencies**: None
**Duration**: 3 days (24h)
**Assignee**: @Neo

### Task 4.1: Create Stats Command (1.5 days, 12h)

**Files to Create**:
- `via/commands/stats.py`

**Implementation Steps**:
1. Create `StatsCommand` class:
   ```python
   class StatsCommand:
       def __init__(self, db_store):
           self.db = db_store

       def execute(self, verbose: int = 0, as_json: bool = False) -> str:
           stats = self._gather_stats(verbose)
           if as_json:
               return json.dumps(stats, indent=2)
           return self._format_stats(stats, verbose)
   ```
2. Implement `_gather_stats()`:
   - Basic: total_symbols, total_files
   - Verbose 1: by_type breakdown
   - Verbose 2: top_files by symbol count, last_indexed
   - Verbose 3: full per-file breakdown
3. Implement `_format_stats()` for human-readable output

**Acceptance Criteria**:
- AC1: Basic stats show totals
- AC2: `-v` shows breakdown by type
- AC3: `-vv` shows top files
- AC4: `--json` outputs JSON
- AC5: Output formatted nicely

**Tests**:
- `test_stats_basic()`
- `test_stats_verbose_1()`
- `test_stats_verbose_2()`
- `test_stats_json_output()`

**Estimated**: 12h

---

### Task 4.2: Add Count Methods to DatabaseStore (0.5 days, 4h)

**Files to Modify**:
- `via/db/store.py`

**Implementation Steps**:
1. Add `count_symbols() -> int`
2. Add `count_files() -> int`
3. Add `count_by_type() -> Dict[str, int]`
4. Add `top_files_by_symbols(limit: int) -> List[tuple]`
5. Add `get_last_index_time() -> Optional[str]`

**Acceptance Criteria**:
- AC1: All count methods return correct values
- AC2: Queries are efficient (use indexes)

**Tests**:
- `test_count_symbols()`
- `test_count_files()`
- `test_count_by_type()`
- `test_top_files_by_symbols()`

**Estimated**: 4h

---

### Task 4.3: Wire Stats into CLI (0.5 days, 4h)

**Files to Modify**:
- `via/__main__.py`
- `via/pipeline/executor.py`

**Implementation Steps**:
1. Detect `stats` command in main
2. Execute stats command with appropriate flags
3. Alternative: Wire into pipeline executor for `via stats -v`

**Acceptance Criteria**:
- AC1: `via stats` shows basic stats
- AC2: `via stats -v` shows verbose stats
- AC3: `via stats --json` outputs JSON

**Tests**:
- `test_cli_stats_command()`
- `test_cli_stats_verbose()`

**Estimated**: 4h

---

### Task 4.4: Add Header Stats (0.5 days, 4h)

**Files to Modify**:
- `via/commands/stats.py`

**Implementation Steps**:
1. Include 'header' in symbol type breakdown
2. Add header-specific stats in verbose mode:
   - Count by level (H1, H2, H3, etc.)
   - Top files by header count

**Acceptance Criteria**:
- AC1: Header count included in stats
- AC2: Level breakdown shown in verbose mode

**Tests**:
- `test_stats_includes_headers()`
- `test_stats_header_levels()`

**Estimated**: 4h

---

**Phase 4 Total**: 24h (3 days)

---

## Phase 5: Tech Debt & Polish (US-TD1-4, 8pts)

**Dependencies**: Phases 1-4
**Duration**: 4 days (32h)
**Assignee**: @Neo

### Task 5.1: Delimiter Control (US-TD1 - 2pts, 8h)

**Issue**: Raw/Formatted renderers output delimiter headers between matches. Users may want to disable these for clean output.

**Files to Modify**:
- `via/renderers/raw.py`
- `via/renderers/formatted.py`
- `via/pipeline/parser.py`

**Implementation Steps**:
1. Add `--nodelims` flag to render parser
2. Pass `show_delimiters` option to renderers
3. When `show_delimiters=False`, omit header comments

**Acceptance Criteria**:
- AC1: `--nodelims` flag works
- AC2: Raw output is clean code only
- AC3: Default behavior unchanged (delimiters shown)

**Tests**:
- `test_raw_renderer_nodelims()`
- `test_formatted_renderer_nodelims()`

**Estimated**: 8h

---

### Task 5.2: HeaderMatchRecord Rendering (US-TD2 - 2pts, 8h)

**Issue**: Ensure HeaderMatchRecord works correctly with all supported renderers.

**Implementation Steps**:
1. Test HeaderMatchRecord with ListRenderer
2. Test HeaderMatchRecord with TableRenderer
3. Test HeaderMatchRecord with RawRenderer (output header line + content below)
4. Test HeaderMatchRecord with FormattedRenderer (syntax highlight markdown)
5. Fix any issues found

**Acceptance Criteria**:
- AC1: Headers render correctly in all supported formats
- AC2: Raw output shows header line
- AC3: Formatted output highlights markdown syntax

**Tests**:
- `test_header_list_render()`
- `test_header_table_render()`
- `test_header_raw_render()`
- `test_header_formatted_render()`

**Estimated**: 8h

---

### Task 5.3: Integration Tests (US-TD3 - 2pts, 8h)

**Files to Create**:
- `tests/integration/test_sprint4_pipeline.py`

**Test Cases**:
1. Full markdown indexing flow: `via index . && via -g '*Install*' -h`
2. Header path matching: `via -g '*Guide*API*' -H`
3. Diagram generation: `via -g '*' -c --via -oD -m`
4. Usage search: `via -g 'parse' -f --via -oU`
5. Stats command: `via stats -vv`
6. Mixed pipeline: `via -g '*' -h --via -oT -m`

**Estimated**: 8h

---

### Task 5.4: Documentation Update (US-TD4 - 2pts, 8h)

**Files to Modify**:
- `docs/USER_GUIDE.md`
- `README.md`

**Content to Add**:
1. Markdown indexing section:
   - How to index markdown files
   - `-h` and `-H` flag usage
   - Example queries
2. Diagram generation section:
   - Using `-oD` flag
   - Mermaid output formats
3. Usage search section:
   - Using `-oU` flag
   - Requirements (ripgrep recommended)
4. Stats command section:
   - Verbose levels
   - JSON output

**Acceptance Criteria**:
- AC1: All new features documented
- AC2: Examples tested and working
- AC3: README updated with Sprint 4 highlights

**Estimated**: 8h

---

**Phase 5 Total**: 32h (4 days)

---

## Sprint 4 Summary

### Total Effort by Phase

| Phase | Story | Priority | Points | Hours | Status |
|-------|-------|----------|--------|-------|--------|
| 1 | MarkdownParser | P0 | 5 | 44h | Ready |
| 2 | DiagramRenderer | P1 | 5 | 40h | Ready |
| 3 | UsageRenderer | P1 | 5 | 40h | Ready |
| 4 | Stats Command | P1 | 3 | 24h | Ready |
| 5 | Tech Debt & Polish | P2 | 8 | 32h | Ready |
| **Total** | | | **26** | **180h** | |
| Testing & Buffer | | | | 28h | |
| **Grand Total** | | | **26** | **208h** | |

### Critical Path

```
Phase 1 (MarkdownParser) ──┬─► Phase 5.2 (Header Rendering)
                           │
                           └─► Phase 5.3 (Integration Tests)

Phase 2 (DiagramRenderer) ─┬─► Phase 5.3 (Integration Tests)
                           │
                           └─► Phase 5.4 (Documentation)

Phase 3 (UsageRenderer) ───┬─► Phase 5.3 (Integration Tests)
                           │
                           └─► Phase 5.4 (Documentation)

Phase 4 (Stats) ───────────► Phase 5.4 (Documentation)
```

### Dependencies Graph

```
                    ┌──────────────────┐
                    │ Phase 1: Parser  │  BLOCKER
                    │ (44h, P0)        │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Phase 2: Diagram│ │ Phase 3: Usage  │ │ Phase 4: Stats  │
│ (40h, P1)       │ │ (40h, P1)       │ │ (24h, P1)       │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Phase 5: Polish  │
                    │ (32h, P2)        │
                    └──────────────────┘
```

### Parallelization Opportunities

Phases 2, 3, and 4 can run in parallel after Phase 1 is complete:
- **@Neo-1**: DiagramRenderer (Phase 2)
- **@Neo-2**: UsageRenderer (Phase 3)
- **@Neo-3**: Stats Command (Phase 4)

Or sequentially by single developer: ~26 days @ 8h/day

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Markdown parsing edge cases | Medium | Low | Comprehensive tests, handle gracefully |
| Mermaid syntax issues | Low | Medium | Validate generated syntax |
| ripgrep not available | Medium | Medium | Fallback to grep |
| Performance with large MD files | Low | Medium | Streaming, limits |

### Success Criteria

**Sprint 4 Complete When**:
- [ ] MarkdownParser indexes `.md` files with headers
- [ ] `-h` flag searches header text
- [ ] `-H` flag searches header path (with ancestors)
- [ ] DiagramRenderer outputs mermaid class diagrams
- [ ] UsageRenderer shows symbol references
- [ ] Stats command shows database statistics
- [ ] All new code has 90%+ test coverage
- [ ] Documentation updated with working examples
- [ ] All 26 story points delivered

---

## Appendix: Flag Reference

### After Sprint 4

| Flag | Type | Description |
|------|------|-------------|
| `-c` | class | Match class definitions |
| `-m` | method | Match class methods |
| `-f` | function | Match top-level functions |
| `-i` | import | Match import statements |
| `-G` | global | Match module-level variables |
| `-F` | filepath | Match full file paths |
| `-N` | filename | Match file names only |
| `-h` | header | Match markdown header text |
| `-H` | headerpath | Match full header path with ancestors |

| Flag | Output | Description |
|------|--------|-------------|
| `-oL` | list | One result per line (default) |
| `-oT` | table | ASCII/MD/HTML table |
| `-oR` | raw | Raw source code |
| `-oF` | formatted | Syntax highlighted source |
| `-oD` | diagram | Mermaid class diagram |
| `-oU` | usage | Symbol usage/references |

---

**Status**: Ready for Implementation
**Created**: 2026-01-22
**Author**: @Mouse (Scrum Master)
