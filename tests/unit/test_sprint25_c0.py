"""Sprint 25 Cycle 0 tests for Dart tree-sitter dependency viability."""

import pytest

from tree_sitter import Language, Parser

language_pack = pytest.importorskip("tree_sitter_language_pack")


DART_FLUTTER_FIXTURE = b"""
import 'package:flutter/widgets.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Text('Hello');
  }
}
"""


def test_dart_tree_sitter_grammar_loads_and_parses_flutter_style_fixture():
    """Prove the selected dependency can load Dart and parse a Flutter snippet."""
    language = language_pack.get_language("dart")

    assert isinstance(language, Language)

    parser = Parser(language)
    tree = parser.parse(DART_FLUTTER_FIXTURE)

    assert tree.root_node.type == "program"
    assert not tree.root_node.has_error
