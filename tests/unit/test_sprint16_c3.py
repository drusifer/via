"""Sprint 16 Cycle 3 / Sprint 27 Cycle 1 tests — coverage import and canned queries."""

import json
import subprocess
import sys

import coverage


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_coverage_import_contexts_adds_per_test_covered_by_relationships(tmp_path):
    src = tmp_path / "app.py"
    src.write_text(
        "def covered():\n"
        "    return 1\n\n"
        "def uncovered():\n"
        "    return 2\n"
    )

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_covered")
    cov_data.add_lines({str(src): {1, 2}})
    cov_data.write()

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    imported = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert imported.returncode == 0, imported.stderr

    uncovered = _run(
        tmp_path, "-mg", "*", "-tf", "--sans", "covered-by", "-mg", "*", "-oJ"
    )
    assert uncovered.returncode == 0, uncovered.stderr
    payload = json.loads(uncovered.stdout)
    names = [row["symbol_name"] for row in payload]
    assert "uncovered" in names
    assert "covered" not in names

    # Per-test attribution: querying covered-by the specific test symbol
    # returns only what that test covers.
    covered_by_test = _run(
        tmp_path, "-mg", "*", "-tf",
        "--via", "covered-by", "-mg", "*test_covered*", "-oJ",
    )
    assert covered_by_test.returncode == 0, covered_by_test.stderr
    payload = json.loads(covered_by_test.stdout)
    names = [row["symbol_name"] for row in payload]
    assert names == ["covered"]


def test_coverage_import_contexts_cleans_up_stale_data_on_reimport(tmp_path):
    src = tmp_path / "app.py"
    src.write_text(
        "def a():\n"
        "    return 1\n\n"
        "def b():\n"
        "    return 2\n"
    )

    data_file = tmp_path / ".coverage"

    def write_context(test_name, lines):
        cov_data = coverage.CoverageData(basename=str(data_file))
        cov_data.set_context(test_name)
        cov_data.add_lines({str(src): lines})
        cov_data.write()

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    write_context("tests/test_app.py::test_alpha", {1, 2})
    first = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert first.returncode == 0, first.stderr

    # Re-importing (e.g. after a suite re-run) must not accumulate duplicate
    # covered-by edges or leave stale per-test symbols behind.
    write_context("tests/test_app.py::test_bravo", {4})
    second = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert second.returncode == 0, second.stderr

    stale = _run(
        tmp_path, "-mg", "*test_alpha*", "-oJ",
    )
    assert stale.returncode == 0, stale.stderr
    assert json.loads(stale.stdout) == []


def test_coverage_import_contexts_warns_on_dramatic_test_count_drop(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("def a():\n    return 1\n")

    data_file = tmp_path / ".coverage"

    def write_contexts(test_names):
        cov_data = coverage.CoverageData(basename=str(data_file))
        for i, name in enumerate(test_names):
            cov_data.set_context(name)
            cov_data.add_lines({str(src): {1}})
        cov_data.write()

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    # First import: 10 tests tracked.
    write_contexts([f"tests/test_app.py::test_{i}" for i in range(10)])
    first = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert first.returncode == 0, first.stderr
    assert "Warning" not in first.stdout

    # Second import: only 1 test — a dramatic drop from 10 — should warn.
    write_contexts(["tests/test_app.py::test_0"])
    second = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert second.returncode == 0, second.stderr
    assert "Warning: this import covers 1 tests, but 10 were previously tracked" in second.stdout


def test_built_in_canned_query_expands(tmp_path):
    src = tmp_path / "calls.py"
    src.write_text(
        "def helper():\n"
        "    pass\n\n"
        "def caller():\n"
        "    helper()\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    result = _run(tmp_path, "--canned", "callers", "--args", "symbol=helper", "-oJ")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    names = [row["symbol_name"] for row in payload]
    assert "caller" in names


def test_custom_canned_query_loaded_from_via_dir(tmp_path):
    src = tmp_path / "demo.py"
    src.write_text("VALUE = 'x'\n")
    canned_dir = tmp_path / ".via" / "canned"
    canned_dir.mkdir(parents=True)
    (canned_dir / "globals.json").write_text(json.dumps({
        "argv": ["-mg", "*", "-tg", "-oJ"]
    }))

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    result = _run(tmp_path, "--canned", "globals")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert any(row["symbol_name"] == "VALUE" for row in payload)
