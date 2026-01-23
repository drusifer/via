"""
UsageRenderer: Shows where symbols are used in the codebase.

Uses grep/ripgrep to find references to symbols and formats them
with location and context information.
"""

import logging
import subprocess
import shutil
from typing import Iterator, List, Optional

from .base import Renderer
from .formatters.usage_formatters import (
    UsageFormatter,
    AsciiUsageFormatter,
    UsageLocation,
)
from ..core.match_record import MatchRecord

logger = logging.getLogger(__name__)

# Maximum usages to show per symbol
MAX_USAGES_PER_SYMBOL = 20

# Timeout for grep operations (seconds)
GREP_TIMEOUT = 10


class UsageRenderer(Renderer):
    """Renderer that shows where symbols are used.

    Uses ripgrep (rg) or grep to find references to symbols,
    excluding the definition line itself.
    """

    HELP = "-oU, --usage: Show symbol usages (grep-based search)"
    FLAG = "-oU"

    def __init__(self, formatter: Optional[UsageFormatter] = None):
        """Initialize UsageRenderer with optional formatter.

        Args:
            formatter: Formatter for output. Defaults to AsciiUsageFormatter.
        """
        self.formatter = formatter or AsciiUsageFormatter()
        self._search_tool = self._detect_search_tool()

    def _detect_search_tool(self) -> str:
        """Detect available search tool (prefer ripgrep)."""
        if shutil.which('rg'):
            return 'rg'
        if shutil.which('grep'):
            return 'grep'
        return ''

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render usage information for each symbol.

        Args:
            records: Iterator of MatchRecord objects
            **options: Additional options (unused currently)

        Returns:
            Formatted string showing usages for each symbol
        """
        if not self._search_tool:
            return "Error: Neither ripgrep (rg) nor grep is available. Install ripgrep for best results."

        outputs = []
        for record in records:
            output = self._render_symbol_usages(record)
            outputs.append(output)

        return '\n\n'.join(outputs)

    def _render_symbol_usages(self, record: MatchRecord) -> str:
        """Render usages for a single symbol.

        Args:
            record: MatchRecord for the symbol

        Returns:
            Formatted string with usages
        """
        symbol_name = record.symbol_name
        usages = self._find_usages(record)

        if not usages:
            return self.formatter.format_no_usages(symbol_name)

        lines = [
            self.formatter.format_header(
                symbol_name,
                record.file_path,
                record.line_number
            ),
            "Used in:"
        ]

        # Limit usages shown
        shown_usages = usages[:MAX_USAGES_PER_SYMBOL]
        remaining = len(usages) - MAX_USAGES_PER_SYMBOL

        for usage in shown_usages:
            lines.append(self.formatter.format_usage(usage))

        if remaining > 0:
            lines.append(self.formatter.format_more_indicator(remaining))

        return '\n'.join(lines)

    def _find_usages(self, record: MatchRecord) -> List[UsageLocation]:
        """Find usages of a symbol using grep/ripgrep.

        Args:
            record: MatchRecord for the symbol to find usages of

        Returns:
            List of UsageLocation objects
        """
        symbol_name = record.symbol_name
        definition_file = record.file_path
        definition_line = record.line_number

        try:
            if self._search_tool == 'rg':
                result = self._search_with_ripgrep(symbol_name)
            else:
                result = self._search_with_grep(symbol_name)

            usages = self._parse_grep_output(result, definition_file, definition_line)
            return usages

        except subprocess.TimeoutExpired:
            logger.warning(f"Search for '{symbol_name}' timed out after {GREP_TIMEOUT}s")
            return []
        except Exception as e:
            logger.warning(f"Error searching for '{symbol_name}': {e}")
            return []

    def _search_with_ripgrep(self, symbol_name: str) -> str:
        """Search using ripgrep.

        Args:
            symbol_name: Symbol to search for

        Returns:
            Raw output from ripgrep
        """
        # Use word boundary matching for more accurate results
        # Escape special regex characters in symbol name
        import re
        escaped = re.escape(symbol_name)

        cmd = [
            'rg',
            '-n',                    # Line numbers
            '--no-heading',          # No file grouping
            '-w',                    # Word boundary
            '--type', 'py',          # Python files only for now
            '--type', 'md',          # Markdown files
            escaped,
            '.'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GREP_TIMEOUT,
            cwd='.'
        )
        return result.stdout

    def _search_with_grep(self, symbol_name: str) -> str:
        """Search using grep as fallback.

        Args:
            symbol_name: Symbol to search for

        Returns:
            Raw output from grep
        """
        import re
        escaped = re.escape(symbol_name)

        cmd = [
            'grep',
            '-r',                    # Recursive
            '-n',                    # Line numbers
            '-w',                    # Word boundary
            '--include=*.py',        # Python files
            '--include=*.md',        # Markdown files
            escaped,
            '.'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GREP_TIMEOUT,
            cwd='.'
        )
        return result.stdout

    def _parse_grep_output(
        self,
        output: str,
        definition_file: str,
        definition_line: int
    ) -> List[UsageLocation]:
        """Parse grep/ripgrep output into UsageLocation objects.

        Args:
            output: Raw grep output
            definition_file: File where symbol is defined (to skip)
            definition_line: Line where symbol is defined (to skip)

        Returns:
            List of UsageLocation objects, excluding definition
        """
        usages = []

        for line in output.strip().split('\n'):
            if not line:
                continue

            # Parse format: file:line:context
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue

            file_path = parts[0]
            try:
                line_num = int(parts[1])
            except ValueError:
                continue
            context = parts[2] if len(parts) > 2 else ''

            # Normalize file path for comparison
            norm_file = file_path.lstrip('./')
            norm_def = definition_file.lstrip('./')

            # Skip definition line
            if norm_file == norm_def and line_num == definition_line:
                continue

            usages.append(UsageLocation(
                file_path=file_path,
                line_number=line_num,
                context=context
            ))

        return usages
