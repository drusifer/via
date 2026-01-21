"""
Formatted renderer for syntax-highlighted source code.

TLDR:
    Extracts source code from files and applies Pygments syntax highlighting.
    Supports code symbols (class, method, function, global). Shows header
    with symbol info. Streams records for O(1) memory usage.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Iterator, Optional

from .base import Renderer
from .formatters.code_formatters import CodeFormatter, AsciiCodeFormatter
from ..core.match_record import MatchRecord


# Symbol types that support formatted rendering
SUPPORTED_TYPES = {'class', 'method', 'function', 'global'}


class FormattedRenderer(Renderer):
    """Renderer that extracts and syntax-highlights source code.

    Uses Pygments for syntax highlighting. Only supports code symbols
    (class, method, function, global). Includes header with symbol info.
    """

    def __init__(self, formatter: Optional[CodeFormatter] = None):
        """Initialize with optional code formatter.

        Args:
            formatter: CodeFormatter instance (default: AsciiCodeFormatter)
        """
        self._formatter = formatter or AsciiCodeFormatter()

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records as syntax-highlighted source code.

        Args:
            records: Iterator of MatchRecord objects
            **options:
                after_context: Lines to show after match (-A)
                before_context: Lines to show before match (-B)
                context: Lines to show before and after (-C)
                theme: Color theme name
                show_line_numbers: Whether to show line numbers

        Returns:
            Syntax-highlighted source code string
        """
        # Extract options
        after_context = options.get('after_context', 0)
        before_context = options.get('before_context', 0)
        context = options.get('context', 0)
        theme = options.get('theme')
        show_line_numbers = options.get('show_line_numbers', False)

        # -C overrides -A and -B
        if context:
            after_context = context
            before_context = context

        outputs = []

        for record in records:
            # Skip unsupported types
            if record.symbol_type not in SUPPORTED_TYPES:
                continue

            # Extract source
            source = self._extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                before_context,
                after_context
            )

            if not source:
                continue

            # Determine language from file extension
            language = self._get_language(record.file_path)

            # Format with syntax highlighting
            formatted = self._formatter.format_code(
                source,
                language,
                start_line=record.line_number,
                theme=theme,
                show_line_numbers=show_line_numbers
            )

            # Add header
            header = self._format_header(record)
            outputs.append(f'{header}\n{formatted}')

        return '\n\n'.join(outputs)

    def _extract_source(
        self,
        file_path: str,
        byte_offset: Optional[int],
        byte_length: Optional[int],
        before_context: int = 0,
        after_context: int = 0
    ) -> str:
        """Extract source code from file.

        Args:
            file_path: Path to source file
            byte_offset: Starting byte offset
            byte_length: Number of bytes to read
            before_context: Lines to include before match
            after_context: Lines to include after match

        Returns:
            Extracted source code string
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except (IOError, OSError):
            return ''

        # If no byte_offset, can't extract specific symbol
        if byte_offset is None:
            return ''

        # Extract the matched region
        start = byte_offset
        end = byte_offset + (byte_length or 0)

        # Add context lines if requested
        if before_context > 0:
            start = self._find_context_start(content, start, before_context)
        if after_context > 0:
            end = self._find_context_end(content, end, after_context)

        # Extract and decode
        extracted = content[start:end]
        return extracted.decode('utf-8', errors='replace')

    def _find_context_start(self, content: bytes, start: int, num_lines: int) -> int:
        """Find start position including N context lines before."""
        pos = start
        lines_found = 0

        while pos > 0 and lines_found <= num_lines:
            pos -= 1
            if content[pos:pos+1] == b'\n':
                lines_found += 1

        if content[pos:pos+1] == b'\n':
            pos += 1

        return pos

    def _find_context_end(self, content: bytes, end: int, num_lines: int) -> int:
        """Find end position including N context lines after."""
        pos = end
        content_len = len(content)

        if pos < content_len and content[pos:pos+1] == b'\n':
            pos += 1

        lines_found = 0
        while pos < content_len and lines_found < num_lines:
            if content[pos:pos+1] == b'\n':
                lines_found += 1
            pos += 1

        return pos

    def _get_language(self, file_path: str) -> str:
        """Get programming language from file extension.

        Args:
            file_path: Path to source file

        Returns:
            Language name for Pygments
        """
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown',
        }

        # Get extension
        import os
        _, ext = os.path.splitext(file_path.lower())

        return ext_map.get(ext, 'text')

    def _format_header(self, record: MatchRecord) -> str:
        """Format header with symbol info.

        Args:
            record: MatchRecord to format header for

        Returns:
            Header string
        """
        return f'# {record.qualified_name} ({record.file_path}:{record.line_number})'
