"""
Usage formatters for UsageRenderer.

Provides ASCII, Markdown, and HTML formatting for symbol usage output.
"""

from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class UsageLocation:
    """Represents a single usage location."""
    file_path: str
    line_number: int
    context: str


class UsageFormatter(ABC):
    """Abstract base class for usage formatters."""

    @abstractmethod
    def format_header(self, symbol_name: str, definition_file: str, definition_line: int) -> str:
        """Format the header for a symbol's usages."""
        pass

    @abstractmethod
    def format_usage(self, usage: UsageLocation) -> str:
        """Format a single usage location."""
        pass

    @abstractmethod
    def format_no_usages(self, symbol_name: str) -> str:
        """Format message when no usages found."""
        pass

    @abstractmethod
    def format_more_indicator(self, remaining: int) -> str:
        """Format indicator for additional usages not shown."""
        pass


class AsciiUsageFormatter(UsageFormatter):
    """Plain text ASCII formatting for terminal output."""

    def format_header(self, symbol_name: str, definition_file: str, definition_line: int) -> str:
        return f"# {symbol_name} (defined at {definition_file}:{definition_line})"

    def format_usage(self, usage: UsageLocation) -> str:
        return f"  {usage.file_path}:{usage.line_number}: {usage.context.strip()}"

    def format_no_usages(self, symbol_name: str) -> str:
        return f"# {symbol_name}: No usages found"

    def format_more_indicator(self, remaining: int) -> str:
        return f"  ... and {remaining} more usages"


class MarkdownUsageFormatter(UsageFormatter):
    """Markdown formatting with clickable links."""

    def format_header(self, symbol_name: str, definition_file: str, definition_line: int) -> str:
        return f"## `{symbol_name}` (defined at [{definition_file}:{definition_line}]({definition_file}#L{definition_line}))"

    def format_usage(self, usage: UsageLocation) -> str:
        link = f"[{usage.file_path}:{usage.line_number}]({usage.file_path}#L{usage.line_number})"
        return f"- {link}: `{usage.context.strip()}`"

    def format_no_usages(self, symbol_name: str) -> str:
        return f"## `{symbol_name}`: No usages found"

    def format_more_indicator(self, remaining: int) -> str:
        return f"- *... and {remaining} more usages*"


class HtmlUsageFormatter(UsageFormatter):
    """HTML formatting for web output."""

    def format_header(self, symbol_name: str, definition_file: str, definition_line: int) -> str:
        return (
            f'<div class="usage-section">\n'
            f'  <h3><code>{symbol_name}</code> '
            f'(defined at <a href="{definition_file}#L{definition_line}">{definition_file}:{definition_line}</a>)</h3>\n'
            f'  <ul class="usages">'
        )

    def format_usage(self, usage: UsageLocation) -> str:
        return (
            f'    <li><a href="{usage.file_path}#L{usage.line_number}">'
            f'{usage.file_path}:{usage.line_number}</a>: '
            f'<code>{usage.context.strip()}</code></li>'
        )

    def format_no_usages(self, symbol_name: str) -> str:
        return (
            f'<div class="usage-section">\n'
            f'  <h3><code>{symbol_name}</code>: No usages found</h3>\n'
            f'</div>'
        )

    def format_more_indicator(self, remaining: int) -> str:
        return f'    <li><em>... and {remaining} more usages</em></li>\n  </ul>\n</div>'
