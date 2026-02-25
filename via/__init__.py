"""
VIA - Python codebase indexing and querying CLI tool.

TLDR:
    Main package exposing public API for VIA indexing system. Provides access
    to database layer (DatabaseStore), parsers (PythonParser, ParserRegistry),
    file discovery (FileDiscovery), and entity dataclasses for code elements.

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
