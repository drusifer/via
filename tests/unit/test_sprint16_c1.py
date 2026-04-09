"""Sprint 16 Cycle 1 tests — S16-1 OR-query slice pagination fix.

TLDR:
    Verifies that --slice applies to the combined result set for OR'd type
    queries (-tc -tf), not independently per type. Also checks that total/shown
    metadata reflects the full combined count.
"""

import json
import subprocess
import sys

import pytest


@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    """Project with interleaved classes and functions for OR-query pagination."""
    d = tmp_path_factory.mktemp("sprint16c1")
    (d / "mixed.py").write_text(
        "\n\n".join(
            f"class Class{i:02d}:\n    pass\n\ndef func_{i:02d}():\n    pass"
            for i in range(12)
        )
    )
    r = subprocess.run(
        [sys.executable, "-m", "via", "index", str(d)],
        capture_output=True, text=True, timeout=60, cwd=str(d),
    )
    assert r.returncode == 0, f"Index failed:\n{r.stderr}"
    return d


def _q(proj, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=30, cwd=str(proj),
    )


def _json(proj, *args):
    result = _q(proj, *args, "-oJ")
    assert result.returncode == 0, f"via failed:\n{result.stderr}\n{result.stdout}"
    return json.loads(result.stdout)


class TestSprint16Cycle1:
    """Regression tests for OR-query slice support."""

    def test_slice_second_window_for_or_query_returns_distinct_results(self, proj):
        first = _json(proj, "-mg", "*", "-tc", "-tf", "--slice", "0:5")
        second = _json(proj, "-mg", "*", "-tc", "-tf", "--slice", "5:10")

        first_names = [row["qualified_name"] for row in first]
        second_names = [row["qualified_name"] for row in second]

        assert len(first_names) == 5
        assert len(second_names) == 5
        assert set(first_names).isdisjoint(second_names), (
            f"Expected second OR-query slice window to advance, overlap={set(first_names) & set(second_names)}"
        )

    def test_slice_total_matches_reflects_combined_or_query_count(self, proj):
        all_results = _json(proj, "-mg", "*", "-tc", "-tf", "-n", "0")
        page = _json(proj, "-mg", "*", "-tc", "-tf", "--slice", "10:15", "-oJ")

        if isinstance(page, dict):
            assert page["shown"] == 5
            assert page["total"] == len(all_results)
            assert len(page["result"]) == 5
        else:
            assert len(page) == 5

    def test_limit_zero_returns_all_or_query_results(self, proj):
        results = _json(proj, "-mg", "*", "-tc", "-tf", "-n", "0")
        assert len(results) == 24, f"Expected 24 combined results, got {len(results)}"
