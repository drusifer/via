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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from via.api.query_builder import ViaQueryBuilder, ViaRunner
from via.core.match_record import MatchRecord
from via.pipeline.types import PipelineStage

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
    runner = ViaRunner(db_store)

    start = time.monotonic()
    record_iter = runner.run(_query_from_stages(stages))
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
    return _builder_from_body(body).build().to_stages()


def _apply_subject_options(builder: ViaQueryBuilder, body: Dict[str, Any]) -> None:
    """Apply optional subject-side filters from *body* to *builder* in place."""
    if body.get("case_insensitive", False):
        builder.case_insensitive()
    if body.get("qualified", False):
        builder.qualified()
    if body.get("newerthan"):
        builder.newerthan(body["newerthan"])
    if body.get("olderthan"):
        builder.olderthan(body["olderthan"])
    if body.get("contains"):
        builder.contains(body["contains"])
    if body.get("contains_pattern"):
        builder.contains(body["contains_pattern"])
    if body.get("language_filter"):
        builder.language(body["language_filter"])
    if body.get("symbol_subtype_filter"):
        builder.subtype(body["symbol_subtype_filter"])
    if body.get("negate_pattern", False):
        builder.negate()


def _apply_relationship_options(rel_builder, rel) -> None:
    """Apply optional relationship-side filters from *rel* to *rel_builder* in place."""
    if rel.object_types:
        rel_builder.types(*rel.object_types)
    if rel.result_newerthan_seconds is not None:
        rel_builder.newerthan(str(int(rel.result_newerthan_seconds)))
    if rel.result_olderthan_seconds is not None:
        rel_builder.olderthan(str(int(rel.result_olderthan_seconds)))
    if rel.result_stale:
        rel_builder.stale()


def _builder_from_body(body: Dict[str, Any]) -> ViaQueryBuilder:
    """Translate a JSON body into a ViaQueryBuilder."""
    builder = ViaQueryBuilder()

    match_type = body.get("match_type", "glob") or "glob"
    pattern = body.get("pattern", "*") or "*"
    builder_method = {
        "glob": builder.glob,
        "regex": builder.regex,
        "sql": builder.sql,
    }.get(match_type, builder.glob)
    builder_method(pattern)

    symbol_types: List[str] = body.get("symbol_types") or []
    if symbol_types:
        builder.types(*symbol_types)

    _apply_subject_options(builder, body)

    # limit=0 means "no limit" in the web API; PipelineExecutor treats 0 as "stop after 0"
    # Use a large sentinel value when no limit is requested
    _NO_LIMIT = 100_000
    limit: int = int(body.get("limit") or 0) or _NO_LIMIT
    builder.limit(limit)

    relationship_name: Optional[str] = body.get("relationship") or None
    if relationship_name:
        rel = _build_relationship_filter(body, relationship_name)
        rel_builder = builder.sans(rel.relationship_type) if rel.is_negative else builder.via(rel.relationship_type)
        object_method = {
            "glob": rel_builder.glob,
            "regex": rel_builder.regex,
            "sql": rel_builder.sql,
            "g": rel_builder.glob,
            "r": rel_builder.regex,
            "s": rel_builder.sql,
        }.get(rel.object_match_syntax, rel_builder.glob)
        object_method(rel.object_pattern)
        _apply_relationship_options(rel_builder, rel)
        rel_builder.done()

    return builder


def _query_from_stages(stages: List[PipelineStage]):
    """Wrap builder-produced stages as a query-like object for execution."""
    from via.api.query_builder import ViaQuery

    return ViaQuery(tuple(stages))


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
    invert: bool = body.get("mode") == "sans"
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
