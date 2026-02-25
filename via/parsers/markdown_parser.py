"""
Markdown parser for extracting headers.

TLDR:
    Parses markdown files to extract headers (H1-H6) as searchable symbols.
    Headers are indexed with their text, level, and qualified name (ancestor path).
    Supports ATX-style headers (# Header) with optional trailing hashes.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import re
from typing import List, Set, Tuple

from .base import MarkdownHeadingEntity, ParserABC, ParseResult


class MarkdownParser(ParserABC):
    """Parser for Markdown files to extract headers."""

    # ATX-style header pattern: # through ###### followed by text
    # Captures: group(1) = hashes, group(2) = header text
    # Handles optional trailing hashes (## Title ##)
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$', re.MULTILINE)

    # Code fence pattern for detecting code blocks
    CODE_FENCE_PATTERN = re.compile(r'^```.*$', re.MULTILINE)

    @property
    def language_name(self) -> str:
        """Get language name."""
        return "markdown"

    def get_supported_extensions(self) -> Set[str]:
        """Get supported Markdown file extensions."""
        return {'.md', '.markdown', '.mdown', '.mkd'}

    def can_parse(self, file_path: str) -> bool:
        """Check if file is a Markdown file."""
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.get_supported_extensions()

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """
        Parse Markdown file and extract headers.

        Args:
            file_path: Path to the file being parsed
            content: File content as bytes

        Returns:
            ParseResult containing extracted headers
        """
        result = ParseResult(file_path=file_path, language="markdown")

        try:
            # Decode content
            text = content.decode('utf-8', errors='replace')

            # Find code block ranges to exclude
            code_ranges = self._find_code_block_ranges(text)

            # Extract headers (excluding those in code blocks)
            for match in self.HEADER_PATTERN.finditer(text):
                # Skip headers inside code blocks
                if self._is_in_code_block(match.start(), code_ranges):
                    continue

                hashes = match.group(1)
                header_text = match.group(2).strip()
                level = len(hashes)

                # Calculate byte offset and length
                byte_offset = match.start()
                byte_length = match.end() - match.start()

                # Calculate line number
                line_number = text[:byte_offset].count('\n') + 1

                heading = MarkdownHeadingEntity(
                    level=level,
                    text=header_text,
                    line_number=line_number,
                    byte_offset=byte_offset,
                    byte_length=byte_length,
                )

                result.markdown_headings.append(heading)

        except Exception as e:
            result.parse_error = f"Parse error: {type(e).__name__}: {e}"

        return result

    def _find_code_block_ranges(self, text: str) -> List[Tuple[int, int]]:
        """
        Find ranges of code blocks in the text.

        Returns list of (start, end) tuples for each code block.
        """
        ranges = []
        in_code_block = False
        code_start = 0

        for match in self.CODE_FENCE_PATTERN.finditer(text):
            if in_code_block:
                # End of code block
                ranges.append((code_start, match.end()))
                in_code_block = False
            else:
                # Start of code block
                code_start = match.start()
                in_code_block = True

        # If file ends inside a code block, close it at EOF
        if in_code_block:
            ranges.append((code_start, len(text)))

        return ranges

    def _is_in_code_block(self, position: int, code_ranges: List[Tuple[int, int]]) -> bool:
        """Check if a position is inside a code block."""
        for start, end in code_ranges:
            if start <= position < end:
                return True
        return False
