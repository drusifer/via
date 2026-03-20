"""
Docstring output formatters for ASCII, Markdown, and HTML targets.

TLDR:
    Defines the UsageFormatter ABC and the DocstringInfo dataclass that carries
    symbol metadata (name, type, file, line, docstring text). Three concrete
    formatters implement format_symbol and format_no_docstring: AsciiUsageFormatter
    (plain # header with indented docstring), MarkdownUsageFormatter (## heading
    with file link and fenced block), and HtmlUsageFormatter (div/h3/pre with
    anchor links). Used exclusively by UsageRenderer.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DocstringInfo:
    """Represents a symbol's docstring information."""
    symbol_name: str
    symbol_type: str
    file_path: str
    line_number: int
    docstring: Optional[str]


class UsageFormatter(ABC):
    """Abstract base class for usage/docstring formatters."""

    @abstractmethod
    def format_symbol(self, info: DocstringInfo) -> str:
        """Format a symbol with its docstring.

        Args:
            info: DocstringInfo containing symbol and docstring data

        Returns:
            Formatted string output
        """
        pass

    @abstractmethod
    def format_no_docstring(self, info: DocstringInfo) -> str:
        """Format message when no docstring found.

        Args:
            info: DocstringInfo for the symbol

        Returns:
            Formatted string indicating no docstring
        """
        pass


class AsciiUsageFormatter(UsageFormatter):
    """Plain text ASCII formatting for terminal output."""

    def format_symbol(self, info: DocstringInfo) -> str:
        loc = f"({info.file_path}:{info.line_number})" if info.file_path else f"(line {info.line_number})"
        header = f"  {info.symbol_type.upper()} {info.symbol_name} {loc}"
        if info.docstring:
            doc_lines = info.docstring.strip().split('\n')
            indented = '\n'.join(f"    {line}" for line in doc_lines)
            return f"{header}\n{indented}"
        return self.format_no_docstring(info)

    def format_no_docstring(self, info: DocstringInfo) -> str:
        loc = f"({info.file_path}:{info.line_number})" if info.file_path else f"(line {info.line_number})"
        return f"  {info.symbol_type.upper()} {info.symbol_name} {loc}"


class MarkdownUsageFormatter(UsageFormatter):
    """Markdown formatting with code blocks."""

    def format_symbol(self, info: DocstringInfo) -> str:
        link = f"[{info.file_path}:{info.line_number}]({info.file_path}#L{info.line_number})"
        header = f"## `{info.symbol_name}` ({info.symbol_type})\n\n*Defined at {link}*"
        if info.docstring:
            return f"{header}\n\n```\n{info.docstring.strip()}\n```"
        return self.format_no_docstring(info)

    def format_no_docstring(self, info: DocstringInfo) -> str:
        link = f"[{info.file_path}:{info.line_number}]({info.file_path}#L{info.line_number})"
        return f"## `{info.symbol_name}` ({info.symbol_type})\n\n*Defined at {link}*\n\n*(no docstring)*"


class HtmlUsageFormatter(UsageFormatter):
    """HTML formatting for web output."""

    def format_symbol(self, info: DocstringInfo) -> str:
        link = f'<a href="{info.file_path}#L{info.line_number}">{info.file_path}:{info.line_number}</a>'
        header = (
            f'<div class="docstring-section">\n'
            f'  <h3><code>{info.symbol_name}</code> ({info.symbol_type})</h3>\n'
            f'  <p class="location">Defined at {link}</p>\n'
        )
        if info.docstring:
            escaped = info.docstring.replace('<', '&lt;').replace('>', '&gt;')
            return f"{header}  <pre class=\"docstring\">{escaped.strip()}</pre>\n</div>"
        return self.format_no_docstring(info)

    def format_no_docstring(self, info: DocstringInfo) -> str:
        link = f'<a href="{info.file_path}#L{info.line_number}">{info.file_path}:{info.line_number}</a>'
        return (
            f'<div class="docstring-section">\n'
            f'  <h3><code>{info.symbol_name}</code> ({info.symbol_type})</h3>\n'
            f'  <p class="location">Defined at {link}</p>\n'
            f'  <p class="no-docstring"><em>(no docstring)</em></p>\n'
            f'</div>'
        )
