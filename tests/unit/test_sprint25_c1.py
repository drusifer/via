"""Sprint 25 Cycle 1 tests for Dart parser foundation."""

import os
import subprocess
import sys

from via.core.discovery import FileDiscovery
from via.core.path_filter import PathFilter
from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore
from via.parsers.dart_parser import DartParser
from via.mcp.server import _build_registry
from via.parsers.registry import ParserRegistry
from via.services.indexing import IndexingService


DART_FIXTURE = b"""
import 'package:flutter/widgets.dart';
export 'src/public.dart';
part 'home.g.dart';

const appName = 'Via';

mixin Trackable {
  void track() {}
}

enum Role { admin, guest }

extension RoleName on Role {
  String label() => name;
}

class HomeScreen extends StatelessWidget with Trackable implements Widget {
  const HomeScreen({super.key});
  HomeScreen.named();

  @override
  Widget build(BuildContext context) {
    return const Text('Hello');
  }
}

void helper() {}
"""


class TestDartParserFoundation:
    def setup_method(self):
        self.parser = DartParser()

    def test_extensions_and_can_parse(self):
        assert self.parser.get_supported_extensions() == {'.dart'}
        assert self.parser.can_parse("lib/main.dart")
        assert not self.parser.can_parse("lib/main.ts")

    def test_extracts_dart_symbols(self):
        result = self.parser.parse("main.dart", DART_FIXTURE)

        assert result.parse_error is None
        assert result.language == "dart"
        assert [imp.module for imp in result.imports] == [
            "package:flutter/widgets.dart",
            "src/public.dart",
            "home.g.dart",
        ]
        assert {glob.name for glob in result.globals} == {"appName"}
        assert {func.name for func in result.functions} == {"helper"}

        classes = {cls.name: cls for cls in result.classes}
        assert classes["Trackable"].symbol_subtype == "mixin"
        assert classes["Role"].symbol_subtype == "enum"
        assert classes["RoleName"].symbol_subtype == "extension"
        assert classes["HomeScreen"].symbol_subtype is None
        assert classes["HomeScreen"].bases == "StatelessWidget, Trackable, Widget"

        method_names = {method.name for method in classes["HomeScreen"].methods}
        assert {"HomeScreen", "HomeScreen.named", "build"} <= method_names
        constructor = next(m for m in classes["HomeScreen"].methods if m.name == "HomeScreen")
        assert constructor.symbol_subtype == "constructor"


class TestDartDiscoveryAndIndexing:
    def test_flutter_default_excludes(self, tmp_path):
        (tmp_path / "pubspec.yaml").write_text("name: via_fixture\n", encoding="utf-8")
        pf = PathFilter(root_dir=str(tmp_path), respect_gitignore=False)

        for dirname in [".dart_tool", "build"]:
            (tmp_path / dirname).mkdir()
            assert not pf.should_include_dir(str(tmp_path), dirname)

        android = tmp_path / "android"
        ios = tmp_path / "ios"
        android.mkdir()
        ios.mkdir()
        assert not pf.should_include_dir(str(android), ".gradle")
        assert not pf.should_include_dir(str(ios), "Pods")

    def test_discovery_marks_dart_parseable(self, tmp_path):
        (tmp_path / "main.dart").write_text("void main() {}", encoding="utf-8")
        (tmp_path / "README.txt").write_text("notes", encoding="utf-8")

        registry = ParserRegistry()
        registry.register(DartParser())
        discovery = FileDiscovery(
            root_dir=str(tmp_path),
            parseable_extensions=registry.get_supported_extensions(),
        )

        discovered = {os.path.basename(f.path): f for f in discovery.discover()}
        assert discovered["main.dart"].is_parseable is True
        assert discovered["README.txt"].is_parseable is False

    def test_indexed_dart_symbols_are_language_filterable(self, tmp_path):
        dart_file = tmp_path / "main.dart"
        dart_file.write_bytes(DART_FIXTURE)
        db_path = tmp_path / "test.db"

        store = DatabaseStore(str(db_path), str(tmp_path))
        store.connect()
        store.initialize_schema()
        try:
            registry = ParserRegistry()
            registry.register(DartParser())
            IndexingService(store, registry).index(str(tmp_path))

            files = list(store.match(
                SymbolType.FILEPATH,
                MatchOp.GLOB,
                "*",
                language="dart",
                limit=0,
            ))
            classes = list(store.match(
                SymbolType.CLASS,
                MatchOp.GLOB,
                "*Screen",
                language="dart",
                limit=0,
            ))
            constructors = list(store.match(
                SymbolType.METHOD,
                MatchOp.GLOB,
                "HomeScreen*",
                language="dart",
                subtype="constructor",
                limit=0,
            ))

            assert [f.symbol_name for f in files] == ["main.dart"]
            assert [cls.symbol_name for cls in classes] == ["HomeScreen"]
            assert {ctor.symbol_name for ctor in constructors} == {
                "HomeScreen",
                "HomeScreen.named",
            }
        finally:
            store.close()

    def test_mcp_registry_resolves_dart_parser(self):
        registry = _build_registry()

        assert isinstance(registry.get_parser("lib/main.dart"), DartParser)

    def test_cli_index_registers_dart_parser(self, tmp_path):
        (tmp_path / "main.dart").write_bytes(DART_FIXTURE)

        index_result = subprocess.run(
            [sys.executable, "-m", "via", "index", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert index_result.returncode == 0, index_result.stderr

        query_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "via",
                "-mg",
                "*Screen",
                "-tc",
                "--lang",
                "dart",
                "-oJ",
            ],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert query_result.returncode == 0, query_result.stderr
        assert "HomeScreen" in query_result.stdout
