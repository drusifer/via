"""
Path inclusion/exclusion filter using gitignore spec and default excludes.

TLDR: Path inclusion/exclusion filtering using gitignore-style patterns and default VIA excludes for indexing and watching.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

import logging
import os
from typing import List, Optional

import pathspec

logger = logging.getLogger(__name__)


CORE_DEFAULT_EXCLUDES: List[str] = [
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git/',
    '.via/',
    '.svn/',
    '.hg/',
]


class PathFilter:
    """Path inclusion/exclusion filter using gitignore spec and default excludes."""

    DEFAULT_EXCLUDES: List[str] = [
        *CORE_DEFAULT_EXCLUDES,
        # JavaScript/Node.js project directories
        'node_modules/',
        'dist/',
        '.next/',
        '.nuxt/',
        '.svelte-kit/',
        'coverage/',
        '.turbo/',
    ]

    def __init__(
        self,
        root_dir: str,
        respect_gitignore: bool = True,
        extra_patterns: Optional[List[str]] = None,
    ) -> None:
        self.root_dir = os.path.abspath(root_dir)
        self._spec = self._build_spec(respect_gitignore, extra_patterns or [])

    def should_include_dir(self, parent_path: str, dirname: str) -> bool:
        """Return True if directory should be walked."""
        dir_path = os.path.join(parent_path, dirname)
        rel_path = os.path.relpath(dir_path, self.root_dir)
        matched = self._spec.match_file(rel_path + '/')
        if matched:
            logger.debug("  Dir excluded: %s/", rel_path)
        return not matched

    def should_include_file(self, file_path: str) -> bool:
        """Return True if file should be indexed."""
        rel_path = os.path.relpath(file_path, self.root_dir)
        return not self._spec.match_file(rel_path)

    def _build_spec(self, respect_gitignore: bool, extra_patterns: List[str]) -> pathspec.PathSpec:
        """Build combined pathspec from defaults, .gitignore, and extra patterns."""
        patterns = list(self.DEFAULT_EXCLUDES)

        if respect_gitignore:
            root_gitignore = os.path.join(self.root_dir, '.gitignore')
            if os.path.exists(root_gitignore):
                try:
                    with open(root_gitignore, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                patterns.append(line)
                except IOError:
                    pass

        patterns.extend(extra_patterns)
        return pathspec.PathSpec.from_lines('gitignore', patterns)
