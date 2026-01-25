# Sprint 4 Architecture - Tech Debt & Markdown Indexing

**Version**: 1.0
**Date**: 2026-01-22
**Architect**: @Morpheus
**Status**: Ready for Review

---

## Executive Summary

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

## 1. Markdown Parser Architecture

### 1.1 Design Rationale

Markdown headers are hierarchical like file paths. Just as we have:
- `-N` matches filename only: `test_foo.py`
- `-F` matches full path: `tests/unit/test_foo.py`

We now have:
- `-h` matches header text only: `Installation`
- `-H` matches full header path: `Getting Started > Installation`

This enables powerful queries like:
```bash
# Find all "Installation" headers anywhere
via -g 'Installation' -h

# Find "Installation" under "Getting Started" specifically
via -g '*Getting Started*Installation*' -H

# Find all level-2 headers (via path depth)
via -g '*>*' -H  # Contains one separator = level 2
```

### 1.2 Database Schema Extension

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

### 1.3 MarkdownParser Implementation

```python
# via/parsers/markdown_parser.py

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

### 1.4 Parser Flag Updates

> **Note**: VIA uses flag groups (`-tX` for type flags). Header flags follow this pattern.

```python
# via/core/flag_groups.py - Add to TYPE_FLAGS

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
# Match header text only (default)
via -mg 'Installation' -tH

# Match full header path (with -Q)
via -mg '*Guide*Installation*' -tH -Q
```

### 1.5 Match Stage Logic

```python
# via/pipeline/executor.py - Updated match logic

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

## 2. DiagramRenderer Architecture

### 2.1 Overview

The DiagramRenderer generates UML class diagrams using Mermaid syntax. It **must materialize** all records because building inheritance relationships requires seeing all classes.

### 2.2 Implementation

```python
# via/renderers/diagram.py

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

### 2.3 Formatters

```python
# via/renderers/formatters/diagram_formatters.py

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

## 3. UsageRenderer Architecture

### 3.1 Overview

The UsageRenderer renders the docstring of the matched symbol.

### 3.2 Database Extension (Optional)

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

### 3.3 Implementation (Grep-based Fallback)

```python
# via/renderers/usage.py

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

## 4. Stats Command Architecture

### 4.1 Overview

The stats command provides database statistics and health information.

### 4.2 Implementation

```python
# via/commands/stats.py

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

### 4.3 DatabaseStore Extensions

```python
# via/db/store.py - New methods

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

## 5. Implementation Plan

### Phase 1: MarkdownParser (P0)

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

### Phase 2: DiagramRenderer (P1)

**Files**:
- `via/renderers/diagram.py` (new)
- `via/renderers/formatters/diagram_formatters.py` (new)
- `via/renderers/factory.py` (register)

**Acceptance**: `via -g '*Renderer' -c --via -oD -m` outputs mermaid diagram

### Phase 3: UsageRenderer (P1)

**Files**:
- `via/renderers/usage.py` (new)
- `via/renderers/factory.py` (register)

**Acceptance**: `via -g 'match' -f -oU` shows the docstring of the match() function

### Phase 4: Stats Command (P1)

**Files**:
- `via/commands/stats.py` (new)
- `via/db/store.py` (add count methods)
- `via/__main__.py` (register command)

**Acceptance**: `via stats -v` shows symbol breakdown by type

---

## 6. File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `via/parsers/markdown_parser.py` | Parse markdown headers |
| `via/renderers/diagram.py` | DiagramRenderer |
| `via/renderers/usage.py` | UsageRenderer |
| `via/renderers/formatters/diagram_formatters.py` | Mermaid formatters |
| `via/commands/stats.py` | Stats command |

### Modified Files
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

## 7. Testing Strategy

### Unit Tests
```python
# tests/unit/test_markdown_parser.py

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

### Integration Tests
```python
# tests/integration/test_markdown_pipeline.py

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

## 8. Success Criteria

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
