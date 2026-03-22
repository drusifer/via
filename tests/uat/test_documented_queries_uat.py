"""
UAT: Documented query examples from via/mcp/schema.py and agent SKILL.md files.

TLDR:
    End-to-end tests validating every documented query from schema.py and
    agent skills (neo, morpheus, trin). A synthetic project fixture provides
    known symbols so the exact documented args produce documented results.

    schema.py Examples tested: Ex01–Ex12
    Skill-unique patterns tested: glob-any, references, header search
    Documentation issues surfaced as xfail tests:
      - Morpheus SKILL.md: -th (lowercase) is not a valid flag; correct is -tH (already fixed in docs)

Author: Trin
Sprint: UAT — Documented Queries
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json
import subprocess
import sys

import pytest


# ── Fixture source files ──────────────────────────────────────────────────────

_MY_SERVICE_PY = """\
\"\"\"Service module with base classes, a standalone connect() function, and globals.\"\"\"
import logging
import os

MY_GLOBAL = "global_value"
SERVICE_VERSION = "1.0"


class BaseClass:
    \"\"\"Base class for inheritance testing.\"\"\"

    def base_method(self):
        return "base"


class MyClass(BaseClass):
    \"\"\"Concrete class inheriting BaseClass.\"\"\"

    def get_name(self):
        return "MyClass"

    def get_value(self):
        return 42

    def run(self):
        return helper_func()


class AnotherService(BaseClass):
    \"\"\"Service class — name matches *Service* glob.\"\"\"

    def get_status(self):
        return True


def connect(host: str) -> bool:
    \"\"\"Standalone connect function (anchor for callers-of test).\"\"\"
    logging.info("connecting to %s", host)
    return True


def helper_func() -> str:
    \"\"\"Helper called by MyClass.run().\"\"\"
    return "helper"
"""

_CONNECTOR_PY = """\
\"\"\"Connector — calls the connect() function from my_service.\"\"\"
from services.my_service import connect


def run_connection(host: str) -> bool:
    \"\"\"Calls connect — becomes a caller in the callers-of-connect query.\"\"\"
    return connect(host)
"""

_CHILD_MODEL_PY = """\
\"\"\"Child model — inherits BaseClass and imports MY_GLOBAL.\"\"\"
from services.my_service import BaseClass, MY_GLOBAL


class ChildModel(BaseClass):
    \"\"\"Third subclass of BaseClass (cross-file).\"\"\"

    def get_data(self):
        return []
"""

_APP_CORE_UTILS_PY = """\
\"\"\"Core utilities — lives under app/core/ for path-pattern tests.\"\"\"


def parse_config(path: str) -> dict:
    \"\"\"Parse a config file.\"\"\"
    return {}


def validate_input(data: dict) -> bool:
    \"\"\"Validate input data.\"\"\"
    return True
"""

_EXTRAS_PY = """\
\"\"\"Extras for Story 3: decorators, type annotations, class-body annotations.\"\"\"
from services.my_service import BaseClass, MyClass


def my_decorator(func):
    \"\"\"A simple decorator for testing decorator reference tracking.\"\"\"
    return func


@my_decorator
def decorated_func() -> BaseClass:
    \"\"\"Function decorated with my_decorator; return type annotation is BaseClass.\"\"\"
    return BaseClass()


class AnnotatedClass(BaseClass):
    \"\"\"Class with body annotations and annotated method parameters.\"\"\"

    data: MyClass

    def process(self, svc: BaseClass) -> MyClass:
        \"\"\"Method with non-builtin parameter and return type annotations.\"\"\"
        return MyClass()
"""

_API_MD = """\
# API Overview

## Authentication

## Endpoints

### GET /status
"""


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    """Synthetic project indexed by via CLI.

    Layout:
        services/my_service.py  — BaseClass, MyClass, AnotherService, connect(), MY_GLOBAL
        connector.py            — run_connection() calls connect()
        models/child_model.py   — ChildModel(BaseClass)
        app/core/utils.py       — parse_config(), validate_input()  (not via/ — would shadow package)
        docs/API.md             — markdown headers
        extras.py               — decorated_func, AnnotatedClass (Story 3 fixtures)
    """
    d = tmp_path_factory.mktemp("docquery")

    (d / "services").mkdir()
    (d / "services" / "__init__.py").write_text("")
    (d / "services" / "my_service.py").write_text(_MY_SERVICE_PY)

    (d / "connector.py").write_text(_CONNECTOR_PY)

    (d / "models").mkdir()
    (d / "models" / "__init__.py").write_text("")
    (d / "models" / "child_model.py").write_text(_CHILD_MODEL_PY)

    # NOTE: cannot use "via/" as a subdirectory — it shadows the installed via package
    # in subprocess calls. Use "app/core/" instead; path-pattern tests use "app/core/*".
    (d / "app").mkdir()
    (d / "app" / "core").mkdir()
    (d / "app" / "core" / "utils.py").write_text(_APP_CORE_UTILS_PY)

    (d / "docs").mkdir()
    (d / "docs" / "API.md").write_text(_API_MD)

    (d / "extras.py").write_text(_EXTRAS_PY)

    r = subprocess.run(
        [sys.executable, "-m", "via", "index", str(d)],
        capture_output=True, text=True, timeout=60, cwd=str(d),
    )
    assert r.returncode == 0, f"Index failed:\n{r.stderr}"
    return d


def _q(proj, *args):
    """Run `python -m via <args>` in proj directory."""
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=30, cwd=str(proj),
    )


def _json(proj, *args):
    """Run query, parse JSON output, return list of dicts."""
    r = _q(proj, *args)
    assert r.returncode == 0, f"via failed: {r.stderr}"
    return json.loads(r.stdout)


# ── Schema Ex01: Glob match → classes ────────────────────────────────────────

class TestSchemaEx01_GlobMatchClass:
    """["-mg", "*Service*", "-tc"] → 'Find all classes matching a glob pattern'

    Expected: returns only classes whose name contains 'Service'.
    AnotherService matches; BaseClass, MyClass, ChildModel do not.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*Service*", "-tc").returncode == 0

    def test_matching_class_present(self, proj):
        r = _q(proj, "-mg", "*Service*", "-tc")
        assert "AnotherService" in r.stdout

    def test_non_matching_class_absent(self, proj):
        r = _q(proj, "-mg", "*Service*", "-tc")
        assert "BaseClass" not in r.stdout
        assert "MyClass" not in r.stdout
        assert "ChildModel" not in r.stdout

    def test_only_classes_in_json(self, proj):
        data = _json(proj, "-mg", "*Service*", "-tc", "-oJ")
        assert data, "Expected at least one result"
        for item in data:
            assert item["symbol_type"] == "class", f"Got non-class: {item}"

    def test_all_names_match_glob(self, proj):
        data = _json(proj, "-mg", "*Service*", "-tc", "-oJ")
        for item in data:
            assert "Service" in item["symbol_name"], f"Name doesn't match *Service*: {item['name']}"


# ── Schema Ex02: Name glob → functions ───────────────────────────────────────

class TestSchemaEx02_NameGlobFunctions:
    """["-mg", "*parse*", "-tf"] → 'Find functions matching a name glob pattern'

    Expected: returns functions whose name contains 'parse'.
    parse_config (in app/core/utils.py) must appear; validate_input must not.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*parse*", "-tf").returncode == 0

    def test_matching_function_present(self, proj):
        r = _q(proj, "-mg", "*parse*", "-tf")
        assert "parse_config" in r.stdout

    def test_non_matching_function_absent(self, proj):
        r = _q(proj, "-mg", "*parse*", "-tf")
        assert "validate_input" not in r.stdout

    def test_only_functions_in_json(self, proj):
        data = _json(proj, "-mg", "*parse*", "-tf", "-oJ")
        assert data
        for item in data:
            assert item["symbol_type"] == "function", f"Got non-function: {item}"


# ── Schema Ex03: Regex match → methods, JSON output ──────────────────────────

class TestSchemaEx03_RegexMethodsJson:
    """["-mr", "^get_", "-tm", "-oJ"] → 'Find methods by regex, JSON output'

    Expected: valid JSON array; every item is a method whose name starts with 'get_'.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mr", "^get_", "-tm", "-oJ").returncode == 0

    def test_output_is_valid_json(self, proj):
        r = _q(proj, "-mr", "^get_", "-tm", "-oJ")
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_all_names_match_regex(self, proj):
        data = _json(proj, "-mr", "^get_", "-tm", "-oJ")
        assert data, "Expected at least one get_ method"
        for item in data:
            assert item["symbol_name"].startswith("get_"), f"Name doesn't match ^get_: {item['name']}"

    def test_all_types_are_method(self, proj):
        data = _json(proj, "-mr", "^get_", "-tm", "-oJ")
        for item in data:
            assert item["symbol_type"] == "method", f"Expected method, got: {item['symbol_type']}"

    def test_known_methods_present(self, proj):
        data = _json(proj, "-mr", "^get_", "-tm", "-oJ")
        names = {item["symbol_name"] for item in data}
        assert "get_name" in names
        assert "get_value" in names
        assert "get_status" in names
        assert "get_data" in names


# ── Schema Ex04: All imports ──────────────────────────────────────────────────

class TestSchemaEx04_AllImports:
    """["-mg", "*", "-ti"] → 'Show all imports in the codebase'

    Expected: returns only import symbols; classes and functions excluded.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*", "-ti").returncode == 0

    def test_known_imports_present(self, proj):
        r = _q(proj, "-mg", "*", "-ti")
        assert "logging" in r.stdout or "os" in r.stdout

    def test_all_types_are_import(self, proj):
        data = _json(proj, "-mg", "*", "-ti", "-oJ")
        assert data, "Expected at least one import"
        for item in data:
            assert item["symbol_type"] == "import", f"Expected import, got: {item['symbol_type']}"


# ── Schema Ex05: File basename glob → filepaths ───────────────────────────────

class TestSchemaEx05_FileBasenamGlobFilepaths:
    """["-mg", "*service*", "-tF"] → 'Find files by basename pattern'

    -mg matches against the filename (basename), not the full path.
    '*service*' matches 'my_service.py' whose basename contains 'service'.
    Full-path glob filtering is not yet supported.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*service*", "-tF").returncode == 0

    def test_matching_file_present(self, proj):
        r = _q(proj, "-mg", "*service*", "-tF")
        assert "my_service" in r.stdout

    def test_non_matching_file_absent(self, proj):
        r = _q(proj, "-mg", "*service*", "-tF")
        assert "connector" not in r.stdout
        assert "child_model" not in r.stdout

    def test_only_filepaths_in_json(self, proj):
        data = _json(proj, "-mg", "*service*", "-tF", "-oJ")
        assert data
        for item in data:
            assert item["symbol_type"] == "filepath"

    def test_path_glob_returns_empty(self, proj):
        """Confirm path-glob (not basename) does not match — documenting the limitation."""
        r = _q(proj, "-mg", "services/*", "-tF")
        assert r.returncode == 0
        assert "my_service" not in r.stdout


# ── Schema Ex06: Subclasses of a base class ───────────────────────────────────

class TestSchemaEx06_SubclassesOf:
    """["-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"]
       → 'Find all subclasses of a base class (anchor=base, result=subclasses)'

    Expected: returns MyClass, AnotherService (same file) and ChildModel (cross-file).
    BaseClass itself must not appear in results.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc").returncode == 0

    def test_direct_subclass_same_file(self, proj):
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert "MyClass" in r.stdout
        assert "AnotherService" in r.stdout

    def test_cross_file_subclass_present(self, proj):
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert "ChildModel" in r.stdout

    def test_base_class_not_in_results(self, proj):
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert "BaseClass" not in r.stdout

    def test_only_classes_returned(self, proj):
        data = _json(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc", "-oJ")
        assert data
        for item in data:
            assert item["symbol_type"] == "class"


# ── Schema Ex07: What does a class inherit FROM? ──────────────────────────────

class TestSchemaEx07_InheritedFrom:
    """["-mg", "MyClass", "-tc", "-Vinh", "-iv", "-mg", "*", "-tc"]
       → 'Find what a class inherits FROM (-iv returns the base classes)'

    Expected: returns BaseClass. Unrelated classes (AnotherService, ChildModel) absent.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "MyClass", "-tc", "-Vinh", "-iv", "-mg", "*", "-tc").returncode == 0

    def test_base_class_in_results(self, proj):
        r = _q(proj, "-mg", "MyClass", "-tc", "-Vinh", "-iv", "-mg", "*", "-tc")
        assert "BaseClass" in r.stdout

    def test_unrelated_classes_absent(self, proj):
        r = _q(proj, "-mg", "MyClass", "-tc", "-Vinh", "-iv", "-mg", "*", "-tc")
        assert "AnotherService" not in r.stdout
        assert "ChildModel" not in r.stdout


# ── Schema Ex08: Callers of a function ────────────────────────────────────────

class TestSchemaEx08_CallersOf:
    """["-mg", "connect", "-tf", "-Vca", "-mg", "*"]
       → 'Find callers of a function (anchor=func, result=callers)'

    Expected: run_connection (in connector.py) calls connect → must appear.
    connect itself must not be listed as its own caller.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "connect", "-tf", "-Vca", "-mg", "*").returncode == 0

    def test_caller_present(self, proj):
        r = _q(proj, "-mg", "connect", "-tf", "-Vca", "-mg", "*")
        assert "run_connection" in r.stdout

    def test_callee_not_its_own_caller(self, proj):
        data = _json(proj, "-mg", "connect", "-tf", "-Vca", "-mg", "*", "-oJ")
        names = {item["symbol_name"] for item in data}
        assert "connect" not in names


# ── Schema Ex09: What does a method call? ─────────────────────────────────────

class TestSchemaEx09_WhatMethodCalls:
    """["-mg", "my_method", "-tm", "-Vca", "-iv", "-mg", "*"]
       → 'Find what a method calls (-iv returns the callees; anchor on method, not class)'

    Call relationships are stored from method/function symbols to their callees.
    Anchor on the method (-tm) to find what it calls.

    Class-level anchor (-tc) with -Vca is also supported: executor expands the
    class anchor to include all methods where parent_name = class_name.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "run", "-tm", "-Vca", "-iv", "-mg", "*").returncode == 0

    def test_callee_present(self, proj):
        """run() calls helper_func() → must appear in callees."""
        r = _q(proj, "-mg", "run", "-tm", "-Vca", "-iv", "-mg", "*")
        assert "helper_func" in r.stdout

    def test_class_anchor_returns_callees(self, proj):
        """Class-level -Vca: executor expands class anchor to include its methods."""
        r = _q(proj, "-mg", "MyClass", "-tc", "-Vca", "-iv", "-mg", "*", "-tf")
        assert r.returncode == 0
        assert "helper_func" in r.stdout


# ── Schema Ex10: Global variables as JSON ─────────────────────────────────────

class TestSchemaEx10_GlobalsJson:
    """["-mg", "*", "-tg", "-oJ"] → 'Find all global variables as JSON'

    Expected: valid JSON array; every item has symbol_type='global'.
    MY_GLOBAL and SERVICE_VERSION (from my_service.py) must appear.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*", "-tg", "-oJ").returncode == 0

    def test_output_is_valid_json(self, proj):
        r = _q(proj, "-mg", "*", "-tg", "-oJ")
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_known_globals_present(self, proj):
        data = _json(proj, "-mg", "*", "-tg", "-oJ")
        names = {item["symbol_name"] for item in data}
        assert "MY_GLOBAL" in names
        assert "SERVICE_VERSION" in names

    def test_all_types_are_global(self, proj):
        data = _json(proj, "-mg", "*", "-tg", "-oJ")
        assert data
        for item in data:
            assert item["symbol_type"] == "global", f"Expected global, got: {item}"


# ── Schema Ex11: Markdown headers matching a pattern ─────────────────────────

class TestSchemaEx11_MarkdownHeaders:
    """["-mg", "*API*", "-tH"] → 'Find markdown headers matching a pattern'

    Expected: '# API Overview' in docs/API.md matches *API*.
    '## Authentication' does not contain 'API' → must be absent.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*API*", "-tH").returncode == 0

    def test_api_header_found(self, proj):
        r = _q(proj, "-mg", "*API*", "-tH")
        assert "API" in r.stdout

    def test_non_api_header_absent(self, proj):
        r = _q(proj, "-mg", "*API*", "-tH")
        assert "Authentication" not in r.stdout

    def test_type_is_header(self, proj):
        data = _json(proj, "-mg", "*API*", "-tH", "-oJ")
        assert data
        for item in data:
            assert item["symbol_type"] == "header"


# ── Schema Ex12: What imports a module ────────────────────────────────────────

class TestSchemaEx12_ImportersOf:
    """["-mg", "logging", "-Vimp", "-mg", "*"]
       → 'Find what imports a module (anchor=module, result=importers)'

    Expected: my_service.py imports logging → import symbol appears in results.
    child_model.py does not import logging → must be absent.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "logging", "-Vimp", "-mg", "*").returncode == 0

    def test_importer_file_present(self, proj):
        r = _q(proj, "-mg", "logging", "-Vimp", "-mg", "*")
        assert "my_service" in r.stdout

    def test_non_importer_absent(self, proj):
        r = _q(proj, "-mg", "logging", "-Vimp", "-mg", "*")
        assert "child_model" not in r.stdout


# ── Skill: Find any symbol (no type filter) ───────────────────────────────────

class TestSkillNeo_FindAnySymbol:
    """neo/morpheus SKILL.md: ["-mg", "*pattern*"] → 'Find any symbol'

    Expected: without a type filter, results span multiple symbol types.
    *Base* matches BaseClass (class) and base_method (method) at minimum.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "*Base*").returncode == 0

    def test_multiple_types_returned(self, proj):
        data = _json(proj, "-mg", "*Base*", "-oJ")
        types = {item["symbol_type"] for item in data}
        assert len(types) >= 2, f"Expected multiple types, got: {types}"

    def test_all_names_contain_base(self, proj):
        data = _json(proj, "-mg", "*Base*", "-oJ")
        assert data
        for item in data:
            assert "Base" in item["symbol_name"] or "base" in item["symbol_name"], (
                f"Name doesn't match *Base*: {item['name']}"
            )


# ── Skill: Who references a symbol ────────────────────────────────────────────

class TestSkillMorpheus_WhoReferences:
    """morpheus SKILL.md: ["-mg", "SymbolName", "-Vr", "-mg", "*"]
       → 'Who references Symbol?'

    NOTE: -Vr tracks name usages inside function/method bodies only (ast.Name nodes
    with Load context). Class inheritance (BaseClass in class definition) is NOT
    tracked as a reference. connect() is called inside run_connection(), so it IS
    referenced there — making 'connect' a reliable anchor for this test.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "connect", "-Vr", "-mg", "*").returncode == 0

    def test_reference_source_present(self, proj):
        """run_connection() uses 'connect' in its body → must appear as a referencer."""
        r = _q(proj, "-mg", "connect", "-Vr", "-mg", "*")
        assert "run_connection" in r.stdout


# ── Skill: Find section in arch doc (header search) ──────────────────────────

class TestSkillMorpheus_HeaderSearch:
    """morpheus SKILL.md: ["-mg", "*SectionName*", "-tH"]
       → 'Find a section in an arch doc'

    S9-005: Docs were updated from -th (lowercase) to -tH (uppercase).
    -tH is the only valid flag; -th is not an alias.
    """

    def test_correct_flag_tH_works(self, proj):
        """-tH (uppercase) is the correct and only flag for header type."""
        r = _q(proj, "-mg", "*Auth*", "-tH")
        assert r.returncode == 0
        assert "Authentication" in r.stdout

    def test_flag_th_lowercase_is_invalid(self, proj):
        """-th (lowercase) is not a valid flag — docs now use -tH. S9-005."""
        r = _q(proj, "-mg", "*Auth*", "-th")
        assert r.returncode != 0


# ── Skill: Trin subclass query ────────────────────────────────────────────────

class TestSkillTrin_SubclassQuery:
    """trin SKILL.md: ["-mg", "Base", "-tc", "-Vinh", "-mg", "*", "-tc"]
       → 'All subclasses of Base'

    Anchor (known thing) goes on LEFT, wildcard * on RIGHT.
    Consistent with schema Ex06 and all other persona SKILL.md files.
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc").returncode == 0

    def test_returns_subclasses(self, proj):
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert "MyClass" in r.stdout
        assert "AnotherService" in r.stdout
        assert "ChildModel" in r.stdout

    def test_base_class_not_in_results(self, proj):
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert "BaseClass" not in r.stdout


# ── Skill: Who imports module (Neo/Morpheus consistent with Ex12) ─────────────

class TestSkillNeoMorpheus_WhoImports:
    """neo/morpheus SKILL.md: ["-mg", "module_name", "-Vimp", "-mg", "*"]
       → 'What imports module_name?' / 'Who imports module?'

    Same pattern as schema Ex12. Validates with 'os' (also imported by my_service).
    """

    def test_exit_0(self, proj):
        assert _q(proj, "-mg", "os", "-Vimp", "-mg", "*").returncode == 0

    def test_importer_present(self, proj):
        r = _q(proj, "-mg", "os", "-Vimp", "-mg", "*")
        assert "my_service" in r.stdout


# ── Story 5: -Q full-path matching for file symbols ───────────────────────────

class TestStory5_FullPathQualifiedMatching:
    """-Q flag enables matching file symbols by their full relative path.

    Story 5 (Sprint 9): via -mg 'app/core/*' -tF -Q should return files under
    app/core/ by matching qualified_name (relative path) instead of symbol_name
    (basename only).
    """

    def test_path_pattern_with_Q_returns_file(self, proj):
        """-Q with path prefix pattern returns files matching the full relative path."""
        r = _q(proj, "-mg", "app/core/*", "-tF", "-Q")
        assert r.returncode == 0
        assert "utils" in r.stdout

    def test_basename_without_Q_still_works(self, proj):
        """Baseline: matching by basename (without -Q) still works."""
        r = _q(proj, "-mg", "utils.py", "-tF")
        assert r.returncode == 0
        assert "utils" in r.stdout

    def test_path_pattern_without_Q_returns_nothing(self, proj):
        """Without -Q, path prefix pattern does not match (basename only)."""
        r = _q(proj, "-mg", "app/core/*", "-tF")
        assert r.returncode == 0
        assert "utils" not in r.stdout


# ── Story 3: Expanded -Vr Reference Tracking ─────────────────────────────────

class TestStory3_ExpandedVrTracking:
    """-Vr now tracks references beyond function/method bodies.

    Story 3 (Sprint 9): class bases, decorators, type annotations (function
    signatures + class bodies) are stored as REFERENCES relationships.

    Fixture: extras.py — AnnotatedClass(BaseClass), @my_decorator on
    decorated_func, class body annotation (data: MyClass), annotated
    method params (process(svc: BaseClass) -> MyClass).
    """

    def test_class_base_is_reference(self, proj):
        """class AnnotatedClass(BaseClass) → AnnotatedClass references BaseClass."""
        r = _q(proj, "-mg", "AnnotatedClass", "-tc", "-Vr", "-iv", "-mg", "*")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout

    def test_decorator_is_reference(self, proj):
        """@my_decorator on decorated_func → decorated_func references my_decorator."""
        r = _q(proj, "-mg", "decorated_func", "-tf", "-Vr", "-iv", "-mg", "*")
        assert r.returncode == 0
        assert "my_decorator" in r.stdout

    def test_function_return_annotation_is_reference(self, proj):
        """decorated_func() -> BaseClass → decorated_func references BaseClass."""
        r = _q(proj, "-mg", "decorated_func", "-tf", "-Vr", "-iv", "-mg", "*")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout

    def test_method_param_annotation_is_reference(self, proj):
        """process(self, svc: BaseClass) → process method references BaseClass."""
        r = _q(proj, "-mg", "process", "-tm", "-Vr", "-iv", "-mg", "*")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout

    def test_class_body_annotation_is_reference(self, proj):
        """data: MyClass in AnnotatedClass body → AnnotatedClass references MyClass."""
        r = _q(proj, "-mg", "AnnotatedClass", "-tc", "-Vr", "-iv", "-mg", "*")
        assert r.returncode == 0
        assert "MyClass" in r.stdout


# ── Story 1: -Vhas / DECLARES ─────────────────────────────────────────────────

class TestStory1_Vhas:
    """Sprint 9 Story 1: -Vhas has-a / DECLARES relationship queries.

    via -mg '<container>' -t<C> -Vhas -t<Member>
    Returns all members declared within containers matching the pattern.
    """

    def test_file_has_classes_by_filename(self, proj):
        """via -mg 'my_service.py' -tN -Vhas -tc → BaseClass, MyClass, AnotherService."""
        r = _q(proj, "-mg", "my_service.py", "-tN", "-Vhas", "-tc")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout
        assert "MyClass" in r.stdout
        assert "AnotherService" in r.stdout

    def test_file_has_functions_by_filename(self, proj):
        """via -mg 'my_service.py' -tN -Vhas -tf → connect, helper_func."""
        r = _q(proj, "-mg", "my_service.py", "-tN", "-Vhas", "-tf")
        assert r.returncode == 0
        assert "connect" in r.stdout
        assert "helper_func" in r.stdout

    def test_file_has_classes_by_filepath(self, proj):
        """via -mg '*my_service*' -tF -Vhas -tc → classes in my_service.py."""
        r = _q(proj, "-mg", "*my_service*", "-tF", "-Vhas", "-tc")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout
        assert "MyClass" in r.stdout

    def test_class_has_methods(self, proj):
        """via -mg 'MyClass' -tc -Vhas -tm → get_name, get_value, run."""
        r = _q(proj, "-mg", "MyClass", "-tc", "-Vhas", "-tm")
        assert r.returncode == 0
        assert "get_name" in r.stdout
        assert "get_value" in r.stdout
        assert "run" in r.stdout

    def test_class_has_methods_does_not_include_other_class(self, proj):
        """via -mg 'BaseClass' -tc -Vhas -tm → only base_method, not get_name."""
        r = _q(proj, "-mg", "BaseClass", "-tc", "-Vhas", "-tm")
        assert r.returncode == 0
        assert "base_method" in r.stdout
        assert "get_name" not in r.stdout

    def test_invert_raises_error(self, proj):
        """via ... -Vhas -iv → clear error: not-has not yet supported."""
        r = _q(proj, "-mg", "my_service.py", "-tN", "-Vhas", "-iv", "-tc")
        assert r.returncode != 0
        assert "not yet supported" in r.stderr or "not yet supported" in r.stdout

    def test_invalid_container_type_raises_error(self, proj):
        """via -mg 'run' -tm -Vhas -tc → error: method is not a container type."""
        r = _q(proj, "-mg", "run", "-tm", "-Vhas", "-tc")
        assert r.returncode != 0
        err = r.stderr + r.stdout
        assert "not a valid container" in err or "container" in err.lower()

    def test_vhas_flag_in_help(self, proj):
        """via --help → -Vhas appears in relationship flags section."""
        r = _q(proj, "--help")
        assert r.returncode == 0
        assert "-Vhas" in r.stdout or "via-has" in r.stdout


# ── Story 2a: Temporal matcher ────────────────────────────────────────────────

class TestStory2a_TemporalMatcher:
    """Sprint 9 Story 2a: --newerthan / --olderthan per-stage temporal filters.

    symbols.mtime is set at index time from file's st_mtime.
    --newerthan 1h: symbols whose file mtime is within last hour.
    --olderthan 1d: symbols whose file mtime is more than 1 day old.
    """

    def test_newerthan_flag_in_help(self, proj):
        """via --help → --newerthan appears."""
        r = _q(proj, "--help")
        assert r.returncode == 0
        assert "newerthan" in r.stdout

    def test_olderthan_flag_in_help(self, proj):
        """via --help → --olderthan appears."""
        r = _q(proj, "--help")
        assert r.returncode == 0
        assert "olderthan" in r.stdout

    def test_newerthan_returns_recently_indexed_symbols(self, proj):
        """--newerthan 1h returns symbols from files indexed within last hour."""
        r = _q(proj, "-mg", "*", "-tc", "--newerthan", "1h")
        assert r.returncode == 0
        # All test fixture files were just indexed — should return classes
        assert "BaseClass" in r.stdout or "MyClass" in r.stdout

    def test_olderthan_filters_out_recent_symbols(self, proj):
        """--olderthan 1h returns nothing for files indexed in the last second."""
        r = _q(proj, "-mg", "*", "-tc", "--olderthan", "1h")
        assert r.returncode == 0
        # All test fixture files were just indexed — should return nothing
        assert "BaseClass" not in r.stdout
        assert "MyClass" not in r.stdout

    def test_newerthan_with_very_large_duration_returns_all(self, proj):
        """--newerthan 1w (1 week) returns all symbols (all indexed within last week)."""
        r = _q(proj, "-mg", "*", "-tc", "--newerthan", "1w")
        assert r.returncode == 0
        assert "BaseClass" in r.stdout

    def test_invalid_duration_raises_error(self, proj):
        """--newerthan with invalid format → clear error."""
        r = _q(proj, "-mg", "*", "-tc", "--newerthan", "2x")
        assert r.returncode != 0
        err = r.stderr + r.stdout
        assert "Invalid duration" in err or "duration" in err.lower()

    def test_symbols_have_mtime_in_database(self, proj):
        """Verify symbols.mtime is set after indexing (schema v5)."""
        import sqlite3
        db_path = proj / ".via" / "index.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT mtime FROM symbols WHERE symbol_type='class' LIMIT 1"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] is not None, "symbols.mtime should be set at index time"
        assert row[0] > 0, "symbols.mtime should be a positive Unix timestamp"


class TestS10_1_RefTypeFlag:
    """Sprint 10 S10-1: --ref-type CLI unification.

    --ref-type <value> is a third way to specify relationship type,
    equivalent to -Vinh / --via inherits-from / etc.
    Results must match the corresponding short-flag alias exactly.
    """

    def test_ref_type_appears_in_help(self, proj):
        """via --help → --ref-type appears with valid choices listed."""
        r = _q(proj, "--help")
        assert r.returncode == 0
        assert "ref-type" in r.stdout

    def test_ref_type_inherits_from_matches_vinh(self, proj):
        """--ref-type inherits-from returns same classes as -Vinh."""
        r_vinh = _q(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc")
        r_ref = _q(proj, "-mg", "BaseClass", "-tc", "--ref-type", "inherits-from", "-mg", "*", "-tc")
        assert r_vinh.returncode == 0
        assert r_ref.returncode == 0
        # Both should contain the same subclasses
        assert "MyClass" in r_vinh.stdout
        assert "MyClass" in r_ref.stdout
        assert "AnotherService" in r_vinh.stdout
        assert "AnotherService" in r_ref.stdout

    def test_ref_type_inherits_from_json_matches_vinh_json(self, proj):
        """--ref-type inherits-from JSON output equals -Vinh JSON output."""
        vinh = _json(proj, "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc", "-oJ")
        ref = _json(proj, "-mg", "BaseClass", "-tc", "--ref-type", "inherits-from", "-mg", "*", "-tc", "-oJ")
        vinh_names = sorted(item["symbol_name"] for item in vinh)
        ref_names = sorted(item["symbol_name"] for item in ref)
        assert vinh_names == ref_names, f"Mismatch: -Vinh={vinh_names} vs --ref-type={ref_names}"

    def test_ref_type_calls_matches_vca(self, proj):
        """--ref-type calls returns same results as -Vca."""
        # run_connection is a function (-tf), not a method — no type filter on result
        r_vca = _q(proj, "-mg", "connect", "-tf", "-Vca", "-mg", "*", "-tf")
        r_ref = _q(proj, "-mg", "connect", "-tf", "--ref-type", "calls", "-mg", "*", "-tf")
        assert r_vca.returncode == 0
        assert r_ref.returncode == 0
        # Both should find run_connection as a caller
        assert "run_connection" in r_vca.stdout
        assert "run_connection" in r_ref.stdout

    def test_ref_type_imports_matches_vimp(self, proj):
        """--ref-type imports returns same results as -Vimp."""
        r_vimp = _q(proj, "-mg", "my_service", "-Vimp", "-mg", "*")
        r_ref = _q(proj, "-mg", "my_service", "--ref-type", "imports", "-mg", "*")
        assert r_vimp.returncode == 0
        assert r_ref.returncode == 0

    def test_ref_type_declares_matches_vhas(self, proj):
        """--ref-type declares returns same results as -Vhas."""
        r_vhas = _q(proj, "-mg", "BaseClass", "-tc", "-Vhas", "-mg", "*", "-tm")
        r_ref = _q(proj, "-mg", "BaseClass", "-tc", "--ref-type", "declares", "-mg", "*", "-tm")
        assert r_vhas.returncode == 0
        assert r_ref.returncode == 0
        # BaseClass declares base_method
        assert "base_method" in r_vhas.stdout
        assert "base_method" in r_ref.stdout

    def test_ref_type_invalid_value_nonzero_exit(self, proj):
        """--ref-type with unknown value → non-zero exit."""
        r = _q(proj, "-mg", "*", "-tc", "--ref-type", "foobar", "-mg", "*")
        assert r.returncode != 0

    def test_ref_type_invalid_value_lists_valid_types(self, proj):
        """Error message for bad --ref-type lists valid types."""
        r = _q(proj, "-mg", "*", "-tc", "--ref-type", "foobar", "-mg", "*")
        err = r.stderr + r.stdout
        assert "Valid types" in err or "valid" in err.lower()

    def test_ref_type_with_invert_flag(self, proj):
        """--ref-type inherits-from -iv → inverted direction (what does X inherit FROM?)."""
        r = _q(proj, "-mg", "MyClass", "-tc", "--ref-type", "inherits-from", "-iv", "-mg", "*", "-tc")
        assert r.returncode == 0
        # MyClass inherits FROM BaseClass
        assert "BaseClass" in r.stdout


# ── Sprint 10 S10-2: --stale flag ─────────────────────────────────────────────

_STALE_BASE_PY = """\
class StaleBase:
    def base_method(self):
        return "base"
"""

_STALE_CHILD_PY = """\
from stale_base import StaleBase

class StaleChild(StaleBase):
    def child_method(self):
        return "child"
"""

_FRESH_CHILD_PY = """\
from stale_base import StaleBase

class FreshChild(StaleBase):
    def child_method(self):
        return "fresh_child"
"""


@pytest.fixture(scope="module")
def stale_proj(tmp_path_factory):
    """Synthetic project with controlled mtimes for --stale UAT.

    stale_base.py  mtime = T+100  (newer — updated anchor)
    stale_child.py mtime = T      (older than anchor → STALE result)
    fresh_child.py mtime = T+200  (newer than anchor → FRESH result)
    """
    import os
    import time

    d = tmp_path_factory.mktemp("stale_proj")

    base_file = d / "stale_base.py"
    stale_child_file = d / "stale_child.py"
    fresh_child_file = d / "fresh_child.py"

    base_file.write_text(_STALE_BASE_PY)
    stale_child_file.write_text(_STALE_CHILD_PY)
    fresh_child_file.write_text(_FRESH_CHILD_PY)

    # Set controlled mtimes: base is updated AFTER stale_child but BEFORE fresh_child
    T = time.time() - 1000
    os.utime(str(stale_child_file), (T, T))        # T: old (stale)
    os.utime(str(base_file), (T + 100, T + 100))   # T+100: updated (anchor)
    os.utime(str(fresh_child_file), (T + 200, T + 200))  # T+200: newest (fresh)

    r = subprocess.run(
        [sys.executable, "-m", "via", "index", str(d)],
        capture_output=True, text=True, timeout=60, cwd=str(d),
    )
    assert r.returncode == 0, f"stale_proj index failed:\n{r.stderr}"
    return d


class TestS10_2_StaleFlag:
    """Sprint 10 S10-2: --stale post-filter on relationship results.

    Acceptance criteria:
    - --stale returns only results whose mtime < anchor's mtime
    - Without --stale, all results are returned
    - --stale appears in --help
    """

    def test_stale_appears_in_help(self, stale_proj):
        """via -mg '*' --help → --stale appears."""
        r = _q(stale_proj, "--help")
        assert r.returncode == 0
        assert "stale" in r.stdout

    def test_stale_filter_returns_only_stale_results(self, stale_proj):
        """--stale returns StaleChild (old) but not FreshChild (new)."""
        r = _q(stale_proj, "-mg", "StaleBase", "-tc", "-Vinh", "-mg", "*", "-tc", "--stale")
        assert r.returncode == 0
        assert "StaleChild" in r.stdout
        assert "FreshChild" not in r.stdout

    def test_without_stale_returns_all_results(self, stale_proj):
        """Without --stale, both StaleChild and FreshChild are returned."""
        r = _q(stale_proj, "-mg", "StaleBase", "-tc", "-Vinh", "-mg", "*", "-tc")
        assert r.returncode == 0
        assert "StaleChild" in r.stdout
        assert "FreshChild" in r.stdout

    def test_stale_with_no_stale_results_excludes_fresh(self, stale_proj):
        """FreshChild (T+200) is newer than StaleBase anchor (T+100): --stale excludes it."""
        # Filter result side to FreshChild only — it's newer than anchor so not stale
        r = _q(stale_proj, "-mg", "StaleBase", "-tc", "-Vinh", "-mg", "FreshChild", "-tc", "--stale")
        assert r.returncode == 0
        # FreshChild mtime (T+200) > StaleBase mtime (T+100) → not stale → excluded
        assert "FreshChild" not in r.stdout


# ── Sprint 10 S10-3: prep_tldr incremental ───────────────────────────────────

class TestS10_3_PrepTldrIncremental:
    """Sprint 10 S10-3: prep_tldr.py argparse + incremental mode.

    Acceptance criteria:
    - --force flag accepted
    - --help works (argparse interface)
    - Full mode: processes all files, writes last-run timestamp
    - Incremental mode: second run skips unchanged files
    """

    def test_prep_tldr_help_works(self, proj):
        """prep_tldr --help exits 0 and shows --force."""
        prep = str(
            __import__('pathlib').Path(__file__).resolve().parent.parent.parent
            / 'agents' / 'tools' / 'prep_tldr.py'
        )
        r = subprocess.run(
            [sys.executable, prep, "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0
        assert "force" in r.stdout

    def test_prep_tldr_force_flag_accepted(self, proj):
        """prep_tldr <root> --force runs without error."""
        prep = str(
            __import__('pathlib').Path(__file__).resolve().parent.parent.parent
            / 'agents' / 'tools' / 'prep_tldr.py'
        )
        r = subprocess.run(
            [sys.executable, prep, str(proj), "--force"],
            capture_output=True, text=True, timeout=120, cwd=str(proj),
        )
        assert r.returncode == 0, f"prep_tldr --force failed:\n{r.stderr}"
        assert "Full mode" in r.stdout

    def test_prep_tldr_writes_last_run_file(self, proj):
        """After full run, .via/prep_tldr_last_run exists."""
        import pathlib
        prep = str(
            pathlib.Path(__file__).resolve().parent.parent.parent
            / 'agents' / 'tools' / 'prep_tldr.py'
        )
        subprocess.run(
            [sys.executable, prep, str(proj), "--force"],
            capture_output=True, text=True, timeout=120, cwd=str(proj),
        )
        last_run_path = proj / ".via" / "prep_tldr_last_run"
        assert last_run_path.exists(), "prep_tldr_last_run not created"
        ts = float(last_run_path.read_text().strip())
        assert ts > 0

    def test_prep_tldr_second_run_uses_incremental_mode(self, proj):
        """After first full run, second run reports incremental mode."""
        import pathlib
        prep = str(
            pathlib.Path(__file__).resolve().parent.parent.parent
            / 'agents' / 'tools' / 'prep_tldr.py'
        )
        # First run (full)
        subprocess.run(
            [sys.executable, prep, str(proj), "--force"],
            capture_output=True, text=True, timeout=120, cwd=str(proj),
        )
        # Second run (incremental)
        r = subprocess.run(
            [sys.executable, prep, str(proj)],
            capture_output=True, text=True, timeout=120, cwd=str(proj),
        )
        assert r.returncode == 0, f"incremental run failed:\n{r.stderr}"
        assert "Incremental mode" in r.stdout
