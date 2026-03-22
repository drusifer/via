"""
Polymorphic MatchRecord system for VIA.

TLDR:
    Defines the MatchRecord abstract dataclass and seven concrete subclasses
    (ClassMatchRecord, MethodMatchRecord, FunctionMatchRecord, FileMatchRecord,
    ImportMatchRecord, GlobalMatchRecord, HeaderMatchRecord), each declaring
    which RenderType values (LIST, TABLE, DIAGRAM, USAGE, RAW, FORMATTED) it
    supports. Also defines the FormatType enum (ASCII, MD, HTML, PNG) and
    MatchRecordFactory, which maps symbol_type strings from database rows to
    the correct subclass and instantiates it with optional rendering metadata.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .interfaces import ArgumentProvider, HelpProvider


class RenderType(Enum):
    """Supported render output types."""
    LIST = 'list'
    TABLE = 'table'
    DIAGRAM = 'diagram'
    USAGE = 'usage'
    RAW = 'raw'
    FORMATTED = 'formatted'
    JSON = 'json'


class FormatType(Enum):
    """Supported output formats."""
    ASCII = 'ascii'
    MD = 'md'
    HTML = 'html'
    PNG = 'png'



@dataclass
class MatchRecord(ABC, ArgumentProvider, HelpProvider):
    """Abstract base class for match records.

    All match records share common fields for symbol data and optional
    rendering metadata. Each subclass implements supports_render_type()
    to declare which render types it can handle.
    """
    # Symbol data fields
    symbol_type: str
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: int
    byte_offset: Optional[int] = None
    byte_length: Optional[int] = None
    parent_name: Optional[str] = None

    # Rendering metadata fields (populated by DatabaseStore)
    column_widths: Optional[Dict[str, int]] = None
    total_matches: Optional[int] = None

    # Temporal fields (Sprint 10 — set by query_relationships for --stale)
    mtime: Optional[float] = None           # this symbol's file mtime at index time
    anchor_mtime: Optional[float] = None    # anchor's mtime (relationship queries only)

    @classmethod
    def add_arguments(cls, parser):
        # Placeholder: to be implemented per record type
        pass

    @classmethod
    def get_help(cls) -> str:
        return getattr(cls, "HELP", f"{cls.__name__}: match record type.")

    def supports_render_type(self, render_type: RenderType) -> bool:
        """JSON is universally supported. Delegate others to subclass."""
        if render_type == RenderType.JSON:
            return True
        return self._supports_render_type(render_type)

    @abstractmethod
    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Subclasses implement type-specific render support."""
        pass

    def __str__(self) -> str:
        """Format as output string with byte position if available."""
        output = f"{self.symbol_type}:{self.file_path}:{self.line_number}:{self.qualified_name}"

        if self.byte_offset is not None:
            output += f":@{self.byte_offset}+{self.byte_length}"

        return output

# Add HELP strings for each record type
@dataclass
class ClassMatchRecord(MatchRecord):
    """Match record for class symbols.

    Classes support all render types including DIAGRAM for inheritance
    visualization.
    """
    HELP = "Class symbol: supports all render types including DIAGRAM for inheritance."
    # Optional lazy-loaded data for diagram rendering
    base_classes: Optional[List[str]] = None
    methods: Optional[List[str]] = None

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Classes support all render types."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.DIAGRAM,
            RenderType.USAGE,
            RenderType.RAW,
            RenderType.FORMATTED,
        }


@dataclass
class MethodMatchRecord(MatchRecord):
    """Match record for method symbols.

    Methods support most render types except DIAGRAM (only classes
    can be shown in inheritance diagrams).
    """
    HELP = "Method symbol: supports all except DIAGRAM."

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Methods support all except DIAGRAM."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW,
            RenderType.FORMATTED,
        }


@dataclass
class FunctionMatchRecord(MatchRecord):
    """Match record for function symbols.

    Functions support most render types except DIAGRAM.
    """
    HELP = "Function symbol: supports all except DIAGRAM."

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Functions support all except DIAGRAM."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW,
            RenderType.FORMATTED,
        }


@dataclass
class FileMatchRecord(MatchRecord):
    """Match record for file path symbols.

    Files have limited render support - no DIAGRAM, USAGE, or FORMATTED
    since they don't contain code symbols.
    """
    HELP = "File path symbol: supports LIST, TABLE, RAW only."

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Files support LIST, TABLE, RAW only."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.RAW,
        }


@dataclass
class ImportMatchRecord(MatchRecord):
    """Match record for import symbols.

    Imports support USAGE to show where they're used but not DIAGRAM
    or FORMATTED.
    """
    HELP = "Import symbol: supports LIST, TABLE, USAGE, RAW."

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Imports support LIST, TABLE, USAGE, RAW."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.USAGE,
            RenderType.RAW,
        }


@dataclass
class GlobalMatchRecord(MatchRecord):
    """Match record for global variable symbols.

    Globals support FORMATTED for syntax highlighting but not DIAGRAM
    or USAGE.
    """
    HELP = "Global variable symbol: supports LIST, TABLE, RAW, FORMATTED."

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Globals support LIST, TABLE, RAW, FORMATTED."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.RAW,
            RenderType.FORMATTED,
        }


@dataclass
class HeaderMatchRecord(MatchRecord):
    """Match record for markdown header symbols.

    Headers support LIST, TABLE, RAW, and FORMATTED for viewing
    markdown content. qualified_name contains the ancestor path
    (e.g., "Guide > Getting Started > Installation").
    """
    HELP = "Markdown header symbol: supports LIST, TABLE, RAW, FORMATTED."
    header_level: int = 1  # 1-6 for h1-h6

    def _supports_render_type(self, render_type: RenderType) -> bool:
        """Headers support LIST, TABLE, RAW, FORMATTED."""
        return render_type in {
            RenderType.LIST,
            RenderType.TABLE,
            RenderType.RAW,
            RenderType.FORMATTED,
        }


class MatchRecordFactory:
    """Factory for creating MatchRecord instances from database rows.

    Maps symbol_type strings to the appropriate MatchRecord subclass.
    """

    _RECORD_TYPES: Dict[str, type] = {
        'class': ClassMatchRecord,
        'method': MethodMatchRecord,
        'function': FunctionMatchRecord,
        'filepath': FileMatchRecord,
        'filename': FileMatchRecord,  # Same as filepath
        'import': ImportMatchRecord,
        'global': GlobalMatchRecord,
        'header': HeaderMatchRecord,
    }

    def create_from_row(
        self,
        row: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MatchRecord:
        """Create a MatchRecord from a database row.

        Args:
            row: Dictionary with symbol data from database
            metadata: Optional rendering metadata (column_widths, total_matches)

        Returns:
            Appropriate MatchRecord subclass instance

        Raises:
            ValueError: If symbol_type is unknown
        """
        symbol_type = row['symbol_type']

        if symbol_type not in self._RECORD_TYPES:
            raise ValueError(f"Unknown symbol type: {symbol_type}")

        record_class = self._RECORD_TYPES[symbol_type]

        # Build kwargs for the record
        kwargs = {
            'symbol_type': row['symbol_type'],
            'symbol_name': row['symbol_name'],
            'qualified_name': row['qualified_name'],
            'file_path': row['file_path'],
            'line_number': row['line_number'],
            'byte_offset': row.get('byte_offset'),
            'byte_length': row.get('byte_length'),
            'parent_name': row.get('parent_name'),
            'mtime': row.get('mtime'),
        }

        # Populate base_classes for class records from the joined base_names column
        if row['symbol_type'] == 'class' and row.get('base_names'):
            kwargs['base_classes'] = row['base_names'].split(',')

        # Add metadata if provided
        if metadata:
            kwargs['column_widths'] = metadata.get('column_widths')
            kwargs['total_matches'] = metadata.get('total_matches')

        return record_class(**kwargs)
