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

import sys
from typing import Any, Callable, Optional, TextIO, TypeVar

from .types import MatchOp

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
