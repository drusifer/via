"""
Factory that wires together renderers and their format-specific sub-formatters.

TLDR:
    RendererFactory.create(render_type, format_type) is the single point of
    construction for all renderers. It maps RenderType (LIST, RAW, TABLE,
    FORMATTED, DIAGRAM, USAGE) x FormatType (ASCII, MD, HTML) to the correct
    renderer/formatter pair, defaulting to ASCII when format_type is omitted.
    Raises ValueError with a helpful message for unimplemented render types.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from typing import Optional

from ..core.match_record import FormatType, RenderType
from .base import Renderer
from .diagram import DiagramRenderer
from .formatted import FormattedRenderer
from .formatters.code_formatters import (
    AsciiCodeFormatter,
    HtmlCodeFormatter,
    MarkdownCodeFormatter,
)
from .formatters.diagram_formatters import (
    MermaidAsciiFormatter,
    MermaidHtmlFormatter,
    MermaidMarkdownFormatter,
)
from .formatters.table_formatters import (
    AsciiTableFormatter,
    HtmlTableFormatter,
    MarkdownTableFormatter,
)
from .formatters.usage_formatters import (
    AsciiUsageFormatter,
    HtmlUsageFormatter,
    MarkdownUsageFormatter,
)
from .json_renderer import JsonRenderer
from .list import ListRenderer
from .raw import RawRenderer
from .table import TableRenderer
from .usage import UsageRenderer

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
        if render_type == RenderType.JSON:
            return JsonRenderer()

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
