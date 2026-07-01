"""Coverage import support for VIA.

TLDR:
    Imports `coverage.xml` into VIA by mapping covered lines to indexed symbols
    and storing `covered-by` relationships against a synthetic coverage artifact
    symbol. Keeps the first implementation format-limited and non-destructive.
"""

from pathlib import Path
from typing import Dict, Iterable, Set
import argparse
import sys
from xml.etree import ElementTree as ET  # nosec B405

from .base import CommandHandlerABC
from via.core.constants import EXIT_ERROR, EXIT_SUCCESS
from via.db.store import DatabaseStore
from via.parsers.dart_parser import DartParser
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry


def _iter_symbol_ranges(parse_result) -> Iterable[tuple[str, str, str | None, int, int]]:
    """Yield (name, type, parent, start, end) tuples from a parse result."""
    for cls in parse_result.classes:
        yield (cls.name, 'class', None, cls.line_start, cls.line_end)
        for method in cls.methods:
            yield (method.name, 'method', cls.name, method.line_start, method.line_end)
    for func in parse_result.functions:
        yield (func.name, 'function', None, func.line_start, func.line_end)


def _parse_covered_lines(xml_file: Path) -> Dict[str, Set[int]]:
    """Parse coverage.xml and return a mapping of relative path → covered line numbers."""
    # coverage.xml is a local developer artifact, not arbitrary remote input.
    tree = ET.parse(xml_file)  # nosec B314
    report = tree.getroot()
    covered: Dict[str, Set[int]] = {}
    for class_node in report.findall(".//class"):
        filename = class_node.get("filename")
        if not filename:
            continue
        lines = {
            int(line.get("number"))
            for line in class_node.findall("./lines/line")
            if int(line.get("hits", "0")) > 0
        }
        if lines:
            covered[filename] = covered.get(filename, set()) | lines
    return covered


def _link_covered_symbols(
    store: DatabaseStore,
    registry: ParserRegistry,
    root: Path,
    covered_lines: Dict[str, Set[int]],
    coverage_symbol: int,
) -> int:
    """Link covered symbols to *coverage_symbol* and return the count."""
    imported = 0
    for rel_path, lines in covered_lines.items():
        abs_path = (root / rel_path).resolve()
        if not abs_path.exists():
            print(f"Warning: coverage path not found in project: {rel_path}")
            continue
        parser = registry.get_parser(str(abs_path))
        if parser is None:
            print(f"Warning: unsupported coverage file type: {rel_path}")
            continue
        parse_result = parser.parse(str(abs_path), abs_path.read_bytes())
        for name, symbol_type, parent, start, end in _iter_symbol_ranges(parse_result):
            if not any(start <= line <= end for line in lines):
                continue
            symbol_id = store.get_symbol_id(name, symbol_type, str(abs_path), parent)
            if symbol_id is None:
                continue
            store.insert_relationship(symbol_id, coverage_symbol, 'covered-by')
            imported += 1
    return imported


def import_coverage_xml(project_root: str, xml_path: str) -> int:
    """Import coverage.xml data into the current index as `covered-by`."""
    root = Path(project_root).resolve()
    xml_file = Path(xml_path).resolve()
    db_path = root / ".via" / "index.db"

    if not xml_file.exists():
        print(f"Error: Coverage file not found: {xml_file}")
        return EXIT_ERROR
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        return EXIT_ERROR

    covered_lines = _parse_covered_lines(xml_file)

    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(MarkdownParser())
    registry.register(JavaScriptParser())
    registry.register(DartParser())

    with DatabaseStore(str(db_path), str(root)) as store:
        store.initialize_schema()
        coverage_symbol = store.get_symbol_id(xml_file.name, 'module', '<coverage>', None)
        if coverage_symbol is None:
            coverage_symbol = store.insert_symbol(
                symbol_name=xml_file.name,
                symbol_type='module',
                file_path='<coverage>',
                line_number=0,
                qualified_name=xml_file.name,
                byte_offset=None,
                byte_length=None,
                parent_name=None,
            )
        imported = _link_covered_symbols(store, registry, root, covered_lines, coverage_symbol)

    print(f"Imported covered-by relationships: {imported}")
    return EXIT_SUCCESS


class CoverageCommandHandler(CommandHandlerABC):
    """Handler for coverage command."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        coverage_sub = parser.add_subparsers(dest="coverage_command")
        coverage_import = coverage_sub.add_parser("import", help="Import coverage.xml")
        coverage_import.add_argument("path", help="Path to coverage.xml")

    @classmethod
    def get_help(cls) -> str:
        return "Import test coverage data"

    def run(self, args: argparse.Namespace) -> int:
        if getattr(args, 'coverage_command', None) == 'import':
            return import_coverage_xml(str(Path('.').resolve()), args.path)
        print("Error: coverage requires a subcommand", file=sys.stderr)
        return EXIT_ERROR

