"""Built-in and user-defined canned queries for VIA."""

import json
from pathlib import Path


_BUILTINS = {
    "unused": ["-mg", "*", "-tf", "--sans", "calls", "-mg", "*", "-tf"],
    "potentially-unused": ["-mg", "*", "-tf", "--sans", "calls", "-mg", "*", "-tf"],
    "callers": ["-mg", "{symbol}", "-tf", "--via", "calls", "-mg", "*", "-tf"],
    "inheritors": ["-mg", "{symbol}", "-tc", "--via", "inherits-from", "-mg", "*", "-tc"],
    "dead-docs": ["-mg", "*.md", "-tF", "--sans", "declares", "-mg", "*", "-tH"],
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
