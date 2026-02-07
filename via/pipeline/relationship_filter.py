"""Relationship filter data structure for pipeline queries.

Holds the parsed relationship query information: relationship type,
object query parameters, and invert flag.

Author: Neo (SWE)
Sprint: 5, Phase 1.4
"""
from dataclasses import dataclass, field
from typing import List, Optional
from via.core.relationship_types import RelationshipType


@dataclass
class RelationshipFilter:
    """Filter for relationship-based queries.

    Attributes:
        relationship_type: Type of relationship (inherits-from, calls, etc.)
        object_pattern: Pattern to match against object symbols
        object_match_syntax: Match syntax for object pattern (glob, regex, sql)
        object_types: Symbol types to filter object matches
        invert: If True, swap subject/object in the relationship query
    """
    relationship_type: RelationshipType
    object_pattern: str
    object_match_syntax: str = 'glob'
    object_types: List[str] = field(default_factory=list)
    invert: bool = False
