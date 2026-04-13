"""Sprint 22 Cycle 1 tests for structured query errors."""
from __future__ import annotations

import logging

from via.__main__ import _run_pipeline_command
from via.core.constants import EXIT_ERROR
from via.db.store import DatabaseStore
from via.mcp.server import _mcp_query_response
from via.pipeline.errors import PipelineParseError, QueryError
from via.pipeline.parser import PipelineParser


class _FailingRunner:
    def __init__(self, exc: Exception):
        self.exc = exc

    def run_cli_args(self, _args):
        raise self.exc


class _EmptyRunner:
    def run_cli_args(self, _args):
        return []


def test_pipeline_parse_error_carries_structured_fields():
    exc = PipelineParseError(
        "Unknown relationship type 'bogus'.",
        code="invalid_relationship",
        hint="Valid relationship types: calls.",
    )

    assert str(exc) == "Unknown relationship type 'bogus'."
    assert exc.code == "invalid_relationship"
    assert exc.hint == "Valid relationship types: calls."
    assert exc.to_query_error().to_dict() == {
        "code": "invalid_relationship",
        "message": "Unknown relationship type 'bogus'.",
        "hint": "Valid relationship types: calls.",
    }


def test_parser_relationship_error_has_code_and_hint():
    try:
        PipelineParser().parse(["-mg", "*", "-tf", "-V", "bogus", "-mg", "*"])
    except PipelineParseError as exc:
        assert exc.code == "invalid_relationship"
        assert "Valid relationship types" in (exc.hint or "")
    else:
        raise AssertionError("expected PipelineParseError")


def test_mcp_pipeline_parse_error_returns_error_output_type():
    response = _mcp_query_response(
        _FailingRunner(PipelineParseError(
            "Invalid match stage arguments: ['--bad']",
            code="invalid_argument",
            hint="Use supported flags.",
        )),
        ["--bad"],
        logging.getLogger(__name__),
    )

    assert response["output_type"] == "error"
    assert response["result"] == []
    assert response["total"] == 0
    assert response["shown"] == 0
    assert response["error"] == {
        "code": "invalid_argument",
        "message": "Invalid match stage arguments: ['--bad']",
        "hint": "Use supported flags.",
    }


def test_mcp_internal_error_uses_error_output_type(caplog):
    with caplog.at_level(logging.ERROR):
        response = _mcp_query_response(
            _FailingRunner(RuntimeError("boom")),
            ["-mg", "*", "-tf"],
            logging.getLogger(__name__),
        )

    assert response["output_type"] == "error"
    assert response["error"]["code"] == "internal_error"
    assert response["result"] == []
    assert "boom" in caplog.text


def test_mcp_valid_empty_result_keeps_json_shape():
    response = _mcp_query_response(
        _EmptyRunner(),
        ["-mg", "NoSuchSymbol", "-tf"],
        logging.getLogger(__name__),
    )

    assert response == {
        "output_type": "json",
        "result": [],
        "total": 0,
        "shown": 0,
    }


def test_cli_parse_error_prints_hint(tmp_path, capsys):
    index_dir = tmp_path / ".via"
    index_dir.mkdir()
    db_path = index_dir / "index.db"
    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()
    store.close()

    result = _run_pipeline_command(
        ["-mg", "*", "-tf", "-V", "bogus", "-mg", "*"],
        directory=str(tmp_path),
    )

    captured = capsys.readouterr()
    assert result == EXIT_ERROR
    assert "Error: Unknown relationship type 'bogus'." in captured.err
    assert "Hint: Valid relationship types:" in captured.err
