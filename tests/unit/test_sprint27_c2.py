"""Sprint 27 Cycle 2 tests — test_runs metadata table (status/duration/last-run)."""

import json
import sqlite3
import subprocess
import sys

import coverage

from via.commands.coverage import import_contexts
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


def test_clear_test_runs_removes_all_rows(tmp_path):
    db_path = tmp_path / "index.db"
    with DatabaseStore(str(db_path), str(tmp_path)) as store:
        store.initialize_schema()
        store.upsert_test_run("tests/test_x.py::test_a", "pass", 0.2, "2026-07-01T00:00:00")
        store.upsert_test_run("tests/test_x.py::test_b", "pass", 0.3, "2026-07-01T00:00:00")

        store.clear_test_runs()

        assert store.get_test_run("tests/test_x.py::test_a") is None
        assert store.get_test_run("tests/test_x.py::test_b") is None


def test_import_contexts_clears_stale_test_runs_on_reimport(tmp_path):
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
    runs_file = via_dir / "test_runs.json"
    runs_file.write_text(json.dumps({
        "tests/test_app.py::test_a": {
            "status": "pass",
            "duration_seconds": 0.03,
            "last_run_at": "2026-07-01T00:00:00",
        },
        "tests/test_deleted.py::test_old": {
            "status": "pass",
            "duration_seconds": 0.5,
            "last_run_at": "2026-07-01T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    # Simulate deleting tests/test_deleted.py and re-importing a fresh run
    runs_file.write_text(json.dumps({
        "tests/test_app.py::test_a": {
            "status": "pass",
            "duration_seconds": 0.02,
            "last_run_at": "2026-07-02T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(via_dir / "index.db"), str(tmp_path)) as store:
        assert store.get_test_run("tests/test_deleted.py::test_old") is None
        eff_ids = [r["test_id"] for r in store.get_test_efficiency_data()]
        assert eff_ids == ["tests/test_app.py::test_a"]


def test_import_contexts_ignores_def_header_only_lines(tmp_path):
    """Import-time `def`/`class` header lines must not mark uncalled symbols covered."""
    src = tmp_path / "app.py"
    src.write_text(
        "class Svc:\n"
        "    def called(self):\n"
        '        """Docstring."""\n'
        "        return 1\n\n"
        "    def uncalled(self):\n"
        "        return 2\n"
    )

    index = _run(tmp_path, "index", str(tmp_path))
    assert index.returncode == 0, index.stderr

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_only_called")
    # Simulate subprocess import hitting lines 1, 2, 6 (`class`/`def` headers)
    # and actually executing only `called()`'s body on line 4.
    cov_data.add_lines({str(src): {1, 2, 4, 6}})
    cov_data.write()

    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(tmp_path / ".via" / "index.db"), str(tmp_path)) as store:
        counts = {
            (r["symbol_type"], r["symbol_name"]): r["covering_test_count"]
            for r in store.get_symbol_coverage_counts()
        }
        assert counts[("method", "called")] == 1
        assert counts[("class", "Svc")] == 1
        assert counts[("method", "uncalled")] == 0
