"""
Reference type definitions for VIA symbol relationships.

TLDR:
    Defines ReferenceType enum covering the five reference kinds stored in
    the database: INHERITS_FROM, CALLS, IMPORTS, REFERENCES, and DECLARES.
    Each member exposes a short CLI flag suffix (e.g. 'inh', 'ca', 'has')
    via properties and class-methods, and helper constructors (from_value,
    from_short_flag) convert between string values, CLI flags, and enum
    members. A module-level _SHORT_FLAGS dict is the single source of truth
    for flag suffix mappings.

    RelationshipType is an alias for ReferenceType (backward compatibility).

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

from enum import Enum


class ReferenceType(Enum):
    """Types of references between symbols.

    Each enum value corresponds to a reference_type stored in the database.
    This is the single source of truth for reference type mappings.
    """
    INHERITS_FROM = 'inherits-from'
    CALLS = 'calls'
    IMPORTS = 'imports'
    REFERENCES = 'references'
    DECLARES = 'declares'        # structural containment (file/class/function declares member)

    @property
    def short_flag(self) -> str:
        """Get the short CLI flag suffix for this reference type."""
        return _SHORT_FLAGS[self]

    @property
    def cli_short(self) -> str:
        """Get full CLI short flag (e.g., '-Vinh')."""
        return f'-V{self.short_flag}'

    @classmethod
    def from_value(cls, value: str) -> 'ReferenceType':
        """Get ReferenceType from its string value (e.g., 'inherits-from')."""
        for rt in cls:
            if rt.value == value:
                return rt
        raise ValueError(f"Unknown reference type: {value}")

    @classmethod
    def from_short_flag(cls, flag: str) -> 'ReferenceType':
        """Get ReferenceType from CLI short flag (e.g., '-Vinh')."""
        # Strip -V prefix if present
        suffix = flag[2:] if flag.startswith('-V') else flag
        for rt, sf in _SHORT_FLAGS.items():
            if sf == suffix:
                return rt
        raise ValueError(f"Unknown relationship flag: {flag}")

    @classmethod
    def get_value_map(cls) -> dict:
        """Get mapping from string values to ReferenceType."""
        return {rt.value: rt for rt in cls}

    @classmethod
    def get_flag_map(cls) -> dict:
        """Get mapping from CLI short flags to ReferenceType."""
        return {rt.cli_short: rt for rt in cls}


# Single source of truth for short flag suffixes
_SHORT_FLAGS = {
    ReferenceType.INHERITS_FROM: 'inh',
    ReferenceType.CALLS: 'ca',
    ReferenceType.IMPORTS: 'imp',
    ReferenceType.REFERENCES: 'r',
    ReferenceType.DECLARES: 'has',
}

# Backward-compatibility alias
RelationshipType = ReferenceType
