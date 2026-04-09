"""
Common utility functions for VIA.

TLDR:
    Consolidates small helpers previously duplicated across modules.
    safe_print wraps print() to gracefully replace unencodable Unicode
    characters when the terminal uses a narrow encoding (ASCII, latin-1).
    get_match_op converts a single-character match-syntax suffix ('g' for
    GLOB, 'r' for REGEXP, 's' for SQL LIKE) into the corresponding MatchOp
    enum value used by the query layer.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import re
import sys
from typing import Any, Callable, Optional, TextIO, TypeVar

from .types import MatchOp

_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

F = TypeVar('F', bound=Callable[..., Any])


def safe_print(text: str, file: Optional[TextIO] = None) -> None:
    """Print text safely, handling Unicode encoding errors.

    Some terminals use latin-1 or ASCII encoding which can't handle
    Unicode characters like emojis. This handles such cases gracefully
    by replacing unencodable characters.

    Args:
        text: The text to print
        file: Output file (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
        safe_text = text.encode(encoding, errors='replace').decode(encoding)
        print(safe_text, file=file)


def parse_line_slice(s: str) -> tuple:
    """Parse a Python-style line slice string into (start, end).

    Both values are 1-based relative to the matched symbol/file start.
    None means "open end" (start=beginning, end=symbol end).

    Examples:
        '5:10' → (5, 10)   lines 5 through 10 inclusive
        '1:'   → (1, None)  from line 1 to end
        ':5'   → (None, 5)  from start through line 5
        '7'    → (7, 7)     single line 7

    Args:
        s: Slice string

    Returns:
        (start, end) tuple where each may be int or None

    Raises:
        ValueError: If the string cannot be parsed
    """
    if ':' not in s:
        n = int(s)
        return (n, n)
    left, right = s.split(':', 1)
    start = int(left) if left else None
    end = int(right) if right else None
    return (start, end)


def parse_result_slice(s: str) -> tuple:
    """Parse a 0-based result slice string into (start, end).

    Semantics: values are 0-based result indices (unlike parse_line_slice which is 1-based).
    None means open end (start=0, end=no limit).

    Examples:
        '0:20'  → (0, 20)    first 20 results (OFFSET 0, LIMIT 20)
        '20:40' → (20, 40)   results 20-39 (OFFSET 20, LIMIT 20)
        '20:'   → (20, None) from result 20 to end
        ':20'   → (None, 20) first 20 results

    Args:
        s: Slice string

    Returns:
        (start, end) tuple where each may be int or None

    Raises:
        ValueError: If the string cannot be parsed
    """
    return parse_line_slice(s)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.

    Args:
        text: Text that may contain ANSI color/style codes

    Returns:
        Text with all ANSI codes removed
    """
    return _ANSI_ESCAPE.sub('', text)


def get_match_op(match_syntax: str) -> MatchOp:
    """Convert match syntax suffix to MatchOp enum.

    Args:
        match_syntax: Single character suffix ('g', 'r', 's')
            - 'g': GLOB pattern (default)
            - 'r': REGEXP (regex)
            - 's': SQL LIKE pattern

    Returns:
        Corresponding MatchOp enum value
    """
    return {
        'r': MatchOp.REGEXP,
        's': MatchOp.LIKE,
    }.get(match_syntax, MatchOp.GLOB)
