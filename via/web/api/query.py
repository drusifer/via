"""
POST /api/query handler for the via Web UI.

TLDR:
    run_query() translates a JSON request body into PipelineStage objects,
    executes them via PipelineExecutor, and returns a serialisable dict.
    For list/table formats, results are a list of record dicts. For diagram
    format, results contain a mermaid_source string from DiagramRenderer.
    A fresh DatabaseStore connection is opened per call (Sprint 6 thread-
    safety lesson).

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
import time
from argparse import Namespace
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from via.core.match_record import MatchRecord
from via.pipeline.executor import PipelineExecutor
from via.pipeline.types import PipelineStage, StageType

if TYPE_CHECKING:
    from via.db.store import DatabaseStore

# Map JSON match_type → match_syntax suffix used by PipelineExecutor
_MATCH_SYNTAX = {"glob": "g", "regex": "r", "sql": "s"}

# Map JSON relationship → ReferenceType.value (must match enum string values)
_REL_MAP = {
    "inherits-from": "inherits-from",
    "calls": "calls",
    "imports": "imports",
    "references": "references",
    "has": "declares",
    "declares": "declares",
}


def run_query(db_store: "DatabaseStore", body: Dict[str, Any]) -> dict:
    """Execute a via pipeline query from a JSON request body.

    Args:
        db_store: Connected DatabaseStore instance (fresh per request).
        body: Parsed JSON request body.

    Returns:
        dict with 'results' list or 'mermaid_source', plus 'count',
        'format', and 'elapsed_ms'.
    """
    stages = _build_stages(body)
    executor = PipelineExecutor(db_store)

    start = time.monotonic()
    record_iter = executor.execute(stages)
    records: List[MatchRecord] = list(record_iter or [])
    elapsed_ms = int((time.monotonic() - start) * 1000)

    output_format = body.get("output_format", "list") or "list"

    if output_format == "diagram":
        from via.core.match_record import RenderType
        from via.renderers.factory import RendererFactory
        renderer = RendererFactory.create(RenderType.DIAGRAM)
        mermaid = renderer.render(iter(records))
        return {
            "mermaid_source": mermaid or "",
            "count": len(records),
            "format": "diagram",
            "elapsed_ms": elapsed_ms,
        }

    return {
        "results": [_record_to_dict(r) for r in records],
        "count": len(records),
        "format": output_format,
        "elapsed_ms": elapsed_ms,
    }


def _build_stages(body: Dict[str, Any]) -> List[PipelineStage]:
    """Translate a JSON query body into a list of PipelineStage objects.

    Args:
        body: Parsed JSON request body.

    Returns:
        List of PipelineStage objects ready for PipelineExecutor.
    """
    match_type = body.get("match_type", "glob") or "glob"
    pattern = body.get("pattern", "*") or "*"
    symbol_types: List[str] = body.get("symbol_types") or []
    # limit=0 means "no limit" in the web API; PipelineExecutor treats 0 as "stop after 0"
    # Use a large sentinel value when no limit is requested
    _NO_LIMIT = 100_000
    limit: int = int(body.get("limit") or 0) or _NO_LIMIT
    case_insensitive: bool = bool(body.get("case_insensitive", False))
    qualified: bool = bool(body.get("qualified", False))
    newerthan: Optional[str] = body.get("newerthan") or None
    olderthan: Optional[str] = body.get("olderthan") or None

    relationship_name: Optional[str] = body.get("relationship") or None

    # symbol_type: single value for DB query; symbol_types: list for multi-type OR
    # When multiple types requested, set symbol_type=None so executor uses symbol_types list
    single_type = symbol_types[0] if len(symbol_types) == 1 else None

    args = Namespace(
        pattern=pattern,
        match_syntax=_MATCH_SYNTAX.get(match_type, "g"),
        symbol_types=symbol_types,
        symbol_type=single_type,
        case_insensitive=case_insensitive,
        limit=limit,
        match_qualified=qualified,
        newerthan=newerthan,
        olderthan=olderthan,
        render_type=None,
        relationship=None,
        line_slice=None,
    )

    if relationship_name:
        args.relationship = _build_relationship_filter(body, relationship_name)

    return [PipelineStage(stage_type=StageType.MATCH, args=args)]


def _build_relationship_filter(body: Dict[str, Any], relationship_name: str):
    """Build a RelationshipFilter from the JSON body relationship fields.

    Args:
        body: Parsed JSON request body.
        relationship_name: Relationship type string from body.

    Returns:
        RelationshipFilter instance.
    """
    from via.core.relationship_types import ReferenceType
    from via.pipeline.relationship_filter import RelationshipFilter

    rel_value = _REL_MAP.get(relationship_name, relationship_name)
    target_types: List[str] = body.get("target_symbol_types") or []
    target_pattern: str = body.get("target_pattern") or "*"
    invert: bool = bool(body.get("invert", False))
    stale: bool = bool(body.get("stale", False))

    return RelationshipFilter(
        relationship_type=ReferenceType(rel_value),
        object_pattern=target_pattern,
        object_types=target_types,
        is_negative=invert,
        result_stale=stale,
        result_newerthan_seconds=None,
        result_olderthan_seconds=None,
    )


def _record_to_dict(r: MatchRecord) -> dict:
    """Serialise a MatchRecord to a JSON-compatible dict.

    Args:
        r: MatchRecord instance.

    Returns:
        dict with symbol fields.
    """
    return {
        "symbol_name": r.symbol_name,
        "qualified_name": r.qualified_name,
        "symbol_type": r.symbol_type,
        "file_path": r.file_path,
        "line_number": r.line_number,
    }
