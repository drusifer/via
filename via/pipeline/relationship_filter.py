"""
Data structure carrying the parsed parameters of a relationship query.

TLDR:
    RelationshipFilter is a dataclass attached to a PipelineStage when the
    user specifies a relationship clause (e.g. -Vinh or --via inherits-from).
    It records the RelationshipType, the object-side pattern and match syntax,
    an optional list of object symbol types to filter on, and an invert flag
    that swaps the subject/object roles so queries can be read in either
    direction ("find what X inherits from" vs. "find what inherits from X").

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
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
        result_newerthan_seconds: Filter results to symbols newer than N seconds ago
        result_olderthan_seconds: Filter results to symbols older than N seconds ago
    """
    relationship_type: RelationshipType
    object_pattern: str
    object_match_syntax: str = 'glob'
    object_types: List[str] = field(default_factory=list)
    invert: bool = False
    result_newerthan_seconds: Optional[float] = None
    result_olderthan_seconds: Optional[float] = None
    result_stale: bool = False
