"""
Reference type definitions for VIA symbol relationships.

TLDR: Enumerated types for symbol relationships (inheritance, calls, imports, etc.) used in the VIA database.

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
    COVERED_BY = 'covered-by'
    HTTP_CALLS = 'http-calls'

    @classmethod
    def from_value(cls, value: str) -> 'ReferenceType':
        """Get ReferenceType from its string value (e.g., 'inherits-from')."""
        for rt in cls:
            if rt.value == value:
                return rt
        raise ValueError(f"Unknown reference type: {value}")

    @classmethod
    def get_value_map(cls) -> dict:
        """Get mapping from string values to ReferenceType."""
        return {rt.value: rt for rt in cls}

    @classmethod
    def get_full_value_map(cls) -> dict:
        """Get mapping including both forward and inverse relationship names.

        Returns dict of {name: (ReferenceType, inverted: bool)}.
        """
        forward = {rt.value: (rt, False) for rt in cls}
        # In the database, DECLARES relationship is stored as member (from) -> container (to).
        # Therefore, 'declares' (container --via declares member) targets the 'to' side (inverted=True),
        # while 'declared-in' (member --via declared-in container) targets the 'from' side (inverted=False).
        forward['declares'] = (ReferenceType.DECLARES, True)
        forward.update(_INVERSE_MAP)
        return forward


# Inverse relationship names → (forward ReferenceType, inverted=True)
_INVERSE_MAP = {
    "called-by": (ReferenceType.CALLS, True),
    "inherited-by": (ReferenceType.INHERITS_FROM, True),
    "imported-by": (ReferenceType.IMPORTS, True),
    "referenced-by": (ReferenceType.REFERENCES, True),
    "declared-in": (ReferenceType.DECLARES, False),
    "covers": (ReferenceType.COVERED_BY, True),
    "http-called-by": (ReferenceType.HTTP_CALLS, True),
}

# Backward-compatibility alias
RelationshipType = ReferenceType
