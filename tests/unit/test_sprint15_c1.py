"""Sprint 15 Cycle 1 tests — S15-3 (--lang -tF), S15-5 (-Q path matching), S15-6 (--help).

TLDR:
    S15-3: --lang + -tF returns filepath symbols filtered by language.
           Root cause: _store_file_path_symbols() was not setting language on filepath symbols.
    S15-5: -Q + -tF matches against qualified_name (relative path), not just filename.
           SQLite GLOB '*' crosses '/', so 'via/pipeline/*' matches all pipeline files.
    S15-6: via --help contains annotated relationship query examples section.

Author: Neo
Sprint: 15, Cycle 1
"""

import subprocess
import sys

import pytest


# ---------------------------------------------------------------------------
# Shared fixture: project with py, js, ts, md and subdirectory structure
# ---------------------------------------------------------------------------

_PY_SERVICE = """\
class ServiceClass:
    def run(self):
        return True
"""

_JS_MODULE = """\
function jsFunc(x) { return x * 2; }
class JsClass {}
"""

_TS_MODULE = """\
interface IConfig { host: string; }
function tsFunc(): void {}
"""

_MD_DOC = """\
# Overview

## Setup

## Usage
"""

_PY_SUB = """\
def sub_func():
    pass
"""

_PY_UTILS = """\
def util_func():
    pass
"""


@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    """Synthetic project with py, js, ts, md files and subdirectories."""
    d = tmp_path_factory.mktemp("sprint15c1")

    (d / "service.py").write_text(_PY_SERVICE)
    (d / "module.js").write_text(_JS_MODULE)
    (d / "types.ts").write_text(_TS_MODULE)
    (d / "docs").mkdir()
    (d / "docs" / "guide.md").write_text(_MD_DOC)
    # Subdirectory for -Q path matching tests
    (d / "pipeline").mkdir()
    (d / "pipeline" / "executor.py").write_text(_PY_SUB)
    (d / "pipeline" / "parser.py").write_text(_PY_UTILS)

    r = subprocess.run(
        [sys.executable, "-m", "via", "index", str(d)],
        capture_output=True, text=True, timeout=60, cwd=str(d),
    )
    assert r.returncode == 0, f"Index failed:\n{r.stderr}"
    return d


def _q(proj, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=30, cwd=str(proj),
    )


def _lines(proj, *args):
    r = _q(proj, *args)
    assert r.returncode == 0, f"via failed:\n{r.stderr}\n{r.stdout}"
    return [l for l in r.stdout.splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# S15-3: --lang + -tF returns only files in that language
# ---------------------------------------------------------------------------

class TestLangFilepath:
    """--lang filter works with -tF (filepath) symbol type."""

    def test_lang_py_tF_returns_python_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "py")
        assert results, "Expected at least one python filepath result"
        assert all(".py" in line for line in results), \
            f"Expected only .py files, got: {results}"

    def test_lang_py_tF_excludes_js_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "py")
        assert not any(".js" in line for line in results), \
            f"Expected no .js files in python results, got: {results}"

    def test_lang_js_tF_returns_js_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "js")
        assert results, "Expected at least one JS filepath result"
        assert all(".js" in line for line in results), \
            f"Expected only .js files, got: {results}"

    def test_lang_ts_tF_returns_ts_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "ts")
        assert results, "Expected at least one TS filepath result"
        assert all(".ts" in line for line in results), \
            f"Expected only .ts files, got: {results}"

    def test_lang_md_tF_returns_md_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "md")
        assert results, "Expected at least one markdown filepath result"
        assert all(".md" in line for line in results), \
            f"Expected only .md files, got: {results}"

    def test_lang_py_tF_finds_multiple_py_files(self, proj):
        results = _lines(proj, "-mg", "*", "-tF", "--lang", "py")
        # Expect service.py + pipeline/executor.py + pipeline/parser.py
        assert len(results) >= 3, \
            f"Expected at least 3 python files, got {len(results)}: {results}"

    def test_lang_py_tF_consistent_with_lang_py_tc(self, proj):
        # -tF --lang py should return only .py filepaths
        # -tc --lang py should return only classes from .py files
        fp_results = _lines(proj, "-mg", "*", "-tF", "--lang", "py")
        tc_results = _lines(proj, "-mg", "*", "-tc", "--lang", "py")
        # All filepath results must be .py
        assert all(".py" in line for line in fp_results)
        # All class results must be from .py files
        assert all(".py" in line for line in tc_results)


# ---------------------------------------------------------------------------
# S15-5: -Q with -tF matches against full relative path
# ---------------------------------------------------------------------------

class TestQualifiedFilepath:
    """With -Q, -tF matches against the full relative path (qualified_name)."""

    def test_Q_path_glob_matches_subdirectory_files(self, proj):
        results = _lines(proj, "-mg", "pipeline/*", "-tF", "-Q")
        assert results, "Expected pipeline/* -Q to return files in pipeline/"
        assert all("pipeline" in line for line in results), \
            f"Expected only pipeline/ files, got: {results}"

    def test_Q_path_glob_matches_both_pipeline_files(self, proj):
        results = _lines(proj, "-mg", "pipeline/*", "-tF", "-Q")
        filenames = [line.split()[-1] for line in results]
        names_joined = " ".join(filenames)
        assert "executor" in names_joined or "executor.py" in names_joined, \
            f"executor.py missing from results: {results}"
        assert "parser" in names_joined or "parser.py" in names_joined, \
            f"parser.py missing from results: {results}"

    def test_Q_path_glob_excludes_root_files(self, proj):
        results = _lines(proj, "-mg", "pipeline/*", "-tF", "-Q")
        assert not any("service.py" in line for line in results), \
            f"service.py should not be in pipeline/* results: {results}"

    def test_without_Q_path_glob_returns_nothing(self, proj):
        # Without -Q, 'pipeline/*' matches against symbol_name (filename only)
        # No file is named 'pipeline/*', so result should be empty
        r = _q(proj, "-mg", "pipeline/*", "-tF")
        assert r.returncode == 0
        result_lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert not result_lines, \
            f"Without -Q, 'pipeline/*' should match no filename, got: {result_lines}"

    def test_Q_docs_path_glob_matches_docs_files(self, proj):
        results = _lines(proj, "-mg", "docs/*", "-tF", "-Q")
        assert results, "Expected docs/* -Q to return docs/ files"
        assert all("docs" in line for line in results), \
            f"Expected only docs/ files: {results}"


# ---------------------------------------------------------------------------
# S15-6: via --help contains annotated relationship examples section
# ---------------------------------------------------------------------------

class TestHelpRelationshipSection:
    """via --help contains a structured Relationship Queries section."""

    @pytest.fixture(scope="class")
    def help_text(self, tmp_path_factory):
        d = tmp_path_factory.mktemp("s15help")
        r = subprocess.run(
            [sys.executable, "-m", "via", "--help"],
            capture_output=True, text=True, timeout=30, cwd=str(d),
        )
        # --help may exit 0 or non-zero depending on argparse version; check output
        return r.stdout + r.stderr

    def test_help_contains_relationship_queries_section(self, help_text):
        assert "Relationship Queries" in help_text, \
            "Expected 'Relationship Queries' section in --help"

    def test_help_contains_relationship_guidance(self, help_text):
        assert "Prefer canned shortcuts" in help_text, \
            "Expected task-first relationship guidance in --help Relationship Queries section"

    def test_help_contains_inherits_from(self, help_text):
        assert "inherits-from" in help_text, \
            "Expected 'inherits-from' in --help relationship types"

    def test_help_contains_calls(self, help_text):
        assert "calls" in help_text, \
            "Expected 'calls' in --help relationship types"

    def test_help_contains_imports(self, help_text):
        assert "imports" in help_text, \
            "Expected 'imports' in --help relationship types"

    def test_help_contains_references(self, help_text):
        assert "references" in help_text, \
            "Expected 'references' in --help relationship types"

    def test_help_contains_declares(self, help_text):
        assert "declares" in help_text, \
            "Expected 'declares' in --help relationship types"

    def test_help_contains_example_with_via(self, help_text):
        assert "--via" in help_text, \
            "Expected '--via' example in --help"

    def test_help_contains_example_with_sans(self, help_text):
        assert "--sans" in help_text, \
            "Expected '--sans' example in --help"

    def test_help_relationship_section_length_reasonable(self, help_text):
        # Verify the help section is present but doesn't bloat output (< 200 extra lines)
        lines = help_text.splitlines()
        assert len(lines) < 200, \
            f"--help output is too long ({len(lines)} lines). Check for bloat."
