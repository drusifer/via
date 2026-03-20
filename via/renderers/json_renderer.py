"""
JSON renderer for VIA — outputs match records as a JSON array.

TLDR:
    JsonRenderer.render() consumes an Iterator[MatchRecord] and returns a JSON
    array string. _to_dict() is a static method that converts a single MatchRecord
    to a dict using its public dataclass fields. None values serialize as JSON null.
    Used by MCP server (via_query tool) and the -oJ CLI flag.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
from typing import Iterator

from .base import Renderer
from ..core.match_record import MatchRecord


class JsonRenderer(Renderer):
    """Renders match records as a JSON array."""

    HELP = "JSON array of symbol objects. One object per match."

    def render(self, records: Iterator[MatchRecord], **options) -> str:
        return json.dumps([self._to_dict(r) for r in records], indent=2)

    @staticmethod
    def _to_dict(r: MatchRecord) -> dict:
        return {
            'symbol_name':    r.symbol_name,
            'symbol_type':    r.symbol_type,
            'qualified_name': r.qualified_name,
            'file_path':      r.file_path,
            'line_number':    r.line_number,
            'byte_offset':    r.byte_offset,
            'byte_length':    r.byte_length,
            'parent_name':    r.parent_name,
        }
