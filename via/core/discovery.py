"""
File discovery and project root location utilities.

TLDR:
    Provides two capabilities: find_index_db() walks up the directory tree to
    locate a .via/index.db project database, and FileDiscovery crawls a
    directory tree while honoring .gitignore rules (via pathspec). DiscoveredFile
    is a dataclass holding path, size, mtime, and parseability metadata for each
    file found. DEFAULT_EXCLUDES always suppresses __pycache__, .pyc, .git, and
    .via entries.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""


def find_index_db(start_path, return_root=False):
    """
    Walk up the directory tree from start_path to find .via/index.db.

    Args:
        start_path: Starting directory path
        return_root: If True, also return the project root directory

    Returns:
        If return_root is False: Path to index.db if found, else None
        If return_root is True: tuple of (Path to index.db, project root) if found, else (None, None)
    """
    from pathlib import Path
    current = Path(start_path).resolve()
    while True:
        candidate = current / ".via" / "index.db"
        if candidate.exists():
            if return_root:
                return candidate, current
            return candidate
        if current.parent == current:
            # Reached root
            if return_root:
                return None, None
            return None
        current = current.parent

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Set

from via.core.path_filter import PathFilter

logger = logging.getLogger(__name__)
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
        '.via/',
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

        # Delegate path filtering to PathFilter
        self._filter = PathFilter(root_dir, respect_gitignore)

    def discover(self) -> List[DiscoveredFile]:
        """
        Discover all files in the directory tree.

        Returns:
            List of DiscoveredFile objects
        """
        discovered = []

        logger.debug(f"Starting discovery in: {self.root_dir}")
        logger.debug(f"Parseable extensions: {self.parseable_extensions}")

        for root, dirs, files in os.walk(self.root_dir):
            rel_root = os.path.relpath(root, self.root_dir)
            logger.debug(f"Walking: {rel_root} (dirs: {dirs[:5]}{'...' if len(dirs) > 5 else ''})")

            # Filter directories
            original_dirs = list(dirs)
            dirs[:] = [d for d in dirs if self._should_include_dir(root, d)]
            excluded_dirs = set(original_dirs) - set(dirs)
            if excluded_dirs:
                logger.debug(f"  Excluded dirs: {excluded_dirs}")

            # Process files
            for filename in files:
                file_path = os.path.join(root, filename)

                if self._should_include_file(file_path):
                    file_info = self._get_file_info(file_path)
                    if file_info:
                        discovered.append(file_info)
                        logger.debug(f"  Discovered: {os.path.relpath(file_path, self.root_dir)} (parseable={file_info.is_parseable})")

        logger.debug(f"Discovery complete: {len(discovered)} files found")
        return discovered

    def _should_include_dir(self, parent_path: str, dirname: str) -> bool:
        """Check if directory should be included (delegates to PathFilter)."""
        return self._filter.should_include_dir(parent_path, dirname)

    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included (delegates to PathFilter)."""
        return self._filter.should_include_file(file_path)

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
