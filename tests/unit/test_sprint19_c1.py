"""Sprint 19 Cycle 1 tests — ViaQueryBuilder."""

import pytest

from via import DatabaseStore
from via.api.query_builder import ViaQueryBuilder, ViaRunner
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService
from via.web.api.query import _build_stages


@pytest.fixture
def builder_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    root = str(tmp_path)
    store = DatabaseStore(db_path, root)
    store.connect()
    store.initialize_schema()

    src = tmp_path / "animals.py"
    src.write_text(
        "class Animal:\n"
        "    pass\n"
        "\n"
        "class Dog(Animal):\n"
        "    pass\n"
        "\n"
        "class Cat(Animal):\n"
        "    pass\n"
        "\n"
        "def helper():\n"
        "    return 'ok'\n"
    )

    registry = ParserRegistry()
    registry.register(PythonParser())
    IndexingService(store, registry).index(str(tmp_path))
    yield store
    store.close()


def test_builder_runs_plain_match_query(builder_db):
    query = (
        ViaQueryBuilder()
        .glob("Dog")
        .classes()
        .build()
    )

    results = list(ViaRunner(builder_db).run(query))
    assert [r.symbol_name for r in results] == ["Dog"]


def test_builder_runs_relationship_query(builder_db):
    query = (
        ViaQueryBuilder()
        .glob("Animal")
        .classes()
        .via("inherits-from")
            .glob("*")
            .classes()
        .done()
        .build()
    )

    results = list(ViaRunner(builder_db).run(query))
    names = {r.symbol_name for r in results}
    assert "Dog" in names
    assert "Cat" in names


def test_web_stage_builder_uses_via_query_builder_for_relationship_body():
    stages = _build_stages({
        "match_type": "glob",
        "pattern": "Animal",
        "symbol_types": ["class"],
        "relationship": "inherits-from",
        "target_pattern": "*",
        "target_symbol_types": ["class"],
    })

    assert len(stages) == 1
    assert stages[0].args.pattern == "Animal"
    assert stages[0].args.symbol_types == ["class"]
    assert stages[0].args.relationship is not None
    assert stages[0].args.relationship.relationship_type.value == "inherits-from"
    assert stages[0].args.relationship.object_pattern == "*"
    assert stages[0].args.relationship.object_types == ["class"]
