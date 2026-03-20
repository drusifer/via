"""
Table renderer producing columnar output for any MatchRecord type.

TLDR:
    TableRenderer accepts a pluggable TableFormatter (ASCII, Markdown, or
    HTML) and emits columns: Type, Name, File, Line, Qualified Name.
    Column widths are sourced from MatchRecord.column_widths metadata so
    the header can be emitted on the first record, keeping memory O(1).
    Appends a footer with "... (N more)" when results are truncated.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Dict, Iterator, Optional

from ..core.match_record import MatchRecord
from .base import Renderer
from .formatters.table_formatters import COLUMNS, TableFormatter


class TableRenderer(Renderer):
    """Renderer that outputs records in table format.

    Uses a TableFormatter for actual formatting (ASCII, Markdown, HTML).
    Streams records using pre-computed column widths from metadata.
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
        lines = []
        count = 0
        total_matches = None
        widths: Optional[Dict[str, int]] = None

        for record in records:
            # Get metadata from first record
            if widths is None:
                widths = record.column_widths or {}
                # Ensure minimum widths for column headers
                for col_key, col_name in COLUMNS:
                    if col_key not in widths:
                        widths[col_key] = len(col_name)
                    else:
                        widths[col_key] = max(widths[col_key], len(col_name))
                # Output header
                lines.append(self._formatter.format_header(widths))

            if total_matches is None and record.total_matches is not None:
                total_matches = record.total_matches

            lines.append(self._formatter.format_row(record, widths))
            count += 1

        # Handle empty input
        if count == 0:
            return ''

        # Add footer
        footer = self._formatter.format_footer(count, total_matches or count)
        if footer:
            lines.append(footer)

        return '\n'.join(lines)
