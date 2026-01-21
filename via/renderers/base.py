"""
Base class for renderers.

TLDR:
    Defines abstract Renderer base class that all renderers inherit from.
    Renderers take an iterator of MatchRecords and produce formatted output.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from typing import Iterator

from ..core.match_record import MatchRecord


class Renderer(ABC):
    """Abstract base class for renderers.

    Renderers consume an iterator of MatchRecords and produce formatted
    string output. They support streaming (O(1) memory) by processing
    records one at a time.
    """

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
