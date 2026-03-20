"""
Integration tests for filepath query result-limit behaviour.

TLDR:
    End-to-end tests for filepath query result limits against a 17-file Python
    project (nested pkg/subpkg layout). Confirms the default -n 10 cap emits a
    stderr warning with the total count, that -n 0 returns all 17 files across
    all subdirectory levels, and that an explicit -n N is honoured exactly.
    Key fixtures: large_python_project (creates 17 .py files in pkg/subpkg dirs
    and indexes them); run (thin subprocess helper).
    Key class: TestFilepathQueryLimit — test_default_limit_truncates_results,
    test_unlimited_returns_all_python_files, test_all_subdirectory_files_are_indexed,
    test_explicit_limit_respected.
    Consumed by: pytest integration suite; depends on via CLI and its -tF/-n flags.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def large_python_project(tmp_path):
    """Create a project with >10 Python files in nested directories."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Nested package layout: pkg/subpkg/*.py
    pkg = project_dir / "pkg"
    subpkg = pkg / "subpkg"
    subpkg.mkdir(parents=True)

    # Create 15 Python files so we exceed the default limit of 10
    files = (
        [project_dir / f"module_{i}.py" for i in range(5)]
        + [pkg / f"pkg_module_{i}.py" for i in range(5)]
        + [subpkg / f"sub_module_{i}.py" for i in range(5)]
    )
    for f in files:
        f.write_text(f"# {f.name}\ndef func(): pass\n")

    # Add __init__.py files (also Python files)
    (pkg / "__init__.py").write_text("")
    (subpkg / "__init__.py").write_text("")

    # Index the project
    result = subprocess.run(
        [sys.executable, "-m", "via", "index", str(project_dir)],
        capture_output=True, text=True, cwd=str(project_dir),
    )
    assert result.returncode == 0, f"index failed: {result.stderr}"

    return project_dir


def run(args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "via"] + args,
        capture_output=True, text=True, cwd=str(cwd),
    )


class TestFilepathQueryLimit:

    def test_default_limit_truncates_results(self, large_python_project):
        """Default -n 10 returns 10 results and prints a cap warning to stderr."""
        result = run(["-mg", "*.py", "-tF"], large_python_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        assert len(lines) == 10, (
            f"Expected 10 (default limit), got {len(lines)}. "
            "If this fails with >10, the default limit was changed."
        )
        # Cap warning must appear on stderr
        assert "--limit=10" in result.stderr
        assert "17" in result.stderr  # total match count

    def test_unlimited_returns_all_python_files(self, large_python_project):
        """With -n 0 (unlimited), all Python files are returned."""
        result = run(["-mg", "*.py", "-tF", "-n", "0"], large_python_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        # 15 module files + 2 __init__.py = 17 total Python files
        assert len(lines) == 17, (
            f"Expected 17 Python files, got {len(lines)}.\n"
            f"stdout:\n{result.stdout}"
        )

    def test_all_subdirectory_files_are_indexed(self, large_python_project):
        """Files in nested subdirectories are in the index (not a discovery gap)."""
        result = run(["-mg", "*.py", "-tF", "-n", "0"], large_python_project)
        assert result.returncode == 0
        output = result.stdout

        # Files from all three directory levels must appear
        assert "module_0.py" in output       # project root
        assert "pkg_module_0.py" in output   # pkg/
        assert "sub_module_0.py" in output   # pkg/subpkg/

    def test_explicit_limit_respected(self, large_python_project):
        """Explicit -n N limits results to exactly N."""
        result = run(["-mg", "*.py", "-tF", "-n", "5"], large_python_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        assert len(lines) == 5
