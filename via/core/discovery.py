"""
File discovery with .gitignore support.

TLDR:
    Discovers files in a directory tree while honoring .gitignore rules using
    pathspec library. Detects oversized files, supports nested .gitignore files,
    and provides DEFAULT_EXCLUDES for common patterns (__pycache__, .pyc, .git).

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Optional

import pathspec
@dataclass
class DiscoveredFile:
    """Represents a discovered file."""

    path: str  # Absolute path
    size_bytes: int
    mtime: float
    is_parseable: bool  # Can be parsed by a registered parser
    is_oversized: bool  # Exceeds size limit
class FileDiscovery:
    """Discovers files in a directory tree with .gitignore support."""

    # Default exclusions (always excluded)
    DEFAULT_EXCLUDES = [
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.git/',
        '.svn/',
        '.hg/',
    ]

    # Default file size limit: 10MB
    DEFAULT_SIZE_LIMIT = 10 * 1024 * 1024

    def __init__(
        self,
        root_dir: str,
        parseable_extensions: Optional[Set[str]] = None,
        size_limit: int = DEFAULT_SIZE_LIMIT,
        respect_gitignore: bool = True,
    ):
        """
        Initialize file discovery.

        Args:
            root_dir: Root directory to scan
            parseable_extensions: Set of file extensions that can be parsed (e.g., {'.py', '.js'})
            size_limit: Maximum file size in bytes (default 10MB)
            respect_gitignore: Whether to honor .gitignore rules (default True)
        """
        self.root_dir = os.path.abspath(root_dir)
        self.parseable_extensions = parseable_extensions or set()
        self.size_limit = size_limit
        self.respect_gitignore = respect_gitignore

        # Build gitignore spec
        self.gitignore_spec = self._build_gitignore_spec()

    def discover(self) -> List[DiscoveredFile]:
        """
        Discover all files in the directory tree.

        Returns:
            List of DiscoveredFile objects
        """
        discovered = []

        for root, dirs, files in os.walk(self.root_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if self._should_include_dir(root, d)]

            # Process files
            for filename in files:
                file_path = os.path.join(root, filename)

                if self._should_include_file(file_path):
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        discovered.append(file_info)

        return discovered

    def _build_gitignore_spec(self) -> pathspec.PathSpec:
        """
        Build pathspec from .gitignore files.

        Returns:
            PathSpec object with exclusion patterns
        """
        # Always include default excludes
        patterns = list(self.DEFAULT_EXCLUDES)

        if not self.respect_gitignore:
            # Only use default excludes
            return pathspec.PathSpec.from_lines('gitignore', patterns)

        # Find all .gitignore files in tree
        gitignore_files = []
        for root, dirs, files in os.walk(self.root_dir):
            if '.gitignore' in files:
                gitignore_files.append(os.path.join(root, '.gitignore'))

        # Read patterns from .gitignore files
        for gitignore_path in gitignore_files:
            try:
                with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except IOError:
                # Skip unreadable .gitignore files
                pass

        # Create pathspec
        return pathspec.PathSpec.from_lines('gitignore', patterns)

    def _should_include_dir(self, parent_path: str, dirname: str) -> bool:
        """
        Check if directory should be included.

        Args:
            parent_path: Parent directory path
            dirname: Directory name

        Returns:
            True if directory should be included
        """
        dir_path = os.path.join(parent_path, dirname)
        rel_path = os.path.relpath(dir_path, self.root_dir)

        # Check with trailing slash (for directory patterns)
        return not self.gitignore_spec.match_file(rel_path + '/')

    def _should_include_file(self, file_path: str) -> bool:
        """
        Check if file should be included.

        Args:
            file_path: File path

        Returns:
            True if file should be included
        """
        rel_path = os.path.relpath(file_path, self.root_dir)
        return not self.gitignore_spec.match_file(rel_path)

    def _get_file_info(self, file_path: str) -> Optional[DiscoveredFile]:
        """
        Get file information.

        Args:
            file_path: File path

        Returns:
            DiscoveredFile or None if file cannot be accessed
        """
        try:
            stat = os.stat(file_path)
            size_bytes = stat.st_size
            mtime = stat.st_mtime

            # Check if parseable
            _, ext = os.path.splitext(file_path)
            is_parseable = ext.lower() in self.parseable_extensions

            # Check if oversized
            is_oversized = size_bytes > self.size_limit

            return DiscoveredFile(
                path=file_path,
                size_bytes=size_bytes,
                mtime=mtime,
                is_parseable=is_parseable,
                is_oversized=is_oversized,
            )
        except (OSError, IOError):
            # Skip files that can't be accessed
            return None

    def count_files(self) -> dict:
        """
        Get file counts by category.

        Returns:
            Dict with counts: total, parseable, oversized
        """
        files = self.discover()

        return {
            'total': len(files),
            'parseable': sum(1 for f in files if f.is_parseable and not f.is_oversized),
            'oversized': sum(1 for f in files if f.is_oversized),
            'non_parseable': sum(1 for f in files if not f.is_parseable),
        }
