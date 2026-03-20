"""
Usage renderer that extracts and displays docstrings for matched symbols.

TLDR:
    UsageRenderer processes class, method, and function MatchRecords (other
    types are skipped) and extracts their Python docstrings via AST parsing.
    It first tries to match by line number, then falls back to name-only search.
    Accepts a pluggable UsageFormatter (ASCII, Markdown, or HTML) and emits
    one formatted docstring block per symbol, separated by blank lines.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

import ast
import logging
from typing import Iterator, Optional

from ..core.match_record import MatchRecord
from .base import Renderer
from .formatters.usage_formatters import (
    AsciiUsageFormatter,
    DocstringInfo,
    UsageFormatter,
)

logger = logging.getLogger(__name__)

# Symbol types that can have docstrings
DOCSTRING_TYPES = {'class', 'method', 'function'}


class UsageRenderer(Renderer):
    """Renderer that shows docstrings for matched symbols.

    Extracts docstrings from Python source files for classes,
    methods, and functions. Supports ASCII, Markdown, and HTML formats.
    """

    HELP = "-oU, --usage: Show symbol docstrings (documentation)"
    FLAG = "-oU"

    def __init__(self, formatter: Optional[UsageFormatter] = None):
        """Initialize UsageRenderer with optional formatter.

        Args:
            formatter: Formatter for output. Defaults to AsciiUsageFormatter.
        """
        self.formatter = formatter or AsciiUsageFormatter()

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render docstrings grouped by file: filename once, then terse symbol entries.

        Args:
            records: Iterator of MatchRecord objects
            **options: Additional options (unused currently)

        Returns:
            Formatted string with docstrings grouped by file
        """
        # Group records by file_path, preserving order
        groups: dict[str, list[MatchRecord]] = {}
        for record in records:
            if record.symbol_type not in DOCSTRING_TYPES:
                continue
            groups.setdefault(record.file_path, []).append(record)

        file_blocks = []
        for file_path, file_records in groups.items():
            symbol_outputs = []
            for record in file_records:
                docstring = self._extract_docstring(record)
                info = DocstringInfo(
                    symbol_name=record.symbol_name,
                    symbol_type=record.symbol_type,
                    file_path='',  # omitted — file is shown as group header
                    line_number=record.line_number,
                    docstring=docstring,
                )
                symbol_outputs.append(self.formatter.format_symbol(info))
            file_blocks.append(f"{file_path}\n" + "\n\n".join(symbol_outputs))

        return '\n\n'.join(file_blocks) + '\n'

    def _extract_docstring(self, record: MatchRecord) -> Optional[str]:
        """Extract docstring for a symbol from its source file.

        Uses AST parsing to find the docstring for the symbol at the
        specified line number.

        Args:
            record: MatchRecord with file_path and line_number

        Returns:
            The docstring if found, None otherwise
        """
        try:
            with open(record.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except (IOError, OSError) as e:
            logger.warning("Could not read file %s: %s", record.file_path, e)
            return None

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning("Could not parse %s: %s", record.file_path, e)
            return None

        # Find the node at the specified line number
        target_line = record.line_number
        symbol_name = record.symbol_name

        for node in ast.walk(tree):
            if not hasattr(node, 'lineno'):
                continue

            # Check if this is the right node
            if node.lineno != target_line:
                continue

            # Extract docstring based on node type
            if isinstance(node, ast.ClassDef) and node.name == symbol_name:
                return ast.get_docstring(node)
            elif isinstance(node, ast.FunctionDef) and node.name == symbol_name:
                return ast.get_docstring(node)
            elif isinstance(node, ast.AsyncFunctionDef) and node.name == symbol_name:
                return ast.get_docstring(node)

        # Fallback: search by name only if line didn't match exactly
        return self._find_docstring_by_name(tree, symbol_name, record.symbol_type)

    def _find_docstring_by_name(
        self,
        tree: ast.AST,
        symbol_name: str,
        symbol_type: str
    ) -> Optional[str]:
        """Find docstring by symbol name as fallback.

        Args:
            tree: Parsed AST
            symbol_name: Name of the symbol to find
            symbol_type: Type of symbol ('class', 'method', 'function')

        Returns:
            Docstring if found, None otherwise
        """
        for node in ast.walk(tree):
            if symbol_type == 'class' and isinstance(node, ast.ClassDef):
                if node.name == symbol_name:
                    return ast.get_docstring(node)
            elif symbol_type in ('method', 'function'):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == symbol_name:
                        return ast.get_docstring(node)

        return None
