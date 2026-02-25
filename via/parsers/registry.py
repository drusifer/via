"""
Parser registry for managing language parsers.

TLDR:
    Provides ParserRegistry for registering and retrieving language parsers.
    Uses extension-based lookup for fast parser selection. Supports global
    singleton pattern via get_global_registry() for application-wide access.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import os
from typing import Dict, List, Optional, Type

from .base import ParserABC


class ParserRegistry:
    """Registry for managing language parsers."""

    def __init__(self):
        """Initialize empty parser registry."""
        self._parsers: List[ParserABC] = []
        self._extension_map: Dict[str, ParserABC] = {}

    def register(self, parser: ParserABC) -> None:
        """
        Register a parser.

        Args:
            parser: Parser instance to register
        """
        self._parsers.append(parser)

        # Build extension map for fast lookup
        for ext in parser.get_supported_extensions():
            self._extension_map[ext.lower()] = parser

    def register_class(self, parser_class: Type[ParserABC]) -> None:
        """
        Register a parser class (instantiates it first).

        Args:
            parser_class: Parser class to instantiate and register
        """
        parser = parser_class()
        self.register(parser)

    def get_parser(self, file_path: str) -> Optional[ParserABC]:
        """
        Get appropriate parser for a file.

        Args:
            file_path: Path to file

        Returns:
            Parser instance if found, None otherwise
        """
        # Try extension-based lookup first (fast)
        _, ext = os.path.splitext(file_path)
        if ext.lower() in self._extension_map:
            return self._extension_map[ext.lower()]

        # Fall back to asking each parser
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser

        return None

    def get_all_parsers(self) -> List[ParserABC]:
        """
        Get all registered parsers.

        Returns:
            List of all parser instances
        """
        return self._parsers.copy()

    def get_supported_extensions(self) -> set:
        """
        Get all supported file extensions.

        Returns:
            Set of all supported extensions
        """
        return set(self._extension_map.keys())
# Global registry instance
_global_registry = ParserRegistry()
def get_global_registry() -> ParserRegistry:
    """
    Get the global parser registry.

    Returns:
        Global ParserRegistry instance
    """
    return _global_registry
def register_parser(parser: ParserABC) -> None:
    """
    Register a parser in the global registry.

    Args:
        parser: Parser instance to register
    """
    _global_registry.register(parser)
def register_parser_class(parser_class: Type[ParserABC]) -> None:
    """
    Register a parser class in the global registry.

    Args:
        parser_class: Parser class to instantiate and register
    """
    _global_registry.register_class(parser_class)
