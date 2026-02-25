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

from ..core.match_record import MatchRecord
from .base import ContextOptions, Renderer
from .utils.source_extraction import extract_source


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
        ctx = ContextOptions.from_options(**options)
        nodelims = options.get('nodelims', False)

        outputs = []

        for record in records:
            source = extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                ctx.before,
                ctx.after,
                read_full_file=True  # FileMatchRecord reads entire file
            )
            if source:
                if nodelims:
                    outputs.append(source)
                else:
                    # Calculate end line from source
                    line_count = source.count('\n') + 1
                    end_line = record.line_number + line_count - 1

                    # Build delimiter header (add newlines for raw output)
                    header = "\n\n" + self.format_delimiter_header(record, end_line) + "\n"
                    outputs.append(header + source)

        return '\n'.join(outputs)
