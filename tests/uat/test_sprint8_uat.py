"""
Sprint 8 UAT — Line Number Index end-to-end acceptance tests.

TLDR:
    UAT81: -mL extracts correct lines from file match (-tF)
    UAT82: -mL extracts correct lines from symbol match (-tc)
    UAT83: open-ended slice (3:) covers line 3 to end of symbol
    UAT84: single-line slice (1:1) returns exactly one line
    UAT85: output byte range matches actual file line content
    UAT86: re-index a modified file; -mL returns updated content
    UAT87: -mL combined with -oF (syntax highlight) does not crash

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import subprocess
import sys

import pytest


# ── Fixtures ─────────────────────────────────────────────────────────────────

# Six-line Python file with predictable, distinct line content.
SAMPLE_PY = """\
class MyClass:
    def method_one(self): pass
    def method_two(self): pass

def top_func():
    return 42
"""

# Lines as bytes for byte-exact assertions:
SAMPLE_LINES = [line + "\n" for line in SAMPLE_PY.splitlines()]
# SAMPLE_LINES[0] = "class MyClass:\n"   (line 1)
# SAMPLE_LINES[1] = "    def method_one(self): pass\n"   (line 2)
# ...


def _via(*args, cwd):
    """Run `python -m via <args>` and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(cwd),
    )


@pytest.fixture
def indexed_project(tmp_path):
    """tmp_path with SAMPLE_PY written to sample.py, fully indexed."""
    src = tmp_path / "sample.py"
    src.write_text(SAMPLE_PY)

    result = _via("index", str(tmp_path), cwd=tmp_path)
    assert result.returncode == 0, f"Index failed: {result.stderr}"
    return tmp_path


# ── UAT81: File line extraction ───────────────────────────────────────────────

class TestUAT81_FileLineExtraction:
    """via -mg 'sample.py' -tF -mL 1:3 -oR returns the first 3 lines."""

    def test_output_contains_line_1(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:3", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "class MyClass:" in r.stdout

    def test_output_contains_line_3(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:3", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "method_two" in r.stdout

    def test_output_does_not_contain_line_5(self, indexed_project):
        """Line 5 (top_func) should NOT appear in a 1:3 slice."""
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:3", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "top_func" not in r.stdout


# ── UAT82: Symbol line extraction ────────────────────────────────────────────

class TestUAT82_SymbolLineExtraction:
    """via -mg 'MyClass' -tc -mL 1:3 -oR returns first 3 lines of the class."""

    def test_class_line1_present(self, indexed_project):
        r = _via("-mg", "MyClass", "-tc", "-mL", "1:3", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "class MyClass:" in r.stdout

    def test_class_first_method_present(self, indexed_project):
        r = _via("-mg", "MyClass", "-tc", "-mL", "1:3", "-oR", cwd=indexed_project)
        assert "method_one" in r.stdout

    def test_top_func_not_in_class_slice(self, indexed_project):
        """top_func is outside the class; should not appear in a 3-line class slice."""
        r = _via("-mg", "MyClass", "-tc", "-mL", "1:3", "-oR", cwd=indexed_project)
        # Use "def top_func" (not just "top_func") to avoid matching the pytest
        # temp directory name, which includes the test function name as a substring.
        assert "def top_func" not in r.stdout


# ── UAT83: Open-ended slice ───────────────────────────────────────────────────

class TestUAT83_OpenSlice:
    """via -mg 'sample.py' -tF -mL 3: -oR returns line 3 to end."""

    def test_line3_present(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "3:", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "method_two" in r.stdout

    def test_last_line_present(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "3:", "-oR", cwd=indexed_project)
        assert "return 42" in r.stdout

    def test_line1_not_present(self, indexed_project):
        """Line 1 (class MyClass:) precedes the slice start — must not appear."""
        r = _via("-mg", "sample.py", "-tF", "-mL", "3:", "-oR", cwd=indexed_project)
        assert "class MyClass:" not in r.stdout


# ── UAT84: Single-line slice ──────────────────────────────────────────────────

class TestUAT84_SingleLine:
    """via -mg 'sample.py' -tF -mL 1:1 -oR returns exactly one line."""

    def test_line1_present(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:1", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "class MyClass:" in r.stdout

    def test_line2_not_present(self, indexed_project):
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:1", "-oR", cwd=indexed_project)
        assert "method_one" not in r.stdout


# ── UAT85: Byte range matches actual file content ────────────────────────────

class TestUAT85_LineNumbersMatch:
    """Output bytes from -mL match what you'd get reading the file directly."""

    def test_extracted_bytes_match_file(self, indexed_project):
        src = indexed_project / "sample.py"
        file_bytes = src.read_bytes()

        # Lines 2:3 in the file
        expected_lines = b"".join(
            line.encode() for line in SAMPLE_LINES[1:3]
        )

        r = _via("-mg", "sample.py", "-tF", "-mL", "2:3", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr

        # The raw output should contain exactly those bytes (may have delimiters around)
        assert expected_lines.decode() in r.stdout


# ── UAT86: Incremental update ─────────────────────────────────────────────────

class TestUAT86_IncrementalUpdate:
    """Modify a file, re-index, -mL returns updated content."""

    def test_reindex_updates_line_slice(self, indexed_project):
        src = indexed_project / "sample.py"

        # Replace with valid Python — completely different content so line 1 changes.
        new_content = "SENTINEL = 'UPDATED'\n\ndef helper(): pass\n"
        src.write_text(new_content)

        # Force re-index
        r = _via("index", "--force", str(indexed_project), cwd=indexed_project)
        assert r.returncode == 0, r.stderr

        # -mL 1:1 should now return the updated line
        r = _via("-mg", "sample.py", "-tF", "-mL", "1:1", "-oR", cwd=indexed_project)
        assert r.returncode == 0, r.stderr
        assert "SENTINEL" in r.stdout

    def test_old_content_gone_after_reindex(self, indexed_project):
        src = indexed_project / "sample.py"
        new_content = "SENTINEL = 'UPDATED'\n\ndef helper(): pass\n"
        src.write_text(new_content)

        _via("index", "--force", str(indexed_project), cwd=indexed_project)

        r = _via("-mg", "sample.py", "-tF", "-mL", "1:1", "-oR", cwd=indexed_project)
        assert "class MyClass:" not in r.stdout


# ── UAT87: Formatted output compatibility ────────────────────────────────────

class TestUAT87_FormattedOutput:
    """-mL works with -oF (syntax highlighting) — no crash, output non-empty."""

    def test_no_crash_with_oF(self, indexed_project):
        # Use class match: filepath symbols don't support -oF, but class symbols do.
        r = _via("-mg", "MyClass", "-tc", "-mL", "1:3", "-oF", cwd=indexed_project)
        assert r.returncode == 0, r.stderr

    def test_output_nonempty_with_oF(self, indexed_project):
        r = _via("-mg", "MyClass", "-tc", "-mL", "1:3", "-oF", cwd=indexed_project)
        assert len(r.stdout.strip()) > 0, "Expected non-empty formatted output"
