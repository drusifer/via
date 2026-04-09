"""Sprint 17 Cycle 1 tests — link symbols."""

import json
import subprocess
import sys

from via.parsers.markdown_parser import MarkdownParser


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_markdown_parser_extracts_structured_links():
    parser = MarkdownParser()
    result = parser.parse(
        "README.md",
        b"# Guide\n\nSee [API](/api/query) and [Docs](https://example.com/docs).\n",
    )

    targets = [link.target for link in result.links]
    assert "/api/query" in targets
    assert "https://example.com/docs" in targets


def test_cli_type_link_query(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Intro\n\nUse the [Query API](/api/query) endpoint.\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    query = _run(tmp_path, "-mg", "/api/query", "-tl", "-oJ")
    assert query.returncode == 0, query.stderr
    payload = json.loads(query.stdout)
    assert payload
    assert any(row["symbol_type"] == "link" and row["symbol_name"] == "/api/query" for row in payload)
