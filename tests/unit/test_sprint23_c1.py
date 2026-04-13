"""Sprint 23 Cycle 1 tests for canned shortcut transparency."""
from __future__ import annotations

import json
import subprocess
import sys

from via.canned import expand_canned_query, load_canned_queries


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_sprint23_built_ins_present_without_deferred_shortcuts(tmp_path):
    queries = load_canned_queries(str(tmp_path))

    for name in [
        "callers",
        "methods-calling",
        "inheritors",
        "docs-headers",
        "symbol-body",
        "paged-scan",
    ]:
        assert name in queries

    assert "callees" not in queries
    assert "declared-in-file" not in queries


def test_callers_shortcut_matches_expanded_query(tmp_path):
    src = tmp_path / "calls.py"
    src.write_text(
        "def helper():\n"
        "    pass\n\n"
        "def caller():\n"
        "    helper()\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    shortcut = _run(tmp_path, "--canned", "callers", "--args", "symbol=helper", "-oJ")
    expanded = _run(tmp_path, "-mg", "*", "-tf", "--via", "calls", "-mg", "helper", "-tf", "-oJ")

    assert shortcut.returncode == 0, shortcut.stderr
    assert expanded.returncode == 0, expanded.stderr
    assert json.loads(shortcut.stdout) == json.loads(expanded.stdout)
    assert {row["symbol_name"] for row in json.loads(shortcut.stdout)} == {"caller"}


def test_methods_calling_and_inheritors_shortcuts_match_expanded_queries(tmp_path):
    src = tmp_path / "sample.py"
    src.write_text(
        "class Base:\n"
        "    pass\n\n"
        "class Child(Base):\n"
        "    def work(self):\n"
        "        helper()\n\n"
        "def helper():\n"
        "    pass\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    method_shortcut = _run(tmp_path, "--canned", "methods-calling", "--args", "symbol=helper", "-oJ")
    method_expanded = _run(tmp_path, "-mg", "*", "-tm", "--via", "calls", "-mg", "helper", "-oJ")
    class_shortcut = _run(tmp_path, "--canned", "inheritors", "--args", "symbol=Base", "-oJ")
    class_expanded = _run(tmp_path, "-mg", "*", "-tc", "--via", "inherits-from", "-mg", "Base", "-tc", "-oJ")

    assert method_shortcut.returncode == 0, method_shortcut.stderr
    assert method_expanded.returncode == 0, method_expanded.stderr
    assert class_shortcut.returncode == 0, class_shortcut.stderr
    assert class_expanded.returncode == 0, class_expanded.stderr

    assert json.loads(method_shortcut.stdout) == json.loads(method_expanded.stdout)
    assert {row["symbol_name"] for row in json.loads(method_shortcut.stdout)} == {"work"}
    assert json.loads(class_shortcut.stdout) == json.loads(class_expanded.stdout)
    assert {row["symbol_name"] for row in json.loads(class_shortcut.stdout)} == {"Child"}


def test_show_expanded_prints_copyable_command_without_executing(tmp_path):
    result = _run(
        tmp_path,
        "--canned", "callers",
        "--args", "symbol=helper",
        "--show-expanded",
        "-oJ",
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.strip() == "via -mg '*' -tf --via calls -mg helper -tf -oJ"


def test_show_expanded_reports_missing_required_arg(tmp_path):
    result = _run(tmp_path, "--canned", "callers", "--show-expanded")

    assert result.returncode != 0
    assert "missing required arg 'symbol'" in result.stderr


def test_docs_headers_and_paged_scan_expand_to_normal_argv(tmp_path):
    headers = expand_canned_query(str(tmp_path), "docs-headers", "pattern=*API*", [])
    paged = expand_canned_query(str(tmp_path), "paged-scan", "pattern=*,slice=0:10", ["-tf"])

    assert headers == ["-mg", "*API*", "-tH"]
    assert paged == ["-mg", "*", "--slice", "0:10", "-tf"]
