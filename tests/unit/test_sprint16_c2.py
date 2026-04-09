"""Sprint 16 Cycle 2 tests — string constants as `-ts`."""

import json
import subprocess
import sys

import pytest

from via.core.types import MatchOp
from via.db.store import DatabaseStore
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


def test_javascript_parser_extracts_string_constants():
    parser = JavaScriptParser()
    result = parser.parse(
        "example.js",
        b"const ROUTE = '/api/query';\nfunction load(){ console.log('hello'); return 'done'; }\n",
    )
    if result.parse_error and "tree-sitter" in result.parse_error:
        pytest.skip(result.parse_error)

    values = [s.value for s in result.string_constants]
    assert "/api/query" in values
    assert "hello" in values
    assert "done" in values


def test_indexing_stores_string_constants_and_owner_references(tmp_path):
    src = tmp_path / "app.py"
    src.write_text(
        "MESSAGE = 'User not found'\n\n"
        "def greet():\n"
        "    print('hello')\n"
        "    return 'done'\n"
    )

    db_path = tmp_path / "test.db"
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()

    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(store, registry)
    svc.index(str(tmp_path))

    string_symbols = list(store.match(None, MatchOp.GLOB, "*", True, limit=0))
    string_symbols = [s for s in string_symbols if s.symbol_type == "string_constant"]
    assert any(s.symbol_name == "User not found" for s in string_symbols)
    assert any(s.symbol_name == "hello" for s in string_symbols)

    refs = list(store.query_relationships(
        relationship_type="references",
        subject_pattern="hello",
        subject_type="string_constant",
        object_pattern="greet",
        object_type="function",
        limit=10,
    ))
    assert refs, "expected string constant to reference its owning function"
    store.close()


def test_cli_type_string_query(tmp_path):
    src = tmp_path / "main.py"
    src.write_text(
        "ERROR_TEXT = 'User not found'\n"
        "def fail():\n"
        "    return 'User not found'\n"
    )
    index = subprocess.run(
        [sys.executable, "-m", "via", "index", str(tmp_path)],
        capture_output=True, text=True, timeout=60, cwd=str(tmp_path),
    )
    assert index.returncode == 0, index.stderr

    query = subprocess.run(
        [sys.executable, "-m", "via", "-mg", "User not found", "-ts", "-oJ"],
        capture_output=True, text=True, timeout=30, cwd=str(tmp_path),
    )
    assert query.returncode == 0, query.stderr
    payload = json.loads(query.stdout)
    assert payload
    assert any(row["symbol_type"] == "string_constant" for row in payload)
