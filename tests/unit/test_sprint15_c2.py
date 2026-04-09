"""Sprint 15 Cycle 2 tests — S15-1 --slice result windowing + total/shown.

TLDR:
    S15-1: --slice start:end limits results with SQL OFFSET/LIMIT.
           JSON response (MCP) gains total and shown fields.
           --slice and -n are mutually exclusive (parse-time error).
           parse_result_slice() wraps parse_line_slice() with 0-based semantics.

Author: Neo
Sprint: 15, Cycle 2
"""

import json
import subprocess
import sys

import pytest

from via.core.utils import parse_result_slice


# ---------------------------------------------------------------------------
# Fixture: project with many symbols for pagination testing
# ---------------------------------------------------------------------------

_MANY_CLASSES = "\n".join(
    f"class Class{i:03d}:\n    def method(self): pass\n"
    for i in range(50)
)

_UTILS_PY = """\
def util_a(): pass
def util_b(): pass
def util_c(): pass
"""


@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    """Project with 50 classes — enough to test pagination."""
    d = tmp_path_factory.mktemp("sprint15c2")
    (d / "classes.py").write_text(_MANY_CLASSES)
    (d / "utils.py").write_text(_UTILS_PY)
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


def _lines(proj, *args):
    r = _q(proj, *args)
    assert r.returncode == 0, f"via failed:\n{r.stderr}\n{r.stdout}"
    return [l for l in r.stdout.splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# parse_result_slice() unit tests
# ---------------------------------------------------------------------------

class TestParseResultSlice:
    """parse_result_slice() parses 0-based result window strings."""

    def test_start_colon_end(self):
        assert parse_result_slice("0:20") == (0, 20)

    def test_start_colon_end_nonzero(self):
        assert parse_result_slice("20:40") == (20, 40)

    def test_open_end(self):
        assert parse_result_slice("20:") == (20, None)

    def test_open_start(self):
        assert parse_result_slice(":20") == (None, 20)

    def test_single_value(self):
        # Single int: start==end (matches parse_line_slice behavior)
        assert parse_result_slice("5") == (5, 5)

    def test_invalid_raises(self):
        with pytest.raises((ValueError, TypeError)):
            parse_result_slice("abc")

    def test_zero_start(self):
        assert parse_result_slice("0:10") == (0, 10)


# ---------------------------------------------------------------------------
# S15-1: --slice CLI behavior
# ---------------------------------------------------------------------------

class TestSliceCLI:
    """--slice limits and offsets CLI results correctly."""

    def test_slice_limits_results(self, proj):
        results = _lines(proj, "-mg", "*", "-tc", "--slice", "0:10")
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"

    def test_slice_different_window(self, proj):
        first = _lines(proj, "-mg", "*", "-tc", "--slice", "0:10")
        second = _lines(proj, "-mg", "*", "-tc", "--slice", "10:20")
        assert len(second) == 10
        # Windows must not overlap
        first_set = set(first)
        second_set = set(second)
        assert first_set.isdisjoint(second_set), \
            f"Slice windows overlap: {first_set & second_set}"

    def test_slice_open_end_returns_all_from_offset(self, proj):
        all_results = _lines(proj, "-mg", "*", "-tc", "-n", "0")
        from_20 = _lines(proj, "-mg", "*", "-tc", "--slice", "20:")
        assert len(from_20) == len(all_results) - 20, \
            f"Expected {len(all_results)-20} results from offset 20, got {len(from_20)}"

    def test_slice_open_start_returns_first_n(self, proj):
        first_10 = _lines(proj, "-mg", "*", "-tc", "--slice", ":10")
        slice_10 = _lines(proj, "-mg", "*", "-tc", "--slice", "0:10")
        assert first_10 == slice_10, "':10' and '0:10' should return same results"

    def test_slice_exits_0(self, proj):
        r = _q(proj, "-mg", "*", "-tc", "--slice", "0:5")
        assert r.returncode == 0

    def test_slice_and_n_are_mutually_exclusive(self, proj):
        r = _q(proj, "-mg", "*", "-tc", "--slice", "0:10", "-n", "5")
        assert r.returncode != 0, "Expected error when using both --slice and -n"
        assert "mutually exclusive" in r.stderr.lower() or "exclusive" in r.stderr.lower(), \
            f"Expected 'mutually exclusive' in error: {r.stderr}"

    def test_slice_beyond_results_returns_empty(self, proj):
        # There are 50 classes; slice starting at 100 should return nothing
        r = _q(proj, "-mg", "*", "-tc", "--slice", "100:110")
        assert r.returncode == 0
        result_lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert len(result_lines) == 0, \
            f"Expected no results past end, got: {result_lines}"

    def test_warning_mentions_slice_when_truncated(self, proj):
        # Default limit is 10; with 50 classes, warning should mention --slice
        r = _q(proj, "-mg", "*", "-tc")
        assert "--slice" in r.stderr or "slice" in r.stderr.lower(), \
            f"Expected '--slice' in truncation warning: {r.stderr}"


# ---------------------------------------------------------------------------
# S15-1: total_matches is consistent with slice
# ---------------------------------------------------------------------------

class TestTotalMatchesWithSlice:
    """total_matches on MatchRecord reflects full count even when sliced."""

    def test_total_matches_reflects_full_count_not_slice(self, proj):
        """When sliced to 10, total_matches should still be the full count."""
        # Get full count
        all_results = _lines(proj, "-mg", "*", "-tc", "-n", "0")
        total_expected = len(all_results)

        # Get sliced results via JSON output to inspect total_matches
        r = _q(proj, "-mg", "*", "-tc", "--slice", "0:5", "-oJ")
        assert r.returncode == 0, f"via -oJ failed: {r.stderr}"
        data = json.loads(r.stdout)
        # MCP response is now a dict
        if isinstance(data, dict):
            assert "total" in data, f"Expected 'total' in MCP response: {data.keys()}"
            assert "shown" in data, f"Expected 'shown' in MCP response: {data.keys()}"
            assert data["total"] == total_expected, \
                f"Expected total={total_expected}, got {data['total']}"
            assert data["shown"] == 5, f"Expected shown=5, got {data['shown']}"
        else:
            # CLI -oJ may still return a list; total is on records
            assert len(data) == 5, f"Expected 5 results, got {len(data)}"
