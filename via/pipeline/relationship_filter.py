"""
Data structure carrying the parsed parameters of a relationship query.

TLDR: Dataclass attached to a PipelineStage to store relationship query parameters for --via and --sans (NOT EXISTS) filters.

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
        filter_pattern: Pattern to match against filter-stage symbols (AFTER --via/--sans)
        filter_match_syntax: Match syntax for filter pattern (glob, regex, sql)
        filter_types: Symbol types to filter matches in the filter stage
        is_negative: If True, execute NOT EXISTS query (--sans semantics)
        inverted: If True, return from the target (to) side of the relationship
        result_newerthan_seconds: Filter results to symbols newer than N seconds ago
        result_olderthan_seconds: Filter results to symbols older than N seconds ago
        result_stale: If True, filter to stale results (not meaningful with --sans)
    """
    relationship_type: ReferenceType
    filter_pattern: str
    filter_match_syntax: str = 'glob'
    filter_types: List[str] = field(default_factory=list)
    is_negative: bool = False
    inverted: bool = False
    result_newerthan_seconds: Optional[float] = None
    result_olderthan_seconds: Optional[float] = None
    result_stale: bool = False
    filter_qualified: bool = False
