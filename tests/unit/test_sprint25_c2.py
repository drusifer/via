"""Sprint 25 Cycle 2 tests for Dart relationships and Flutter examples."""

from via.core.discovery import DiscoveredFile
from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore
from via.mcp.schema import build_tool_schema
from via.parsers.dart_parser import DartParser
from via.parsers.registry import ParserRegistry
from via.pipeline.executor import PipelineExecutor
from via.pipeline.parser import PipelineParser
from via.services.indexing import IndexingService


FLUTTER_FIXTURE = b"""
import 'package:flutter/widgets.dart';
part 'details_page.g.dart';

class DetailsPage extends StatefulWidget {
  const DetailsPage({super.key});

  @override
  State<DetailsPage> createState() => _DetailsPageState();
}

class _DetailsPageState extends State<DetailsPage> {
  @override
  Widget build(BuildContext context) {
    return helperWidget();
  }
}

Widget helperWidget() => const Text('Details');
"""


def _index_dart_project(tmp_path, content: bytes = FLUTTER_FIXTURE):
    dart_file = tmp_path / "details_page.dart"
    dart_file.write_bytes(content)
    db_path = tmp_path / "test.db"

    store = DatabaseStore(str(db_path), str(tmp_path))
    store.connect()
    store.initialize_schema()
    registry = ParserRegistry()
    registry.register(DartParser())
    file_info = DiscoveredFile(
        path=str(dart_file),
        size_bytes=dart_file.stat().st_size,
        mtime=dart_file.stat().st_mtime,
        is_parseable=True,
        is_oversized=False,
    )
    IndexingService(store, registry)._index_file(file_info)
    store.resolve_pending_relationships()
    return store


def _execute(store: DatabaseStore, argv: list[str]):
    stages = PipelineParser().parse(argv)
    result = PipelineExecutor(store).execute(stages)
    return list(result) if result is not None else []


def test_flutter_fixture_relationships_are_queryable(tmp_path):
    store = _index_dart_project(tmp_path)
    try:
        subclasses = _execute(
            store,
            ["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "StatefulWidget", "-tc"],
        )
        state_subclasses = _execute(
            store,
            ["-mg", "*", "-tc", "--via", "inherits-from", "-mg", "State", "-tc"],
        )
        callers = _execute(
            store,
            ["-mg", "*", "-tm", "--via", "calls", "-mg", "helperWidget", "-tf"],
        )

        import_targets = {
            row[0]
            for row in store.conn.execute(
                """
                SELECT t.symbol_name
                FROM symbol_references r
                JOIN symbols s ON s.id = r.from_symbol_id
                JOIN symbols t ON t.id = r.to_symbol_id
                WHERE r.reference_type = 'imports'
                  AND s.symbol_type = 'import'
                """
            )
        }
        declared_symbols = {
            row[0]
            for row in store.conn.execute(
                """
                SELECT s.symbol_name
                FROM symbol_references r
                JOIN symbols s ON s.id = r.from_symbol_id
                JOIN symbols t ON t.id = r.to_symbol_id
                WHERE r.reference_type = 'declares'
                  AND t.symbol_name = 'details_page.dart'
                """
            )
        }

        assert [record.symbol_name for record in subclasses] == ["DetailsPage"]
        assert [record.symbol_name for record in state_subclasses] == ["_DetailsPageState"]
        assert [record.symbol_name for record in callers] == ["build"]
        visible_classes = {
            record.symbol_name
            for record in store.match(SymbolType.CLASS, MatchOp.GLOB, "*", limit=0)
        }
        assert "StatefulWidget" not in visible_classes
        assert "State" not in visible_classes
        assert import_targets == {"package:flutter/widgets.dart", "details_page.g.dart"}
        assert {"DetailsPage", "_DetailsPageState", "helperWidget"} <= declared_symbols
    finally:
        store.close()


def test_dart_flutter_docs_and_mcp_examples_are_visible():
    schema = build_tool_schema()
    schema_text = schema["description"]
    example_args = [example["args"] for example in schema["examples"]]

    with open("docs/specs/installation_and_indexing.md", encoding="utf-8") as guide_file:
        guide = guide_file.read()
    with open("README.md", encoding="utf-8") as readme_file:
        readme = readme_file.read()

    assert "Dart" in readme
    assert "`via -mg \"*Screen\" -tc --lang dart`" in guide
    assert "Dart imports, exports, and parts are directive strings" in guide
    assert "does not infer widget trees, route graphs, pub dependencies, or Dart analyzer semantics" in guide
    assert "Dart/Flutter examples:" in schema_text
    assert ["-mg", "*Screen", "-tc", "--lang", "dart"] in example_args
    assert [
        "-mg",
        "*",
        "-tc",
        "--lang",
        "dart",
        "--via",
        "inherits-from",
        "-mg",
        "StatefulWidget",
        "-tc",
    ] in example_args


def test_dart_syntax_error_returns_partial_parse_result():
    result = DartParser().parse(
        "broken.dart",
        b"""
class StillVisible {
  void ok() {}
}

class Broken {
  void bad(
}
""",
    )

    assert result.parse_error is not None
    assert any(cls.name == "StillVisible" for cls in result.classes)
