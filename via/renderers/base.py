"""
Abstract base class and shared utilities for all renderers.

TLDR:
    Defines the Renderer ABC that every concrete renderer inherits from.
    All renderers consume an Iterator[MatchRecord] and return a formatted
    string. Also provides ContextOptions (consolidates -A/-B/-C flag handling)
    and format_delimiter_header (the # divider block shown above each match).

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from ..core.interfaces import ArgumentProvider, HelpProvider
from ..core.match_record import MatchRecord

# Constants for header formatting
HEADER_DIVIDER_WIDTH = 60
HEADER_DIVIDER_CHAR = '#'


@dataclass
class ContextOptions:
    """Options for context lines around matches.

    Consolidates -A, -B, -C option handling that was duplicated
    in RawRenderer and FormattedRenderer.
    """
    before: int = 0
    after: int = 0

    @classmethod
    def from_options(cls, **options) -> 'ContextOptions':
        """Create from render options dict.

        Args:
            **options: Render options including:
                - after_context: Lines after match (-A)
                - before_context: Lines before match (-B)
                - context: Lines both sides (-C, overrides -A/-B)

        Returns:
            ContextOptions instance
        """
        context = options.get('context')
        if context:
            return cls(before=context, after=context)
        return cls(
            before=options.get('before_context', 0),
            after=options.get('after_context', 0)
        )


class Renderer(ABC, ArgumentProvider, HelpProvider):
    """Abstract base class for renderers.

    Renderers consume an iterator of MatchRecords and produce formatted
    string output. They support streaming (O(1) memory) by processing
    records one at a time.
    """

    @classmethod
    def add_arguments(cls, parser):
        # Placeholder: to be implemented per renderer
        pass

    @classmethod
    def get_help(cls) -> str:
        return getattr(cls, "HELP", f"{cls.__name__}: renderer.")

    @abstractmethod
    def render(self, records: Iterator[MatchRecord], **options) -> str:
        """Render records to formatted string output.

        Args:
            records: Iterator of MatchRecord objects
            **options: Renderer-specific options

        Returns:
            Formatted string output
        """
        pass

    def format_delimiter_header(
        self,
        record: MatchRecord,
        end_line: int,
        divider_char: str = HEADER_DIVIDER_CHAR,
        width: int = HEADER_DIVIDER_WIDTH
    ) -> str:
        """Format delimiter header for a match.

        Args:
            record: The match record
            end_line: Calculated end line number
            divider_char: Character for divider line
            width: Width of divider line

        Returns:
            Formatted header string
        """
        divider = divider_char * width
        return (
            f"{divider}\n"
            f"{divider_char} {record.file_path}:{record.line_number}-{end_line}\n"
            f"{divider_char}     {record.symbol_type} *{record.symbol_name}*\n"
            f"{divider}"
        )
