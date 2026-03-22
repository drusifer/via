"""
Human-friendly duration string parser for temporal query operators.

TLDR:
    parse_duration converts human-friendly strings like '1h', '30m', '2d' to
    seconds as a float. Used by --newerthan and --olderthan CLI flags.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""
import re


_UNITS = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
}

_DURATION_RE = re.compile(r'^(\d+)([smhdw])$')


def parse_duration(value: str) -> float:
    """Parse a human-friendly duration string to seconds.

    Args:
        value: Duration string like '30s', '5m', '2h', '1d', '1w'

    Returns:
        Number of seconds as float

    Raises:
        ValueError: if format is not recognized
    """
    m = _DURATION_RE.match(value.strip())
    if not m:
        raise ValueError(
            f"Invalid duration '{value}'. Use format: 30s, 5m, 2h, 1d, 1w."
        )
    amount = int(m.group(1))
    unit = m.group(2)
    return float(amount * _UNITS[unit])
