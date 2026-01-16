# Sprint 3 Architecture - Internal Pipeline & Polymorphic Render System

**Version**: 1.0
**Date**: 2026-01-16
**Architect**: @Morpheus
**Status**: Ready for Implementation

---

## Executive Summary

Sprint 3 introduces a **zero-copy internal pipeline architecture** that enables chaining operations within a single command invocation. The system uses polymorphic MatchRecord types and a flexible rendering framework to support multiple output formats.

**Key Architectural Decisions**:
1. **Internal Pipeline** - Parse `--via` flags to create stage chain, no subprocess overhead
2. **Polymorphic MatchRecords** - Factory pattern creates type-specific records with render capabilities
3. **Generator-based Streaming** - Zero-copy iterators pass data between stages
4. **Strategy Pattern for Renderers** - Pluggable render types and output formatters
5. **Pygments Integration** - Use existing library for syntax highlighting (DRY principle)

---

## 1. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                           │
│                      via/__main__.py                              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Pipeline Parser                              │
│              Split args by --via flags                            │
│         Create PipelineStage objects                              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Pipeline Executor                              │
│         Execute stages sequentially                               │
│         Pass Iterator[MatchRecord] between stages                 │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ├─────► Stage 1: MatchStage
                 │       └─► DatabaseStore.match()
                 │           └─► Iterator[MatchRecord]
                 │
                 ├─────► Stage 2: FilterStage
                 │       └─► Filter prev results
                 │           └─► Iterator[MatchRecord]
                 │
                 └─────► Stage 3: RenderStage
                         └─► RenderType.render(records)
                             └─► OutputFormatter.format()
                                 └─► stdout
```

---

## 2. Core Components

### 2.1 Pipeline Parser (`via/pipeline/parser.py`)

**Responsibility**: Parse command line into pipeline stages using argparse

```python
import argparse
from typing import List, Dict, Any

@dataclass
class PipelineStage:
    """Single stage in the pipeline."""
    stage_type: StageType  # MATCH, RENDER, STATS
    args: argparse.Namespace  # Parsed arguments from argparse

class PipelineParser:
    """Parse argv into pipeline stages using argparse."""

    def __init__(self):
        self.match_parser = self._create_match_parser()
        self.render_parser = self._create_render_parser()
        self.stats_parser = self._create_stats_parser()

    def parse(self, argv: List[str]) -> List[PipelineStage]:
        """Split argv on --via, parse each segment with argparse."""
        segments = self._split_on_via(argv)
        stages = []

        for segment in segments:
            stage = self._parse_stage(segment)
            stages.append(stage)

        return stages

    def _split_on_via(self, argv: List[str]) -> List[List[str]]:
        """Split argv into segments at each --via flag."""
        segments = [[]]
        for arg in argv:
            if arg == '--via':
                segments.append([])
            else:
                segments[-1].append(arg)
        return [s for s in segments if s]  # Remove empty

    def _parse_stage(self, args: List[str]) -> PipelineStage:
        """Parse single stage using appropriate argparse parser."""
        if not args:
            raise PipelineParseError("Empty pipeline stage")

        # Detect stage type from command/flags
        if args[0] == 'match' or '-m' in args or any(a in ['-g', '-r', '-s'] for a in args):
            return self._parse_match_stage(args)
        elif args[0] == 'render' or '-r' in args or any(a.startswith('-r') for a in args if len(a) > 2):
            return self._parse_render_stage(args)
        elif args[0] == 'stats':
            return self._parse_stats_stage(args)
        else:
            raise PipelineParseError(f"Unknown stage type: {args}")

    def _parse_match_stage(self, args: List[str]) -> PipelineStage:
        """Parse match stage using argparse."""
        try:
            # Remove 'match' if present (for long form)
            if args[0] == 'match':
                args = args[1:]

            parsed_args = self.match_parser.parse_args(args)
            return PipelineStage(StageType.MATCH, parsed_args)
        except SystemExit:
            # argparse calls sys.exit() on error - catch and re-raise
            raise PipelineParseError(f"Invalid match stage arguments: {args}")

    def _parse_render_stage(self, args: List[str]) -> PipelineStage:
        """Parse render stage using argparse."""
        try:
            if args[0] == 'render':
                args = args[1:]

            parsed_args = self.render_parser.parse_args(args)
            return PipelineStage(StageType.RENDER, parsed_args)
        except SystemExit:
            raise PipelineParseError(f"Invalid render stage arguments: {args}")

    def _parse_stats_stage(self, args: List[str]) -> PipelineStage:
        """Parse stats stage using argparse."""
        try:
            if args[0] == 'stats':
                args = args[1:]

            parsed_args = self.stats_parser.parse_args(args)
            return PipelineStage(StageType.STATS, parsed_args)
        except SystemExit:
            raise PipelineParseError(f"Invalid stats stage arguments: {args}")

    def _create_match_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for match stage."""
        parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)

        # Symbol type
        parser.add_argument('-t', '--type', dest='symbol_type',
                          choices=['class', 'method', 'function', 'import', 'global', 'filepath', 'filename'])
        parser.add_argument('-c', '--class', dest='symbol_type', action='store_const', const='class')
        parser.add_argument('-m', '--method', dest='symbol_type', action='store_const', const='method')
        parser.add_argument('-f', '--function', dest='symbol_type', action='store_const', const='function')
        parser.add_argument('-i', '--import', dest='symbol_type', action='store_const', const='import')
        parser.add_argument('-G', '--global', dest='symbol_type', action='store_const', const='global')
        parser.add_argument('-F', '--file', dest='symbol_type', action='store_const', const='filepath')
        parser.add_argument('-N', '--filename', dest='symbol_type', action='store_const', const='filename')

        # Match syntax (mutually exclusive)
        syntax_group = parser.add_mutually_exclusive_group()
        syntax_group.add_argument('-g', '--glob', dest='pattern', metavar='PATTERN')
        syntax_group.add_argument('-r', '--regex', dest='pattern', metavar='PATTERN')
        syntax_group.add_argument('-s', '--sql', dest='pattern', metavar='PATTERN')

        # Qualifiers
        parser.add_argument('-I', '--case-insensitive', action='store_true')
        parser.add_argument('-n', '--limit', type=int, default=10)

        return parser

    def _create_render_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for render stage."""
        parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)

        # Render type (mutually exclusive)
        render_group = parser.add_mutually_exclusive_group()
        render_group.add_argument('-rL', '--list', dest='render_type', action='store_const', const='list')
        render_group.add_argument('-rT', '--table', dest='render_type', action='store_const', const='table')
        render_group.add_argument('-rD', '--diagram', dest='render_type', action='store_const', const='diagram')
        render_group.add_argument('-rU', '--usage', dest='render_type', action='store_const', const='usage')
        render_group.add_argument('-rR', '--raw', dest='render_type', action='store_const', const='raw')
        render_group.add_argument('-rF', '--formatted', dest='render_type', action='store_const', const='formatted')

        # Output format
        format_group = parser.add_mutually_exclusive_group()
        format_group.add_argument('-a', '--ascii', dest='format', action='store_const', const='ascii')
        format_group.add_argument('-m', '--md', dest='format', action='store_const', const='md')
        format_group.add_argument('-h', '--html', dest='format', action='store_const', const='html')
        format_group.add_argument('-p', '--png', dest='format', action='store_const', const='png')

        # Context lines (for raw render)
        parser.add_argument('-A', '--after-context', type=int, default=0)
        parser.add_argument('-B', '--before-context', type=int, default=0)
        parser.add_argument('-C', '--context', type=int)

        # Theme
        parser.add_argument('--theme', type=str)

        return parser

    def _create_stats_parser(self) -> argparse.ArgumentParser:
        """Create argparse parser for stats stage."""
        parser = argparse.ArgumentParser(add_help=False, exit_on_error=False)

        parser.add_argument('-v', '--verbose', action='count', default=0)
        parser.add_argument('--json', action='store_true')

        return parser


class PipelineParseError(Exception):
    """Raised when pipeline parsing fails."""
    pass
```

**Design Notes**:
- Uses Python's `argparse.ArgumentParser` with `exit_on_error=False` (Python 3.9+) to prevent sys.exit() calls
- Separate parsers for each stage type (match, render, stats)
- Shorthand flags like `-c`, `-m`, `-f` use `action='store_const'` to set symbol_type
- Combined flags like `-rT`, `-rD` for render types
- Catches `SystemExit` and re-raises as `PipelineParseError` for clean error handling

---

### 2.2 Pipeline Executor (`via/pipeline/executor.py`)

**Responsibility**: Execute stages in sequence, pass iterators between stages

```python
class PipelineExecutor:
    """Execute pipeline stages sequentially."""

    def __init__(self, db_store: DatabaseStore):
        self.db = db_store
        self.record_factory = MatchRecordFactory()

    def execute(self, stages: List[PipelineStage]) -> Iterator[MatchRecord]:
        """Execute all stages, return final iterator."""
        result_iter = None

        for stage in stages:
            if stage.stage_type == StageType.MATCH:
                # First match stage queries DB
                if result_iter is None:
                    result_iter = self._execute_match_stage(stage, None)
                # Subsequent match stages filter previous results
                else:
                    result_iter = self._execute_filter_stage(stage, result_iter)

            elif stage.stage_type == StageType.RENDER:
                # Render consumes iterator and outputs formatted results
                self._execute_render_stage(stage, result_iter)
                return  # Render is terminal stage

            elif stage.stage_type == StageType.STATS:
                self._execute_stats_stage(stage)
                return  # Stats is terminal stage

        # No render stage - default to list output
        if result_iter:
            for record in result_iter:
                print(record)  # Uses __str__() method

    def _execute_match_stage(
        self,
        stage: PipelineStage,
        prev_results: Optional[Iterator[MatchRecord]]
    ) -> Iterator[MatchRecord]:
        """Execute match stage against database."""
        args = stage.args  # argparse.Namespace

        # Extract arguments
        symbol_type = SymbolType(args.symbol_type)
        pattern = args.pattern
        case_sensitive = not args.case_insensitive
        limit = args.limit

        # Determine match operator from which flag was used
        if hasattr(args, 'glob') and args.glob:
            match_op = MatchOp.GLOB
            pattern = args.glob
        elif hasattr(args, 'regex') and args.regex:
            match_op = MatchOp.REGEXP
            pattern = args.regex
        elif hasattr(args, 'sql') and args.sql:
            match_op = MatchOp.LIKE
            pattern = args.sql
        else:
            match_op = MatchOp.GLOB  # Default to glob

        # Query database
        results = self.db.match(symbol_type, match_op, pattern, case_sensitive, limit)

        # Convert DB rows to MatchRecords using factory
        for row in results:
            record = self.record_factory.create_from_row(row)
            yield record

    def _execute_filter_stage(
        self,
        stage: PipelineStage,
        prev_results: Iterator[MatchRecord]
    ) -> Iterator[MatchRecord]:
        """Filter previous results (for chained matches)."""
        # For chained match stages:
        # Example: via -mg -c '*Match*' --via -mr -m '__*__'
        # Stage 2 filters Stage 1 results for methods matching pattern

        target_type = SymbolType(stage.flags['type'])
        pattern = stage.flags['pattern']
        match_op = MatchOp(stage.flags['match_op'])

        for record in prev_results:
            # Filter by type
            if record.symbol_type != target_type:
                continue

            # Apply pattern match
            if self._pattern_matches(record.symbol_name, pattern, match_op):
                yield record

    def _execute_render_stage(
        self,
        stage: PipelineStage,
        records: Iterator[MatchRecord]
    ):
        """Render records to stdout."""
        args = stage.args  # argparse.Namespace

        render_type = RenderType(args.render_type)
        format_type = FormatType(args.format if args.format else 'ascii')

        # Get appropriate renderer
        renderer = RendererFactory.create(render_type, format_type)

        # Build options dict from args
        options = {}
        if args.context:
            options['context_before'] = args.context
            options['context_after'] = args.context
        else:
            options['context_before'] = args.before_context
            options['context_after'] = args.after_context

        if args.theme:
            options['theme'] = args.theme

        # Render (may consume iterator fully or stream)
        output = renderer.render(records, **options)
        print(output, end='')
```

**Design Note**: Each stage returns/consumes Iterator[MatchRecord] - this enables zero-copy streaming and lazy evaluation. Only materialize when needed (e.g., diagrams need all records).

---

### 2.3 MatchRecord System (`via/core/match_record.py`)

**Responsibility**: Polymorphic record types with rendering metadata for streaming

**Key Innovation**: Each MatchRecord contains rendering metadata (column widths, total count) so it can be rendered independently without materializing all records. This enables streaming for TableRenderer and other formatters.

```python
@dataclass
class MatchRecord(ABC):
    """Base class for all match results with rendering metadata.

    Each record is self-contained with all data needed for rendering,
    including shared metadata like column widths and total count.
    This enables streaming renderers (Table, List, Raw, Formatted).
    """
    # Symbol data
    symbol_type: str
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: int
    byte_offset: Optional[int] = None
    byte_length: Optional[int] = None
    parent_name: Optional[str] = None

    # Rendering metadata (shared across all results in this query)
    # Attached to EVERY record so each can render independently
    column_widths: Optional[Dict[str, int]] = None  # {'name': 25, 'file': 40, 'type': 10}
    total_matches: Optional[int] = None  # Total available (for "... N more" indicator)

    @abstractmethod
    def supports_render_type(self, render_type: RenderType) -> bool:
        """Check if this record type supports the render type."""
        pass

    def __str__(self) -> str:
        """Default list format (compatible with Sprint 2)."""
        output = f"{self.symbol_type}:{self.file_path}:{self.line_number}:{self.qualified_name}"
        if self.byte_offset is not None:
            output += f":@{self.byte_offset}+{self.byte_length}"
        return output


class ClassMatchRecord(MatchRecord):
    """Match record for classes."""
    base_classes: Optional[List[str]] = None
    methods: Optional[List[str]] = None  # Populated lazily for diagrams

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.DIAGRAM,
            RenderType.USAGE,
            RenderType.RAW
        }

    def get_methods(self, db: DatabaseStore) -> List['MethodMatchRecord']:
        """Lazy load methods for this class (used by diagram renderer)."""
        if self.methods is None:
            # Query DB for methods of this class
            self.methods = db.get_methods_for_class(self.qualified_name)
        return self.methods


class MethodMatchRecord(MatchRecord):
    """Match record for methods."""

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW,
            RenderType.FORMATTED
        }


class FunctionMatchRecord(MatchRecord):
    """Match record for functions."""

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW,
            RenderType.FORMATTED
        }


class FileMatchRecord(MatchRecord):
    """Match record for files."""

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.RAW  # Can output raw file contents
        }


class ImportMatchRecord(MatchRecord):
    """Match record for imports."""

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW  # Can show import statement
        }


class GlobalMatchRecord(MatchRecord):
    """Match record for global variables."""

    def supports_render_type(self, render_type: RenderType) -> bool:
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.RAW,
            RenderType.FORMATTED
        }
```

**Design Pattern**: Template Method - Base class defines interface, derived classes override supported operations.

---

### 2.4 MatchRecord Factory (`via/core/match_record.py`)

**Responsibility**: Create appropriate MatchRecord subclass from database row with metadata

```python
class MatchRecordFactory:
    """Factory to create MatchRecord instances from DB rows with rendering metadata."""

    _RECORD_TYPES = {
        'class': ClassMatchRecord,
        'method': MethodMatchRecord,
        'function': FunctionMatchRecord,
        'filepath': FileMatchRecord,
        'filename': FileMatchRecord,
        'import': ImportMatchRecord,
        'global': GlobalMatchRecord,
    }

    def create_from_row(
        self,
        row: sqlite3.Row,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MatchRecord:
        """Create MatchRecord from database row with optional rendering metadata.

        Args:
            row: Database row containing symbol data
            metadata: Optional dict with 'column_widths' and 'total_matches'
        """
        symbol_type = row['symbol_type']

        # Get appropriate record class
        record_class = self._RECORD_TYPES.get(symbol_type)
        if not record_class:
            raise ValueError(f"Unknown symbol type: {symbol_type}")

        # Create record instance with metadata
        return record_class(
            symbol_type=symbol_type,
            symbol_name=row['symbol_name'],
            qualified_name=row['qualified_name'],
            file_path=row['file_path'],
            line_number=row['line_number'],
            byte_offset=row.get('byte_offset'),
            byte_length=row.get('byte_length'),
            parent_name=row.get('parent_name'),
            # Attach rendering metadata
            column_widths=metadata.get('column_widths') if metadata else None,
            total_matches=metadata.get('total_matches') if metadata else None,
        )
```

**Design Pattern**: Factory Method - Encapsulates object creation logic, easy to extend with new types.

---

### 2.5 DatabaseStore Match with Metadata (`via/database/store.py`)

**Responsibility**: Query database and compute rendering metadata for streaming

**Key Optimization**: Single metadata query before streaming results enables TableRenderer to stream without materializing all records.

```python
class DatabaseStore:
    def match(
        self,
        symbol_type: SymbolType,
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool = True,
        limit: int = 10
    ) -> Iterator[MatchRecord]:
        """Query symbols with metadata for streaming renderers.

        Performs two queries:
        1. Metadata query (COUNT, MAX column widths) - runs once
        2. Results query (actual matches) - streams lazily

        Returns:
            Iterator of MatchRecords with metadata attached to each record
        """
        # Step 1: Get metadata (total count + column widths) in single query
        metadata = self._get_match_metadata(symbol_type, match_op, pattern, case_sensitive)

        # Step 2: Stream results with metadata attached
        results = self._stream_match_results(
            symbol_type, match_op, pattern, case_sensitive, limit
        )

        for row in results:
            # Create MatchRecord with metadata attached
            record = MatchRecordFactory().create_from_row(row, metadata)
            yield record

    def _get_match_metadata(
        self,
        symbol_type: SymbolType,
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool
    ) -> Dict[str, Any]:
        """Calculate metadata for the result set (runs BEFORE streaming results).

        Returns dict with:
        - total_matches: Total count of matches (for "... N more" indicator)
        - column_widths: Max width of each column across ALL matches
        """
        # Single aggregation query to get metadata
        query = f"""
        SELECT
            COUNT(*) as total_count,
            MAX(LENGTH(symbol_name)) as max_name_width,
            MAX(LENGTH(qualified_name)) as max_qualified_width,
            MAX(LENGTH(file_path)) as max_file_width,
            MAX(LENGTH(symbol_type)) as max_type_width,
            MAX(LENGTH(COALESCE(parent_name, ''))) as max_parent_width
        FROM symbols
        WHERE symbol_type = ?
          AND symbol_name {match_op.sql_op} ?
          {'' if case_sensitive else 'COLLATE NOCASE'}
        """

        row = self.conn.execute(query, (symbol_type.value, pattern)).fetchone()

        return {
            'total_matches': row['total_count'],
            'column_widths': {
                'name': row['max_name_width'] or 10,
                'qualified': row['max_qualified_width'] or 20,
                'file': row['max_file_width'] or 30,
                'type': row['max_type_width'] or 10,
                'parent': row['max_parent_width'] or 10,
                'line': 6,  # Line numbers are max 6 chars
            }
        }

    def _stream_match_results(
        self,
        symbol_type: SymbolType,
        match_op: MatchOp,
        pattern: str,
        case_sensitive: bool,
        limit: int
    ) -> Iterator[sqlite3.Row]:
        """Stream match results from database."""
        query = f"""
        SELECT
            symbol_type,
            symbol_name,
            qualified_name,
            file_path,
            line_number,
            byte_offset,
            byte_length,
            parent_name
        FROM symbols
        WHERE symbol_type = ?
          AND symbol_name {match_op.sql_op} ?
          {'' if case_sensitive else 'COLLATE NOCASE'}
        ORDER BY file_path, line_number
        LIMIT ?
        """

        cursor = self.conn.execute(query, (symbol_type.value, pattern, limit))
        yield from cursor
```

**Performance**: Metadata query is fast (single aggregation), results stream lazily. Total overhead: ~5-10ms for metadata query regardless of result set size.

**Benefits**:
- TableRenderer can stream without materializing
- Each MatchRecord knows total count (for "... N more" indicator)
- Column widths calculated once across ALL matches (not just limited set)
- Zero memory overhead for streaming renderers

---

## 3. Rendering System

### 3.1 Renderer Architecture

```
RendererFactory
    │
    ├─► ListRenderer (all types)
    │   └─► (formats: ascii only - simple line output)
    │
    ├─► TableRenderer (all types)
    │   ├─► AsciiTableFormatter
    │   ├─► MarkdownTableFormatter
    │   └─► HtmlTableFormatter
    │
    ├─► RawRenderer (ALL types - truly raw, no formatting)
    │   └─► (outputs pure source code, no colors/line numbers/indentation)
    │   └─► (for piping to other tools, diffs, processing)
    │
    ├─► FormattedRenderer (class, method, function, global - NOT files/imports)
    │   ├─► AsciiCodeFormatter (pygments terminal + line numbers)
    │   ├─► HtmlCodeFormatter (pygments html)
    │   └─► MarkdownCodeFormatter (md code blocks)
    │   └─► (human-readable with syntax highlighting, line numbers, context)
    │
    ├─► DiagramRenderer (class only)
    │   ├─► MermaidFormatter (md)
    │   ├─► MermaidHtmlFormatter (html with mermaid.js)
    │   └─► MermaidPngFormatter (png via mermaid-cli - optional)
    │
    └─► UsageRenderer (class, method, function, import)
        ├─► AsciiUsageFormatter
        ├─► MarkdownUsageFormatter
        └─► HtmlUsageFormatter
```

**Design Decision**: Split Raw vs Formatted
- **RawRenderer**: Pure source code, no decoration. For piping, diffs, automation. Supports ALL types.
- **FormattedRenderer**: Pretty printing for humans. Syntax highlighting, line numbers, indentation. Only code symbols (class/method/function/global).

### 3.2 Renderer Base Class (`via/renderers/base.py`)

```python
class Renderer(ABC):
    """Base class for all renderers.

    Most renderers stream (List, Table, Raw, Formatted).
    Only DiagramRenderer materializes (needs all records to build relationships).
    """

    def __init__(self, formatter: Formatter):
        self.formatter = formatter

    @abstractmethod
    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records to string output.

        Renderers should stream when possible. Only materialize (list(records))
        when absolutely necessary (e.g., DiagramRenderer needs all classes for
        inheritance relationships).
        """
        pass
```

### 3.3 List Renderer (Default)

```python
class ListRenderer(Renderer):
    """Simple line-by-line list output (Sprint 2 compatible)."""

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render as simple list."""
        limit = options.get('limit', 10)
        count = 0
        more = 0

        lines = []
        for record in records:
            if limit > 0 and count >= limit:
                more += 1
                continue

            lines.append(str(record))
            count += 1

        output = '\n'.join(lines)
        if more > 0:
            output += f"\n... ({more} more matches, use -n 0 for all)"

        return output
```

### 3.4 Table Renderer (NOW STREAMS!)

```python
class TableRenderer(Renderer):
    """Tabular output - STREAMS using metadata for column widths.

    Previous design: Materialized all records to calculate column widths.
    New design: Column widths come from metadata, so we can stream!
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render as table by streaming records (widths already known)."""
        lines = []
        first_record = True
        column_widths = None
        total_matches = None
        count = 0

        for record in records:  # STREAMING - not materialized!
            # First record: extract metadata and print header
            if first_record:
                column_widths = record.column_widths or self._default_widths()
                total_matches = record.total_matches
                lines.append(self._render_header(column_widths))
                first_record = False

            # Render row using column widths from metadata
            row = self._render_row(record, column_widths)
            lines.append(row)
            count += 1

        # Add "... N more" indicator if results were limited
        if total_matches and count < total_matches:
            lines.append(f"\n... ({total_matches - count} more matches, use -n 0 for all)")

        return '\n'.join(lines)

    def _render_header(self, widths: Dict[str, int]) -> str:
        """Render table header with proper column widths."""
        header = (
            f"| {'Name':<{widths['name']}} "
            f"| {'Type':<{widths['type']}} "
            f"| {'File':<{widths['file']}} "
            f"| {'Line':>{widths['line']}} |"
        )
        separator = (
            f"|{'-' * (widths['name'] + 2)}"
            f"|{'-' * (widths['type'] + 2)}"
            f"|{'-' * (widths['file'] + 2)}"
            f"|{'-' * (widths['line'] + 2)}|"
        )
        return f"{header}\n{separator}"

    def _render_row(self, record: MatchRecord, widths: Dict[str, int]) -> str:
        """Render single row with proper column widths."""
        return (
            f"| {record.symbol_name:<{widths['name']}} "
            f"| {record.symbol_type:<{widths['type']}} "
            f"| {record.file_path:<{widths['file']}} "
            f"| {record.line_number:>{widths['line']}} |"
        )

    def _default_widths(self) -> Dict[str, int]:
        """Fallback column widths if metadata missing."""
        return {'name': 20, 'type': 10, 'file': 30, 'line': 6}
```

**Key Innovation**: TableRenderer now streams! Column widths come from metadata (calculated once in DatabaseStore), so no need to materialize all records.

### 3.5 Raw Renderer (Truly Raw - No Formatting)

```python
class RawRenderer(Renderer):
    """Pure raw source code output - NO formatting, colors, or line numbers.

    Use case: Piping to other tools, diffs, automation, text processing.
    For human-readable output, use FormattedRenderer instead.
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render pure source code with optional context lines."""
        context_before = options.get('context_before', 0)
        context_after = options.get('context_after', 0)
        context = options.get('context')  # -C flag
        if context:
            context_before = context_after = context

        outputs = []
        for record in records:
            # Extract source code - just the raw bytes
            source = self._extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                context_before,
                context_after
            )

            # NO formatting - just output the raw source
            outputs.append(source)

        return '\n'.join(outputs)  # Separate records with single newline

    def _extract_source(
        self,
        file_path: str,
        byte_offset: Optional[int],
        byte_length: Optional[int],
        context_before: int,
        context_after: int
    ) -> str:
        """Extract source code with optional context lines.

        If byte_offset/length are None (e.g., for files), read entire file.
        """
        with open(file_path, 'rb') as f:
            if byte_offset is not None and byte_length is not None:
                # Specific symbol - seek and read
                f.seek(byte_offset)
                source = f.read(byte_length).decode('utf-8')

                # TODO: Add context lines if requested
                # For now, just return symbol content
                return source
            else:
                # Entire file (for FileMatchRecord)
                return f.read().decode('utf-8')
```

### 3.6 Formatted Renderer (Human-Readable with Syntax Highlighting)

```python
class FormattedRenderer(Renderer):
    """Formatted source code renderer with syntax highlighting, line numbers, colors.

    Use case: Human viewing, code review, documentation.
    For machine processing, use RawRenderer instead.
    """

    def __init__(self, formatter: CodeFormatter):
        super().__init__(formatter)
        self.formatter = formatter  # pygments-based formatter

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render formatted source code with context lines."""
        context_before = options.get('context_before', 0)
        context_after = options.get('context_after', 0)
        context = options.get('context')  # -C flag
        if context:
            context_before = context_after = context

        theme = options.get('theme', 'auto')  # Auto-detect terminal theme

        outputs = []
        for record in records:
            # Extract source code
            source = self._extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                context_before,
                context_after
            )

            # Format with syntax highlighting + line numbers
            formatted = self.formatter.format_code(
                source,
                language='python',
                start_line=record.line_number - context_before,
                theme=theme,
                show_line_numbers=True
            )

            # Add header with symbol info
            header = f"# {record.qualified_name} ({record.file_path}:{record.line_number})"
            outputs.append(f"{header}\n{formatted}")

        return '\n\n'.join(outputs)

    def _extract_source(
        self,
        file_path: str,
        byte_offset: int,
        byte_length: int,
        context_before: int,
        context_after: int
    ) -> str:
        """Extract source code with context lines."""
        with open(file_path, 'rb') as f:
            # Seek to byte offset
            f.seek(byte_offset)

            # Read main content
            main_content = f.read(byte_length).decode('utf-8')

            # TODO: Read context lines (scan backwards/forwards by line)
            # For now, just return symbol content
            return main_content
```

### 3.7 Diagram Renderer (MUST Materialize)

```python
class DiagramRenderer(Renderer):
    """UML class diagram renderer using Mermaid syntax.

    IMPORTANT: This is the ONLY renderer that MUST materialize all records.
    Reason: Building class inheritance relationships requires seeing all classes.

    No helper method needed - just explicit list(records) for clarity.
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render class diagram.

        Explicitly materializes records because we need to:
        1. See all classes to find parent-child relationships
        2. Build complete inheritance tree
        3. Group methods by class
        """
        # Explicitly materialize - clear and Pythonic, no abstraction needed
        all_records = list(records)

        # Filter for classes only
        classes = [r for r in all_records if isinstance(r, ClassMatchRecord)]

        if not classes:
            return "No classes to diagram"

        # Generate mermaid syntax (requires all classes for inheritance)
        mermaid = self._generate_mermaid(classes)

        # Delegate to formatter (MD/HTML/PNG)
        return self.formatter.format_diagram(mermaid)

    def _generate_mermaid(self, classes: List[ClassMatchRecord]) -> str:
        """Generate mermaid classDiagram syntax."""
        lines = ['classDiagram']

        for cls in classes:
            # Class definition
            lines.append(f'    class {cls.symbol_name} {{')

            # Methods (lazy load from DB if needed)
            if hasattr(cls, 'get_methods'):
                methods = cls.get_methods(self.db)
                for method in methods:
                    lines.append(f'        +{method.symbol_name}()')

            lines.append('    }')

            # Inheritance (if base_classes populated)
            if hasattr(cls, 'base_classes') and cls.base_classes:
                for base in cls.base_classes:
                    lines.append(f'    {base} <|-- {cls.symbol_name}')

        return '\n'.join(lines)
```

---

## 4. Implementation Strategy

### Phase 1: Core Pipeline (P0 - Story 1)
**Duration**: 5 days

1. Create `via/pipeline/parser.py` - PipelineParser class
2. Create `via/pipeline/executor.py` - PipelineExecutor class
3. Update `via/__main__.py` to use pipeline
4. Add tests for parser (split on --via, parse flags)
5. Add tests for executor (multi-stage execution)

**Acceptance**: `via -mg -c '*' --via -mr -m '*'` executes both stages

---

### Phase 2: MatchRecord System (P0 - Story 2)
**Duration**: 5 days

1. Create `via/core/match_record.py` with base class + derived types
2. Create MatchRecordFactory
3. Update DatabaseStore.match() to return MatchRecord objects
4. Update pipeline executor to use factory
5. Add tests for all MatchRecord types

**Acceptance**: Each symbol type has appropriate MatchRecord class

---

### Phase 3: List & Table Renderers (P0 - Story 3)
**Duration**: 3 days

1. Create `via/renderers/base.py` - Renderer base class
2. Create `via/renderers/list.py` - ListRenderer
3. Create `via/renderers/table.py` - TableRenderer
4. Create formatters: AsciiTableFormatter, MarkdownTableFormatter
5. Wire renderers into pipeline executor
6. Add tests

**Acceptance**: `via -mg -c '*' --via -rTm` outputs markdown table

---

### Phase 4: Raw Renderer (P0 - Story 4a)
**Duration**: 2 days

1. Create `via/renderers/raw.py` - RawRenderer (truly raw, no formatting)
2. Implement source extraction with byte offset/length
3. Support ALL symbol types (including files, imports)
4. Add context line extraction
5. Add tests

**Acceptance**: `via -mg -f 'calculate' --via -rR` outputs pure source code, no colors/line numbers

---

### Phase 4b: Formatted Renderer (P0 - Story 4b)
**Duration**: 3 days

1. Create `via/renderers/formatted.py` - FormattedRenderer
2. Integrate Pygments for syntax highlighting
3. Add line number formatting
4. Implement theme detection (light/dark terminal)
5. Add tests

**Acceptance**: `via -mg -f 'calculate' --via -rF -C 5` shows formatted source with syntax highlighting and line numbers

---

### Phase 5: Streaming & Limits (P0 - Story 9)
**Duration**: 2 days

1. Update DatabaseStore.match() to respect limit parameter
2. Update ListRenderer to show "... N more" indicator
3. Add -n flag parsing
4. Set default limit to 10
5. Add tests

**Acceptance**: Default shows 10 results with indicator if more exist

---

### Phase 6: Diagram Renderer (P1 - Story 5)
**Duration**: 5 days

1. Create `via/renderers/diagram.py` - DiagramRenderer
2. Implement mermaid syntax generation
3. Add lazy-loading of class methods
4. Create MermaidFormatter variants (MD/HTML)
5. Add tests

**Acceptance**: `via -mg -c '*Database*' --via -rDm` outputs mermaid diagram

---

### Phase 7: Usage Renderer (P1 - Story 6)
**Duration**: 5 days

1. Create `via/renderers/usage.py` - UsageRenderer
2. Query symbol_references table
3. Format caller -> callee relationships
4. Add tests

**Acceptance**: `via -mg -m 'save' --via -rU` shows where save() is called

---

### Phase 8: Stats Command (P1 - Story 7)
**Duration**: 3 days

1. Create `via/commands/stats.py`
2. Query database for counts
3. Implement verbosity levels (-v/-vv/-vvv)
4. Add JSON output (--json)
5. Add tests

**Acceptance**: `via stats -vv` shows detailed breakdown

---

### Phase 9: Theme System (P1 - Story 8)
**Duration**: 2 days

1. Research Pygments styles
2. Implement terminal theme detection
3. Add --theme flag
4. Create --preview-themes command
5. Add tests

**Acceptance**: Syntax highlighting adapts to terminal theme

---

## 5. Testing Strategy

### Unit Tests
- Pipeline parser: Test splitting, flag parsing
- Pipeline executor: Test stage execution, filtering
- MatchRecord factory: Test all record types
- Each renderer: Test output formatting
- Formatters: Test ascii/md/html output

### Integration Tests
- Full pipeline: `via -mg -c '*' --via -mr -m '*' --via -rT`
- Context lines: Verify correct line extraction
- Limit behavior: Verify default 10, custom limits
- Theme detection: Mock terminal env vars

### Acceptance Tests
- All examples from requirements document
- Verify output matches expected format

---

## 6. Key Design Decisions

### Decision 1: Generator-based Pipeline
**Rationale**: Enables streaming, low memory usage, lazy evaluation
**Tradeoff**: Some renderers (table, diagram) must materialize all records
**Mitigation**: Only materialize when needed, document in renderer base class

### Decision 2: Polymorphic MatchRecords
**Rationale**: Type-specific behavior (supports_render_type), extensible
**Tradeoff**: More classes, slightly more complex
**Mitigation**: Factory pattern encapsulates creation, clear separation of concerns

### Decision 3: Use Pygments (not custom theme system)
**Rationale**: DRY principle, battle-tested, many themes included
**Tradeoff**: External dependency
**Mitigation**: Graceful fallback to plain text if not available

### Decision 4: Mermaid for Diagrams
**Rationale**: Text-based, no image rendering needed for MD output, widely supported
**Tradeoff**: Limited diagram types
**Mitigation**: Sufficient for class diagrams, can extend later

### Decision 5: String-based Rendering (not file output)
**Rationale**: Simple, composable with unix tools (| less, > file)
**Tradeoff**: Large outputs may overwhelm terminal
**Mitigation**: Default limit of 10 records, user can pipe to pager

---

## 7. File Structure

```
via/
├── __main__.py                 # CLI entry point
├── pipeline/
│   ├── __init__.py
│   ├── parser.py              # PipelineParser
│   ├── executor.py            # PipelineExecutor
│   └── types.py               # PipelineStage, StageType enums
├── core/
│   ├── types.py               # SymbolType, MatchOp (existing)
│   ├── match_record.py        # MatchRecord classes + factory
│   └── constants.py           # RenderType, FormatType enums
├── renderers/
│   ├── __init__.py
│   ├── base.py                # Renderer base class
│   ├── list.py                # ListRenderer
│   ├── table.py               # TableRenderer
│   ├── raw.py                 # RawRenderer
│   ├── diagram.py             # DiagramRenderer
│   ├── usage.py               # UsageRenderer
│   └── formatters/
│       ├── __init__.py
│       ├── table_formatters.py
│       ├── code_formatters.py
│       └── diagram_formatters.py
├── commands/
│   ├── __init__.py
│   ├── index.py               # Existing
│   ├── match.py               # Existing
│   ├── stats.py               # New
│   └── themes.py              # New (--preview-themes)
└── db/
    ├── store.py               # DatabaseStore (existing)
    └── schema.py              # Database schema (existing)
```

---

## 8. Dependencies

**New Dependencies**:
- `pygments` - Syntax highlighting (REQUIRED for raw renderer)
- `tabulate` (optional) - Better ASCII table formatting
- `mermaid-cli` (optional) - PNG diagram export

**Existing Dependencies**:
- `pathspec` - .gitignore support
- `sqlite3` - Database (stdlib)

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Pygments not available | High | Graceful fallback to plain text |
| Large result sets OOM | Medium | Default limit 10, streaming |
| Complex flag parsing | Medium | Thorough tests, clear error messages |
| Mermaid syntax errors | Low | Validate generated syntax, add tests |
| Theme detection fails | Low | Default to neutral theme |

---

## 10. Success Criteria

**Sprint 3 is complete when**:
- ✅ Internal pipeline works: `via -mg -c '*' --via -mr -m '*' --via -rT`
- ✅ All P0 stories implemented (18 points)
- ✅ All render types work: list, table, raw
- ✅ Default limit 10 with streaming
- ✅ 95%+ test coverage for new code
- ✅ All acceptance tests passing
- ✅ Documentation updated (README, USER_GUIDE)

---

**Status**: ✅ Architecture Design Complete
**Next**: @Mouse creates detailed task breakdown for @Neo
