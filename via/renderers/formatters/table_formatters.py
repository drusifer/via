"""
Table formatters for different output formats.

TLDR:
    Defines TableFormatter base class and implementations for ASCII,
    Markdown, and HTML table formats. Used by TableRenderer to generate
    formatted table output.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from typing import Dict

from ...core.match_record import MatchRecord

# Default column order and display names
COLUMNS = [
    ('symbol_type', 'Type'),
    ('symbol_name', 'Name'),
    ('file_path', 'File'),
    ('line_number', 'Line'),
    ('qualified_name', 'Qualified Name'),
]


class TableFormatter(ABC):
    """Abstract base class for table formatters."""

    @abstractmethod
    def format_header(self, widths: Dict[str, int]) -> str:
        """Format table header row.

        Args:
            widths: Column widths

        Returns:
            Formatted header string (may include separator)
        """
        pass

    @abstractmethod
    def format_row(self, record: MatchRecord, widths: Dict[str, int]) -> str:
        """Format a single data row.

        Args:
            record: MatchRecord to format
            widths: Column widths

        Returns:
            Formatted row string
        """
        pass

    @abstractmethod
    def format_footer(self, count: int, total: int) -> str:
        """Format table footer with count info.

        Args:
            count: Number of rows shown
            total: Total matches

        Returns:
            Formatted footer string (empty if not needed)
        """
        pass


class AsciiTableFormatter(TableFormatter):
    """Formatter for ASCII pipe-separated tables."""

    def format_header(self, widths: Dict[str, int]) -> str:
        """Create ASCII header with separator line."""
        # Build header row
        cells = []
        separator_cells = []
        for col_key, col_name in COLUMNS:
            width = widths.get(col_key, len(col_name))
            width = max(width, len(col_name))
            cells.append(col_name.ljust(width))
            separator_cells.append('-' * width)

        header = '| ' + ' | '.join(cells) + ' |'
        separator = '|-' + '-|-'.join(separator_cells) + '-|'
        return header + '\n' + separator

    def format_row(self, record: MatchRecord, widths: Dict[str, int]) -> str:
        """Create ASCII data row."""
        values = {
            'symbol_type': record.symbol_type,
            'symbol_name': record.symbol_name,
            'file_path': record.file_path,
            'line_number': str(record.line_number),
            'qualified_name': record.qualified_name,
        }

        cells = []
        for col_key, col_name in COLUMNS:
            width = widths.get(col_key, len(col_name))
            width = max(width, len(col_name))
            value = values.get(col_key, '')
            cells.append(str(value).ljust(width))

        return '| ' + ' | '.join(cells) + ' |'

    def format_footer(self, count: int, total: int) -> str:
        """Create footer with more indicator if needed."""
        if total > count:
            remaining = total - count
            return f'\n... ({remaining} more)'
        return ''


class MarkdownTableFormatter(TableFormatter):
    """Formatter for Markdown tables."""

    def format_header(self, widths: Dict[str, int]) -> str:
        """Create Markdown header with separator line."""
        # Build header row
        cells = []
        separator_cells = []
        for col_key, col_name in COLUMNS:
            width = widths.get(col_key, len(col_name))
            width = max(width, len(col_name))
            cells.append(col_name)
            separator_cells.append('-' * width)

        header = '| ' + ' | '.join(cells) + ' |'
        separator = '| ' + ' | '.join(separator_cells) + ' |'
        return header + '\n' + separator

    def format_row(self, record: MatchRecord, widths: Dict[str, int]) -> str:
        """Create Markdown data row."""
        values = [
            record.symbol_type,
            record.symbol_name,
            record.file_path,
            str(record.line_number),
            record.qualified_name,
        ]
        return '| ' + ' | '.join(values) + ' |'

    def format_footer(self, count: int, total: int) -> str:
        """Create footer with more indicator if needed."""
        if total > count:
            remaining = total - count
            return f'\n*... ({remaining} more)*'
        return ''


class HtmlTableFormatter(TableFormatter):
    """Formatter for HTML tables."""

    def format_header(self, widths: Dict[str, int]) -> str:
        """Create HTML table header."""
        header_cells = ''.join(
            f'<th>{col_name}</th>' for _, col_name in COLUMNS
        )
        return f'<table>\n<thead>\n<tr>{header_cells}</tr>\n</thead>\n<tbody>'

    def format_row(self, record: MatchRecord, widths: Dict[str, int]) -> str:
        """Create HTML table row."""
        values = [
            record.symbol_type,
            record.symbol_name,
            record.file_path,
            str(record.line_number),
            record.qualified_name,
        ]
        cells = ''.join(f'<td>{v}</td>' for v in values)
        return f'<tr>{cells}</tr>'

    def format_footer(self, count: int, total: int) -> str:
        """Create HTML table footer."""
        footer = '</tbody>\n'
        if total > count:
            remaining = total - count
            footer += f'<tfoot><tr><td colspan="{len(COLUMNS)}">... ({remaining} more)</td></tr></tfoot>\n'
        footer += '</table>'
        return footer
