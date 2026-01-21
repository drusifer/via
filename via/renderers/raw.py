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

from typing import Iterator, Optional

from .base import Renderer
from ..core.match_record import MatchRecord


class RawRenderer(Renderer):
    """Renderer that extracts raw source code from files.

    Uses byte_offset and byte_length from MatchRecord to extract
    the exact source code. Supports context lines for additional
    context around the extracted code.
    """

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records as raw source code.

        Args:
            records: Iterator of MatchRecord objects
            **options:
                after_context: Lines to show after match (-A)
                before_context: Lines to show before match (-B)
                context: Lines to show before and after (-C)

        Returns:
            Raw source code string
        """
        # Extract context options
        after_context = options.get('after_context', 0)
        before_context = options.get('before_context', 0)
        context = options.get('context', 0)

        # -C overrides -A and -B
        if context:
            after_context = context
            before_context = context

        outputs = []

        for record in records:
            source = self._extract_source(
                record.file_path,
                record.byte_offset,
                record.byte_length,
                before_context,
                after_context
            )
            if source:
                outputs.append(source)

        return '\n'.join(outputs)

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
            byte_offset: Starting byte offset (None = read entire file)
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
            # File not found or unreadable
            return ''

        # If no byte_offset, read entire file (FileMatchRecord)
        if byte_offset is None:
            return content.decode('utf-8', errors='replace')

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
        """Find start position including N context lines before.

        Args:
            content: File content as bytes
            start: Current start position
            num_lines: Number of lines to include before

        Returns:
            New start position (start of the Nth line before)
        """
        pos = start
        lines_found = 0

        # Need to find N+1 newlines to get N lines before
        # (first newline is end of current line, subsequent are line breaks)
        while pos > 0 and lines_found <= num_lines:
            pos -= 1
            if content[pos:pos+1] == b'\n':
                lines_found += 1

        # Move past the newline to start of line (if we found one)
        if content[pos:pos+1] == b'\n':
            pos += 1

        return pos

    def _find_context_end(self, content: bytes, end: int, num_lines: int) -> int:
        """Find end position including N context lines after.

        Args:
            content: File content as bytes
            end: Current end position
            num_lines: Number of lines to include after

        Returns:
            New end position (after the Nth newline)
        """
        pos = end
        content_len = len(content)

        # Skip newline at current position (it's the end of matched content)
        if pos < content_len and content[pos:pos+1] == b'\n':
            pos += 1

        # Find N more newlines for N context lines
        lines_found = 0
        while pos < content_len and lines_found < num_lines:
            if content[pos:pos+1] == b'\n':
                lines_found += 1
            pos += 1

        return pos
