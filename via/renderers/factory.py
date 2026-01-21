"""
Factory for creating renderer instances.

TLDR:
    RendererFactory creates the appropriate renderer based on RenderType
    and FormatType. Encapsulates the mapping between types and renderer
    implementations.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Optional

from .base import Renderer
from .list import ListRenderer
from .table import TableRenderer
from .raw import RawRenderer
from .formatted import FormattedRenderer
from .formatters.table_formatters import (
    AsciiTableFormatter,
    MarkdownTableFormatter,
    HtmlTableFormatter,
)
from .formatters.code_formatters import (
    AsciiCodeFormatter,
    HtmlCodeFormatter,
    MarkdownCodeFormatter,
)
from ..core.match_record import RenderType, FormatType


class RendererFactory:
    """Factory for creating renderer instances."""

    @staticmethod
    def create(
        render_type: RenderType,
        format_type: Optional[FormatType] = None
    ) -> Renderer:
        """Create a renderer for the given type and format.

        Args:
            render_type: The type of renderer to create
            format_type: Optional format type (for TABLE renderer)

        Returns:
            Renderer instance

        Raises:
            ValueError: If render_type is not supported
        """
        if render_type == RenderType.LIST:
            return ListRenderer()

        if render_type == RenderType.TABLE:
            # Default to ASCII format
            if format_type is None:
                format_type = FormatType.ASCII

            if format_type == FormatType.ASCII:
                return TableRenderer(AsciiTableFormatter())
            elif format_type == FormatType.MD:
                return TableRenderer(MarkdownTableFormatter())
            elif format_type == FormatType.HTML:
                return TableRenderer(HtmlTableFormatter())
            else:
                raise ValueError(f"Unsupported format type for TABLE: {format_type}")

        if render_type == RenderType.RAW:
            return RawRenderer()

        if render_type == RenderType.FORMATTED:
            # Default to ASCII format
            if format_type is None:
                format_type = FormatType.ASCII

            if format_type == FormatType.ASCII:
                return FormattedRenderer(AsciiCodeFormatter())
            elif format_type == FormatType.MD:
                return FormattedRenderer(MarkdownCodeFormatter())
            elif format_type == FormatType.HTML:
                return FormattedRenderer(HtmlCodeFormatter())
            else:
                return FormattedRenderer(AsciiCodeFormatter())

        raise ValueError(f"Unsupported render type: {render_type}")
