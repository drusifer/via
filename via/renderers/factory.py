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
from .diagram import DiagramRenderer
from .usage import UsageRenderer
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
from .formatters.diagram_formatters import (
    MermaidAsciiFormatter,
    MermaidMarkdownFormatter,
    MermaidHtmlFormatter,
)
from .formatters.usage_formatters import (
    AsciiUsageFormatter,
    MarkdownUsageFormatter,
    HtmlUsageFormatter,
)
from ..core.match_record import RenderType, FormatType


# Lookup tables for formatter classes (reduces cyclomatic complexity)
TABLE_FORMATTERS = {
    FormatType.ASCII: AsciiTableFormatter,
    FormatType.MD: MarkdownTableFormatter,
    FormatType.HTML: HtmlTableFormatter,
}

CODE_FORMATTERS = {
    FormatType.ASCII: AsciiCodeFormatter,
    FormatType.MD: MarkdownCodeFormatter,
    FormatType.HTML: HtmlCodeFormatter,
}

DIAGRAM_FORMATTERS = {
    FormatType.ASCII: MermaidAsciiFormatter,
    FormatType.MD: MermaidMarkdownFormatter,
    FormatType.HTML: MermaidHtmlFormatter,
}

USAGE_FORMATTERS = {
    FormatType.ASCII: AsciiUsageFormatter,
    FormatType.MD: MarkdownUsageFormatter,
    FormatType.HTML: HtmlUsageFormatter,
}


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
            format_type: Optional format type (for TABLE/FORMATTED renderers)

        Returns:
            Renderer instance

        Raises:
            ValueError: If render_type is not supported
        """
        if render_type == RenderType.LIST:
            return ListRenderer()

        if render_type == RenderType.RAW:
            return RawRenderer()

        if render_type == RenderType.TABLE:
            formatter_cls = TABLE_FORMATTERS.get(format_type or FormatType.ASCII, AsciiTableFormatter)
            return TableRenderer(formatter_cls())

        if render_type == RenderType.FORMATTED:
            formatter_cls = CODE_FORMATTERS.get(format_type or FormatType.ASCII, AsciiCodeFormatter)
            return FormattedRenderer(formatter_cls())

        if render_type == RenderType.DIAGRAM:
            formatter_cls = DIAGRAM_FORMATTERS.get(format_type or FormatType.ASCII, MermaidAsciiFormatter)
            return DiagramRenderer(formatter_cls())

        if render_type == RenderType.USAGE:
            formatter_cls = USAGE_FORMATTERS.get(format_type or FormatType.ASCII, AsciiUsageFormatter)
            return UsageRenderer(formatter_cls())

        # Show helpful error for unimplemented render types
        implemented = ['list (-oL)', 'table (-oT)', 'raw (-oR)', 'formatted (-oF)', 'diagram (-oD)', 'usage (-oU)']
        raise ValueError(
            f"Render type '{render_type.value}' is not implemented yet. "
            f"Available: {', '.join(implemented)}"
        )
