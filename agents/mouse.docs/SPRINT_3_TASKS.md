# Sprint 3 Task Breakdown - Internal Pipeline & Render System

**Version**: 1.0
**Date**: 2026-01-16
**Task Owner**: @Mouse
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 3 implements the internal pipeline architecture with polymorphic rendering system. Total: 34 story points, ~68 hours of work.

**Critical Path**: Pipeline → MatchRecord → Streaming → Renderers
**MVP Scope**: 20 P0 story points (Stories 1, 2, 3, 4a, 4b, 9)
**Optional**: 15 P1 story points (Stories 5, 6, 7, 8)

---

## Implementation Phases

### Phase 1: Core Pipeline (Story 1 - P0, 5pts)
**Dependencies**: None (BLOCKER for all other work)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 1.1: Create Pipeline Parser with argparse (2 days, 16h)

**Files to Create**:
- `via/pipeline/__init__.py`
- `via/pipeline/parser.py`
- `via/pipeline/types.py`

**Implementation Steps**:
1. Create `StageType` enum in `types.py`:
   - `MATCH`, `RENDER`, `STATS`
2. Create `PipelineStage` dataclass in `types.py`:
   - Fields: `stage_type: StageType`, `args: argparse.Namespace`
3. Create `PipelineParser` class in `parser.py`:
   - `__init__()`: Create separate ArgumentParser for each stage type
   - `_create_match_parser()`: Build match stage parser with all flags
     - Symbol types: `-c`, `-m`, `-f`, `-i`, `-G`, `-F`, `-N`
     - Match syntax: `-g`, `-r`, `-s` (mutually exclusive)
     - Options: `-I`, `-n`
   - `_create_render_parser()`: Build render stage parser
     - Render types: `-rL`, `-rT`, `-rD`, `-rU`, `-rR`, `-rF`
     - Formats: `-a`, `-m`, `-h`, `-p`
     - Context: `-A`, `-B`, `-C`
     - Theme: `--theme`
   - `_create_stats_parser()`: Build stats stage parser
     - `-v`, `--json`
   - `_split_on_via(argv)`: Split argv on `--via` flags
   - `_parse_stage(args)`: Detect stage type and parse with appropriate parser
   - `parse(argv)`: Main entry point, returns `List[PipelineStage]`
4. Create `PipelineParseError` exception
5. Use `exit_on_error=False` in all ArgumentParser instances
6. Catch `SystemExit` and re-raise as `PipelineParseError`

**Acceptance Criteria**:
- AC1: Parser splits argv on `--via` flags correctly
- AC2: Each stage parsed with appropriate argparse parser
- AC3: Short flags work: `-mg -c '*'` parses to match stage
- AC4: Long flags work: `match --type class --glob '*'` parses correctly
- AC5: Combined flags work: `-rTm` parses to render table in markdown
- AC6: Mutually exclusive groups enforced (e.g., can't use `-g` and `-r` together)
- AC7: Invalid flags raise `PipelineParseError` with helpful message

**Tests**:
- `test_split_on_via()`: Various argv combinations
- `test_parse_match_stage_shorthand()`: `-mg -c '*'`
- `test_parse_match_stage_longform()`: `match --type class --glob '*'`
- `test_parse_render_stage()`: `-rTm`
- `test_parse_multi_stage()`: `['-mg', '-c', '*', '--via', '-rT']`
- `test_invalid_flags_raises_error()`: Invalid combinations
- `test_mutually_exclusive_groups()`: Can't use `-g` and `-r` together

**Estimated**: 16h

---

#### Task 1.2: Create Pipeline Executor (2 days, 16h)

**Files to Create**:
- `via/pipeline/executor.py`

**Implementation Steps**:
1. Create `PipelineExecutor` class:
   - `__init__(db_store: DatabaseStore)`: Store DB reference
   - `execute(stages: List[PipelineStage])`: Main entry point
2. Implement `_execute_match_stage(stage, prev_results)`:
   - If `prev_results` is None: Query database
   - Extract args from `stage.args` (argparse.Namespace)
   - Determine `MatchOp` from flags (glob/regex/sql)
   - Call `db_store.match()` and return iterator
3. Implement `_execute_filter_stage(stage, prev_results)`:
   - For chained match stages (2nd+ match in pipeline)
   - Filter `prev_results` iterator based on stage criteria
   - Apply pattern matching to symbol names
4. Implement `_execute_render_stage(stage, records)`:
   - Extract render type and format from args
   - Get appropriate renderer from factory
   - Build options dict from args (context, theme)
   - Call `renderer.render(records, **options)`
   - Print output to stdout
   - Return (render is terminal stage)
5. Implement `_execute_stats_stage(stage)`:
   - Placeholder for Phase 8
6. Implement default output (no render stage):
   - Print each record using `__str__()` method

**Acceptance Criteria**:
- AC1: Single match stage executes and returns iterator
- AC2: Chained match stages filter previous results
- AC3: Render stage consumes iterator and outputs formatted results
- AC4: Pipeline with no render stage defaults to list output
- AC5: Iterator passed between stages (zero-copy streaming)
- AC6: Each stage properly handles argparse.Namespace objects

**Tests**:
- `test_execute_single_match_stage()`
- `test_execute_chained_match_stages()`
- `test_execute_match_and_render()`
- `test_execute_default_output()`
- `test_filter_by_type_and_pattern()`

**Estimated**: 16h

---

#### Task 1.3: Wire Pipeline into CLI Entry Point (0.5 days, 4h)

**Files to Modify**:
- `via/__main__.py`

**Implementation Steps**:
1. Import `PipelineParser` and `PipelineExecutor`
2. Update `main()` function:
   - Replace old command detection with pipeline parser
   - Create parser: `parser = PipelineParser()`
   - Parse argv: `stages = parser.parse(sys.argv[1:])`
   - Create executor: `executor = PipelineExecutor(db_store)`
   - Execute: `executor.execute(stages)`
3. Add error handling:
   - Catch `PipelineParseError` and print helpful message
   - Exit with code 1 on errors
4. Preserve backward compatibility:
   - `via match -t class -g '*'` should still work (treated as single-stage pipeline)

**Acceptance Criteria**:
- AC1: New pipeline syntax works: `via -mg -c '*' --via -rT`
- AC2: Old syntax works: `via match -t class -g '*'`
- AC3: Error messages are helpful and actionable
- AC4: Exit codes correct (0 success, 1 error)

**Tests**:
- `test_cli_pipeline_execution()`
- `test_cli_backward_compatibility()`
- `test_cli_error_handling()`

**Estimated**: 4h

---

#### Task 1.4: Integration Tests for Pipeline (0.5 days, 4h)

**Files to Create**:
- `tests/integration/test_pipeline.py`

**Test Cases**:
1. `test_simple_match_pipeline()`: `via -mg -c '*'`
2. `test_match_and_render()`: `via -mg -c '*' --via -rL`
3. `test_chained_matches()`: `via -mg -c '*Match*' --via -mr -m '__*__'`
4. `test_full_pipeline()`: `via -mg -c '*' --via -mr -m '*' --via -rT`
5. `test_context_flags()`: `via -mg -f 'calc*' --via -rR -C 5`
6. `test_limit_flag()`: `via -mg -c '*' -n 20`
7. `test_case_insensitive()`: `via -mg -I -c 'user*'`

**Estimated**: 4h

**Phase 1 Total**: 40h (5 days)

---

### Phase 2: Polymorphic MatchRecord System (Story 2 - P0, 5pts)
**Dependencies**: None (can run parallel with Phase 1)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 2.1: Create MatchRecord Base Class and Enums (1 day, 8h)

**Files to Create**:
- `via/core/match_record.py`
- `via/core/constants.py`

**Implementation Steps**:
1. Create enums in `constants.py`:
   - `RenderType`: `LIST`, `TABLE`, `DIAGRAM`, `USAGE`, `RAW`, `FORMATTED`
   - `FormatType`: `ASCII`, `MD`, `HTML`, `PNG`
2. Create `MatchRecord` base class in `match_record.py`:
   - Symbol data fields:
     - `symbol_type: str`
     - `symbol_name: str`
     - `qualified_name: str`
     - `file_path: str`
     - `line_number: int`
     - `byte_offset: Optional[int]`
     - `byte_length: Optional[int]`
     - `parent_name: Optional[str]`
   - Rendering metadata fields:
     - `column_widths: Optional[Dict[str, int]]`
     - `total_matches: Optional[int]`
   - Abstract method: `supports_render_type(render_type: RenderType) -> bool`
   - Implement `__str__()`: Sprint 2 compatible list format
     - Format: `type:file:line:qualified:@byte+len`

**Acceptance Criteria**:
- AC1: Base MatchRecord class is abstract (can't instantiate)
- AC2: All required fields present
- AC3: Metadata fields optional (default None)
- AC4: `__str__()` outputs Sprint 2 compatible format
- AC5: Enums defined for all render types and formats

**Tests**:
- `test_matchrecord_str_format()`
- `test_matchrecord_with_metadata()`
- `test_render_type_enum()`

**Estimated**: 8h

---

#### Task 2.2: Create Derived MatchRecord Classes (1.5 days, 12h)

**Files to Modify**:
- `via/core/match_record.py`

**Implementation Steps**:
1. Create `ClassMatchRecord`:
   - Additional fields: `base_classes: Optional[List[str]]`, `methods: Optional[List[str]]`
   - `supports_render_type()`: LIST, TABLE, DIAGRAM, USAGE, RAW, FORMATTED
   - `get_methods(db)`: Lazy load methods for diagram rendering
2. Create `MethodMatchRecord`:
   - `supports_render_type()`: LIST, TABLE, USAGE, RAW, FORMATTED
3. Create `FunctionMatchRecord`:
   - `supports_render_type()`: LIST, TABLE, USAGE, RAW, FORMATTED
4. Create `FileMatchRecord`:
   - `supports_render_type()`: LIST, TABLE, RAW
5. Create `ImportMatchRecord`:
   - `supports_render_type()`: LIST, TABLE, USAGE, RAW
6. Create `GlobalMatchRecord`:
   - `supports_render_type()`: LIST, TABLE, RAW, FORMATTED

**Acceptance Criteria**:
- AC1: All 6 derived classes created
- AC2: Each class correctly reports supported render types
- AC3: ClassMatchRecord has lazy method loading
- AC4: All classes inherit from MatchRecord
- AC5: Each class uses `@dataclass` decorator

**Tests**:
- `test_class_match_record_supports_diagram()`
- `test_method_match_record_no_diagram()`
- `test_file_match_record_supports_raw()`
- `test_import_match_record_supports_usage()`
- `test_global_match_record_supports_formatted()`
- `test_lazy_load_methods()`

**Estimated**: 12h

---

#### Task 2.3: Create MatchRecordFactory (1 day, 8h)

**Files to Modify**:
- `via/core/match_record.py`

**Implementation Steps**:
1. Create `MatchRecordFactory` class:
   - Class variable: `_RECORD_TYPES` dict mapping symbol_type to class
   - `create_from_row(row: sqlite3.Row, metadata: Optional[Dict]) -> MatchRecord`
2. Implementation:
   - Extract `symbol_type` from row
   - Lookup record class in `_RECORD_TYPES`
   - Create instance with all fields from row
   - Attach metadata (column_widths, total_matches)
   - Return instance
3. Handle unknown symbol types (raise ValueError)

**Acceptance Criteria**:
- AC1: Factory creates correct MatchRecord subclass based on symbol_type
- AC2: All fields from DB row mapped to record fields
- AC3: Metadata attached when provided
- AC4: Unknown symbol types raise ValueError with helpful message
- AC5: Factory is reusable (no state)

**Tests**:
- `test_factory_creates_class_record()`
- `test_factory_creates_method_record()`
- `test_factory_creates_file_record()`
- `test_factory_with_metadata()`
- `test_factory_without_metadata()`
- `test_factory_unknown_type_raises_error()`

**Estimated**: 8h

---

#### Task 2.4: Update DatabaseStore to Use Factory (1 day, 8h)

**Files to Modify**:
- `via/database/store.py`

**Implementation Steps**:
1. Import `MatchRecordFactory` and `MatchRecord`
2. Create factory instance in `DatabaseStore.__init__()`
3. Update `match()` method signature:
   - Return type: `Iterator[MatchRecord]` (instead of raw rows)
4. Implementation (placeholder for metadata, will complete in Phase 3):
   - Execute query (existing logic)
   - For each row:
     - Call `factory.create_from_row(row, metadata=None)`
     - Yield MatchRecord
5. Note: Metadata computation will be added in Task 3.1

**Acceptance Criteria**:
- AC1: `match()` returns `Iterator[MatchRecord]`
- AC2: Factory used to create records from DB rows
- AC3: All existing tests still pass
- AC4: Records can be printed using `__str__()`

**Tests**:
- `test_match_returns_matchrecords()`
- `test_match_creates_correct_record_type()`
- `test_backward_compatibility_with_sprint2()`

**Estimated**: 8h

---

#### Task 2.5: Integration Tests for MatchRecord System (0.5 days, 4h)

**Files to Create**:
- `tests/integration/test_match_records.py`

**Test Cases**:
1. `test_match_returns_correct_record_types()`: Verify factory creates right classes
2. `test_record_str_format_compatible_with_sprint2()`: Backward compatibility
3. `test_supports_render_type_for_all_types()`: Each type reports correctly
4. `test_lazy_load_methods_for_classes()`: ClassMatchRecord.get_methods()

**Estimated**: 4h

**Phase 2 Total**: 40h (5 days)

---

### Phase 3: Streaming & Metadata Query (Story 9 - P0, 2pts)
**Dependencies**: Phase 2 (needs MatchRecord)
**Duration**: 2 days (16h)
**Assignee**: @Neo

#### Task 3.1: Implement Metadata Computation in DatabaseStore (1.5 days, 12h)

**Files to Modify**:
- `via/database/store.py`

**Implementation Steps**:
1. Create `_get_match_metadata()` method:
   - Parameters: `symbol_type`, `match_op`, `pattern`, `case_sensitive`
   - Query: Single aggregation with COUNT and MAX(LENGTH(...)) for all columns
   - Return dict with:
     - `total_matches`: Total count
     - `column_widths`: Dict with max widths (name, qualified, file, type, parent, line)
2. Update `match()` method:
   - Before streaming results: Call `_get_match_metadata()`
   - Pass metadata to factory: `factory.create_from_row(row, metadata)`
3. Create `_stream_match_results()` method:
   - Extract existing query logic
   - Apply limit parameter
   - Yield rows from cursor

**Acceptance Criteria**:
- AC1: Metadata query runs BEFORE result streaming
- AC2: Metadata contains total_matches and column_widths
- AC3: Each MatchRecord has metadata attached
- AC4: Metadata query overhead is ~5-10ms (measure with EXPLAIN QUERY PLAN)
- AC5: Results still stream lazily (don't materialize)

**Tests**:
- `test_metadata_computed_before_streaming()`
- `test_metadata_contains_correct_fields()`
- `test_column_widths_reflect_all_matches()`
- `test_total_matches_accurate()`
- `test_metadata_query_performance()`

**Estimated**: 12h

---

#### Task 3.2: Add Limit Parameter and Default (0.5 days, 4h)

**Files to Modify**:
- `via/database/store.py`
- `via/pipeline/executor.py`

**Implementation Steps**:
1. Update `DatabaseStore.match()`:
   - Add `limit: int = 10` parameter
   - Apply limit in `_stream_match_results()` query
   - Document: `-n 0` means no limit
2. Update `PipelineExecutor._execute_match_stage()`:
   - Extract limit from `stage.args.limit` (default 10)
   - Pass to `db_store.match()`
3. Handle `-n 0` for unlimited results:
   - If limit == 0: Use `LIMIT -1` in SQL (SQLite unlimited)

**Acceptance Criteria**:
- AC1: Default limit is 10 matches
- AC2: `-n 20` returns 20 matches
- AC3: `-n 0` returns all matches
- AC4: `-n 1` returns single match

**Tests**:
- `test_default_limit_is_10()`
- `test_custom_limit()`
- `test_unlimited_results()`
- `test_single_result()`

**Estimated**: 4h

**Phase 3 Total**: 16h (2 days)

---

### Phase 4: List & Table Renderers (Story 3 - P0, 3pts)
**Dependencies**: Phase 2 (needs MatchRecord), Phase 3 (needs metadata)
**Duration**: 3 days (24h)
**Assignee**: @Neo

#### Task 4.1: Create Renderer Base Class and Factory (0.5 days, 4h)

**Files to Create**:
- `via/renderers/__init__.py`
- `via/renderers/base.py`
- `via/renderers/factory.py`

**Implementation Steps**:
1. Create `Renderer` abstract base class in `base.py`:
   - `__init__(formatter: Formatter)`: Store formatter
   - Abstract method: `render(records: Iterator[MatchRecord], **options) -> str`
2. Create `RendererFactory` in `factory.py`:
   - `create(render_type: RenderType, format_type: FormatType) -> Renderer`
   - Registry of renderer classes
   - Handle invalid combinations (e.g., list only supports ASCII)

**Acceptance Criteria**:
- AC1: Renderer base class is abstract
- AC2: Factory creates correct renderer for type+format combo
- AC3: Invalid combinations raise helpful error

**Tests**:
- `test_renderer_factory_creates_list_renderer()`
- `test_renderer_factory_creates_table_renderer()`
- `test_renderer_factory_invalid_combo_raises_error()`

**Estimated**: 4h

---

#### Task 4.2: Implement ListRenderer (0.5 days, 4h)

**Files to Create**:
- `via/renderers/list.py`

**Implementation Steps**:
1. Create `ListRenderer(Renderer)`:
   - `render(records, **options)`:
     - Stream records
     - For each record: call `str(record)` and append to lines
     - Track count
     - If `total_matches > count`: Add "... (N more)" indicator
     - Return joined lines
2. No formatter needed (just uses `__str__()`)

**Acceptance Criteria**:
- AC1: Outputs one line per record
- AC2: Format matches Sprint 2 output: `type:file:line:qualified:@byte+len`
- AC3: Shows "... (N more)" when results limited
- AC4: Streams records (O(1) memory)

**Tests**:
- `test_list_renderer_basic_output()`
- `test_list_renderer_with_limit()`
- `test_list_renderer_more_indicator()`
- `test_list_renderer_streams()`

**Estimated**: 4h

---

#### Task 4.3: Implement TableRenderer (1.5 days, 12h)

**Files to Create**:
- `via/renderers/table.py`
- `via/renderers/formatters/__init__.py`
- `via/renderers/formatters/table_formatters.py`

**Implementation Steps**:
1. Create `TableFormatter` base class in `table_formatters.py`:
   - Abstract method: `format_header(widths: Dict[str, int]) -> str`
   - Abstract method: `format_row(record: MatchRecord, widths: Dict[str, int]) -> str`
   - Abstract method: `format_footer(count: int, total: int) -> str`
2. Create `AsciiTableFormatter`:
   - Pipe-separated columns with padding
   - Header with separator line
   - Footer with "... (N more)" if needed
3. Create `MarkdownTableFormatter`:
   - Markdown table syntax
   - Header with `|---|` separator
4. Create `HtmlTableFormatter`:
   - HTML `<table>` with `<thead>` and `<tbody>`
   - Basic CSS classes for styling
5. Create `TableRenderer(Renderer)`:
   - `render(records, **options)`:
     - On first record: Extract metadata (column_widths, total_matches)
     - Render header using formatter
     - For each record: Render row using formatter
     - Track count
     - Render footer with count/total
     - Return formatted table
6. Handle missing metadata:
   - Fallback to default widths if metadata not present

**Acceptance Criteria**:
- AC1: TableRenderer streams records (no materialization)
- AC2: Column widths from metadata used for all rows
- AC3: Header rendered on first record
- AC4: Footer shows "... (N more)" indicator
- AC5: ASCII format works in terminal
- AC6: Markdown format valid
- AC7: HTML format valid

**Tests**:
- `test_table_renderer_streams()`
- `test_table_renderer_uses_metadata_widths()`
- `test_table_renderer_ascii_format()`
- `test_table_renderer_markdown_format()`
- `test_table_renderer_html_format()`
- `test_table_renderer_more_indicator()`
- `test_table_renderer_fallback_widths()`

**Estimated**: 12h

---

#### Task 4.4: Wire Renderers into Pipeline (0.5 days, 4h)

**Files to Modify**:
- `via/pipeline/executor.py`

**Implementation Steps**:
1. Import `RendererFactory`
2. Update `_execute_render_stage()`:
   - Extract render_type and format from `stage.args`
   - Call `RendererFactory.create(render_type, format_type)`
   - Extract options from args (limit, etc.)
   - Call `renderer.render(records, **options)`
   - Print output

**Acceptance Criteria**:
- AC1: Render stages use factory to create renderer
- AC2: Options passed correctly to renderer
- AC3: Output printed to stdout

**Tests**:
- `test_executor_uses_renderer_factory()`
- `test_executor_passes_options_to_renderer()`

**Estimated**: 4h

**Phase 4 Total**: 24h (3 days)

---

### Phase 5: Raw Renderer (Story 4a - P0, 2pts)
**Dependencies**: Phase 4 (needs renderer framework)
**Duration**: 2 days (16h)
**Assignee**: @Neo

#### Task 5.1: Implement RawRenderer (2 days, 16h)

**Files to Create**:
- `via/renderers/raw.py`

**Implementation Steps**:
1. Create `RawRenderer(Renderer)`:
   - `render(records, **options)`:
     - Extract context options (-A/-B/-C)
     - For each record:
       - Call `_extract_source()` to get raw code
       - Append to outputs (no formatting)
     - Join outputs with single newline
     - Return raw text
2. Implement `_extract_source()`:
   - Parameters: file_path, byte_offset, byte_length, context_before, context_after
   - Open file in binary mode
   - If byte_offset is None (FileMatchRecord): Read entire file
   - Else: Seek to byte_offset, read byte_length
   - Decode as UTF-8
   - Return raw source string
3. Implement context line extraction:
   - Scan backwards from byte_offset for N newlines (-B context)
   - Scan forwards after byte_offset+byte_length for N newlines (-A context)
   - Include context lines in output
4. Handle special cases:
   - FileMatchRecord: Read entire file
   - ImportMatchRecord: Extract import statement (single line)

**Acceptance Criteria**:
- AC1: RawRenderer supports ALL symbol types
- AC2: Output is truly raw (no colors, no line numbers, no formatting)
- AC3: Context lines work (-A/-B/-C flags)
- AC4: FileMatchRecord reads entire file
- AC5: ImportMatchRecord extracts import statement
- AC6: Streams records (O(1) memory)
- AC7: Output suitable for piping to other tools

**Tests**:
- `test_raw_renderer_class_source()`
- `test_raw_renderer_method_source()`
- `test_raw_renderer_function_source()`
- `test_raw_renderer_file_source()`
- `test_raw_renderer_import_source()`
- `test_raw_renderer_context_lines()`
- `test_raw_renderer_no_formatting()`
- `test_raw_renderer_streams()`

**Estimated**: 16h

**Phase 5 Total**: 16h (2 days)

---

### Phase 6: Formatted Renderer (Story 4b - P0, 3pts)
**Dependencies**: Phase 5 (can reuse extraction logic)
**Duration**: 3 days (24h)
**Assignee**: @Neo

#### Task 6.1: Integrate Pygments (0.5 days, 4h)

**Files to Create**:
- `via/renderers/formatters/code_formatters.py`

**Implementation Steps**:
1. Add `pygments` to dependencies in `pyproject.toml`
2. Create `CodeFormatter` base class in `code_formatters.py`:
   - Abstract method: `format_code(source: str, language: str, start_line: int, theme: str, show_line_numbers: bool) -> str`
3. Create `AsciiCodeFormatter`:
   - Use Pygments `TerminalFormatter` or `Terminal256Formatter`
   - Add line numbers manually (Pygments linenos=True doesn't fit our needs)
   - Support theme selection
4. Create `HtmlCodeFormatter`:
   - Use Pygments `HtmlFormatter`
   - Include CSS for styling
5. Create `MarkdownCodeFormatter`:
   - Format as markdown code block with language hint
   - Add line numbers as comments

**Acceptance Criteria**:
- AC1: Pygments installed and importable
- AC2: Code formatters support Python syntax highlighting
- AC3: ASCII formatter works in terminal
- AC4: HTML formatter generates valid HTML
- AC5: Markdown formatter generates valid markdown

**Tests**:
- `test_ascii_code_formatter()`
- `test_html_code_formatter()`
- `test_markdown_code_formatter()`
- `test_code_formatter_line_numbers()`

**Estimated**: 4h

---

#### Task 6.2: Implement FormattedRenderer (1.5 days, 12h)

**Files to Create**:
- `via/renderers/formatted.py`

**Implementation Steps**:
1. Create `FormattedRenderer(Renderer)`:
   - `__init__(formatter: CodeFormatter)`
   - `render(records, **options)`:
     - Extract context options (-A/-B/-C)
     - Extract theme option (--theme, default 'auto')
     - For each record:
       - Validate record type (only class/method/function/global)
       - Call `_extract_source()` (reuse from RawRenderer or import)
       - Format with Pygments via formatter
       - Add header with symbol info (qualified name, file:line)
       - Append to outputs
     - Join outputs with double newline
     - Return formatted string
2. Implement `_extract_source()`:
   - Copy logic from RawRenderer
   - Or import and reuse (refactor to shared utility)
3. Add header formatting:
   - Header: `# {qualified_name} ({file_path}:{line_number})`
   - Separator line
4. Handle unsupported types:
   - If FileMatchRecord or ImportMatchRecord: Skip with warning

**Acceptance Criteria**:
- AC1: FormattedRenderer only accepts code symbols (class/method/function/global)
- AC2: Output has syntax highlighting via Pygments
- AC3: Line numbers shown correctly
- AC4: Header with symbol info displayed
- AC5: Context lines work (-A/-B/-C)
- AC6: Theme selection works (--theme flag)
- AC7: Streams records (O(1) memory)

**Tests**:
- `test_formatted_renderer_class_source()`
- `test_formatted_renderer_method_source()`
- `test_formatted_renderer_syntax_highlighting()`
- `test_formatted_renderer_line_numbers()`
- `test_formatted_renderer_header()`
- `test_formatted_renderer_context_lines()`
- `test_formatted_renderer_theme_selection()`
- `test_formatted_renderer_rejects_file_type()`

**Estimated**: 12h

---

#### Task 6.3: Implement Theme Detection (1 day, 8h)

**Files to Modify**:
- `via/renderers/formatters/code_formatters.py`

**Implementation Steps**:
1. Create `detect_terminal_theme()` utility function:
   - Check environment variables: `$COLORFGBG`, `$TERM_BACKGROUND`
   - Parse `$COLORFGBG` format: `foreground;background`
   - Light background: RGB values > 127
   - Dark background: RGB values < 127
   - Default to dark if detection fails
2. Update `AsciiCodeFormatter`:
   - If theme == 'auto': Call `detect_terminal_theme()`
   - Map light/dark to Pygments style names
   - Light themes: 'default', 'tango', 'friendly'
   - Dark themes: 'monokai', 'native', 'material'
3. Add `--theme` flag support:
   - Allow explicit theme names (Pygments style names)
   - List available themes with `--list-themes` (future)

**Acceptance Criteria**:
- AC1: Terminal theme auto-detected from environment
- AC2: Light themes used for light terminals
- AC3: Dark themes used for dark terminals
- AC4: `--theme` flag overrides auto-detection
- AC5: Invalid theme names fall back to default

**Tests**:
- `test_detect_light_terminal()`
- `test_detect_dark_terminal()`
- `test_theme_auto_detection()`
- `test_theme_explicit_override()`
- `test_theme_fallback_on_invalid()`

**Estimated**: 8h

**Phase 6 Total**: 24h (3 days)

---

## P0 Implementation Complete (20 story points, ~120h)

At this point, the MVP is complete with all P0 stories implemented:
- ✅ Story 1: Internal Pipeline (5pts)
- ✅ Story 2: MatchRecord System (5pts)
- ✅ Story 3: List & Table Renderers (3pts)
- ✅ Story 4a: Raw Renderer (2pts)
- ✅ Story 4b: Formatted Renderer (3pts)
- ✅ Story 9: Streaming & Limits (2pts)

**User can now**:
- Use internal pipeline: `via -mg -c '*' --via -mr -m '*' --via -rT`
- Render as list/table/raw/formatted
- Stream results with O(1) memory
- Control output with -A/-B/-C context flags
- Select themes with --theme

---

## Optional P1 Features (15 story points, ~120h)

### Phase 7: Diagram Renderer (Story 5 - P1, 5pts)
**Dependencies**: Phase 2 (needs ClassMatchRecord)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 7.1: Implement DiagramRenderer (3 days, 24h)

**Files to Create**:
- `via/renderers/diagram.py`
- `via/renderers/formatters/diagram_formatters.py`

**Implementation Steps**:
1. Create `DiagramFormatter` base class in `diagram_formatters.py`:
   - Abstract method: `format_diagram(mermaid: str) -> str`
2. Create `MermaidFormatter`:
   - Return mermaid syntax as-is (for MD output)
3. Create `MermaidHtmlFormatter`:
   - Wrap mermaid in HTML with mermaid.js script
   - Include basic styling
4. Create `MermaidPngFormatter` (optional):
   - Use mermaid-cli to render PNG
   - Requires external mermaid-cli installation
5. Create `DiagramRenderer(Renderer)`:
   - `render(records, **options)`:
     - **Explicitly materialize**: `all_records = list(records)`
     - Filter for `ClassMatchRecord` only
     - If no classes: Return "No classes to diagram"
     - Call `_generate_mermaid(classes)`
     - Delegate to formatter
     - Return formatted diagram
6. Implement `_generate_mermaid()`:
   - Generate `classDiagram` header
   - For each class:
     - Output class definition
     - Lazy load methods: `cls.get_methods(db)`
     - Output methods
     - Output inheritance relationships (if base_classes present)
   - Return mermaid syntax string

**Acceptance Criteria**:
- AC1: DiagramRenderer explicitly materializes with `list(records)`
- AC2: Only ClassMatchRecord processed (others ignored)
- AC3: Mermaid classDiagram syntax generated correctly
- AC4: Inheritance relationships shown (parent <|-- child)
- AC5: Methods shown for each class
- AC6: Empty result handled gracefully
- AC7: MD format returns mermaid syntax
- AC8: HTML format includes mermaid.js rendering

**Tests**:
- `test_diagram_renderer_materializes()`
- `test_diagram_renderer_filters_classes_only()`
- `test_diagram_renderer_mermaid_syntax()`
- `test_diagram_renderer_inheritance()`
- `test_diagram_renderer_methods()`
- `test_diagram_renderer_empty_result()`
- `test_diagram_renderer_md_format()`
- `test_diagram_renderer_html_format()`

**Estimated**: 24h

---

#### Task 7.2: Implement Lazy Method Loading (1 day, 8h)

**Files to Modify**:
- `via/core/match_record.py`
- `via/database/store.py`

**Implementation Steps**:
1. Update `ClassMatchRecord`:
   - Add `get_methods(db: DatabaseStore)` method
   - Query database for methods where `parent_name = self.qualified_name`
   - Cache results in `self.methods`
   - Return list of MethodMatchRecord
2. Update `DatabaseStore`:
   - Add `get_methods_for_class(qualified_name: str) -> List[MethodMatchRecord]`
   - Query symbols table where `symbol_type='method'` and `parent_name=?`
   - Use factory to create MethodMatchRecord instances
   - Return list

**Acceptance Criteria**:
- AC1: Methods loaded lazily (only when requested)
- AC2: Methods cached after first load
- AC3: Query efficient (uses index on parent_name)

**Tests**:
- `test_lazy_load_methods()`
- `test_methods_cached_after_load()`
- `test_get_methods_for_class()`

**Estimated**: 8h

---

#### Task 7.3: Integration Tests for Diagram Renderer (1 day, 8h)

**Files to Create**:
- `tests/integration/test_diagram_renderer.py`

**Test Cases**:
1. `test_diagram_single_class()`
2. `test_diagram_with_inheritance()`
3. `test_diagram_with_methods()`
4. `test_diagram_multiple_classes()`
5. `test_diagram_md_output()`
6. `test_diagram_html_output()`
7. `test_diagram_empty_result()`

**Estimated**: 8h

**Phase 7 Total**: 40h (5 days)

---

### Phase 8: Stats Command (Story 7 - P1, 3pts)
**Dependencies**: None (can run parallel)
**Duration**: 3 days (24h)
**Assignee**: @Neo

#### Task 8.1: Implement Basic Stats Command (1.5 days, 12h)

**Files to Create**:
- `via/commands/stats.py`

**Implementation Steps**:
1. Create `StatsCommand` class:
   - `execute(db: DatabaseStore, verbose: int = 0, json_output: bool = False)`
2. Implement basic stats query:
   - COUNT symbols by type (class, method, function, import, global)
   - COUNT files indexed
   - Get database file size
   - Get last updated timestamp (from index metadata)
3. Format output:
   - Header: "VIA Index Statistics"
   - Sections: Files, Symbols
   - Table with counts
4. Implement JSON output:
   - If `--json` flag: Return stats as JSON dict

**Acceptance Criteria**:
- AC1: Basic stats show counts by symbol type
- AC2: File count and database size shown
- AC3: Last updated timestamp shown
- AC4: JSON output option works
- AC5: Output formatted nicely for terminal

**Tests**:
- `test_stats_basic_output()`
- `test_stats_counts_by_type()`
- `test_stats_json_output()`

**Estimated**: 12h

---

#### Task 8.2: Implement Verbose Levels (1 day, 8h)

**Files to Modify**:
- `via/commands/stats.py`

**Implementation Steps**:
1. Level 1 (`-v`): Per-file symbol counts
   - Query: `SELECT file_path, COUNT(*) FROM symbols GROUP BY file_path`
   - Show top 10 files by symbol count
2. Level 2 (`-vv`): Largest classes/functions
   - Query: Use byte_length to find largest symbols
   - Show top 10 by size
3. Level 3 (`-vvv`): Full breakdown
   - Per-file breakdown
   - Per-type breakdown
   - Size distribution histogram

**Acceptance Criteria**:
- AC1: `-v` shows per-file counts (top 10)
- AC2: `-vv` shows largest symbols (top 10)
- AC3: `-vvv` shows full breakdown
- AC4: Verbose output readable and useful

**Tests**:
- `test_stats_verbose_level_1()`
- `test_stats_verbose_level_2()`
- `test_stats_verbose_level_3()`

**Estimated**: 8h

---

#### Task 8.3: Wire Stats into Pipeline (0.5 days, 4h)

**Files to Modify**:
- `via/pipeline/executor.py`

**Implementation Steps**:
1. Import `StatsCommand`
2. Update `_execute_stats_stage()`:
   - Extract verbose and json flags from `stage.args`
   - Create `StatsCommand` instance
   - Call `execute(db, verbose, json_output)`
   - Print output
3. Update pipeline parser to recognize `stats` command

**Acceptance Criteria**:
- AC1: `via stats` executes stats command
- AC2: Verbose and JSON flags work
- AC3: Stats is terminal stage (no further pipeline)

**Tests**:
- `test_pipeline_stats_stage()`
- `test_stats_verbose_flag()`
- `test_stats_json_flag()`

**Estimated**: 4h

**Phase 8 Total**: 24h (3 days)

---

### Phase 9: Usage Renderer (Story 6 - P1, 5pts)
**Dependencies**: Phase 2 (needs reference table schema)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 9.1: Verify Reference Table Schema (0.5 days, 4h)

**Files to Review**:
- `via/database/schema.py`

**Implementation Steps**:
1. Check if `symbol_references` table exists in schema
2. Verify columns:
   - `caller_qualified_name`
   - `callee_qualified_name`
   - `caller_file`
   - `callee_file`
   - `caller_line`
3. If missing: Add reference table to schema
4. Update indexer to populate references during parsing (future sprint)

**Acceptance Criteria**:
- AC1: Reference table exists in schema
- AC2: Required columns present
- AC3: Indexes on caller/callee columns

**Estimated**: 4h

---

#### Task 9.2: Implement UsageRenderer (2 days, 16h)

**Files to Create**:
- `via/renderers/usage.py`
- `via/renderers/formatters/usage_formatters.py`

**Implementation Steps**:
1. Create `UsageFormatter` base class:
   - Abstract method: `format_usage(caller: str, callee: str, file: str, line: int) -> str`
2. Create formatters:
   - `AsciiUsageFormatter`: Simple text output
   - `MarkdownUsageFormatter`: Markdown list
   - `HtmlUsageFormatter`: HTML list
3. Create `UsageRenderer(Renderer)`:
   - `render(records, **options)`:
     - For each record:
       - Query `symbol_references` for references to this symbol
       - Format as caller -> callee relationships
       - Group by caller
     - Delegate to formatter
     - Return formatted output
4. Implement reference query:
   - Query: `SELECT * FROM symbol_references WHERE callee_qualified_name = ?`
   - Return list of callers

**Acceptance Criteria**:
- AC1: UsageRenderer queries reference table
- AC2: Shows where symbols are used (caller sites)
- AC3: Groups by caller
- AC4: Formats work (ASCII/MD/HTML)
- AC5: Handles symbols with no references

**Tests**:
- `test_usage_renderer_finds_callers()`
- `test_usage_renderer_formats()`
- `test_usage_renderer_no_references()`

**Estimated**: 16h

---

#### Task 9.3: Integration Tests for Usage Renderer (1 day, 8h)

**Files to Create**:
- `tests/integration/test_usage_renderer.py`

**Test Cases**:
1. `test_usage_for_function()`
2. `test_usage_for_class()`
3. `test_usage_for_method()`
4. `test_usage_for_import()`
5. `test_usage_no_references()`
6. `test_usage_multiple_callers()`

**Estimated**: 8h

---

#### Task 9.4: Populate Reference Table in Indexer (1.5 days, 12h)

**Files to Modify**:
- `via/indexer/python_parser.py`

**Implementation Steps**:
1. During AST traversal:
   - Detect function calls: `ast.Call` nodes
   - Extract caller (current function/method context)
   - Extract callee (function being called)
   - Record reference in database
2. Detect import usage:
   - When imported name is used: Record reference
3. Handle attribute access:
   - `obj.method()`: Record method call reference

**Acceptance Criteria**:
- AC1: Function calls recorded in reference table
- AC2: Method calls recorded
- AC3: Import usage recorded
- AC4: References queryable by callee

**Tests**:
- `test_indexer_records_function_calls()`
- `test_indexer_records_method_calls()`
- `test_indexer_records_import_usage()`

**Estimated**: 12h

**Phase 9 Total**: 40h (5 days)

---

### Phase 10: Theme System (Story 8 - P1, 2pts)
**Dependencies**: Phase 6 (builds on FormattedRenderer)
**Duration**: 2 days (16h)
**Assignee**: @Neo

#### Task 10.1: Theme Preview Command (1 day, 8h)

**Files to Create**:
- `via/commands/themes.py`

**Implementation Steps**:
1. Create `ThemesCommand` class:
   - `execute(preview: bool = False)`
2. Implement `--preview-themes`:
   - List all available Pygments styles
   - For each style:
     - Render sample Python code
     - Show style name
3. Sample code:
   - Use representative Python snippet (class, function, method)
   - Include common syntax elements (strings, keywords, comments)

**Acceptance Criteria**:
- AC1: `via --preview-themes` lists all available themes
- AC2: Each theme shown with sample code
- AC3: Output readable in terminal

**Tests**:
- `test_preview_themes_lists_all()`
- `test_preview_themes_renders_sample()`

**Estimated**: 8h

---

#### Task 10.2: Bundle Themes in Build (1 day, 8h)

**Files to Modify**:
- `pyproject.toml`
- Build configuration

**Implementation Steps**:
1. Ensure Pygments included in dependencies
2. Verify Pygments styles bundled in package
3. Test theme availability in installed package

**Acceptance Criteria**:
- AC1: Pygments bundled in distribution
- AC2: Themes available without external dependency
- AC3: Installation includes all themes

**Tests**:
- `test_themes_available_after_install()`

**Estimated**: 8h

**Phase 10 Total**: 16h (2 days)

---

## Testing & Documentation

### Task T.1: Comprehensive Integration Tests (2 days, 16h)

**Files to Create**:
- `tests/integration/test_sprint3_end_to_end.py`

**Test Cases**:
1. Full pipeline tests:
   - `test_match_and_list()`
   - `test_match_and_table()`
   - `test_match_and_raw()`
   - `test_match_and_formatted()`
   - `test_chained_matches_and_render()`
2. Context line tests:
   - `test_context_before()`
   - `test_context_after()`
   - `test_context_both()`
3. Limit tests:
   - `test_default_limit()`
   - `test_custom_limit()`
   - `test_unlimited()`
4. Theme tests:
   - `test_theme_auto_detection()`
   - `test_theme_explicit()`
5. Error handling:
   - `test_invalid_pipeline_syntax()`
   - `test_unsupported_render_type_for_symbol()`

**Estimated**: 16h

---

### Task T.2: Update Documentation (1 day, 8h)

**Files to Update**:
- `README.md`
- `docs/USER_GUIDE.md` (create if needed)

**Content to Add**:
1. Internal pipeline syntax:
   - Explanation of `--via` flag
   - Shorthand flags reference
   - Usage examples
2. Render types:
   - List, table, raw, formatted, diagram, usage
   - When to use each
   - Format options
3. Common workflows:
   - Finding and viewing code
   - Generating diagrams
   - Analyzing usage
4. Configuration:
   - Theme selection
   - Context lines
   - Limits

**Acceptance Criteria**:
- AC1: README updated with Sprint 3 features
- AC2: User guide comprehensive and easy to follow
- AC3: All examples tested and working

**Estimated**: 8h

---

## Sprint 3 Summary

### Total Effort by Phase

| Phase | Story | Priority | Points | Hours | Status |
|-------|-------|----------|--------|-------|--------|
| 1 | Pipeline Architecture | P0 | 5 | 40h | Ready |
| 2 | MatchRecord System | P0 | 5 | 40h | Ready |
| 3 | Streaming & Metadata | P0 | 2 | 16h | Ready |
| 4 | List & Table Renderers | P0 | 3 | 24h | Ready |
| 5 | Raw Renderer | P0 | 2 | 16h | Ready |
| 6 | Formatted Renderer | P0 | 3 | 24h | Ready |
| **P0 Total** | **6 stories** | **P0** | **20** | **160h** | **MVP** |
| 7 | Diagram Renderer | P1 | 5 | 40h | Optional |
| 8 | Stats Command | P1 | 3 | 24h | Optional |
| 9 | Usage Renderer | P1 | 5 | 40h | Optional |
| 10 | Theme System | P1 | 2 | 16h | Optional |
| **P1 Total** | **4 stories** | **P1** | **15** | **120h** | **Optional** |
| Testing & Docs | - | - | - | 24h | Required |
| **Grand Total** | **10 stories** | - | **35** | **304h** | - |

### Critical Path (MVP - 160h)

1. **Phase 1: Pipeline** (40h) - BLOCKER
2. **Phase 2: MatchRecord** (40h) - BLOCKER
3. **Phase 3: Streaming** (16h) - Enables metadata
4. **Phase 4: Renderers (List/Table)** (24h) - Basic rendering
5. **Phase 5: Raw Renderer** (16h) - For automation
6. **Phase 6: Formatted Renderer** (24h) - For humans

**MVP delivery**: 160h (4 weeks @ 40h/week, or 3 weeks @ 50-55h/week)

### Dependencies Graph

```
Phase 1 (Pipeline) ──┬─► Phase 4 (Renderers)
                     │
Phase 2 (MatchRecord)├─► Phase 3 (Streaming) ──► Phase 4 (Renderers)
                     │
                     ├─► Phase 5 (Raw) ──► Phase 6 (Formatted)
                     │
                     ├─► Phase 7 (Diagram) [P1]
                     │
                     └─► Phase 9 (Usage) [P1]

Phase 8 (Stats) [P1] ──► (Independent)
Phase 10 (Themes) [P1] ─► (Builds on Phase 6)
```

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| argparse complexity | Medium | Medium | Thorough testing, clear error messages |
| Pygments integration issues | Low | Medium | Fallback to plain text |
| Metadata query performance | Low | High | Measure with EXPLAIN, optimize if needed |
| Context line extraction complexity | Medium | Medium | Start simple, iterate |
| Mermaid syntax errors | Low | Low | Validate generated syntax |

### Success Criteria

**Sprint 3 MVP Complete When**:
- ✅ All P0 stories implemented (20 points)
- ✅ Internal pipeline works: `via -mg -c '*' --via -mr -m '*' --via -rT`
- ✅ List, table, raw, formatted renderers functional
- ✅ Streaming works with O(1) memory
- ✅ Default limit of 10 with indicator
- ✅ Context lines work (-A/-B/-C)
- ✅ Themes work (auto-detect + --theme)
- ✅ 95%+ test coverage
- ✅ Documentation updated

**Sprint 3 Full Complete When**:
- ✅ All MVP criteria met
- ✅ All P1 stories implemented (15 points)
- ✅ Diagram renderer generates mermaid diagrams
- ✅ Usage renderer shows call sites
- ✅ Stats command provides insights
- ✅ Theme preview works
- ✅ User guide comprehensive

---

## Next Steps

1. **@Neo**: Review task breakdown and ask questions
2. **@Neo**: Start with Phase 1 (Pipeline Architecture)
3. **@Mouse**: Stand by for task tracking and progress monitoring
4. **@Oracle**: Record decisions as they're made during implementation
5. **@QA**: Prepare test strategy for Sprint 3 features

---

**Status**: ✅ Task Breakdown Complete - Ready for Implementation
**Created**: 2026-01-16
**Last Updated**: 2026-01-16
