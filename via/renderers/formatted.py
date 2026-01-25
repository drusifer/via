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

import os
from typing import Iterator, Optional

from .base import Renderer, ContextOptions
from .formatters.code_formatters import CodeFormatter, AsciiCodeFormatter
from .utils.source_extraction import extract_source
from ..core.match_record import MatchRecord


# Symbol types that support formatted rendering
SUPPORTED_TYPES = {'class', 'method', 'function', 'global'}


class FormattedRenderer(Renderer):
    """Renderer that extracts and syntax-highlights source code.

    Uses Pygments for syntax highlighting. Only supports code symbols
    (class, method, function, global). Includes header with symbol info.
    """

    HELP = "-oF, --formatted: Syntax-highlighted source (Pygments)"
    FLAG = "-oF"

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
                nodelims: Disable delimiter headers (default: False)

        Returns:
            Syntax-highlighted source code string
        """
        ctx = ContextOptions.from_options(**options)
        theme = options.get('theme')
        show_line_numbers = options.get('show_line_numbers', False)
        nodelims = options.get('nodelims', False)

        outputs = []

        for record in records:
            # Skip unsupported types
            if record.symbol_type not in SUPPORTED_TYPES:
                continue

            # Extract source
            source = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                ctx.before,
                ctx.after,
                read_full_file=False  # FormattedRenderer requires byte_offset
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

            if nodelims:
                outputs.append(formatted)
            else:
                # Calculate end line from source
                line_count = source.count('\n') + 1
                end_line = record.line_number + line_count - 1

                # Add delimiter header
                header = self.format_delimiter_header(record, end_line)
                outputs.append(f'{header}\n{formatted}')

        return '\n\n'.join(outputs)

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
        _, ext = os.path.splitext(file_path.lower())

        return ext_map.get(ext, 'text')
