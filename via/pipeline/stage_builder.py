"""Shared helpers for constructing executor-facing match stages."""

from __future__ import annotations

from argparse import Namespace
from typing import Optional

from via.core.duration import parse_duration
from via.core.relationship_types import ReferenceType
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
    object_args: Namespace,
    is_negative: bool,
) -> RelationshipFilter:
    """Build a relationship filter from normalized object-side args."""
    finalize_match_namespace(object_args)

    if is_negative and getattr(object_args, 'stale', False):
        raise ValueError("--stale cannot be combined with --sans")

    return RelationshipFilter(
        relationship_type=relationship_type,
        object_pattern=getattr(object_args, 'pattern', None) or '*',
        object_match_syntax=getattr(object_args, 'match_syntax', 'glob'),
        object_types=getattr(object_args, 'symbol_types', None) or [],
        is_negative=is_negative,
        result_newerthan_seconds=(
            parse_duration(object_args.newerthan)
            if getattr(object_args, 'newerthan', None) else None
        ),
        result_olderthan_seconds=(
            parse_duration(object_args.olderthan)
            if getattr(object_args, 'olderthan', None) else None
        ),
        result_stale=getattr(object_args, 'stale', False),
    )


def build_match_stage(
    parsed_args: Namespace,
    relationship: Optional[RelationshipFilter] = None,
    negate_pattern: bool = False,
) -> PipelineStage:
    """Wrap normalized match args as a match pipeline stage."""
    finalize_match_namespace(parsed_args)
    parsed_args.relationship = relationship
    parsed_args.negate_pattern = negate_pattern
    return PipelineStage(StageType.MATCH, parsed_args)
