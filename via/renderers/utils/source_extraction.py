"""
Shared utilities for source code extraction.

TLDR:
    Provides functions for extracting source code from files using byte offsets,
    with support for context lines. Used by RawRenderer and FormattedRenderer.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_source(
    file_path: str,
    byte_offset: Optional[int],
    byte_length: Optional[int],
    before_context: int = 0,
    after_context: int = 0,
    read_full_file: bool = False
) -> str:
    """Extract source code from file.

    Args:
        file_path: Path to source file
        byte_offset: Starting byte offset (None with read_full_file=True reads entire file)
        byte_length: Number of bytes to read
        before_context: Lines to include before match
        after_context: Lines to include after match
        read_full_file: If True and byte_offset is None, read entire file

    Returns:
        Extracted source code string, empty string on error
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
    except (IOError, OSError) as e:
        logger.warning("Could not read file %s: %s", file_path, e)
        return ''

    # If no byte_offset, handle based on read_full_file flag
    if byte_offset is None:
        if read_full_file:
            return content.decode('utf-8', errors='replace')
        return ''

    # Extract the matched region
    start = byte_offset
    end = byte_offset + (byte_length or 0)

    # Add context lines if requested
    if before_context > 0:
        start = find_context_start(content, start, before_context)
    if after_context > 0:
        end = find_context_end(content, end, after_context)

    # Extract and decode
    extracted = content[start:end]
    return extracted.decode('utf-8', errors='replace')


def find_context_start(content: bytes, start: int, num_lines: int) -> int:
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


def find_context_end(content: bytes, end: int, num_lines: int) -> int:
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
