"""
VIA - Python codebase indexing and querying CLI tool.

TLDR:
    Top-level package that re-exports the complete public API for the VIA
    indexing system. Exported symbols include: DatabaseStore (SQLite persistence),
    FileDiscovery and DiscoveredFile (filesystem crawling), ParserABC and
    ParseResult (parser contracts), entity dataclasses (FunctionEntity,
    ClassEntity, ImportEntity, GlobalEntity, LogStatementEntity,
    MarkdownHeadingEntity), and ParserRegistry / get_global_registry / PythonParser
    for language-specific parsing. Import from here rather than internal modules.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

__version__ = "0.1.0"

# Public API exports - Database layer
# Public API exports - Core
from .core.discovery import DiscoveredFile, FileDiscovery
from .db.store import DatabaseStore

# Public API exports - Parsers
from .parsers.base import (
    ClassEntity,
    FunctionEntity,
    GlobalEntity,
    ImportEntity,
    LogStatementEntity,
    MarkdownHeadingEntity,
    ParserABC,
    ParseResult,
)
from .parsers.python_parser import PythonParser
from .parsers.registry import ParserRegistry, get_global_registry

__all__ = [
    # Version
    "__version__",
    # Database
    "DatabaseStore",
    # Parser base classes and entities
    "ParserABC",
    "ParseResult",
    "FunctionEntity",
    "ClassEntity",
    "ImportEntity",
    "GlobalEntity",
    "LogStatementEntity",
    "MarkdownHeadingEntity",
    # Parser registry
    "ParserRegistry",
    "get_global_registry",
    "PythonParser",
    # File discovery
    "FileDiscovery",
    "DiscoveredFile",
]
