"""
Raw renderer for extracting source code without formatting.

TLDR:
    Extracts raw source code from files using byte offsets. Supports
    context lines (-A/-B/-C). Output is plain text suitable for piping.
    Streams records for O(1) memory usage.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Iterator

from .base import Renderer
from .utils.source_extraction import extract_source
from ..core.match_record import MatchRecord


class RawRenderer(Renderer):
    """Renderer that extracts raw source code from files.

    Uses byte_offset and byte_length from MatchRecord to extract
    the exact source code. Supports context lines for additional
    context around the extracted code.
    """

    HELP = "-oR, --raw: Raw source code extraction"
    FLAG = "-oR"

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records as raw source code.

        Args:
            records: Iterator of MatchRecord objects
            **options:
                after_context: Lines to show after match (-A)
                before_context: Lines to show before match (-B)
                context: Lines to show before and after (-C)
                nodelims: Disable delimiter headers (default: False)

        Returns:
            Raw source code string
        """
        # Extract context options
        after_context = options.get('after_context', 0)
        before_context = options.get('before_context', 0)
        context = options.get('context', 0)
        nodelims = options.get('nodelims', False)

        # -C overrides -A and -B
        if context:
            after_context = context
            before_context = context

        outputs = []

        for record in records:
            source = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                before_context,
                after_context,
                read_full_file=True  # FileMatchRecord reads entire file
            )
            if source:
                if nodelims:
                    outputs.append(source)
                else:
                    # Calculate end line from source
                    line_count = source.count('\n') + 1
                    end_line = record.line_number + line_count - 1

                    # Build delimiter header
                    header = self._format_header(record, end_line)
                    outputs.append(header + source)

        return '\n'.join(outputs)

    def _format_header(self, record: MatchRecord, end_line: int) -> str:
        """Format the delimiter header for a match.

        Args:
            record: The match record
            end_line: Calculated end line number

        Returns:
            Formatted header string
        """
        divider = '#' * 60
        return (
            f"\n\n{divider}\n"
            f"# {record.file_path}:{record.line_number}-{end_line}\n"
            f"#     {record.symbol_type} *{record.symbol_name}*\n"
            f"{divider}\n"
        )
