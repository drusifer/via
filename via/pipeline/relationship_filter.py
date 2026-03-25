"""
Data structure carrying the parsed parameters of a relationship query.

TLDR:
    RelationshipFilter is a dataclass attached to a PipelineStage when the
    user specifies a relationship clause (--via or --sans).
    It records the ReferenceType, the object-side pattern and match syntax,
    an optional list of object symbol types to filter on, and is_negative
    which triggers NOT EXISTS execution for --sans queries.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from dataclasses import dataclass, field
from typing import List, Optional

from via.core.relationship_types import ReferenceType


@dataclass
class RelationshipFilter:
    """Filter for relationship-based queries.

    Attributes:
        relationship_type: Type of relationship (inherits-from, calls, etc.)
        object_pattern: Pattern to match against object symbols (AFTER --via/--sans)
        object_match_syntax: Match syntax for object pattern (glob, regex, sql)
        object_types: Symbol types to filter object matches
        is_negative: If True, execute NOT EXISTS query (--sans semantics)
        result_newerthan_seconds: Filter results to symbols newer than N seconds ago
        result_olderthan_seconds: Filter results to symbols older than N seconds ago
        result_stale: If True, filter to stale results (not meaningful with --sans)
    """
    relationship_type: ReferenceType
    object_pattern: str
    object_match_syntax: str = 'glob'
    object_types: List[str] = field(default_factory=list)
    is_negative: bool = False
    result_newerthan_seconds: Optional[float] = None
    result_olderthan_seconds: Optional[float] = None
    result_stale: bool = False
