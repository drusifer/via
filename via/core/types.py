"""
Core type definitions for VIA match command.

TLDR:
    Defines SymbolType enum, MatchOp enum, and MatchResult dataclass for the
    denormalized symbols table query system. Simple enums map to SQL operators.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class SymbolType(Enum):
    """Entity types that can be matched in the symbols table.

    Each enum value corresponds directly to a symbol_type value in the database.
    """

    METHOD = 'method'
    CLASS = 'class'
    FUNCTION = 'function'
    FILEPATH = 'filepath'
    FILENAME = 'filename'
    IMPORT = 'import'
    GLOBAL = 'global'
    HEADER = 'header'


class MatchOp(Enum):
    """Match operators that map to SQL operators.

    Each enum provides:
    - op_name: Display name for the operator
    - sql_op: The SQL operator string (=, GLOB, LIKE, REGEXP)
    - needs_escaping: Whether single quotes in patterns need escaping

    Tuple format: (op_name, sql_operator, needs_escaping)
    """

    EXACT = ('exact', '=', True)
    GLOB = ('glob', 'GLOB', True)
    LIKE = ('like', 'LIKE', True)
    REGEXP = ('regexp', 'REGEXP', True)

    def __init__(self, op_name: str, sql_op: str, needs_escaping: bool):
        self.op_name = op_name
        self.sql_op = sql_op
        self.needs_escaping = needs_escaping


@dataclass
class MatchResult:
    """Single match result with complete position information.

    Attributes:
        symbol_type: Entity type (method, class, function, etc.)
        symbol_name: Simple name (e.g., "save", "User")
        qualified_name: Fully qualified name (e.g., "models.user.User.save")
        file_path: Relative file path
        line_number: Starting line number (0 for files)
        byte_offset: File byte offset (None for files without position)
        byte_length: Entity byte length (None for files without position)
        parent_name: Parent class name for methods (None otherwise)
    """

    symbol_type: str
    symbol_name: str
    qualified_name: str
    file_path: str
    line_number: Optional[int]
    byte_offset: Optional[int]
    byte_length: Optional[int]
    parent_name: Optional[str]

    def __str__(self) -> str:
        """Format as output string with byte position if available."""
        output = f"{self.symbol_type}:{self.file_path}:{self.line_number}:{self.qualified_name}"

        # Include byte position if available
        if self.byte_offset is not None:
            output += f":@{self.byte_offset}+{self.byte_length}"

        return output
