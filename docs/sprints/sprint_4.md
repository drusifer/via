# Sprint 4 Consolidated Documentation

This document consolidates all documentation for Sprint 4.

## Table of Contents

- [SPRINT_4_ARCHITECTURE.md](#sprint-4-architecturemd) (originally `agents/morpheus.docs/SPRINT_4_ARCHITECTURE.md`)

- [SPRINT_4_CODE_REVIEW.md](#sprint-4-code-reviewmd) (originally `agents/morpheus.docs/SPRINT_4_CODE_REVIEW.md`)

- [SPRINT_4_REFACTORING.md](#sprint-4-refactoringmd) (originally `agents/morpheus.docs/SPRINT_4_REFACTORING.md`)

- [SPRINT_4_TASKS.md](#sprint-4-tasksmd) (originally `agents/mouse.docs/SPRINT_4_TASKS.md`)

- [UAT_REPORT_SPRINT_4.md](#uat-report-sprint-4md) (originally `agents/trin.docs/archive/UAT_REPORT_SPRINT_4.md`)

- [UAT_REPORT_SPRINT_4_20260122202755.md](#uat-report-sprint-4-20260122202755md) (originally `.history/agents/trin.docs/UAT_REPORT_SPRINT_4_20260122202755.md`)

- [UAT_REPORT_SPRINT_4_20260122202822.md](#uat-report-sprint-4-20260122202822md) (originally `.history/agents/trin.docs/UAT_REPORT_SPRINT_4_20260122202822.md`)


---


## SPRINT_4_ARCHITECTURE.md

**Original Location**: `agents/morpheus.docs/SPRINT_4_ARCHITECTURE.md`


## Sprint 4 Architecture - Tech Debt & Markdown Indexing

**Version**: 1.0
**Date**: 2026-01-22
**Architect**: @Morpheus
**Status**: Ready for Review

---

### Executive Summary

Sprint 4 is a **tech debt sprint** that completes the renderer set and adds markdown indexing support. The goal is to fill gaps from Sprint 3 and enable searching markdown documentation with the same power as Python code.

**Key Deliverables**:
1. **DiagramRenderer** - Mermaid-based class diagrams
2. **UsageRenderer** - Show where symbols are used
3. **Stats Command** - Database statistics and health
4. **MarkdownParser** - Index markdown headers as searchable symbols

**Key Design Decision**:
Header flags mirror the existing `-N`/`-F` pattern:
- `-h`: Match header text only (like `-N` for filename)
- `-H`: Match full header path with ancestors (like `-F` for filepath)

---

### 1. Markdown Parser Architecture

#### 1.1 Design Rationale

Markdown headers are hierarchical like file paths. Just as we have:
- `-N` matches filename only: `test_foo.py`
- `-F` matches full path: `tests/unit/test_foo.py`

We now have:
- `-h` matches header text only: `Installation`
- `-H` matches full header path: `Getting Started > Installation`

This enables powerful queries like:
```bash
## Find all "Installation" headers anywhere
via -g 'Installation' -h

## Find "Installation" under "Getting Started" specifically
via -g '*Getting Started*Installation*' -H

## Find all level-2 headers (via path depth)
via -g '*>*' -H  # Contains one separator = level 2
```

#### 1.2 Database Schema Extension

```sql
-- Existing symbols table (extended)
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    symbol_type TEXT NOT NULL,      -- 'class', 'method', 'function', 'import', 'global', 'header'
    symbol_name TEXT NOT NULL,      -- 'Installation' (header text only)
    qualified_name TEXT NOT NULL,   -- 'Getting Started > Installation' (full path)
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    byte_offset INTEGER,
    byte_length INTEGER,
    parent_name TEXT,               -- 'Getting Started' (immediate parent header)

    -- New column for headers
    header_level INTEGER,           -- 1-6 for markdown headers (NULL for non-headers)

    UNIQUE(file_path, symbol_type, qualified_name)
);

-- Index for header queries
CREATE INDEX idx_symbols_header_level ON symbols(header_level) WHERE header_level IS NOT NULL;
```

**Storage Design**:
| Header | symbol_name | qualified_name | header_level | parent_name |
|--------|-------------|----------------|--------------|-------------|
| `# Guide` | Guide | Guide | 1 | NULL |
| `## Getting Started` | Getting Started | Guide > Getting Started | 2 | Guide |
| `### Installation` | Installation | Guide > Getting Started > Installation | 3 | Getting Started |

#### 1.3 MarkdownParser Implementation

```python
## via/parsers/markdown_parser.py

import re
from pathlib import Path
from typing import List, Iterator, Optional
from via.parsers.base import ParserABC
from via.core.types import ParsedSymbol


class MarkdownParser(ParserABC):
    """Parse markdown files to extract headers as searchable symbols.

    Headers are indexed with:
    - symbol_name: The header text only (for -h matching)
    - qualified_name: Full path with ancestors (for -H matching)
    - header_level: 1-6 (for sorting/rendering)
    """

    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)(?:\s*#*)?\s*$', re.MULTILINE)

    @property
    def language_name(self) -> str:
        return "markdown"

    def get_supported_extensions(self) -> List[str]:
        return ['.md', '.markdown', '.mdown', '.mkd']

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.get_supported_extensions()

    def parse(self, file_path: Path, content: str) -> Iterator[ParsedSymbol]:
        """Parse markdown content and yield header symbols."""
        # Track header hierarchy for building qualified names
        header_stack: List[tuple[int, str]] = []  # [(level, name), ...]

        for match in self.HEADER_PATTERN.finditer(content):
            hashes = match.group(1)
            header_text = match.group(2).strip()
            level = len(hashes)

            # Calculate byte offset and line number
            byte_offset = match.start()
            byte_length = match.end() - match.start()
            line_number = content[:byte_offset].count('\n') + 1

            # Update header stack (pop headers at same or higher level)
            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()

            # Build qualified name from stack
            parent_name = header_stack[-1][1] if header_stack else None
            ancestors = [name for _, name in header_stack]
            ancestors.append(header_text)
            qualified_name = ' > '.join(ancestors)

            # Add current header to stack
            header_stack.append((level, header_text))

            yield ParsedSymbol(
                symbol_type='header',
                symbol_name=header_text,
                qualified_name=qualified_name,
                file_path=str(file_path),
                line_number=line_number,
                byte_offset=byte_offset,
                byte_length=byte_length,
                parent_name=parent_name,
                extra={'header_level': level}  # Stored in header_level column
            )
```

#### 1.4 Parser Flag Updates

> **Note**: VIA uses flag groups (`-tX` for type flags). Header flags follow this pattern.

```python
## via/core/flag_groups.py - Add to TYPE_FLAGS

TYPE_FLAGS: List[Flag] = [
    # ... existing flags ...
    Flag(FlagGroup.TYPE, 'c', 'type-class', 'symbol_type', 'class', 'Classes'),
    Flag(FlagGroup.TYPE, 'f', 'type-function', 'symbol_type', 'function', 'Functions'),
    Flag(FlagGroup.TYPE, 'm', 'type-method', 'symbol_type', 'method', 'Methods'),
    Flag(FlagGroup.TYPE, 'i', 'type-import', 'symbol_type', 'import', 'Imports'),
    Flag(FlagGroup.TYPE, 'g', 'type-global', 'symbol_type', 'global', 'Globals'),
    Flag(FlagGroup.TYPE, 'F', 'type-filepath', 'symbol_type', 'filepath', 'File paths'),
    Flag(FlagGroup.TYPE, 'N', 'type-filename', 'symbol_type', 'filename', 'File names'),

    # NEW: Header type flag (already added in Sprint 3)
    Flag(FlagGroup.TYPE, 'H', 'type-header', 'symbol_type', 'header', 'Markdown headers'),
]
```

**Flag Behavior** (using flag group pattern):

| Flag | Long Form | Matches Against | Example |
|------|-----------|-----------------|---------|
| `-tH` | `--type-header` | symbol_name | `via -mg 'Install*' -tH` |

**Header Path Matching**: Use `-Q` (qualified) flag with `-tH`:

```bash
## Match header text only (default)
via -mg 'Installation' -tH

## Match full header path (with -Q)
via -mg '*Guide*Installation*' -tH -Q
```

#### 1.5 Match Stage Logic

```python
## via/pipeline/executor.py - Updated match logic

def _execute_match_stage(self, stage: PipelineStage, prev_results) -> Iterator[MatchRecord]:
    args = stage.args
    symbol_type = args.symbol_type

    # Handle header variants
    if symbol_type == 'header':
        # Match against symbol_name only (like -N for filename)
        return self.db.match(
            symbol_type='header',
            match_column='symbol_name',  # NEW: specify which column to match
            match_op=self._get_match_op(args),
            pattern=args.pattern,
            case_sensitive=not args.case_insensitive,
            limit=args.limit
        )
    elif symbol_type == 'headerpath':
        # Match against qualified_name (like -F for filepath)
        return self.db.match(
            symbol_type='header',
            match_column='qualified_name',  # Match against full path
            match_op=self._get_match_op(args),
            pattern=args.pattern,
            case_sensitive=not args.case_insensitive,
            limit=args.limit
        )
    # ... existing logic for other types
```

---

### 2. DiagramRenderer Architecture

#### 2.1 Overview

The DiagramRenderer generates UML class diagrams using Mermaid syntax. It **must materialize** all records because building inheritance relationships requires seeing all classes.

#### 2.2 Implementation

```python
## via/renderers/diagram.py

from typing import Iterator, List, Optional
from via.renderers.base import Renderer
from via.core.match_record import MatchRecord, ClassMatchRecord


class DiagramRenderer(Renderer):
    """UML class diagram renderer using Mermaid syntax.

    This is the ONLY renderer that MUST materialize all records.
    Reason: Building class inheritance relationships requires seeing all classes.
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render class diagram.

        Materializes records to build complete inheritance tree.
        """
        # Materialize - required for diagram generation
        all_records = list(records)

        # Filter for classes only
        classes = [r for r in all_records if isinstance(r, ClassMatchRecord)]

        if not classes:
            return "No classes to diagram"

        # Generate mermaid syntax
        mermaid = self._generate_mermaid(classes)

        # Apply formatter (ascii/md/html)
        return self.formatter.format_diagram(mermaid)

    def _generate_mermaid(self, classes: List[ClassMatchRecord]) -> str:
        """Generate mermaid classDiagram syntax."""
        lines = ['classDiagram']

        # Build class name set for relationship filtering
        class_names = {cls.symbol_name for cls in classes}

        for cls in classes:
            # Class definition
            lines.append(f'    class {cls.symbol_name} {{')

            # Add methods if available
            if hasattr(cls, 'methods') and cls.methods:
                for method in cls.methods:
                    # Determine visibility prefix
                    if method.startswith('_'):
                        prefix = '-'  # private
                    else:
                        prefix = '+'  # public
                    lines.append(f'        {prefix}{method}()')

            lines.append('    }')

            # Inheritance relationships (only if parent in result set)
            if hasattr(cls, 'base_classes') and cls.base_classes:
                for base in cls.base_classes:
                    if base in class_names:
                        lines.append(f'    {base} <|-- {cls.symbol_name}')

        return '\n'.join(lines)
```

#### 2.3 Formatters

```python
## via/renderers/formatters/diagram_formatters.py

class MermaidAsciiFormatter:
    """Plain text mermaid syntax (for terminals/piping)."""

    def format_diagram(self, mermaid: str) -> str:
        return mermaid


class MermaidMarkdownFormatter:
    """Mermaid in markdown code block."""

    def format_diagram(self, mermaid: str) -> str:
        return f"```mermaid\n{mermaid}\n```"


class MermaidHtmlFormatter:
    """Mermaid with HTML + mermaid.js for rendering."""

    def format_diagram(self, mermaid: str) -> str:
        return f'''<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="mermaid">
{mermaid}
    </div>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</body>
</html>'''
```

---

### 3. UsageRenderer Architecture

#### 3.1 Overview

The UsageRenderer renders the docstring of the matched symbol.

#### 3.2 Database Extension (Optional)

```sql
-- Optional: Pre-computed references for faster usage queries
CREATE TABLE symbol_references (
    id INTEGER PRIMARY KEY,
    source_symbol_id INTEGER REFERENCES symbols(id),
    target_symbol_id INTEGER REFERENCES symbols(id),
    reference_type TEXT,  -- 'call', 'import', 'inheritance', 'attribute'
    file_path TEXT,
    line_number INTEGER,
    byte_offset INTEGER
);
```

#### 3.3 Implementation (Grep-based Fallback)

```python
## via/renderers/usage.py

import subprocess
from typing import Iterator, List
from via.renderers.base import Renderer
from via.core.match_record import MatchRecord


class UsageRenderer(Renderer):
    """Show where symbols are used.

    Uses grep to find references when pre-computed table not available.
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render usage information for each symbol."""
        outputs = []

        for record in records:
            usages = self._find_usages(record)

            if usages:
                header = f"# {record.qualified_name} ({record.file_path}:{record.line_number})"
                usage_lines = [f"  {u['file']}:{u['line']}: {u['context']}" for u in usages]
                outputs.append(f"{header}\nUsed in:\n" + '\n'.join(usage_lines))
            else:
                outputs.append(f"# {record.qualified_name}: No usages found")

        return '\n\n'.join(outputs)

    def _find_usages(self, record: MatchRecord) -> List[dict]:
        """Find usages of symbol using grep."""
        # Use ripgrep if available, fallback to grep
        symbol_name = record.symbol_name

        try:
            result = subprocess.run(
                ['rg', '-n', '--no-heading', symbol_name, '.'],
                capture_output=True,
                text=True,
                timeout=10
            )

            usages = []
            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        # Skip definition line
                        if parts[0] == record.file_path and parts[1] == str(record.line_number):
                            continue
                        usages.append({
                            'file': parts[0],
                            'line': parts[1],
                            'context': parts[2].strip()
                        })

            return usages[:20]  # Limit to 20 usages

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
```

---

### 4. Stats Command Architecture

#### 4.1 Overview

The stats command provides database statistics and health information.

#### 4.2 Implementation

```python
## via/commands/stats.py

from typing import Dict, Any
import json


class StatsCommand:
    """Display database statistics."""

    def __init__(self, db_store):
        self.db = db_store

    def execute(self, verbose: int = 0, as_json: bool = False) -> str:
        """Execute stats command.

        Args:
            verbose: 0 = summary, 1 = breakdown, 2 = detailed, 3 = full
            as_json: Output as JSON instead of text
        """
        stats = self._gather_stats(verbose)

        if as_json:
            return json.dumps(stats, indent=2)

        return self._format_stats(stats, verbose)

    def _gather_stats(self, verbose: int) -> Dict[str, Any]:
        """Gather statistics from database."""
        stats = {}

        # Basic counts
        stats['total_symbols'] = self.db.count_symbols()
        stats['total_files'] = self.db.count_files()

        if verbose >= 1:
            # Breakdown by type
            stats['by_type'] = self.db.count_by_type()

        if verbose >= 2:
            # Top files by symbol count
            stats['top_files'] = self.db.top_files_by_symbols(10)

            # Index age
            stats['last_indexed'] = self.db.get_last_index_time()

        if verbose >= 3:
            # Full breakdown
            stats['by_file'] = self.db.symbols_per_file()

        return stats

    def _format_stats(self, stats: Dict[str, Any], verbose: int) -> str:
        """Format stats as human-readable text."""
        lines = []

        lines.append(f"Total symbols: {stats['total_symbols']}")
        lines.append(f"Total files: {stats['total_files']}")

        if verbose >= 1 and 'by_type' in stats:
            lines.append("\nBy type:")
            for stype, count in stats['by_type'].items():
                lines.append(f"  {stype}: {count}")

        if verbose >= 2 and 'top_files' in stats:
            lines.append("\nTop files by symbol count:")
            for file, count in stats['top_files']:
                lines.append(f"  {count:4d}  {file}")

        return '\n'.join(lines)
```

#### 4.3 DatabaseStore Extensions

```python
## via/db/store.py - New methods

def count_symbols(self) -> int:
    """Count total symbols in database."""
    return self.conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

def count_files(self) -> int:
    """Count unique files in database."""
    return self.conn.execute("SELECT COUNT(DISTINCT file_path) FROM symbols").fetchone()[0]

def count_by_type(self) -> Dict[str, int]:
    """Count symbols by type."""
    rows = self.conn.execute(
        "SELECT symbol_type, COUNT(*) FROM symbols GROUP BY symbol_type ORDER BY COUNT(*) DESC"
    ).fetchall()
    return {row[0]: row[1] for row in rows}

def top_files_by_symbols(self, limit: int = 10) -> List[tuple]:
    """Get files with most symbols."""
    return self.conn.execute(
        "SELECT file_path, COUNT(*) as cnt FROM symbols GROUP BY file_path ORDER BY cnt DESC LIMIT ?",
        (limit,)
    ).fetchall()

def get_last_index_time(self) -> Optional[str]:
    """Get timestamp of last index operation."""
    row = self.conn.execute(
        "SELECT MAX(indexed_at) FROM file_metadata"
    ).fetchone()
    return row[0] if row else None
```

---

### 5. Implementation Plan

#### Phase 1: MarkdownParser (P0)

**Files**:
- `via/parsers/markdown_parser.py` (new)
- `via/db/store.py` (add header_level column)
- `via/pipeline/parser.py` (add -h/-H flags)
- `via/pipeline/executor.py` (handle header/headerpath types)
- `via/core/match_record.py` (add HeaderMatchRecord)

**Changes Summary**:
1. Create MarkdownParser following ParserABC interface
2. Register in discovery.py
3. Add header_level column to schema
4. Add `-h`/`-H` flags to match parser
5. Create HeaderMatchRecord class

**Acceptance**: `via -g 'Install*' -h` finds markdown headers

#### Phase 2: DiagramRenderer (P1)

**Files**:
- `via/renderers/diagram.py` (new)
- `via/renderers/formatters/diagram_formatters.py` (new)
- `via/renderers/factory.py` (register)

**Acceptance**: `via -g '*Renderer' -c --via -oD -m` outputs mermaid diagram

#### Phase 3: UsageRenderer (P1)

**Files**:
- `via/renderers/usage.py` (new)
- `via/renderers/factory.py` (register)

**Acceptance**: `via -g 'match' -f -oU` shows the docstring of the match() function

#### Phase 4: Stats Command (P1)

**Files**:
- `via/commands/stats.py` (new)
- `via/db/store.py` (add count methods)
- `via/__main__.py` (register command)

**Acceptance**: `via stats -v` shows symbol breakdown by type

---

### 6. File Changes Summary

#### New Files
| File | Purpose |
|------|---------|
| `via/parsers/markdown_parser.py` | Parse markdown headers |
| `via/renderers/diagram.py` | DiagramRenderer |
| `via/renderers/usage.py` | UsageRenderer |
| `via/renderers/formatters/diagram_formatters.py` | Mermaid formatters |
| `via/commands/stats.py` | Stats command |

#### Modified Files
| File | Changes |
|------|---------|
| `via/db/store.py` | Add header_level column, count methods |
| `via/pipeline/parser.py` | Add -h/-H flags |
| `via/pipeline/executor.py` | Handle header/headerpath types |
| `via/core/match_record.py` | Add HeaderMatchRecord |
| `via/core/types.py` | Add header to SymbolType enum |
| `via/core/discovery.py` | Register MarkdownParser |
| `via/renderers/factory.py` | Register new renderers |
| `via/__main__.py` | Register stats command |

---

### 7. Testing Strategy

#### Unit Tests
```python
## tests/unit/test_markdown_parser.py

def test_parse_single_header():
    parser = MarkdownParser()
    content = "# Hello World"
    symbols = list(parser.parse(Path("test.md"), content))

    assert len(symbols) == 1
    assert symbols[0].symbol_name == "Hello World"
    assert symbols[0].qualified_name == "Hello World"
    assert symbols[0].extra['header_level'] == 1

def test_parse_nested_headers():
    parser = MarkdownParser()
    content = "# Guide\n## Getting Started\n### Installation"
    symbols = list(parser.parse(Path("test.md"), content))

    assert len(symbols) == 3
    assert symbols[2].symbol_name == "Installation"
    assert symbols[2].qualified_name == "Guide > Getting Started > Installation"
    assert symbols[2].parent_name == "Getting Started"

def test_header_with_trailing_hashes():
    parser = MarkdownParser()
    content = "## Section ##"
    symbols = list(parser.parse(Path("test.md"), content))

    assert symbols[0].symbol_name == "Section"
```

#### Integration Tests
```python
## tests/integration/test_markdown_pipeline.py

def test_header_search():
    """Test full pipeline with markdown headers."""
    # Index markdown files
    result = run_via("index", ".")

    # Search headers by name
    result = run_via("-g", "Installation", "-h")
    assert "Installation" in result.stdout

    # Search by path
    result = run_via("-g", "*Guide*Installation*", "-H")
    assert "Guide > Getting Started > Installation" in result.stdout
```

---

### 8. Success Criteria

**Sprint 4 is complete when**:
- [ ] MarkdownParser indexes headers from .md files
- [ ] `-h` flag searches header text (symbol_name)
- [ ] `-H` flag searches header path (qualified_name)
- [ ] DiagramRenderer outputs mermaid class diagrams
- [ ] UsageRenderer shows symbol references
- [ ] Stats command shows database statistics
- [ ] All new code has 90%+ test coverage
- [ ] Documentation updated (USER_GUIDE.md)

---

**Status**: Ready for Review
**Next**: @Cypher creates Sprint 4 PRD, @Mouse creates task breakdown


---


## SPRINT_4_CODE_REVIEW.md

**Original Location**: `agents/morpheus.docs/SPRINT_4_CODE_REVIEW.md`


## Sprint 4 Code Review - Tech Debt Assessment

**Reviewer**: Morpheus (SE Lead)
**Date**: 2026-01-24
**Scope**: Full codebase review for code quality (DRY, KISS, Code Smells)
**Target**: @Neo for implementation

---

### Executive Summary

**Verdict**: NEEDS REFACTORING - Multiple code quality issues identified

| Severity | Count | Action Required |
|----------|-------|-----------------|
| HIGH | 6 | Must fix in Sprint 4 |
| MEDIUM | 5 | Should fix in Sprint 4 |
| LOW | 4 | Nice to have |

---

### HIGH Priority Issues

#### H1: Duplicated `_safe_print` Function
**Location**:
- [__main__.py:22-43](via/__main__.py#L22-L43)
- [executor.py:13-26](via/pipeline/executor.py#L13-L26)

**Problem**: Identical implementation copied verbatim in two files.

**Fix**: Extract to `via/core/utils.py`:
```python
## via/core/utils.py
def safe_print(text: str, file=None) -> None:
    """Print text safely, handling Unicode encoding errors."""
    ...
```

**Files to modify**: 2

---

#### H2: Duplicated `_format_header` Method
**Location**:
- [raw.py:84-100](via/renderers/raw.py#L84-L100)
- [formatted.py:161-177](via/renderers/formatted.py#L161-L177)

**Problem**: Nearly identical header formatting logic in both renderers.

**Fix**: Extract to base class or shared utility:
```python
## via/renderers/base.py
def format_delimiter_header(record: MatchRecord, end_line: int, divider_char='#', width=60) -> str:
    ...
```

**Files to modify**: 3

---

#### H3: Duplicated Context Option Extraction
**Location**:
- [raw.py:48-57](via/renderers/raw.py#L48-L57)
- [formatted.py:64-74](via/renderers/formatted.py#L64-L74)

**Problem**: Same pattern for handling -A, -B, -C options duplicated.

**Fix**: Create a dataclass for context options:
```python
@dataclass
class ContextOptions:
    before: int = 0
    after: int = 0

    @classmethod
    def from_options(cls, **options) -> 'ContextOptions':
        context = options.get('context', 0)
        before = context or options.get('before_context', 0)
        after = context or options.get('after_context', 0)
        return cls(before=before, after=after)
```

**Files to modify**: 3

---

#### H4: Repeated Database Connection Check
**Location**: [store.py](via/db/store.py) (~30 occurrences)

**Problem**: Every method starts with:
```python
if not self.conn:
    raise RuntimeError("Database not connected")
```

**Fix**: Use a decorator:
```python
def require_connection(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.conn:
            raise RuntimeError("Database not connected")
        return func(self, *args, **kwargs)
    return wrapper

## Usage
@require_connection
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    ...
```

**Files to modify**: 1, but many methods

---

#### H5: Duplicated Match Syntax Logic
**Location**:
- [executor.py:135-142](via/pipeline/executor.py#L135-L142)
- [executor.py:217-225](via/pipeline/executor.py#L217-L225)

**Problem**: Same if/elif block for converting match_syntax to MatchOp appears twice.

**Fix**: Extract to helper function:
```python
def get_match_op(match_syntax: str) -> MatchOp:
    """Convert match syntax suffix to MatchOp enum."""
    return {
        'r': MatchOp.REGEXP,
        's': MatchOp.LIKE,
    }.get(match_syntax, MatchOp.GLOB)
```

**Files to modify**: 1

---

#### H6: Render Support Defined in Two Places
**Location**:
- [executor.py:30-41](via/pipeline/executor.py#L30-L41) (SYMBOL_RENDER_SUPPORT dict)
- [match_record.py](via/core/match_record.py) (each subclass's `supports_render_type`)

**Problem**: Symbol render support is defined polymorphically in MatchRecord AND as a dict in executor. These can drift out of sync.

**Fix**: Remove `SYMBOL_RENDER_SUPPORT` dict from executor. The polymorphic `supports_render_type()` is the single source of truth.

**Files to modify**: 1

---

### MEDIUM Priority Issues

#### M1: Long Method - `_run_index_command`
**Location**: [__main__.py:220-326](via/__main__.py#L220-L326)

**Problem**: 106 lines - violates Single Responsibility. Does validation, initialization, execution, and output.

**Fix**: Extract into smaller functions:
- `_validate_index_args(args) -> Path`
- `_initialize_indexer(db_path, target_dir) -> IndexingService`
- `_print_index_summary(stats)`

---

#### M2: Primitive Obsession - String Symbol Types
**Location**: Multiple files

**Problem**: `symbol_type: str` used in MatchRecord when we have `SymbolType` enum.

**Current**:
```python
@dataclass
class MatchRecord(ABC):
    symbol_type: str  # 'class', 'method', etc.
```

**Better**:
```python
@dataclass
class MatchRecord(ABC):
    symbol_type: SymbolType  # Use the enum
```

**Files to modify**: 3-4

---

#### M3: Dead Code - `MatchResult` Class
**Location**: [types.py:58-91](via/core/types.py#L58-L91)

**Problem**: `MatchResult` dataclass appears to be superseded by `MatchRecord`. It's defined but likely unused (MatchRecord is the current implementation).

**Fix**: Verify no usages, then delete.

---

#### M4: Complex Pipeline Detection
**Location**: [__main__.py:507-554](via/__main__.py#L507-L554)

**Problem**: `_is_pipeline_syntax()` has complex logic with many conditions.

**Fix**: Simplify by checking for known subcommands first:
```python
def _is_pipeline_syntax(argv: list) -> bool:
    if not argv:
        return False
    subcommands = {'index', 'i', 'match', 'm', 'stats', 's', '--help', '-h', '--version'}
    if argv[0] in subcommands:
        return False
    # Everything else is pipeline syntax
    return True
```

---

#### M5: Redundant symbol_type Handling in Parser
**Location**: [parser.py:149-159](via/pipeline/parser.py#L149-L159)

**Problem**: Complex logic handling both `symbol_types` list and `symbol_type` single value.

**Fix**: Always use the list. Set default to empty list, no special single-type handling needed.

---

### LOW Priority Issues

#### L1: Magic Numbers
**Location**:
- [raw.py:94](via/renderers/raw.py#L94): `'#' * 60`
- [formatted.py:171](via/renderers/formatted.py#L171): `'#' * 60`
- [parser.py:251](via/pipeline/parser.py#L251): `default=10`

**Fix**: Extract to constants:
```python
## via/core/constants.py
HEADER_DIVIDER_WIDTH = 60
DEFAULT_RESULT_LIMIT = 10
```

---

#### L2: Data Clump - Context Options
**Location**: Renderers

**Problem**: `after_context`, `before_context`, `context` always travel together.

**Fix**: Already addressed in H3 with `ContextOptions` dataclass.

---

#### L3: Inconsistent Error Handling
**Location**: Various

**Problem**: Some methods return None, some raise exceptions, some print to stderr.

**Recommendation**: Establish pattern:
- Validation errors: raise `ValueError`
- Runtime errors: raise `RuntimeError`
- User-facing errors: print to stderr AND return error code

---

#### L4: Feature Envy in Executor
**Location**: [executor.py:269-293](via/pipeline/executor.py#L269-L293)

**Problem**: `_execute_render_stage` accesses many attributes of `stage.args`.

**Fix**: Consider extracting a `RenderOptions` dataclass that `stage.args` can provide.

---

### Refactoring Priority Order

For Sprint 4, I recommend tackling in this order:

1. **H1** (safe_print) - Quick win, 2 files
2. **H5** (match_syntax) - Quick win, 1 file
3. **H6** (render support) - Delete redundant code
4. **H2 + H3** (renderer duplication) - Related, do together
5. **H4** (connection decorator) - Many changes but mechanical
6. **M3** (dead code) - Verify and delete

Estimated effort: 3-4 hours for HIGH priority items.

---

### Files Modified Count

| File | Changes |
|------|---------|
| via/__main__.py | 3 changes |
| via/pipeline/executor.py | 3 changes |
| via/db/store.py | 1 large refactor |
| via/renderers/raw.py | 2 changes |
| via/renderers/formatted.py | 2 changes |
| via/renderers/base.py | 1 new method |
| via/core/utils.py | NEW FILE |
| via/core/types.py | 1 deletion |
| via/pipeline/parser.py | 1 change |

---

### Sign-off

**Reviewed by**: Morpheus
**Status**: Ready for @Neo implementation
**Next Action**: @Neo *swe refactor H1-H6 per review

---
*Code review complete. DRY violations are the primary concern.*


---


## SPRINT_4_REFACTORING.md

**Original Location**: `agents/morpheus.docs/SPRINT_4_REFACTORING.md`


## Sprint 4 Refactoring Architecture

**Version**: 1.0
**Date**: 2026-01-24
**Architect**: @Morpheus
**Status**: Ready for Implementation
**Reference**: [SPRINT_4_CODE_REVIEW.md](SPRINT_4_CODE_REVIEW.md)

---

### Executive Summary

This document provides architectural guidance for the Sprint 4 tech debt refactoring. It establishes patterns and conventions to eliminate DRY violations and improve code quality.

**Goal**: Reduce code duplication by ~40% in core modules while maintaining backward compatibility.

---

### 1. New Core Utils Module

#### 1.1 Create `via/core/utils.py`

Extract common utilities that are duplicated across modules.

```python
## via/core/utils.py
"""Common utility functions for VIA.

This module consolidates utilities that were previously duplicated
across multiple modules.
"""

import sys
from functools import wraps
from typing import Callable, TypeVar, Any

from .types import MatchOp

F = TypeVar('F', bound=Callable[..., Any])


def safe_print(text: str, file=None) -> None:
    """Print text safely, handling Unicode encoding errors.

    Some terminals use latin-1 or ASCII encoding which can't handle
    Unicode characters like emojis. This handles such cases gracefully.

    Args:
        text: The text to print
        file: Output file (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        print(safe_text, file=file)


def get_match_op(match_syntax: str) -> MatchOp:
    """Convert match syntax suffix to MatchOp enum.

    Args:
        match_syntax: Single character suffix ('g', 'r', 's')

    Returns:
        Corresponding MatchOp enum value
    """
    return {
        'r': MatchOp.REGEXP,
        's': MatchOp.LIKE,
    }.get(match_syntax, MatchOp.GLOB)
```

#### 1.2 Migration

| Old Location | New Location |
|--------------|--------------|
| `via/__main__.py:_safe_print()` | `via.core.utils.safe_print()` |
| `via/pipeline/executor.py:_safe_print()` | `via.core.utils.safe_print()` |
| `via/pipeline/executor.py:135-142` | `via.core.utils.get_match_op()` |
| `via/pipeline/executor.py:217-225` | `via.core.utils.get_match_op()` |

---

### 2. Database Connection Decorator

#### 2.1 Pattern: `@require_connection`

Add a decorator to eliminate repeated connection checks in `store.py`.

```python
## via/db/store.py (add at top after imports)

def require_connection(func: F) -> F:
    """Decorator that ensures database connection exists.

    Raises:
        RuntimeError: If database is not connected
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.conn:
            raise RuntimeError("Database not connected")
        return func(self, *args, **kwargs)
    return wrapper
```

#### 2.2 Usage

```python
## Before (repeated ~30 times)
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    if not self.conn:
        raise RuntimeError("Database not connected")
    # ... actual logic

## After
@require_connection
def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
    # ... actual logic (cleaner!)
```

#### 2.3 Methods to Refactor

All public methods in `DatabaseStore` except:
- `__init__`
- `connect`
- `close`
- `__enter__` / `__exit__`

---

### 3. Renderer Base Class Consolidation

#### 3.1 Context Options Dataclass

Extract repeated context option handling into a dataclass.

```python
## via/renderers/base.py (add to existing file)

from dataclasses import dataclass
from typing import Optional


@dataclass
class ContextOptions:
    """Options for context lines around matches.

    Consolidates -A, -B, -C option handling that was duplicated
    in RawRenderer and FormattedRenderer.
    """
    before: int = 0
    after: int = 0

    @classmethod
    def from_options(cls, **options) -> 'ContextOptions':
        """Create from render options dict.

        Args:
            **options: Render options including:
                - after_context: Lines after match (-A)
                - before_context: Lines before match (-B)
                - context: Lines both sides (-C, overrides -A/-B)

        Returns:
            ContextOptions instance
        """
        context = options.get('context')
        if context:
            return cls(before=context, after=context)
        return cls(
            before=options.get('before_context', 0),
            after=options.get('after_context', 0)
        )
```

#### 3.2 Header Formatting Method

Add shared header formatting to base `Renderer` class.

```python
## via/renderers/base.py (add to Renderer class)

## Constants
HEADER_DIVIDER_WIDTH = 60
HEADER_DIVIDER_CHAR = '#'


class Renderer(ABC):
    # ... existing code ...

    def format_delimiter_header(
        self,
        record: 'MatchRecord',
        end_line: int,
        divider_char: str = HEADER_DIVIDER_CHAR,
        width: int = HEADER_DIVIDER_WIDTH
    ) -> str:
        """Format delimiter header for a match.

        Args:
            record: The match record
            end_line: Calculated end line number
            divider_char: Character for divider line
            width: Width of divider line

        Returns:
            Formatted header string
        """
        divider = divider_char * width
        return (
            f"{divider}\n"
            f"{divider_char} {record.file_path}:{record.line_number}-{end_line}\n"
            f"{divider_char}     {record.symbol_type} *{record.symbol_name}*\n"
            f"{divider}"
        )
```

#### 3.3 Renderer Updates

```python
## via/renderers/raw.py - Updated

from .base import Renderer, ContextOptions

class RawRenderer(Renderer):
    def render(self, records: Iterator[MatchRecord], **options) -> str:
        ctx = ContextOptions.from_options(**options)  # Use shared class
        nodelims = options.get('nodelims', False)

        outputs = []
        for record in records:
            source = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                ctx.before,  # Use dataclass
                ctx.after,
                read_full_file=True
            )
            if source:
                if nodelims:
                    outputs.append(source)
                else:
                    line_count = source.count('\n') + 1
                    end_line = record.line_number + line_count - 1
                    header = self.format_delimiter_header(record, end_line)  # Use base method
                    outputs.append(header + '\n' + source)

        return '\n'.join(outputs)

    # DELETE: _format_header method (now in base class)
```

---

### 4. Remove Redundant Render Support

#### 4.1 Problem

Render support is defined in TWO places:
1. `via/pipeline/executor.py:SYMBOL_RENDER_SUPPORT` dict
2. Each `MatchRecord` subclass's `supports_render_type()` method

#### 4.2 Solution

Delete `SYMBOL_RENDER_SUPPORT` dict from executor.py. The polymorphic method is the single source of truth.

```python
## via/pipeline/executor.py

## DELETE these lines (30-41):
## SYMBOL_RENDER_SUPPORT: Dict[str, Set[RenderType]] = {
##     'class': {RenderType.LIST, ...},
##     ...
## }

## DELETE: _print_unsupported_warning method that uses it

## UPDATE: _execute_render_stage to use record.supports_render_type() only
```

#### 4.3 Updated Warning Logic

```python
## via/pipeline/executor.py - Simplified warning

def _execute_render_stage(self, stage: PipelineStage, records: Iterator[MatchRecord]):
    # ... existing setup ...

    skipped_types: Dict[str, int] = {}

    def filter_supported(records_iter: Iterator[MatchRecord]) -> Iterator[MatchRecord]:
        for record in records_iter:
            if record.supports_render_type(render_type):
                yield record
            else:
                skipped_types[record.symbol_type] = skipped_types.get(record.symbol_type, 0) + 1

    # ... render ...

    if skipped_types:
        total = sum(skipped_types.values())
        types_str = ', '.join(f"{t}({c})" for t, c in skipped_types.items())
        print(f"Warning: {total} records skipped (unsupported render type): {types_str}",
              file=sys.stderr)
```

---

### 5. Constants Consolidation

#### 5.1 Add to `via/core/constants.py`

```python
## via/core/constants.py (additions)

## Rendering
HEADER_DIVIDER_WIDTH = 60
HEADER_DIVIDER_CHAR = '#'

## Defaults
DEFAULT_RESULT_LIMIT = 10
```

---

### 6. Dead Code Removal

#### 6.1 Remove `MatchResult` Class

The `MatchResult` dataclass in `via/core/types.py` is superseded by `MatchRecord`.

**Verification**: Search for usages before deletion.
```bash
via -mg 'MatchResult' -tc -tf
```

If no usages found, delete lines 58-91 in `types.py`.

---

### 7. Implementation Order

Execute in this order for minimal risk:

| Step | Task | Files | Risk |
|------|------|-------|------|
| 1 | Create `via/core/utils.py` | New file | Low |
| 2 | Import `safe_print` in __main__.py, executor.py | 2 files | Low |
| 3 | Import `get_match_op` in executor.py | 1 file | Low |
| 4 | Add `@require_connection` decorator | store.py | Medium |
| 5 | Add `ContextOptions` to base.py | 1 file | Low |
| 6 | Add `format_delimiter_header` to base.py | 1 file | Low |
| 7 | Update raw.py to use base methods | 1 file | Low |
| 8 | Update formatted.py to use base methods | 1 file | Low |
| 9 | Remove `SYMBOL_RENDER_SUPPORT` from executor.py | 1 file | Low |
| 10 | Remove `MatchResult` from types.py | 1 file | Low |
| 11 | Add constants to constants.py | 1 file | Low |

**Run tests after each step!**

---

### 8. Testing Strategy

#### 8.1 Before Refactoring

```bash
source .venv/bin/activate && pytest -v
```

Record baseline: all tests should pass.

#### 8.2 After Each Step

```bash
pytest -v
```

All tests must continue to pass.

#### 8.3 Regression Tests

No new tests needed - existing tests cover the functionality. Refactoring should not change behavior.

---

### 9. Success Criteria

- [ ] `via/core/utils.py` exists with `safe_print` and `get_match_op`
- [ ] No duplicate `_safe_print` functions in codebase
- [ ] No duplicate match_syntax→MatchOp logic in codebase
- [ ] `@require_connection` decorator used in store.py
- [ ] `ContextOptions` used in raw.py and formatted.py
- [ ] `format_delimiter_header` in Renderer base class only
- [ ] `SYMBOL_RENDER_SUPPORT` deleted from executor.py
- [ ] `MatchResult` deleted from types.py
- [ ] All tests pass
- [ ] No functional changes (pure refactoring)

---

**Status**: Ready for @Neo implementation
**Estimated Effort**: 3-4 hours
**Next**: @Neo *swe refactor per this architecture


---


## SPRINT_4_TASKS.md

**Original Location**: `agents/mouse.docs/SPRINT_4_TASKS.md`


## Sprint 4 Task Breakdown - Tech Debt & Markdown Indexing

**Version**: 1.0
**Date**: 2026-01-22
**Task Owner**: @Mouse
**Status**: Ready for Implementation

---

### Executive Summary

Sprint 4 is a **tech debt sprint** that completes the renderer set, adds markdown indexing, and fills gaps in format support. Total: 26 story points, ~208 hours.

**Sprint Theme**: Complete the tooling and enable markdown search

**Critical Path**: MarkdownParser (P0) → DiagramRenderer → UsageRenderer → Stats

---

### Current State Assessment

#### Renderer Implementation Status

| Render Type | Implemented | ASCII | MD | HTML | PNG |
|-------------|-------------|-------|-----|------|-----|
| LIST (-oL) | ✅ | ✅ | - | - | - |
| TABLE (-oT) | ✅ | ✅ | ✅ | ✅ | - |
| RAW (-oR) | ✅ | ✅ | - | - | - |
| FORMATTED (-oF) | ✅ | ✅ | ✅ | ✅ | - |
| DIAGRAM (-oD) | ❌ | - | - | - | - |
| USAGE (-oU) | ❌ | - | - | - | - |

#### Tech Debt Backlog

| Item | Source | Priority | Sprint 4? |
|------|--------|----------|-----------|
| DiagramRenderer not implemented | Sprint 3 P1 | P1 | ✅ |
| UsageRenderer not implemented | Sprint 3 P1 | P1 | ✅ |
| Stats command not implemented | Sprint 3 P1 | P1 | ✅ |
| REGEXP SQLite extension | Sprint 3 Known Issue | P3 | ❌ Defer |
| Theme preview command | Sprint 3 P1 | P2 | ❌ Defer |

---

### Sprint 4 Scope

#### Story Points Summary

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

### Phase 1: MarkdownParser (US-MD1 - P0, 5pts)

**Dependencies**: None (BLOCKER for markdown search)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 1.1: Create MarkdownParser Class (2 days, 16h)

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

#### Task 1.2: Register MarkdownParser in Discovery (0.5 days, 4h)

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

#### Task 1.3: Add header_level Column to Database (0.5 days, 4h)

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

#### Task 1.4: Add -h and -H Flags to Parser (1 day, 8h)

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

#### Task 1.5: Update Executor for Header Matching (1 day, 8h)

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

#### Task 1.6: Create HeaderMatchRecord (0.5 days, 4h)

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

### Phase 2: DiagramRenderer (US-RD1 - P1, 5pts)

**Dependencies**: None (ClassMatchRecord exists)
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 2.1: Create Diagram Formatters (1 day, 8h)

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

#### Task 2.2: Implement DiagramRenderer (2 days, 16h)

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

#### Task 2.3: Implement Lazy Method Loading (1 day, 8h)

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

#### Task 2.4: Register DiagramRenderer in Factory (0.5 days, 4h)

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

#### Task 2.5: Integration Tests for DiagramRenderer (0.5 days, 4h)

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

### Phase 3: UsageRenderer (US-RD2 - P1, 5pts)

**Dependencies**: None
**Duration**: 5 days (40h)
**Assignee**: @Neo

#### Task 3.1: Create Usage Formatters (0.5 days, 4h)

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

#### Task 3.2: Implement UsageRenderer (2.5 days, 20h)

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

#### Task 3.3: Register UsageRenderer in Factory (0.5 days, 4h)

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

#### Task 3.4: Integration Tests for UsageRenderer (1 day, 8h)

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

#### Task 3.5: Handle Missing ripgrep (0.5 days, 4h)

**Implementation Steps**:
1. Check if `rg` command available
2. Fallback to `grep` if ripgrep not installed
3. Provide helpful error if neither available

**Estimated**: 4h

---

**Phase 3 Total**: 40h (5 days)

---

### Phase 4: Stats Command (US-ST1 - P1, 3pts)

**Dependencies**: None
**Duration**: 3 days (24h)
**Assignee**: @Neo

#### Task 4.1: Create Stats Command (1.5 days, 12h)

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

#### Task 4.2: Add Count Methods to DatabaseStore (0.5 days, 4h)

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

#### Task 4.3: Wire Stats into CLI (0.5 days, 4h)

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

#### Task 4.4: Add Header Stats (0.5 days, 4h)

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

### Phase 5: Tech Debt & Polish (US-TD1-4, 8pts)

**Dependencies**: Phases 1-4
**Duration**: 4 days (32h)
**Assignee**: @Neo

#### Task 5.1: Delimiter Control (US-TD1 - 2pts, 8h)

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

#### Task 5.2: HeaderMatchRecord Rendering (US-TD2 - 2pts, 8h)

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

#### Task 5.3: Integration Tests (US-TD3 - 2pts, 8h)

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

#### Task 5.4: Documentation Update (US-TD4 - 2pts, 8h)

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

### Sprint 4 Summary

#### Total Effort by Phase

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

#### Critical Path

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

#### Dependencies Graph

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

#### Parallelization Opportunities

Phases 2, 3, and 4 can run in parallel after Phase 1 is complete:
- **@Neo-1**: DiagramRenderer (Phase 2)
- **@Neo-2**: UsageRenderer (Phase 3)
- **@Neo-3**: Stats Command (Phase 4)

Or sequentially by single developer: ~26 days @ 8h/day

#### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Markdown parsing edge cases | Medium | Low | Comprehensive tests, handle gracefully |
| Mermaid syntax issues | Low | Medium | Validate generated syntax |
| ripgrep not available | Medium | Medium | Fallback to grep |
| Performance with large MD files | Low | Medium | Streaming, limits |

#### Success Criteria

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

### Appendix: Flag Reference

#### After Sprint 4

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


---


## UAT_REPORT_SPRINT_4.md

**Original Location**: `agents/trin.docs/archive/UAT_REPORT_SPRINT_4.md`


## Sprint 4 UAT Report

**Date:** 2026-01-22
**QA Owner:** Trin

### Executive Summary
Sprint 4 focused on tech debt and feature completion: MarkdownParser, DiagramRenderer, UsageRenderer, and Stats command. All TDD and implementation tasks are complete, and all related unit tests pass.

### User Acceptance Criteria
- [x] MarkdownParser parses all header levels, builds qualified names, and handles edge cases
- [x] DiagramRenderer renders class diagrams in all required formats
- [x] UsageRenderer outputs the docstring of the symbol with correct formatting and handles unicode/missing fields
- [x] Stats command provides accurate statistics and supports verbose/json output

### Test Results
- All unit tests for new and updated components pass
- DiagramRenderer and UsageRenderer tested for output correctness and edge cases
- MarkdownParser verified for header parsing, byte offsets, and qualified names
- Stats command tested for all output modes

### Manual QA
- CLI tested interactively for Markdown, Diagram, Usage, and Stats features
- No regressions or critical bugs found
- All acceptance criteria met

### Outstanding Issues
- None blocking release

### Recommendation
Sprint 4 is ready for release. All acceptance criteria are met and quality is sufficient for production.

---

*Report generated by Trin, QA persona (Bob Protocol)*


---


## UAT_REPORT_SPRINT_4_20260122202755.md

**Original Location**: `.history/agents/trin.docs/UAT_REPORT_SPRINT_4_20260122202755.md`


## Sprint 4 UAT Report

**Date:** 2026-01-22
**QA Owner:** Trin

### Executive Summary
Sprint 4 focused on tech debt and feature completion: MarkdownParser, DiagramRenderer, UsageRenderer, and Stats command. All TDD and implementation tasks are complete, and all related unit tests pass.

### User Acceptance Criteria
- [x] MarkdownParser parses all header levels, builds qualified names, and handles edge cases
- [x] DiagramRenderer renders class diagrams in all required formats
- [x] UsageRenderer outputs symbol usage with correct formatting and handles unicode/missing fields
- [x] Stats command provides accurate statistics and supports verbose/json output

### Test Results
- All unit tests for new and updated components pass
- DiagramRenderer and UsageRenderer tested for output correctness and edge cases
- MarkdownParser verified for header parsing, byte offsets, and qualified names
- Stats command tested for all output modes

### Manual QA
- CLI tested interactively for Markdown, Diagram, Usage, and Stats features
- No regressions or critical bugs found
- All acceptance criteria met

### Outstanding Issues
- None blocking release

### Recommendation
Sprint 4 is ready for release. All acceptance criteria are met and quality is sufficient for production.

---

*Report generated by Trin, QA persona (Bob Protocol)*


---


## UAT_REPORT_SPRINT_4_20260122202822.md

**Original Location**: `.history/agents/trin.docs/UAT_REPORT_SPRINT_4_20260122202822.md`


## Sprint 4 UAT Report

**Date:** 2026-01-22
**QA Owner:** Trin

### Executive Summary
Sprint 4 focused on tech debt and feature completion: MarkdownParser, DiagramRenderer, UsageRenderer, and Stats command. All TDD and implementation tasks are complete, and all related unit tests pass.

### User Acceptance Criteria
- [x] MarkdownParser parses all header levels, builds qualified names, and handles edge cases
- [x] DiagramRenderer renders class diagrams in all required formats
- [x] UsageRenderer outputs symbol usage with correct formatting and handles unicode/missing fields
- [x] Stats command provides accurate statistics and supports verbose/json output

### Test Results
- All unit tests for new and updated components pass
- DiagramRenderer and UsageRenderer tested for output correctness and edge cases
- MarkdownParser verified for header parsing, byte offsets, and qualified names
- Stats command tested for all output modes

### Manual QA
- CLI tested interactively for Markdown, Diagram, Usage, and Stats features
- No regressions or critical bugs found
- All acceptance criteria met

### Outstanding Issues
- None blocking release

### Recommendation
Sprint 4 is ready for release. All acceptance criteria are met and quality is sufficient for production.

---

*Report generated by Trin, QA persona (Bob Protocol)*


---
