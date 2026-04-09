"""Sprint 16 Cycle 3 tests — coverage import and canned queries."""

import json
import subprocess
import sys


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_coverage_import_adds_covered_by_relationships(tmp_path):
    src = tmp_path / "app.py"
    src.write_text(
        "def covered():\n"
        "    return 1\n\n"
        "def uncovered():\n"
        "    return 2\n"
    )

    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package name=".">
      <classes>
        <class name="app.py" filename="app.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    imported = _run(tmp_path, "coverage", "import", str(coverage_xml))
    assert imported.returncode == 0, imported.stderr

    uncovered = _run(
        tmp_path, "-mg", "*", "-tf", "--sans", "covered-by", "-mg", "*", "-oJ"
    )
    assert uncovered.returncode == 0, uncovered.stderr
    payload = json.loads(uncovered.stdout)
    names = [row["symbol_name"] for row in payload]
    assert "uncovered" in names
    assert "covered" not in names


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
