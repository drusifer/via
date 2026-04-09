"""Sprint 17 Cycle 2 tests — JS HTTP bridge primitives."""

import json
import subprocess
import sys

import pytest

from via.parsers.javascript_parser import JavaScriptParser


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_javascript_parser_extracts_http_calls():
    parser = JavaScriptParser()
    result = parser.parse(
        "client.js",
        b"function load(){ return fetch('/api/query'); }\n"
        b"const save = () => axios.post('/api/save');\n",
    )
    if result.parse_error and "tree-sitter" in result.parse_error:
        pytest.skip(result.parse_error)

    targets = [call.callee_name for call in result.http_calls]
    assert "/api/query" in targets
    assert "/api/save" in targets


def test_cli_http_calls_relationship_query(tmp_path):
    (tmp_path / "client.js").write_text(
        "function load(){ return fetch('/api/query'); }\n"
        "const noop = () => 'ok';\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    query = _run(
        tmp_path,
        "-mg", "/api/query", "-ts",
        "--via", "http-calls", "-mg", "*", "-tf", "--lang", "js",
        "-oJ",
    )
    assert query.returncode == 0, query.stderr
    payload = json.loads(query.stdout)
    names = [row["symbol_name"] for row in payload]
    assert "load" in names
    assert "noop" not in names
