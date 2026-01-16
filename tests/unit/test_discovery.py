"""Unit tests for file discovery."""

import os
import tempfile
from pathlib import Path

import pytest

from via.core.discovery import FileDiscovery, DiscoveredFile


@pytest.fixture
def temp_project():
    """Create a temporary project directory with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        os.makedirs(os.path.join(tmpdir, "src"))
        os.makedirs(os.path.join(tmpdir, "tests"))
        os.makedirs(os.path.join(tmpdir, "build"))
        os.makedirs(os.path.join(tmpdir, "__pycache__"))

        # Create Python files
        Path(os.path.join(tmpdir, "main.py")).write_text("print('main')")
        Path(os.path.join(tmpdir, "src", "module.py")).write_text("def func(): pass")
        Path(os.path.join(tmpdir, "tests", "test_module.py")).write_text("def test(): pass")

        # Create non-Python files
        Path(os.path.join(tmpdir, "README.md")).write_text("# README")
        Path(os.path.join(tmpdir, "config.json")).write_text("{}")

        # Create files in excluded directories
        Path(os.path.join(tmpdir, "build", "output.py")).write_text("# build output")
        Path(os.path.join(tmpdir, "__pycache__", "cached.pyc")).write_text("")

        # Create .gitignore
        gitignore_content = """
build/
*.pyc
*.log
"""
        Path(os.path.join(tmpdir, ".gitignore")).write_text(gitignore_content)

        yield tmpdir


class TestFileDiscovery:
    """Test FileDiscovery class."""

    def test_discover_python_files(self, temp_project):
        """Test discovering Python files."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        files = discovery.discover()

        # Should find Python files
        paths = [f.path for f in files]
        assert any('main.py' in p for p in paths)
        assert any('module.py' in p for p in paths)
        assert any('test_module.py' in p for p in paths)

    def test_respects_gitignore(self, temp_project):
        """Test that .gitignore is respected."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
            respect_gitignore=True,
        )

        files = discovery.discover()
        paths = [f.path for f in files]

        # Should not find files in build/ directory
        assert not any('build' in p for p in paths)

    def test_excludes_pycache(self, temp_project):
        """Test that __pycache__ is always excluded."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py', '.pyc'},
            respect_gitignore=False,  # Even without gitignore
        )

        files = discovery.discover()
        paths = [f.path for f in files]

        # Should not find files in __pycache__
        assert not any('__pycache__' in p for p in paths)

    def test_discover_without_gitignore(self, temp_project):
        """Test discovery without respecting .gitignore."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
            respect_gitignore=False,
        )

        files = discovery.discover()
        paths = [f.path for f in files]

        # Should find files in build/ (but not __pycache__ - that's always excluded)
        # Note: __pycache__ is in DEFAULT_EXCLUDES
        assert any('output.py' in p and 'build' in p for p in paths)

    def test_is_parseable_flag(self, temp_project):
        """Test that is_parseable flag is set correctly."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        files = discovery.discover()

        # Python files should be parseable
        for f in files:
            if f.path.endswith('.py'):
                assert f.is_parseable
            elif f.path.endswith('.md') or f.path.endswith('.json'):
                assert not f.is_parseable

    def test_oversized_file_detection(self, temp_project):
        """Test oversized file detection."""
        # Create a large file
        large_file = os.path.join(temp_project, "large.py")
        with open(large_file, 'w') as f:
            f.write("x" * (11 * 1024 * 1024))  # 11MB

        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
            size_limit=10 * 1024 * 1024,  # 10MB
        )

        files = discovery.discover()

        # Find the large file
        large = next((f for f in files if 'large.py' in f.path), None)
        assert large is not None
        assert large.is_oversized

    def test_file_info_fields(self, temp_project):
        """Test that file info contains all required fields."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        files = discovery.discover()
        assert len(files) > 0

        for f in files:
            assert hasattr(f, 'path')
            assert hasattr(f, 'size_bytes')
            assert hasattr(f, 'mtime')
            assert hasattr(f, 'is_parseable')
            assert hasattr(f, 'is_oversized')
            assert isinstance(f.path, str)
            assert isinstance(f.size_bytes, int)
            assert isinstance(f.mtime, float)
            assert isinstance(f.is_parseable, bool)
            assert isinstance(f.is_oversized, bool)

    def test_count_files(self, temp_project):
        """Test file counting."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        counts = discovery.count_files()

        assert 'total' in counts
        assert 'parseable' in counts
        assert 'oversized' in counts
        assert 'non_parseable' in counts

        assert counts['total'] > 0
        assert counts['parseable'] > 0  # Should have .py files

    def test_nested_gitignore_not_supported(self, temp_project):
        """Test that nested .gitignore files are NOT processed.

        Only the root .gitignore is respected. Nested .gitignore files
        would need to have their patterns applied relative to their location,
        which is more complex. For now, we only support root .gitignore.
        """
        # Create nested directory with its own .gitignore
        nested_dir = os.path.join(temp_project, "src", "nested")
        os.makedirs(nested_dir)

        Path(os.path.join(nested_dir, "file.py")).write_text("code")
        Path(os.path.join(nested_dir, "ignored.py")).write_text("code")

        # Add .gitignore in nested directory (should be ignored)
        Path(os.path.join(nested_dir, ".gitignore")).write_text("ignored.py\n")

        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        files = discovery.discover()
        paths = [f.path for f in files]

        # Both files should be found - nested .gitignore is NOT processed
        assert any('file.py' in p and 'nested' in p for p in paths)
        assert any('ignored.py' in p for p in paths)  # Changed: now found

    def test_absolute_paths(self, temp_project):
        """Test that returned paths are absolute."""
        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py'},
        )

        files = discovery.discover()

        for f in files:
            assert os.path.isabs(f.path)

    def test_empty_directory(self):
        """Test discovery in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = FileDiscovery(
                root_dir=tmpdir,
                parseable_extensions={'.py'},
            )

            files = discovery.discover()
            assert len(files) == 0

    def test_multiple_extensions(self, temp_project):
        """Test discovery with multiple extensions."""
        # Create files with different extensions
        Path(os.path.join(temp_project, "script.pyx")).write_text("# cython")
        Path(os.path.join(temp_project, "stub.pyi")).write_text("# stub")

        discovery = FileDiscovery(
            root_dir=temp_project,
            parseable_extensions={'.py', '.pyx', '.pyi'},
        )

        files = discovery.discover()

        # Should find all Python-related files
        exts = set(os.path.splitext(f.path)[1] for f in files if f.is_parseable)
        assert '.py' in exts
        assert '.pyx' in exts
        assert '.pyi' in exts
