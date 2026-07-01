"""Loading and expanding of predefined 'canned' search queries.

TLDR:
    Handles built-in and user-defined canned queries from JSON configuration files.
    Key functions: load_canned_queries() (reads queries from disk),
    expand_canned_query() (expands a canned name into CLI arguments).
    Role: Consumed by CLI routing to support canned search shortcuts.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
from pathlib import Path


_BUILTINS = {
    "unused": ["-mg", "*", "-tf", "--sans", "called-by", "-mg", "*", "-tf"],
    "potentially-unused": ["-mg", "*", "-tf", "--sans", "called-by", "-mg", "*", "-tf"],
    "callers": ["-mg", "*", "-tf", "--via", "calls", "-mg", "{symbol}", "-tf"],
    "methods-calling": ["-mg", "*", "-tm", "--via", "calls", "-mg", "{symbol}"],
    "inheritors": ["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "{symbol}", "-tc"],
    "docs-headers": ["-mg", "{pattern}", "-tH"],
    "symbol-body": ["-mg", "{symbol}", "-tf", "-tm", "-tc", "-oR"],
    "paged-scan": ["-mg", "{pattern}", "--slice", "{slice}"],
    "dead-docs": ["-mg", "*.md", "-tF", "--sans", "declared-in", "-mg", "*", "-tH"],
}


def _parse_args_map(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    result = {}
    for item in raw.split(","):
        if not item.strip():
            continue
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"Invalid --args item '{item}'. Use key=value.")
        result[key.strip()] = value.strip()
    return result


def load_canned_queries(project_root: str) -> dict[str, list[str]]:
    """Load built-in and user-defined canned queries."""
    queries = dict(_BUILTINS)
    canned_dir = Path(project_root) / ".via" / "canned"
    if not canned_dir.exists():
        return queries

    for path in canned_dir.glob("*.json"):
        payload = json.loads(path.read_text())
        if isinstance(payload, dict) and "argv" in payload:
            name = payload.get("name", path.stem)
            queries[name] = payload["argv"]
    return queries


def expand_canned_query(project_root: str, name: str, raw_args: str | None, extras: list[str]) -> list[str]:
    """Expand a canned query into a normal via argv list."""
    queries = load_canned_queries(project_root)
    if name not in queries:
        raise ValueError(f"Unknown canned query '{name}'.")

    arg_map = _parse_args_map(raw_args)
    expanded = []
    for token in queries[name]:
        try:
            expanded.append(token.format(**arg_map))
        except KeyError as exc:
            raise ValueError(
                f"Canned query '{name}' is missing required arg '{exc.args[0]}'."
            ) from exc

    return expanded + extras
