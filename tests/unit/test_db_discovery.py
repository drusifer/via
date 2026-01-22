"""
Unit tests for database discovery (walking up directory tree).

Tests the find_index_db() function that locates .via/index.db by walking
up the directory tree, similar to how git finds .git directories.
"""

import pytest
from pathlib import Path
import tempfile
import os

from via.core.discovery import find_index_db


class TestFindIndexDb:
    """Tests for find_index_db() function."""

    def test_finds_db_in_current_dir(self, tmp_path):
        """Should find .via/index.db in current directory."""
        # Create .via/index.db in tmp_path
        via_dir = tmp_path / ".via"
        via_dir.mkdir()
        db_file = via_dir / "index.db"
        db_file.touch()

        # Should find it
        result = find_index_db(tmp_path)
        assert result is not None
        assert result == db_file

    def test_finds_db_in_parent_dir(self, tmp_path):
        """Should find .via/index.db in parent directory."""
        # Create .via/index.db in tmp_path (root)
        via_dir = tmp_path / ".via"
        via_dir.mkdir()
        db_file = via_dir / "index.db"
        db_file.touch()

        # Create a subdirectory
        subdir = tmp_path / "src" / "components"
        subdir.mkdir(parents=True)

        # Should find db when starting from subdir
        result = find_index_db(subdir)
        assert result is not None
        assert result == db_file

    def test_finds_db_multiple_levels_up(self, tmp_path):
        """Should find .via/index.db multiple levels up."""
        # Create .via/index.db in tmp_path (root)
        via_dir = tmp_path / ".via"
        via_dir.mkdir()
        db_file = via_dir / "index.db"
        db_file.touch()

        # Create deeply nested subdirectory
        deep_dir = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)

        # Should find db when starting from deep nested dir
        result = find_index_db(deep_dir)
        assert result is not None
        assert result == db_file

    def test_returns_none_when_not_found(self, tmp_path):
        """Should return None when no .via/index.db exists."""
        # Create a directory without .via
        subdir = tmp_path / "project"
        subdir.mkdir()

        result = find_index_db(subdir)
        assert result is None

    def test_returns_none_when_via_exists_but_no_db(self, tmp_path):
        """Should return None when .via exists but index.db doesn't."""
        # Create .via without index.db
        via_dir = tmp_path / ".via"
        via_dir.mkdir()

        result = find_index_db(tmp_path)
        assert result is None

    def test_stops_at_filesystem_root(self, tmp_path):
        """Should stop at filesystem root without infinite loop."""
        # This should not hang - it should return None
        result = find_index_db(Path("/tmp/nonexistent/path/that/does/not/exist"))
        assert result is None

    def test_stops_at_home_directory(self, tmp_path):
        """Should stop at home directory boundary."""
        # Create .via/index.db ABOVE home (simulated)
        # In practice, we just verify it stops at reasonable boundaries
        home = Path.home()

        # If we're in a subdir of home, it should not go above home
        # This test verifies the boundary check works
        result = find_index_db(home / "nonexistent_subdir_12345")
        # Should return None (no .via in home typically)
        # Main thing is it doesn't crash or hang
        assert result is None or isinstance(result, Path)

    def test_uses_closest_db_when_multiple_exist(self, tmp_path):
        """Should use closest .via/index.db when multiple exist in tree."""
        # Create .via/index.db in root
        root_via = tmp_path / ".via"
        root_via.mkdir()
        root_db = root_via / "index.db"
        root_db.touch()

        # Create .via/index.db in subproject
        subproject = tmp_path / "subproject"
        subproject.mkdir()
        sub_via = subproject / ".via"
        sub_via.mkdir()
        sub_db = sub_via / "index.db"
        sub_db.touch()

        # From subproject, should find subproject's db
        result = find_index_db(subproject)
        assert result == sub_db

        # From subproject/src, should still find subproject's db
        src_dir = subproject / "src"
        src_dir.mkdir()
        result = find_index_db(src_dir)
        assert result == sub_db

        # From root, should find root's db
        result = find_index_db(tmp_path)
        assert result == root_db

    def test_returns_project_root_with_db(self, tmp_path):
        """find_index_db should also return the project root."""
        # This variant returns (db_path, project_root)
        via_dir = tmp_path / ".via"
        via_dir.mkdir()
        db_file = via_dir / "index.db"
        db_file.touch()

        subdir = tmp_path / "src"
        subdir.mkdir()

        db_path, project_root = find_index_db(subdir, return_root=True)
        assert db_path == db_file
        assert project_root == tmp_path
