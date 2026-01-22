"""
Code formatters for syntax highlighting.

TLDR:
    Provides code formatters using Pygments for syntax highlighting.
    Supports ASCII (terminal), HTML, and Markdown output formats.
    Includes terminal theme auto-detection.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import Terminal256Formatter, HtmlFormatter
from pygments.styles import get_style_by_name


def detect_terminal_theme() -> str:
    """Detect terminal theme from environment.

    Checks environment variables to determine if terminal has
    light or dark background.

    Returns:
        'light' or 'dark'
    """
    # Check COLORFGBG (format: foreground;background)
    colorfgbg = os.environ.get('COLORFGBG', '')
    if colorfgbg:
        parts = colorfgbg.split(';')
        if len(parts) >= 2:
            try:
                bg = int(parts[-1])
                # Standard terminal colors: 0-7 are dark, 8-15 are bright
                # Background >= 7 typically indicates light theme
                if bg >= 7 and bg != 8:  # 8 is bright black (dark gray)
                    return 'light'
                return 'dark'
            except ValueError:
                pass

    # Check TERM_BACKGROUND (some terminals set this)
    term_bg = os.environ.get('TERM_BACKGROUND', '').lower()
    if term_bg in ('light', 'white'):
        return 'light'
    if term_bg in ('dark', 'black'):
        return 'dark'

    # Default to dark (most common)
    return 'dark'


class CodeFormatter(ABC):
    """Abstract base class for code formatters."""

    @abstractmethod
    def format_code(
        self,
        source: str,
        language: str,
        start_line: int = 1,
        theme: Optional[str] = None,
        show_line_numbers: bool = False
    ) -> str:
        """Format source code with syntax highlighting.

        Args:
            source: Source code to format
            language: Programming language (e.g., 'python')
            start_line: Starting line number for display
            theme: Color theme name (None for auto)
            show_line_numbers: Whether to show line numbers

        Returns:
            Formatted source code string
        """
        pass

    def _get_lexer(self, language: str, source: str):
        """Get Pygments lexer for language.

        Args:
            language: Programming language name
            source: Source code (for guessing if needed)

        Returns:
            Pygments lexer
        """
        try:
            return get_lexer_by_name(language)
        except Exception:
            try:
                return guess_lexer(source)
            except Exception:
                return get_lexer_by_name('text')


class AsciiCodeFormatter(CodeFormatter):
    """Formatter for terminal output with ANSI colors."""

    # Map theme names to Pygments styles
    LIGHT_STYLES = ['default', 'tango', 'friendly', 'colorful']
    DARK_STYLES = ['monokai', 'native', 'material', 'dracula', 'one-dark']

    def format_code(
        self,
        source: str,
        language: str,
        start_line: int = 1,
        theme: Optional[str] = None,
        show_line_numbers: bool = False
    ) -> str:
        """Format code with ANSI terminal colors.

        Args:
            source: Source code to format
            language: Programming language
            start_line: Starting line number
            theme: Color theme ('auto', 'light', 'dark', or Pygments style name)
            show_line_numbers: Whether to show line numbers

        Returns:
            ANSI-colored source code
        """
        # Resolve theme
        style_name = self._resolve_theme(theme)

        # Get lexer and formatter
        lexer = self._get_lexer(language, source)

        try:
            style = get_style_by_name(style_name)
            formatter = Terminal256Formatter(style=style)
        except Exception:
            formatter = Terminal256Formatter()

        # Highlight code
        highlighted = highlight(source, lexer, formatter)

        # Add line numbers if requested
        if show_line_numbers:
            highlighted = self._add_line_numbers(highlighted, start_line)

        return highlighted.rstrip('\n')

    def _resolve_theme(self, theme: Optional[str]) -> str:
        """Resolve theme name to Pygments style.

        Args:
            theme: Theme name or 'auto'

        Returns:
            Pygments style name
        """
        if theme is None or theme == 'auto':
            terminal_theme = detect_terminal_theme()
            if terminal_theme == 'light':
                return 'default'
            return 'monokai'

        if theme == 'light':
            return 'default'
        if theme == 'dark':
            return 'monokai'

        # Assume it's a Pygments style name
        try:
            get_style_by_name(theme)
            return theme
        except Exception:
            return 'monokai'  # Fallback

    def _add_line_numbers(self, code: str, start_line: int) -> str:
        """Add line numbers to code.

        Args:
            code: Source code (may contain ANSI codes)
            start_line: Starting line number

        Returns:
            Code with line numbers
        """
        lines = code.split('\n')
        width = len(str(start_line + len(lines) - 1))
        numbered_lines = []
        for i, line in enumerate(lines):
            line_num = start_line + i
            numbered_lines.append(f'{line_num:>{width}} | {line}')
        return '\n'.join(numbered_lines)


class HtmlCodeFormatter(CodeFormatter):
    """Formatter for HTML output."""

    def format_code(
        self,
        source: str,
        language: str,
        start_line: int = 1,
        theme: Optional[str] = None,
        show_line_numbers: bool = False
    ) -> str:
        """Format code as HTML with CSS classes.

        Args:
            source: Source code to format
            language: Programming language
            start_line: Starting line number
            theme: Color theme (Pygments style name)
            show_line_numbers: Whether to show line numbers

        Returns:
            HTML-formatted source code
        """
        lexer = self._get_lexer(language, source)

        # Resolve style
        style_name = theme or 'default'
        try:
            get_style_by_name(style_name)
        except Exception:
            style_name = 'default'

        formatter = HtmlFormatter(
            style=style_name,
            linenos='table' if show_line_numbers else False,
            linenostart=start_line,
            cssclass='highlight'
        )

        return highlight(source, lexer, formatter)


class MarkdownCodeFormatter(CodeFormatter):
    """Formatter for Markdown output."""

    def format_code(
        self,
        source: str,
        language: str,
        start_line: int = 1,
        theme: Optional[str] = None,
        show_line_numbers: bool = False
    ) -> str:
        """Format code as Markdown code block.

        Args:
            source: Source code to format
            language: Programming language
            start_line: Starting line number (ignored for markdown)
            theme: Color theme (ignored for markdown)
            show_line_numbers: Whether to show line numbers

        Returns:
            Markdown-formatted source code
        """
        # Add line numbers as comments if requested
        if show_line_numbers:
            lines = source.split('\n')
            numbered_lines = []
            for i, line in enumerate(lines):
                line_num = start_line + i
                # Add line number as trailing comment
                numbered_lines.append(f'{line}  # L{line_num}')
            source = '\n'.join(numbered_lines)

        return f'```{language}\n{source}\n```'
