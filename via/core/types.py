"""
Core type definitions for the VIA match command.

TLDR:
    Defines two enums used throughout the query layer. SymbolType enumerates
    the entity kinds stored in the symbols table (class, method, function,
    filepath, filename, import, global, header). MatchOp maps user-facing
    match modes to SQL operators (=, GLOB, LIKE, REGEXP); each member carries
    its display name, SQL operator string, and an escaping flag as a tuple.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from enum import Enum


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
