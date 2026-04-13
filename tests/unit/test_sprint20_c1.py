"""Sprint 20 Cycle 1 tests — shared CLI/builder construction seam."""

from via import ViaQueryBuilder
from via.pipeline.parser import PipelineParser


def _stage_signature(stage):
    rel = stage.args.relationship
    rel_sig = None
    if rel is not None:
        rel_sig = (
            rel.relationship_type.value,
            rel.filter_pattern,
            tuple(rel.filter_types or []),
            rel.filter_match_syntax,
            rel.is_negative,
            rel.result_stale,
        )
    return {
        "pattern": stage.args.pattern,
        "match_syntax": stage.args.match_syntax,
        "symbol_types": tuple(stage.args.symbol_types or []),
        "symbol_type": stage.args.symbol_type,
        "case_insensitive": stage.args.case_insensitive,
        "limit": stage.args.limit,
        "result_slice": stage.args.result_slice,
        "match_qualified": stage.args.match_qualified,
        "negate_pattern": stage.args.negate_pattern,
        "language_filter": stage.args.language_filter,
        "symbol_subtype_filter": stage.args.symbol_subtype_filter,
        "contains_pattern": stage.args.contains_pattern,
        "render_type": stage.args.render_type,
        "relationship": rel_sig,
    }


def test_builder_and_parser_share_plain_match_stage_shape():
    parser_stage = PipelineParser()._parse_stage(
        ['-mg', '*Service', '-tc', '-I', '--contains', 'rate_limit', '-n', '20']
    )
    builder_stage = (
        ViaQueryBuilder()
        .glob('*Service')
        .classes()
        .case_insensitive()
        .contains('rate_limit')
        .limit(20)
        .build()
        .to_stages()[0]
    )

    assert _stage_signature(builder_stage) == _stage_signature(parser_stage)


def test_builder_and_parser_share_relationship_stage_shape():
    parser_stage = PipelineParser()._parse_stage(
        ['-mg', '*', '-tc', '--via', 'inherits-from', '-mg', 'Base', '-tc']
    )
    builder_stage = (
        ViaQueryBuilder()
        .glob('*')
        .classes()
        .via('inherits-from')
            .glob('Base')
            .classes()
        .done()
        .build()
        .to_stages()[0]
    )

    assert _stage_signature(builder_stage) == _stage_signature(parser_stage)


def test_top_level_via_exports_builder_api():
    from via import ViaQueryBuilder, ViaRunner

    assert ViaQueryBuilder is not None
    assert ViaRunner is not None
