"""Unit tests for `via coverage report` (standalone HTML test quality report)."""

import json
import subprocess
import sys

import coverage

from via.commands.coverage import import_contexts
from via.commands.coverage_report import (
    build_test_quality_data,
    generate_coverage_report,
    render_test_quality_html,
)
from via.db.store import DatabaseStore


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


def _seed_project(tmp_path):
    """Create a small indexed project with two functions and three tests."""
    src = tmp_path / "app.py"
    src.write_text(
        "def alpha(flag):\n"
        "    if flag:\n"
        "        return 1\n"
        "    return 2\n\n"
        "def beta():\n"
        "    return 3\n"
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        "import pytest\n"
        "from app import alpha, beta\n\n"
        "def test_fast_alpha():\n"
        "    assert alpha(True) == 1\n"
        "    assert alpha(False) == 2\n\n"
        "def test_slow_duplicate_alpha():\n"
        "    assert alpha(True) == 1\n\n"
        "def test_slow_zero():\n"
        "    assert True\n"
    )
    assert _run(tmp_path, "index", str(tmp_path)).returncode == 0
    return src


def test_build_test_quality_data_flags_slow_zero_and_overlap_and_counts_asserts(tmp_path):
    src = _seed_project(tmp_path)

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_fast_alpha")
    cov_data.add_arcs({str(src): {(1, 2), (2, 3), (2, 4)}})
    cov_data.set_context("tests/test_app.py::test_slow_duplicate_alpha")
    cov_data.add_arcs({str(src): {(1, 2), (2, 3)}})
    cov_data.write()

    via_dir = tmp_path / ".via"
    (via_dir / "test_runs.json").write_text(json.dumps({
        "tests/test_app.py::test_fast_alpha": {
            "status": "pass", "duration_seconds": 0.01, "last_run_at": "2026-11-25T00:00:00",
        },
        "tests/test_app.py::test_slow_duplicate_alpha": {
            "status": "pass", "duration_seconds": 1.2, "last_run_at": "2026-11-25T00:00:00",
        },
        "tests/test_app.py::test_slow_zero": {
            "status": "pass", "duration_seconds": 0.8, "last_run_at": "2026-11-25T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(via_dir / "index.db"), str(tmp_path)) as store:
        payload = build_test_quality_data(store, branch_data_file=str(data_file), slow_threshold=0.5)

    by_id = {t["test_id"]: t for t in payload["tests"]}
    assert payload["overlap_mode"] == "branches"
    assert by_id["tests/test_app.py::test_fast_alpha"]["flag"] == "ok"
    assert by_id["tests/test_app.py::test_fast_alpha"]["asserts"] == 2
    assert by_id["tests/test_app.py::test_slow_zero"]["flag"] == "slow-zero"
    assert by_id["tests/test_app.py::test_slow_duplicate_alpha"]["flag"] == "slow-low"
    assert by_id["tests/test_app.py::test_slow_duplicate_alpha"]["subsumed"] is True
    assert by_id["tests/test_app.py::test_slow_duplicate_alpha"]["peer"] == "tests/test_app.py::test_fast_alpha"
    assert by_id["tests/test_app.py::test_slow_duplicate_alpha"]["asserts"] == 1
    assert payload["kpis"]["slow_zero_count"] == 1


def test_build_test_quality_data_uses_branch_arcs_when_available(tmp_path):
    src = _seed_project(tmp_path)

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    # Branch 1 (flag=True): arc (2, 3)
    cov_data.set_context("tests/test_app.py::test_fast_alpha")
    cov_data.add_arcs({str(src): {(1, 2), (2, 3)}})
    # Branch 2 (flag=False): arc (2, 4) — same symbol `alpha`, DIFFERENT branch!
    cov_data.set_context("tests/test_app.py::test_slow_duplicate_alpha")
    cov_data.add_arcs({str(src): {(1, 2), (2, 4)}})
    cov_data.write()

    via_dir = tmp_path / ".via"
    (via_dir / "test_runs.json").write_text(json.dumps({
        "tests/test_app.py::test_fast_alpha": {
            "status": "pass", "duration_seconds": 0.01, "last_run_at": "2026-11-25T00:00:00",
        },
        "tests/test_app.py::test_slow_duplicate_alpha": {
            "status": "pass", "duration_seconds": 1.0, "last_run_at": "2026-11-25T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(via_dir / "index.db"), str(tmp_path)) as store:
        payload = build_test_quality_data(
            store, branch_data_file=str(data_file), slow_threshold=0.5
        )

    assert payload["overlap_mode"] == "branches"
    slow = next(t for t in payload["tests"] if t["test_id"].endswith("test_slow_duplicate_alpha"))
    # Different branch arc means NOT subsumed (only 1 of 3 union arcs shared -> 33.3%)
    assert slow["subsumed"] is False
    assert slow["overlap_pct"] < 50.0


def test_coverage_report_rejects_line_only_and_missing_coverage_file(tmp_path, capsys):
    src = _seed_project(tmp_path)
    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_fast_alpha")
    cov_data.add_lines({str(src): {2, 3}})
    cov_data.write()

    out_file = tmp_path / "out" / "quality.html"
    rc = generate_coverage_report(str(tmp_path), output_path=str(out_file), coverage_file=str(data_file))
    assert rc == 1
    assert not out_file.exists()
    err = capsys.readouterr().err
    assert "--cov-branch" in err

    rc_missing = generate_coverage_report(
        str(tmp_path), output_path=str(out_file), coverage_file=str(tmp_path / "nope.coverage")
    )
    assert rc_missing == 1
    assert "--cov-branch" in capsys.readouterr().err


def test_render_html_escapes_script_closing_tags():
    payload = {
        "generated_at": "2026-11-25 00:00 UTC",
        "overlap_mode": "symbols",
        "kpis": {
            "total_tests": 1, "total_dur": 1.0, "slow_threshold": 0.5,
            "slow_count": 1, "slow_dur": 1.0, "slow_pct_time": 100.0,
            "slow_zero_count": 1, "slow_zero_dur": 1.0,
            "slow_low_count": 0, "slow_low_dur": 0.0,
            "slow_overlap_count": 0, "slow_overlap_dur": 0.0,
            "slow_0uniq_count": 0, "slow_0uniq_dur": 0.0,
            "mocks_only_count": 0,
        },
        "tests": [{
            "test_id": "tests/t.py::test_</script><img onerror=1>",
            "file": "tests/t.py", "status": "pass", "dur": 1.0, "cov": 0,
            "imp": None, "uniq": 0, "sps": 0.0, "asserts": 1,
            "mocks": 0, "mocks_only": False, "overlap_pct": 0.0,
            "subsumed": False, "peer": None, "flag": "slow-zero",
        }],
        "files": [],
    }
    html = render_test_quality_html(payload)
    assert "</script><img" not in html
    assert "<\\/script><img" in html


def test_cli_coverage_report_writes_standalone_html(tmp_path):
    src = _seed_project(tmp_path)
    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    cov_data.set_context("tests/test_app.py::test_fast_alpha")
    cov_data.add_arcs({str(src): {(1, 2), (2, 3)}})
    cov_data.write()

    (tmp_path / ".via" / "test_runs.json").write_text(json.dumps({
        "tests/test_app.py::test_fast_alpha": {
            "status": "pass", "duration_seconds": 0.01, "last_run_at": "2026-11-25T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    out_file = tmp_path / "out" / "quality.html"
    rc = generate_coverage_report(str(tmp_path), output_path=str(out_file), coverage_file=str(data_file))
    assert rc == 0
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "VIA Test Quality Report" in content
    assert "test_fast_alpha" in content
    assert "Agent Instructions" in content
    assert "Prevent shared-resource flakiness" in content
    assert "Coverage Safety Net" in content

    # Also exercise CLI subcommand dispatch via `via coverage report`
    cli_out = tmp_path / "out" / "cli_quality.html"
    res = _run(tmp_path, "coverage", "report", "-o", str(cli_out))
    assert res.returncode == 0, res.stderr
    assert cli_out.is_file()


def test_coverage_safety_net_detects_newly_uncovered_regression_and_is_idempotent(tmp_path):
    src = _seed_project(tmp_path)
    data_file = tmp_path / ".coverage"

    # Run 1: both `alpha` (lines 2-4) and `beta` (line 7) are covered
    cov1 = coverage.CoverageData(basename=str(data_file))
    cov1.set_context("tests/test_app.py::test_fast_alpha")
    cov1.add_arcs({str(src): {(1, 2), (2, 3), (2, 4), (6, 7)}})
    cov1.write()
    (tmp_path / ".via" / "test_runs.json").write_text(json.dumps({
        "tests/test_app.py::test_fast_alpha": {
            "status": "pass", "duration_seconds": 0.01, "last_run_at": "2026-11-25T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(tmp_path / ".via" / "index.db"), str(tmp_path)) as store:
        run1 = build_test_quality_data(store, branch_data_file=str(data_file))
    assert run1["coverage"]["has_previous"] is False
    assert run1["coverage"]["newly_uncovered"] == []
    assert run1["coverage"]["covered_symbols"] == 2

    # Run 2: `beta` loses coverage
    data_file.unlink()
    cov2 = coverage.CoverageData(basename=str(data_file))
    cov2.set_context("tests/test_app.py::test_fast_alpha")
    cov2.add_arcs({str(src): {(1, 2), (2, 3), (2, 4)}})
    cov2.write()
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(tmp_path / ".via" / "index.db"), str(tmp_path)) as store:
        run2 = build_test_quality_data(store, branch_data_file=str(data_file))
        # Re-running on the same .coverage must stay idempotent and preserve the regression diff
        run2_repeat = build_test_quality_data(store, branch_data_file=str(data_file))

    assert run2["coverage"]["has_previous"] is True
    assert any(sym.endswith(":beta") for sym in run2["coverage"]["newly_uncovered"])
    assert run2_repeat["coverage"]["newly_uncovered"] == run2["coverage"]["newly_uncovered"]
    assert any(u["symbol"].endswith(":beta") for u in run2["coverage"]["uncovered_top"])
    cmp = run2["coverage"]["comparison"]
    assert cmp is not None
    assert len(cmp["prev_scatter"]) == 1
    assert cmp["prev_scatter"][0][0] == "tests/test_app.py::test_fast_alpha"
    html = render_test_quality_html(run2)
    assert "scatter-mode-toggle" in html
    assert "before-after-card" in html
    assert "kpi-delta" in html
    assert "symbol-lookup-card" in html
    syms_by_key = {entry[0]: entry[2] for entry in run2["symbols"]}
    alpha_key = next(k for k in syms_by_key if k.endswith(":alpha"))
    beta_key = next(k for k in syms_by_key if k.endswith(":beta"))
    assert len(syms_by_key[alpha_key]) == 1
    assert run2["tests"][syms_by_key[alpha_key][0]]["test_id"] == "tests/test_app.py::test_fast_alpha"
    assert syms_by_key[beta_key] == []


def test_ast_assertion_smell_detection_catches_false_greens_without_flagging_helpers(tmp_path):
    from via.commands.coverage_report import _analyze_test_file_ast

    tf = tmp_path / "test_smells.py"
    tf.write_text(
        "import pytest\n\n"
        "def _check_positive(val):\n"
        "    assert val > 0\n\n"
        "@pytest.fixture\n"
        "def test_fixture_named_like_test():\n"
        "    return 42\n\n"
        "def test_clean_with_helper():\n"
        "    _check_positive(1)\n\n"
        "def test_clean_literal_loop():\n"
        "    for v in (1, 2, 3):\n"
        "        assert v > 0\n\n"
        "def test_tautology():\n"
        "    assert True\n\n"
        "def test_broad_raises():\n"
        "    with pytest.raises(Exception):\n"
        "        raise ValueError('boom')\n\n"
        "def test_conditional_only(items):\n"
        "    for x in items:\n"
        "        assert x > 0\n\n"
        "def test_swallowed_assert():\n"
        "    try:\n"
        "        assert 1 == 2\n"
        "    except Exception:\n"
        "        pass\n\n"
        "def test_no_asserts():\n"
        "    x = 1 + 1\n\n"
        "def test_mock_only_asserts(m):\n"
        "    m.assert_called_once_with(1)\n\n"
        "def test_mock_plus_value_assert(m):\n"
        "    m.assert_called_once()\n"
        "    assert m.return_value == 1\n"
    )
    info = _analyze_test_file_ast(str(tf))
    assert info[(None, "test_fixture_named_like_test")][1] == []
    assert info[(None, "test_clean_with_helper")][1] == []
    assert info[(None, "test_clean_literal_loop")][1] == []
    assert info[(None, "test_mock_plus_value_assert")][1] == []
    assert "tautology" in info[(None, "test_tautology")][1]
    assert "broad-raises" in info[(None, "test_broad_raises")][1]
    assert "conditional-only" in info[(None, "test_conditional_only")][1]
    assert "swallowed-assert" in info[(None, "test_swallowed_assert")][1]
    assert "no-asserts" in info[(None, "test_no_asserts")][1]
    assert "mock-only-asserts" in info[(None, "test_mock_only_asserts")][1]


def test_shared_fixture_attribution_suppresses_false_slow_zero(tmp_path):
    src = _seed_project(tmp_path)
    (tmp_path / "tests" / "test_shared.py").write_text(
        "import pytest\n"
        "from app import alpha\n\n"
        "@pytest.fixture(scope='module')\n"
        "def live_daemon():\n"
        "    return alpha(True)\n\n"
        "@pytest.fixture(scope='class')\n"
        "def step_result(live_daemon):\n"
        "    return live_daemon\n\n"
        "class TestShared:\n"
        "    def test_first(self, live_daemon):\n"
        "        assert live_daemon == 1\n\n"
        "    def test_second(self, step_result):\n"
        "        assert step_result == 1\n"
    )
    assert _run(tmp_path, "index", str(tmp_path)).returncode == 0

    data_file = tmp_path / ".coverage"
    cov_data = coverage.CoverageData(basename=str(data_file))
    # Only test_first gets coverage attributed (simulating a shared module daemon)
    cov_data.set_context("tests/test_shared.py::TestShared::test_first")
    cov_data.add_arcs({str(src): {(1, 2), (2, 3)}})
    cov_data.write()

    (tmp_path / ".via" / "test_runs.json").write_text(json.dumps({
        "tests/test_shared.py::TestShared::test_first": {
            "status": "pass", "duration_seconds": 0.2, "last_run_at": "2026-11-25T00:00:00",
        },
        "tests/test_shared.py::TestShared::test_second": {
            "status": "pass", "duration_seconds": 0.8, "last_run_at": "2026-11-25T00:00:00",
        },
    }))
    assert import_contexts(str(tmp_path), str(data_file)) == 0

    with DatabaseStore(str(tmp_path / ".via" / "index.db"), str(tmp_path)) as store:
        payload = build_test_quality_data(store, branch_data_file=str(data_file), slow_threshold=0.5)

    by_id = {t["test_id"]: t for t in payload["tests"]}
    second = by_id["tests/test_shared.py::TestShared::test_second"]
    assert second["flag"] == "ok"
    assert second["shared_fixture"] is not None
    assert "live_daemon" in second["shared_fixture"]
    assert payload["kpis"]["slow_zero_count"] == 0
    file_row = next(f for f in payload["files"] if f["file"] == "tests/test_shared.py")
    assert file_row["zero_cov"] == 0
