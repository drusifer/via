"""Sprint 15 Cycle 3 tests — S15-2 MCP output wrapper + S15-4 markdown declares.

TLDR:
    S15-2: MCP via_query() now returns {"output_type": ..., "result": ...} instead of
           a bare list. Non-JSON output flags (-oD, -oR, etc.) capture rendered text.
           Empty diagram falls back to JSON with a 'note' field.
    S15-4: markdown files gain 'declares' relationships for each header symbol, enabling
           --via declares queries on .md files the same way as .py files.
    strip_ansi: new utility in core/utils.py strips ANSI escape codes from text.

Author: Neo
Sprint: 15, Cycle 3
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile

import pytest

from via.core.utils import strip_ansi
from via.db.store import DatabaseStore
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParser
from via.renderers.json_renderer import JsonRenderer
from via.services.indexing import IndexingService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def md_store(tmp_path_factory):
    """DatabaseStore with an indexed markdown file containing 3 headers."""
    d = tmp_path_factory.mktemp("sprint15c3_md")
    md_file = d / "guide.md"
    md_file.write_text(
        "# Introduction\n\nSome text.\n\n"
        "## Getting Started\n\nMore text.\n\n"
        "### Installation\n\nInstall instructions.\n"
    )
    db_path = d / "test.db"
    store = DatabaseStore(str(db_path), str(d))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(MarkdownParser())
    svc = IndexingService(store, registry)
    svc.index(str(d))
    yield store
    store.close()


@pytest.fixture(scope="module")
def py_store(tmp_path_factory):
    """DatabaseStore with an indexed Python file containing 2 classes."""
    d = tmp_path_factory.mktemp("sprint15c3_py")
    py_file = d / "mymodule.py"
    py_file.write_text(
        "class Alpha:\n    def run(self): pass\n\n"
        "class Beta:\n    def go(self): pass\n"
    )
    db_path = d / "test.db"
    store = DatabaseStore(str(db_path), str(d))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(store, registry)
    svc.index(str(d))
    yield store
    store.close()


def _q(proj_dir, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=30, cwd=str(proj_dir),
    )


# ---------------------------------------------------------------------------
# strip_ansi unit tests
# ---------------------------------------------------------------------------

class TestStripAnsi:
    """strip_ansi() removes ANSI escape codes from strings."""

    def test_strips_color_code(self):
        assert strip_ansi("\x1b[32mgreen\x1b[0m") == "green"

    def test_strips_bold(self):
        assert strip_ansi("\x1b[1mBold\x1b[0m") == "Bold"

    def test_no_codes_unchanged(self):
        assert strip_ansi("plain text") == "plain text"

    def test_empty_string(self):
        assert strip_ansi("") == ""

    def test_mixed_content(self):
        result = strip_ansi("before \x1b[31mred\x1b[0m after")
        assert result == "before red after"


# ---------------------------------------------------------------------------
# S15-4: markdown declares — unit tests
# ---------------------------------------------------------------------------

class TestMarkdownDeclares:
    """markdown _store_declares_relationships() creates 'declares' rows for headers."""

    def test_three_headers_create_three_declares_rows(self, md_store):
        """3 headers in guide.md → 3 declares rows linking each header to the file."""
        results = list(md_store.query_relationships(
            relationship_type='declares',
            subject_pattern='*',
            object_pattern='guide.md',
            subject_type='header',
            object_type='filepath',
            invert=False,
            limit=20,
            case_sensitive=False,
        ))
        assert len(results) == 3, (
            f"Expected 3 declares rows for 3 headers, got {len(results)}: "
            f"{[r.symbol_name for r in results]}"
        )

    def test_header_names_are_correct(self, md_store):
        """The declared header names match the markdown headings."""
        results = list(md_store.query_relationships(
            relationship_type='declares',
            subject_pattern='*',
            object_pattern='guide.md',
            subject_type='header',
            object_type='filepath',
            invert=False,
            limit=20,
            case_sensitive=False,
        ))
        names = {r.symbol_name for r in results}
        assert 'Introduction' in names
        assert 'Getting Started' in names
        assert 'Installation' in names

    def test_python_declares_unchanged(self, py_store):
        """Existing Python declares still work after the header loop addition."""
        results = list(py_store.query_relationships(
            relationship_type='declares',
            subject_pattern='*',
            object_pattern='mymodule.py',
            subject_type='class',
            object_type='filepath',
            invert=False,
            limit=20,
            case_sensitive=False,
        ))
        assert len(results) == 2, (
            f"Expected 2 class declares rows, got {len(results)}: "
            f"{[r.symbol_name for r in results]}"
        )
        names = {r.symbol_name for r in results}
        assert 'Alpha' in names
        assert 'Beta' in names


# ---------------------------------------------------------------------------
# S15-4: markdown declares — CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def md_proj(tmp_path_factory):
    """CLI project with a markdown file for --via declares tests."""
    d = tmp_path_factory.mktemp("sprint15c3_cli")
    (d / "README.md").write_text(
        "# Overview\n\nIntro.\n\n"
        "## Installation\n\nHow to install.\n\n"
        "## Usage\n\nHow to use.\n"
    )
    (d / "empty.md").write_text("No headers here.\n")
    r = subprocess.run(
        [sys.executable, "-m", "via", "index", str(d)],
        capture_output=True, text=True, timeout=60, cwd=str(d),
    )
    assert r.returncode == 0, f"Index failed:\n{r.stderr}"
    return d


class TestMarkdownDeclaresIntegration:
    """CLI integration: --via declared-in on markdown files returns headers."""

    def test_via_declares_returns_headers(self, md_proj):
        r = _q(md_proj, "-mg", "*", "-tH", "--via", "declared-in", "-mg", "README.md", "-tF", "-Q")
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert len(lines) == 3, f"Expected 3 headers, got {len(lines)}: {lines}"
        output = r.stdout
        assert "Overview" in output
        assert "Installation" in output
        assert "Usage" in output

    def test_sans_declares_returns_empty_markdown(self, md_proj):
        r = _q(md_proj, "-mg", "*.md", "-tF", "--sans", "declares", "-mg", "*", "-tH")
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        # Only empty.md has no headers
        assert len(lines) == 1, f"Expected 1 headerless file, got {len(lines)}: {lines}"
        assert "empty.md" in lines[0]

    def test_via_declares_glob_filter_on_headers(self, md_proj):
        r = _q(md_proj, "-mg", "Install*", "-tH", "--via", "declared-in",
               "-mg", "README.md", "-tF", "-Q")
        assert r.returncode == 0, f"CLI failed:\n{r.stderr}"
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert len(lines) == 1
        assert "Installation" in lines[0]


# ---------------------------------------------------------------------------
# S15-2: MCP output type wrapper — unit tests via executor simulation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mcp_store(tmp_path_factory):
    """DatabaseStore with indexed Python file for MCP output tests."""
    d = tmp_path_factory.mktemp("sprint15c3_mcp")
    py_file = d / "calc.py"
    py_file.write_text(
        "class Calculator:\n"
        "    def add(self, a, b): return a + b\n"
        "    def sub(self, a, b): return a - b\n"
        "\n"
        "class Logger:\n"
        "    pass\n"
    )
    db_path = d / "test.db"
    store = DatabaseStore(str(db_path), str(d))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(PythonParser())
    svc = IndexingService(store, registry)
    svc.index(str(d))
    yield store
    store.close()


def _via_query_json(store, args):
    """Simulate the MCP via_query JSON path."""
    _OUTPUT_FLAGS = {'-oL', '-oT', '-oD', '-oU', '-oR', '-oF', '-oJ',
                     '--output-list', '--output-table', '--output-diagram',
                     '--output-usage', '--output-raw', '--output-formatted', '--output-json'}
    clean_args = [a for a in args if a not in _OUTPUT_FLAGS]
    stages = PipelineParser().parse(clean_args)
    executor = PipelineExecutor(store)
    results = list(executor.execute(stages) or [])
    dicts = [JsonRenderer._to_dict(r) for r in results]
    total = results[0].total_matches if results else 0
    return {"output_type": "json", "result": dicts, "total": total, "shown": len(dicts)}


def _via_query_render(store, args, output_type):
    """Simulate the MCP via_query non-JSON path."""
    stages = PipelineParser().parse(args)
    executor = PipelineExecutor(store)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        executor.execute(stages)
    rendered = strip_ansi(buf.getvalue()).rstrip('\n')
    # Fall back to JSON when diagram has no symbols (not a real classDiagram)
    if output_type == 'diagram' and (
        not rendered.strip() or 'classDiagram' not in rendered
    ):
        return {
            "output_type": "json", "result": [], "total": 0, "shown": 0,
            "note": "No diagram content produced; falling back to JSON.",
        }
    return {"output_type": output_type, "result": rendered, "total": 0, "shown": 0}


class TestMCPOutputType:
    """MCP via_query returns output_type field; non-JSON paths capture rendered text."""

    def test_json_default_has_output_type(self, mcp_store):
        r = _via_query_json(mcp_store, ["-mg", "*", "-tc"])
        assert r["output_type"] == "json"
        assert isinstance(r["result"], list)
        assert r["total"] >= 2
        assert r["shown"] == len(r["result"])

    def test_json_result_is_list_backward_compat(self, mcp_store):
        r = _via_query_json(mcp_store, ["-mg", "*", "-tc"])
        assert isinstance(r["result"], list), "result must remain a list for JSON output"
        assert all(isinstance(x, dict) for x in r["result"])

    def test_raw_output_type(self, mcp_store):
        r = _via_query_render(mcp_store, ["-mg", "Calculator", "-tc", "-oR"], "raw")
        assert r["output_type"] == "raw"
        assert isinstance(r["result"], str)

    def test_table_output_type(self, mcp_store):
        r = _via_query_render(mcp_store, ["-mg", "*", "-tc", "-oT"], "table")
        assert r["output_type"] == "table"
        assert isinstance(r["result"], str)

    def test_list_output_type(self, mcp_store):
        r = _via_query_render(mcp_store, ["-mg", "*", "-tc", "-oL"], "list")
        assert r["output_type"] == "list"
        assert isinstance(r["result"], str)

    def test_empty_diagram_falls_back_to_json(self, mcp_store):
        """When -oD renders empty output (no matching symbols), fall back to JSON."""
        # Pattern that matches nothing → empty stdout → fallback
        r = _via_query_render(mcp_store, ["-mg", "NonExistentClass999", "-tc", "-oD"], "diagram")
        assert r["output_type"] == "json"
        assert r["result"] == []
        assert "note" in r
        assert "falling back" in r["note"].lower() or "json" in r["note"].lower()

    def test_rendered_result_is_string_not_list(self, mcp_store):
        r = _via_query_render(mcp_store, ["-mg", "*", "-tc", "-oT"], "table")
        assert isinstance(r["result"], str), "non-JSON result must be a string"

    def test_total_shown_present_in_json_response(self, mcp_store):
        r = _via_query_json(mcp_store, ["-mg", "*", "-tc"])
        assert "total" in r
        assert "shown" in r
