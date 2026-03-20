"""
Renderer system for VIA output formatting.

TLDR:
    Re-exports the public renderer API: the Renderer base class, RendererFactory
    for selecting a renderer by output type, and the four concrete renderers
    (ListRenderer, TableRenderer, RawRenderer, FormattedRenderer).

"""

from .base import Renderer
from .factory import RendererFactory
from .formatted import FormattedRenderer
from .list import ListRenderer
from .raw import RawRenderer
from .table import TableRenderer

__all__ = [
    'Renderer', 'RendererFactory', 'ListRenderer', 'TableRenderer',
    'RawRenderer', 'FormattedRenderer'
]
