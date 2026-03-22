"""
Table renderer producing columnar output for any MatchRecord type.

TLDR:
    TableRenderer accepts a pluggable TableFormatter (ASCII, Markdown, or
    HTML) and emits columns: Type, Name, File, Line, Qualified Name.
    Buffers all records, computes column widths from actual data, then
    emits header + rows. Appends a footer with "... (N more)" when
    results are truncated (uses total_matches from records if present).

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Dict, Iterator

from ..core.match_record import MatchRecord
from .base import Renderer
from .formatters.table_formatters import COLUMNS, TableFormatter


class TableRenderer(Renderer):
    """Renderer that outputs records in table format.

    Uses a TableFormatter for actual formatting (ASCII, Markdown, HTML).
    Buffers all records and computes column widths from actual field data.
    """

    HELP = "-oT, --table: ASCII/Markdown/HTML table output"
    FLAG = "-oT"

    def __init__(self, formatter: TableFormatter):
        """Initialize with a table formatter.

        Args:
            formatter: TableFormatter implementation for output format
        """
        self._formatter = formatter

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records as formatted table.

        Args:
            records: Iterator of MatchRecord objects
            **options: Not used by TableRenderer

        Returns:
            Formatted table string
        """
        buffered = list(records)
        if not buffered:
            return ''

        # Compute column widths from actual data, with header name as minimum
        widths: Dict[str, int] = {col_key: len(col_name) for col_key, col_name in COLUMNS}
        for record in buffered:
            values = {
                'symbol_type': record.symbol_type or '',
                'symbol_name': record.symbol_name or '',
                'file_path': record.file_path or '',
                'line_number': str(record.line_number),
                'qualified_name': record.qualified_name or '',
            }
            for col_key, _ in COLUMNS:
                widths[col_key] = max(widths[col_key], len(values[col_key]))

        # Use total_matches from records if present (e.g. set by tests or future lazy count)
        total_matches = buffered[0].total_matches

        lines = [self._formatter.format_header(widths)]
        for record in buffered:
            lines.append(self._formatter.format_row(record, widths))

        footer = self._formatter.format_footer(len(buffered), total_matches or len(buffered))
        if footer:
            lines.append(footer)

        return '\n'.join(lines)
