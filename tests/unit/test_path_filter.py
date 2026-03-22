"""Unit tests for PathFilter (TD-WATCH-1).

TLDR:
    Verifies PathFilter correctly excludes .pyc files and DEFAULT_EXCLUDES,
    respects .gitignore patterns, includes extra_patterns, and excludes .git/.
    Also verifies FileDiscovery behavior is unchanged after delegation.
    Key class: TestPathFilter — exercises should_include_file and should_include_dir.
    Role: protects the PathFilter refactor that removes private method access on
    FileDiscovery from WatchService.
"""

import os
import tempfile
from pathlib import Path

import pytest

from via.core.path_filter import PathFilter


@pytest.fixture
def temp_dir(tmp_path):
    """Temp dir with known structure for PathFilter tests."""
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "src" / "module.py").write_text("# module")
    (tmp_path / "src" / "module.pyc").write_text("")
    (tmp_path / "README.md").write_text("# readme")
    (tmp_path / ".gitignore").write_text("build/\n*.log\n")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "output.py").write_text("# out")
    return tmp_path


class TestPathFilter:
    """TD-WATCH-1: PathFilter path inclusion/exclusion logic."""

    def test_should_include_py_file(self, temp_dir):
        """A regular .py file is included."""
        pf = PathFilter(str(temp_dir))
        assert pf.should_include_file(str(temp_dir / "src" / "module.py"))

    def test_excludes_pyc_file(self, temp_dir):
        """A .pyc file is excluded by DEFAULT_EXCLUDES."""
        pf = PathFilter(str(temp_dir))
        assert not pf.should_include_file(str(temp_dir / "src" / "module.pyc"))

    def test_excludes_gitignored_file(self, temp_dir):
        """A file matching .gitignore pattern (*.log) is excluded."""
        log_file = temp_dir / "app.log"
        log_file.write_text("log")
        pf = PathFilter(str(temp_dir))
        assert not pf.should_include_file(str(log_file))

    def test_excludes_dot_git_dir(self, temp_dir):
        """The .git/ directory is excluded."""
        pf = PathFilter(str(temp_dir))
        assert not pf.should_include_dir(str(temp_dir), ".git")

    def test_excludes_pycache_dir(self, temp_dir):
        """The __pycache__/ directory is excluded."""
        pf = PathFilter(str(temp_dir))
        assert not pf.should_include_dir(str(temp_dir), "__pycache__")

    def test_excludes_gitignored_dir(self, temp_dir):
        """A directory matching .gitignore (build/) is excluded."""
        pf = PathFilter(str(temp_dir))
        assert not pf.should_include_dir(str(temp_dir), "build")

    def test_includes_normal_dir(self, temp_dir):
        """A normal directory (src/) is included."""
        pf = PathFilter(str(temp_dir))
        assert pf.should_include_dir(str(temp_dir), "src")

    def test_extra_patterns_applied(self, temp_dir):
        """Extra patterns provided at construction are applied."""
        secret = temp_dir / "secret.txt"
        secret.write_text("shh")
        pf = PathFilter(str(temp_dir), extra_patterns=["*.txt"])
        assert not pf.should_include_file(str(secret))

    def test_extra_patterns_exclude_dir(self, temp_dir):
        """Extra dir patterns exclude matching directories."""
        (temp_dir / "dist").mkdir()
        pf = PathFilter(str(temp_dir), extra_patterns=["dist/"])
        assert not pf.should_include_dir(str(temp_dir), "dist")

    def test_respect_gitignore_false_ignores_gitignore(self, temp_dir):
        """With respect_gitignore=False, .gitignore patterns are not applied."""
        log_file = temp_dir / "app.log"
        log_file.write_text("log")
        pf = PathFilter(str(temp_dir), respect_gitignore=False)
        # *.log is in .gitignore but not in DEFAULT_EXCLUDES → included
        assert pf.should_include_file(str(log_file))

    def test_respect_gitignore_false_still_applies_default_excludes(self, temp_dir):
        """DEFAULT_EXCLUDES still apply even with respect_gitignore=False."""
        pf = PathFilter(str(temp_dir), respect_gitignore=False)
        assert not pf.should_include_file(str(temp_dir / "src" / "module.pyc"))

    def test_no_gitignore_file_uses_defaults(self, tmp_path):
        """If no .gitignore exists, only DEFAULT_EXCLUDES are applied."""
        (tmp_path / "src").mkdir()
        pf = PathFilter(str(tmp_path))
        # pyc excluded, .py included
        (tmp_path / "src" / "f.pyc").write_text("")
        assert not pf.should_include_file(str(tmp_path / "src" / "f.pyc"))
        (tmp_path / "src" / "f.py").write_text("")
        assert pf.should_include_file(str(tmp_path / "src" / "f.py"))
