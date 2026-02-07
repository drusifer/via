"""
Relationship type definitions for VIA symbol relationships.

TLDR:
    Defines RelationshipType enum for querying symbol relationships such as
    inheritance, calls, imports, and references.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from enum import Enum


class RelationshipType(Enum):
    """Types of relationships between symbols.

    Each enum value corresponds to a relationship type stored in the database.
    This is the single source of truth for relationship type mappings.
    """
    INHERITS_FROM = 'inherits-from'
    CALLS = 'calls'
    IMPORTS = 'imports'
    REFERENCES = 'references'

    @property
    def short_flag(self) -> str:
        """Get the short CLI flag suffix for this relationship type."""
        return _SHORT_FLAGS[self]

    @property
    def cli_short(self) -> str:
        """Get full CLI short flag (e.g., '-Vinh')."""
        return f'-V{self.short_flag}'

    @classmethod
    def from_value(cls, value: str) -> 'RelationshipType':
        """Get RelationshipType from its string value (e.g., 'inherits-from')."""
        for rt in cls:
            if rt.value == value:
                return rt
        raise ValueError(f"Unknown relationship type: {value}")

    @classmethod
    def from_short_flag(cls, flag: str) -> 'RelationshipType':
        """Get RelationshipType from CLI short flag (e.g., '-Vinh')."""
        # Strip -V prefix if present
        suffix = flag[2:] if flag.startswith('-V') else flag
        for rt, sf in _SHORT_FLAGS.items():
            if sf == suffix:
                return rt
        raise ValueError(f"Unknown relationship flag: {flag}")

    @classmethod
    def get_value_map(cls) -> dict:
        """Get mapping from string values to RelationshipType."""
        return {rt.value: rt for rt in cls}

    @classmethod
    def get_flag_map(cls) -> dict:
        """Get mapping from CLI short flags to RelationshipType."""
        return {rt.cli_short: rt for rt in cls}


# Single source of truth for short flag suffixes
_SHORT_FLAGS = {
    RelationshipType.INHERITS_FROM: 'inh',
    RelationshipType.CALLS: 'ca',
    RelationshipType.IMPORTS: 'imp',
    RelationshipType.REFERENCES: 'r',
}
