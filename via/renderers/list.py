"""
List renderer for simple line-by-line output.

TLDR:
    Outputs one line per record using MatchRecord.__str__(). Shows
    "... (N more)" indicator when results are limited. Streams records
    for O(1) memory usage.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Iterator

from ..core.match_record import MatchRecord
from .base import Renderer


class ListRenderer(Renderer):
    """Renderer that outputs one line per record.

    Uses MatchRecord.__str__() for formatting, which produces:
    type:file:line:qualified:@byte+len
    """

    HELP = "-oL, --list: One result per line (default)"
    FLAG = "-oL"

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records as simple list.

        Args:
            records: Iterator of MatchRecord objects
            **options: Not used by ListRenderer

        Returns:
            Formatted string with one record per line
        """
        lines = []
        count = 0
        total_matches = None

        for record in records:
            lines.append(str(record))
            count += 1

            # Capture total_matches from first record's metadata
            if total_matches is None and record.total_matches is not None:
                total_matches = record.total_matches

        # Add "more" indicator if there are more results
        if total_matches is not None and total_matches > count:
            remaining = total_matches - count
            lines.append(f'... ({remaining} more)')

        return '\n'.join(lines)
