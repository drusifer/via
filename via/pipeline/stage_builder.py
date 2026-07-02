"""Helper utilities to construct normalized match stages and relationship filters.

TLDR:
    Provides construction helper functions for building match stages and filters.
    Key functions: finalize_match_namespace() (normalizes CLI options),
    build_relationship_filter() (builds filters), and build_match_stage()
    (constructs match pipeline stages).
    Role: Builder helper functions. Consumed by parser.py and query_builder.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""

from __future__ import annotations

from argparse import Namespace
from typing import Optional, Sequence, Type

from via.core.duration import parse_duration
from via.core.relationship_types import Relation, ReferenceType
from via.pipeline.relationship_filter import RelationshipFilter
from via.pipeline.types import PipelineStage, StageType


def finalize_match_namespace(parsed_args: Namespace) -> Namespace:
    """Normalize a match namespace to the shape expected by the executor."""
    if hasattr(parsed_args, 'symbol_types') and parsed_args.symbol_types:
        if len(parsed_args.symbol_types) == 1:
            parsed_args.symbol_type = parsed_args.symbol_types[0]
        else:
            parsed_args.symbol_type = None
    else:
        parsed_args.symbol_type = None
        parsed_args.symbol_types = []

    defaults = {
        'relationship': None,
        'relationships': [],
        'negate_pattern': False,
        'line_slice': None,
        'language_filter': None,
        'symbol_subtype_filter': None,
        'contains_pattern': None,
        'render_type': None,
        'format': None,
        'newerthan': None,
        'olderthan': None,
        'after_context': 0,
        'before_context': 0,
        'context': None,
        'theme': None,
        'nodelims': False,
        'stale': False,
        'match_syntax': 'g',
        'pattern': '*',
        'case_insensitive': False,
        'limit': None,
        'result_slice': None,
        'match_qualified': False,
    }
    for key, value in defaults.items():
        if not hasattr(parsed_args, key):
            setattr(parsed_args, key, value)

    return parsed_args


def build_relationship_filter(
    relationship_type: ReferenceType,
    filter_args: Namespace,
    is_negative: bool,
    inverted: bool = False,
) -> RelationshipFilter:
    """Build a relationship filter from normalized filter-side args."""
    finalize_match_namespace(filter_args)

    if is_negative and getattr(filter_args, 'stale', False):
        raise ValueError("--stale cannot be combined with --sans")

    return RelationshipFilter(
        relationship_type=relationship_type,
        filter_pattern=getattr(filter_args, 'pattern', None) or '*',
        filter_match_syntax=getattr(filter_args, 'match_syntax', 'glob'),
        filter_types=getattr(filter_args, 'symbol_types', None) or [],
        is_negative=is_negative,
        inverted=inverted,
        result_newerthan_seconds=(
            parse_duration(filter_args.newerthan)
            if getattr(filter_args, 'newerthan', None) else None
        ),
        result_olderthan_seconds=(
            parse_duration(filter_args.olderthan)
            if getattr(filter_args, 'olderthan', None) else None
        ),
        result_stale=getattr(filter_args, 'stale', False),
        filter_qualified=getattr(filter_args, 'match_qualified', False),
    )


def build_match_stage(
    parsed_args: Namespace,
    relationship: Optional[RelationshipFilter] = None,
    relationships: Optional[Sequence[RelationshipFilter]] = None,
    negate_pattern: bool = False,
) -> PipelineStage:
    """Wrap normalized match args as a match pipeline stage."""
    finalize_match_namespace(parsed_args)
    if relationships is None:
        relationships = [relationship] if relationship is not None else []
    parsed_args.relationships = list(relationships)
    parsed_args.relationship = relationship or (parsed_args.relationships[0] if parsed_args.relationships else None)
    parsed_args.negate_pattern = negate_pattern
    return PipelineStage(StageType.MATCH, parsed_args)
