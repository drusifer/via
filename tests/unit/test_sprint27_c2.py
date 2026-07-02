"""Sprint 27 Cycle 2 tests — test_runs metadata table (status/duration/last-run)."""

import json
import sqlite3
import subprocess
import sys

import coverage

from via.db.store import DatabaseStore


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def test_upsert_test_run_inserts_then_updates_same_row(tmp_path):
    db_path = tmp_path / "index.db"
    with DatabaseStore(str(db_path), str(tmp_path)) as store:
        store.initialize_schema()

        store.upsert_test_run("tests/test_x.py::test_a", "pass", 0.5, "2026-07-01T00:00:00")
        store.upsert_test_run("tests/test_x.py::test_a", "fail", 1.2, "2026-07-01T00:05:00")

        run = store.get_test_run("tests/test_x.py::test_a")
        assert run["status"] == "fail"
        assert run["duration_seconds"] == 1.2
        assert run["last_run_at"] == "2026-07-01T00:05:00"

        count = store.conn.execute(
            "SELECT COUNT(*) FROM test_runs WHERE test_id = ?",
            ("tests/test_x.py::test_a",),
        ).fetchone()[0]
        assert count == 1


def test_get_test_run_returns_none_when_absent(tmp_path):
    db_path = tmp_path / "index.db"
    with DatabaseStore(str(db_path), str(tmp_path)) as store:
        store.initialize_schema()
        assert store.get_test_run("never/ran.py::test_nothing") is None


def test_import_contexts_populates_test_runs_from_conftest_json(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("def a():\n    return 1\n")

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_a")
    cov_data.add_lines({str(src): {1, 2}})
    cov_data.write()

    via_dir = tmp_path / ".via"
    via_dir.mkdir(exist_ok=True)
    (via_dir / "test_runs.json").write_text(json.dumps({
        "tests/test_app.py::test_a": {
            "status": "pass",
            "duration_seconds": 0.03,
            "last_run_at": "2026-07-01T00:00:00",
        },
        "tests/test_app.py::test_b": {
            "status": "fail",
            "duration_seconds": 0.01,
            "last_run_at": "2026-07-01T00:00:00",
        },
    }))

    imported = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert imported.returncode == 0, imported.stderr
    assert "Imported test run metadata: 2 tests" in imported.stdout

    conn = sqlite3.connect(tmp_path / ".via" / "index.db")
    rows = dict(conn.execute("SELECT test_id, status FROM test_runs").fetchall())
    assert rows == {
        "tests/test_app.py::test_a": "pass",
        "tests/test_app.py::test_b": "fail",
    }


def test_import_contexts_without_test_runs_json_does_not_error(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("def a():\n    return 1\n")

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_a")
    cov_data.add_lines({str(src): {1, 2}})
    cov_data.write()

    imported = _run(tmp_path, "coverage", "import-contexts", str(data_file))
    assert imported.returncode == 0, imported.stderr
    assert "Imported test run metadata: 0 tests" in imported.stdout
