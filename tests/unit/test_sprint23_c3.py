"""Sprint 23 Cycle 3 tests for MCP diagram fallback payloads."""
from __future__ import annotations

import logging

import pytest

from via.api import ViaRunner
from via.db.store import DatabaseStore
from via.mcp.server import _mcp_query_response
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


@pytest.fixture()
def diagram_store(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        "class Alpha:\n"
        "    pass\n\n"
        "class Beta(Alpha):\n"
        "    pass\n\n"
        "def helper():\n"
        "    return 1\n"
    )
    store = DatabaseStore(str(tmp_path / "index.db"), str(tmp_path))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(PythonParser())
    IndexingService(store, registry).index(str(tmp_path))
    try:
        yield store
    finally:
        store.close()


def test_diagram_fallback_preserves_json_results_for_unsupported_shape(diagram_store):
    response = _mcp_query_response(
        ViaRunner(diagram_store),
        ["-mg", "helper", "-tf", "-oD"],
        logging.getLogger(__name__),
    )

    assert response["output_type"] == "json"
    assert response["shown"] == 1
    assert response["total"] == 1
    assert response["result"][0]["symbol_name"] == "helper"
    assert "returning matching records as JSON" in response["note"]


def test_empty_diagram_fallback_keeps_empty_json_shape(diagram_store):
    response = _mcp_query_response(
        ViaRunner(diagram_store),
        ["-mg", "NoSuchClass", "-tc", "-oD"],
        logging.getLogger(__name__),
    )

    assert response["output_type"] == "json"
    assert response["result"] == []
    assert response["total"] == 0
    assert response["shown"] == 0
    assert "empty JSON results" in response["note"]


def test_valid_diagram_response_remains_diagram_output(diagram_store):
    response = _mcp_query_response(
        ViaRunner(diagram_store),
        ["-mg", "*", "-tc", "-oD"],
        logging.getLogger(__name__),
    )

    assert response["output_type"] == "diagram"
    assert isinstance(response["result"], str)
    assert "classDiagram" in response["result"]
    assert "Alpha" in response["result"]
