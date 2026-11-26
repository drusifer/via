"""Coverage import support for VIA.

TLDR:
    Imports coverage.py's per-test dynamic-context data (produced by
    `pytest --cov-context=test`) into VIA, linking covered symbols to a
    synthetic symbol per test id via `covered-by`. Also imports per-test run
    metadata (status/duration/last-run) written by the project's conftest.py
    into the test_runs table. Replaces the earlier whole-suite `coverage.xml`
    import: `covered-by` now always means "covered by this specific test",
    not "covered by the suite as a whole".
"""

import ast
import json
from pathlib import Path
from typing import Callable, Dict, Iterable, Set
import argparse
import sys

import coverage

from .base import CommandHandlerABC
from .coverage_report import (
    DEFAULT_REPORT_PATH,
    DEFAULT_SLOW_THRESHOLD,
    generate_coverage_report,
)
from via.core.constants import EXIT_ERROR, EXIT_SUCCESS
from via.db.store import DatabaseStore
from via.parsers.dart_parser import DartParser
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.markdown_parser import MarkdownParser
from via.parsers.python_parser import PythonParser
from via.parsers.registry import ParserRegistry

TEST_SYMBOL_FILE_PATH = '<test>'
COVERAGE_ARTIFACT_FILE_PATH = '<coverage>'
TEST_RUNS_JSON_NAME = 'test_runs.json'


def _iter_symbol_ranges(parse_result) -> Iterable[tuple[str, str, str | None, int, int]]:
    """Yield (name, type, parent, start, end) tuples from a parse result."""
    for cls in parse_result.classes:
        yield (cls.name, 'class', None, cls.line_start, cls.line_end)
        for method in cls.methods:
            yield (method.name, 'method', cls.name, method.line_start, method.line_end)
    for func in parse_result.functions:
        yield (func.name, 'function', None, func.line_start, func.line_end)


def _test_id_from_context(context: str) -> str:
    """Strip coverage.py's dynamic-context phase suffix (e.g. '|run') from a context label."""
    return context.rsplit('|', 1)[0]


def _covered_lines_by_test(data_file: str) -> Dict[str, Dict[str, Set[int]]]:
    """Read a coverage.py data file and return test_id -> {rel_path: covered line numbers}.

    Lines recorded under the empty context (module-level execution outside any
    test, e.g. import time) are not attributable to a specific test and are
    skipped.
    """
    cov_data = coverage.CoverageData(basename=data_file)
    cov_data.read()

    by_test: Dict[str, Dict[str, Set[int]]] = {}
    for measured_file in cov_data.measured_files():
        contexts_by_line = cov_data.contexts_by_lineno(measured_file)
        for line_number, contexts in contexts_by_line.items():
            for context in contexts:
                if not context:
                    continue
                test_id = _test_id_from_context(context)
                file_lines = by_test.setdefault(test_id, {})
                file_lines.setdefault(measured_file, set()).add(line_number)
    return by_test


def _func_body_range(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]:
    """Return (start, end) executable body line range, skipping def header & docstring."""
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    end = node.end_lineno or node.lineno
    if not body:
        return (node.lineno, end)
    return (body[0].lineno, end)


def _python_body_ranges(abs_path: Path) -> Dict[tuple[str, str, str | None], tuple[int, int]]:
    """Map Python (name, symbol_type, parent) -> executable body (start, end) lines.

    Prevents import-time `def` header execution (e.g. inside subprocesses or
    lazy imports) from falsely marking uncalled functions/methods as covered.
    """
    if abs_path.suffix not in ('.py', '.pyi'):
        return {}
    try:
        tree = ast.parse(abs_path.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return {}
    ranges: Dict[tuple[str, str, str | None], tuple[int, int]] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ranges[(stmt.name, 'function', None)] = _func_body_range(stmt)
        elif isinstance(stmt, ast.ClassDef):
            for item in stmt.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    ranges[(item.name, 'method', stmt.name)] = _func_body_range(item)
    return ranges


def _link_symbol_tests(
    store: DatabaseStore,
    symbol_id: int,
    start: int,
    end: int,
    tests_lines: Dict[str, Set[int]],
    get_test_symbol: Callable[[str], int],
) -> Set[str]:
    """Insert `covered-by` edges for tests hitting [start, end]; return covering test IDs."""
    covering: Set[str] = set()
    for test_id, lines in tests_lines.items():
        if any(start <= line <= end for line in lines):
            store.insert_relationship(symbol_id, get_test_symbol(test_id), 'covered-by')
            covering.add(test_id)
    return covering


def _link_file_covered_symbols(
    store: DatabaseStore,
    registry: ParserRegistry,
    file_path: str,
    tests_lines: Dict[str, Set[int]],
    get_test_symbol: Callable[[str], int],
) -> int:
    """Parse one file and insert `covered-by` edges for all covered symbols in it."""
    abs_path = Path(file_path).resolve()
    if not abs_path.exists():
        print(f"Warning: coverage path not found in project: {file_path}")
        return 0
    parser = registry.get_parser(str(abs_path))
    if parser is None:
        return 0
    parse_result = parser.parse(str(abs_path), abs_path.read_bytes())
    body_ranges = _python_body_ranges(abs_path)
    classes_with_methods = {cls.name for cls in parse_result.classes if cls.methods}
    class_covered_by: Dict[str, Set[str]] = {}
    deferred_classes: list[tuple[str, int]] = []
    imported = 0

    for name, symbol_type, parent, start, end in _iter_symbol_ranges(parse_result):
        symbol_id = store.get_symbol_id(name, symbol_type, str(abs_path), parent)
        if symbol_id is None:
            continue
        if symbol_type == 'class' and name in classes_with_methods and body_ranges:
            deferred_classes.append((name, symbol_id))
            continue
        match_start, match_end = body_ranges.get((name, symbol_type, parent), (start, end))
        covering = _link_symbol_tests(
            store, symbol_id, match_start, match_end, tests_lines, get_test_symbol
        )
        imported += len(covering)
        if symbol_type == 'method' and parent:
            class_covered_by.setdefault(parent, set()).update(covering)

    for cls_name, symbol_id in deferred_classes:
        for test_id in class_covered_by.get(cls_name, ()):
            store.insert_relationship(symbol_id, get_test_symbol(test_id), 'covered-by')
            imported += 1
    return imported


def _link_covered_symbols(
    store: DatabaseStore,
    registry: ParserRegistry,
    covered_lines_by_test: Dict[str, Dict[str, Set[int]]],
) -> int:
    """Link symbols to the test(s) that cover them via `covered-by` and return the count.

    Iterates by FILE (parsing each exactly once) rather than by test, then
    checks which of that file's covering tests overlap each symbol's line
    range. The naive by-test loop re-parsed every covered file once per test
    (O(tests * files)) — at this project's own scale (1300+ tests) that took
    minutes; this is O(files) parses plus O(files * symbols) get_symbol_id
    lookups, with relationship inserts as the only O(tests * symbols) part,
    which is inherent (one edge per covered symbol-test pair).
    """
    # Invert test_id -> {file: lines} into file -> {test_id: lines}, so each
    # file is parsed once regardless of how many tests cover it.
    lines_by_file_then_test: Dict[str, Dict[str, Set[int]]] = {}
    for test_id, files in covered_lines_by_test.items():
        for file_path, lines in files.items():
            lines_by_file_then_test.setdefault(file_path, {})[test_id] = lines

    test_symbol_ids: Dict[str, int] = {}

    def _test_symbol(test_id: str) -> int:
        if test_id not in test_symbol_ids:
            test_symbol_ids[test_id] = store.insert_symbol(
                symbol_name=test_id,
                symbol_type='test',
                file_path=TEST_SYMBOL_FILE_PATH,
                line_number=0,
                qualified_name=test_id,
                byte_offset=None,
                byte_length=None,
                parent_name=None,
            )
        return test_symbol_ids[test_id]

    imported = 0
    for file_path, tests_lines in lines_by_file_then_test.items():
        imported += _link_file_covered_symbols(
            store, registry, file_path, tests_lines, _test_symbol
        )
    return imported


def _import_test_runs(store: DatabaseStore, root: Path) -> int:
    """Upsert test_runs rows from .via/test_runs.json (written by conftest.py), if present."""
    runs_file = root / ".via" / TEST_RUNS_JSON_NAME
    if not runs_file.exists():
        return 0
    payload = json.loads(runs_file.read_text())
    for test_id, run in payload.items():
        store.upsert_test_run(
            test_id=test_id,
            status=run['status'],
            duration_seconds=run['duration_seconds'],
            last_run_at=run['last_run_at'],
        )
    return len(payload)


def import_contexts(project_root: str, data_path: str) -> int:
    """Import per-test coverage from a coverage.py context data file as `covered-by`.

    Breaking change from the earlier `coverage import <coverage.xml>` command:
    `covered-by` now links to one synthetic symbol per test id instead of one
    blanket suite-level symbol, so callers get per-test attribution. Stale
    data from either the old aggregate import or a previous run of this
    command is cleared first so results never mix old and new semantics.
    Also imports per-test run metadata (status/duration/last-run) from
    .via/test_runs.json if the project's conftest.py wrote one.
    """
    root = Path(project_root).resolve()
    data_file = Path(data_path).resolve()
    db_path = root / ".via" / "index.db"

    if not data_file.exists():
        print(f"Error: Coverage data file not found: {data_file}")
        return EXIT_ERROR
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        return EXIT_ERROR

    covered_lines_by_test = _covered_lines_by_test(str(data_file))

    registry = ParserRegistry()
    registry.register(PythonParser())
    registry.register(MarkdownParser())
    registry.register(JavaScriptParser())
    registry.register(DartParser())

    with DatabaseStore(str(db_path), str(root)) as store:
        store.initialize_schema()

        # Warn (don't block — shrinking the suite or an intentional subset
        # workflow are both legitimate) if this import would replace a much
        # larger previously-tracked set of tests with a much smaller one, so
        # a partial run doesn't silently wipe per-test data for tests that
        # weren't included in *data_path*.
        previous_test_count = store.count_symbols_by_file(TEST_SYMBOL_FILE_PATH)
        new_test_count = len(covered_lines_by_test)
        if previous_test_count > 0 and new_test_count < previous_test_count // 2:
            print(
                f"Warning: this import covers {new_test_count} tests, but "
                f"{previous_test_count} were previously tracked. Continuing "
                "will remove per-test data for tests not in this import. "
                "Re-run against the full suite's coverage file if that "
                "isn't intended."
            )

        # Clean up stale data before writing new results: the old blanket
        # aggregate-coverage symbol (pre-Sprint-27 semantics) and any per-test
        # symbols from a previous run of this command (cascade-deletes their
        # `covered-by` edges via the existing symbol_references FK).
        store.delete_symbols_by_file(COVERAGE_ARTIFACT_FILE_PATH)
        store.delete_symbols_by_file(TEST_SYMBOL_FILE_PATH)
        store.clear_test_runs()

        imported = _link_covered_symbols(store, registry, covered_lines_by_test)

        runs_imported = _import_test_runs(store, root)

    print(f"Imported per-test covered-by relationships: {imported} across {len(covered_lines_by_test)} tests")
    print(f"Imported test run metadata: {runs_imported} tests")
    return EXIT_SUCCESS


class CoverageCommandHandler(CommandHandlerABC):
    """Handler for coverage command."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        coverage_sub = parser.add_subparsers(dest="coverage_command")
        coverage_import = coverage_sub.add_parser(
            "import-contexts",
            help="Import per-test coverage from a coverage.py context data file (e.g. .coverage from pytest --cov-context=test)",
        )
        coverage_import.add_argument(
            "path", nargs="?", default=".coverage",
            help="Path to coverage.py data file (default: .coverage)",
        )
        coverage_report = coverage_sub.add_parser(
            "report",
            help="Generate a standalone HTML test quality report (slow, low-coverage, and overlapping tests)",
        )
        coverage_report.add_argument(
            "-o", "--output", default=DEFAULT_REPORT_PATH,
            help=f"Output HTML file path (default: {DEFAULT_REPORT_PATH})",
        )
        coverage_report.add_argument(
            "--slow-threshold", type=float, default=DEFAULT_SLOW_THRESHOLD,
            help=f"Duration threshold in seconds for slow tests (default: {DEFAULT_SLOW_THRESHOLD})",
        )
        coverage_report.add_argument(
            "--coverage-file", default=".coverage",
            help="Optional coverage.py file for branch-arc overlap analysis (default: .coverage)",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Import per-test coverage data and generate test quality HTML reports"

    def run(self, args: argparse.Namespace) -> int:
        cmd = getattr(args, 'coverage_command', None)
        if cmd == 'import-contexts':
            return import_contexts(str(Path('.').resolve()), args.path)
        if cmd == 'report':
            return generate_coverage_report(
                str(Path('.').resolve()),
                output_path=args.output,
                slow_threshold=args.slow_threshold,
                coverage_file=args.coverage_file,
            )
        print("Error: coverage requires a subcommand", file=sys.stderr)
        return EXIT_ERROR
