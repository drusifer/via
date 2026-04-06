"""Sprint 14 Cycle 2 tests — --lang and --subtype filter flags.

TLDR:
    Unit + UAT tests for S14-2 (--lang) and S14-3 (--subtype).

    Fixture: synthetic project with Python, JavaScript, and TypeScript files
    so language filtering can be verified against known symbol counts.

    S14-2 --lang:
      - Short aliases: py, js, ts, md → normalized to canonical names
      - Canonical forms work directly: python, javascript, typescript, markdown
      - Filters to only symbols in that language
      - Invalid alias → non-zero exit + error message mentioning valid options

    S14-3 --subtype:
      - Matches symbols whose symbol_subtype column equals the given value
      - Unknown subtype silently returns empty (no error)
      - Case-sensitive: 'arrow_function' matches, 'Arrow_Function' does not

Author: Trin
Sprint: 14, Cycle 2
"""

import subprocess
import sys

import pytest


# ---------------------------------------------------------------------------
# Fixture source files
# ---------------------------------------------------------------------------

_PY_SERVICE = """\
\"\"\"Python service with classes and functions.\"\"\"


class ServiceClass:
    def run(self):
        return True

    def stop(self):
        pass


def standalone_func():
    pass
"""

_JS_MODULE = """\
// JavaScript module with functions and arrow functions
function jsFunc(x) {
    return x * 2;
}

const arrowFunc = (x) => x + 1;

class JsClass {
    constructor() {}

    method() {
        return arrowFunc(1);
    }
}
"""

_TS_MODULE = """\
// TypeScript module
interface IConfig {
    host: string;
    port: number;
}

enum Status {
    Active,
    Inactive,
}

function tsFunc(cfg: IConfig): Status {
    return Status.Active;
}
"""

_MD_DOC = """\
# Overview

## Setup

## Usage
"""


# ---------------------------------------------------------------------------
# Fixture — synthetic project with py, js, ts, md files
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def proj(tmp_path_factory):
    """Synthetic project with Python, JS, TS, and Markdown files."""
    d = tmp_path_factory.mktemp("sprint14c2")

    (d / "service.py").write_text(_PY_SERVICE)
    (d / "module.js").write_text(_JS_MODULE)
    (d / "types.ts").write_text(_TS_MODULE)
    (d / "docs").mkdir()
    (d / "docs" / "guide.md").write_text(_MD_DOC)

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
# S14-2: --lang filter
# ---------------------------------------------------------------------------

class TestLangFilter:
    """--lang narrows match results to one language."""

    def test_lang_py_alias_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tc", "--lang", "py").returncode == 0

    def test_lang_python_canonical_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tc", "--lang", "python").returncode == 0

    def test_lang_py_returns_only_python_symbols(self, proj):
        results = _lines(proj, "-mg", "*", "-tc", "--lang", "py")
        # All results must reference service.py (the only python source)
        assert all("service.py" in line for line in results), \
            f"Expected only python symbols, got: {results}"

    def test_lang_python_same_as_py(self, proj):
        py_results = _lines(proj, "-mg", "*", "-tc", "--lang", "py")
        python_results = _lines(proj, "-mg", "*", "-tc", "--lang", "python")
        assert py_results == python_results

    def test_lang_js_alias_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tc", "--lang", "js").returncode == 0

    def test_lang_js_returns_only_js_symbols(self, proj):
        results = _lines(proj, "-mg", "*", "-tc", "--lang", "js")
        assert all("module.js" in line for line in results), \
            f"Expected only JS symbols, got: {results}"

    def test_lang_javascript_canonical_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tc", "--lang", "javascript").returncode == 0

    def test_lang_js_same_as_javascript(self, proj):
        js = _lines(proj, "-mg", "*", "-tc", "--lang", "js")
        javascript = _lines(proj, "-mg", "*", "-tc", "--lang", "javascript")
        assert js == javascript

    def test_lang_ts_alias_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tc", "--lang", "ts").returncode == 0

    def test_lang_ts_returns_only_ts_symbols(self, proj):
        results = _lines(proj, "-mg", "*", "-tc", "--lang", "ts")
        assert all("types.ts" in line for line in results), \
            f"Expected only TS symbols, got: {results}"

    def test_lang_typescript_same_as_ts(self, proj):
        ts = _lines(proj, "-mg", "*", "-tc", "--lang", "ts")
        typescript = _lines(proj, "-mg", "*", "-tc", "--lang", "typescript")
        assert ts == typescript

    def test_lang_md_alias_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tH", "--lang", "md").returncode == 0

    def test_lang_md_returns_only_markdown_symbols(self, proj):
        results = _lines(proj, "-mg", "*", "-tH", "--lang", "md")
        assert all("guide.md" in line for line in results), \
            f"Expected only markdown symbols, got: {results}"

    def test_lang_markdown_same_as_md(self, proj):
        md = _lines(proj, "-mg", "*", "-tH", "--lang", "md")
        markdown = _lines(proj, "-mg", "*", "-tH", "--lang", "markdown")
        assert md == markdown

    def test_lang_py_excludes_js_symbols(self, proj):
        py = set(_lines(proj, "-mg", "*", "-tc", "--lang", "py"))
        js = set(_lines(proj, "-mg", "*", "-tc", "--lang", "js"))
        assert py.isdisjoint(js), "py and js results should not overlap"

    def test_lang_case_insensitive_alias(self, proj):
        # 'PY' should normalize same as 'py'
        assert _q(proj, "-mg", "*", "-tc", "--lang", "PY").returncode == 0

    def test_invalid_lang_exits_nonzero(self, proj):
        r = _q(proj, "-mg", "*", "-tc", "--lang", "cobol")
        assert r.returncode != 0

    def test_invalid_lang_error_mentions_valid_options(self, proj):
        r = _q(proj, "-mg", "*", "-tc", "--lang", "cobol")
        combined = r.stdout + r.stderr
        assert "py/python" in combined or "Valid" in combined, \
            f"Error should mention valid options, got:\n{combined}"

    def test_invalid_lang_error_mentions_unknown_value(self, proj):
        r = _q(proj, "-mg", "*", "-tc", "--lang", "cobol")
        combined = r.stdout + r.stderr
        assert "cobol" in combined, \
            f"Error should echo the unknown value, got:\n{combined}"

    def test_lang_with_glob_pattern(self, proj):
        # --lang combined with a specific glob still works
        results = _lines(proj, "-mg", "Service*", "-tc", "--lang", "py")
        assert any("ServiceClass" in line for line in results)

    def test_lang_filters_within_glob(self, proj):
        # 'JsClass' only exists in JS — should appear with --lang js but not --lang py
        js_results = _lines(proj, "-mg", "Js*", "-tc", "--lang", "js")
        assert any("JsClass" in line for line in js_results)
        py_results = _q(proj, "-mg", "Js*", "-tc", "--lang", "py")
        assert py_results.returncode == 0
        assert "JsClass" not in py_results.stdout


# ---------------------------------------------------------------------------
# S14-3: --subtype filter
# ---------------------------------------------------------------------------

class TestSubtypeFilter:
    """--subtype narrows results to one symbol_subtype value."""

    def test_subtype_arrow_function_exits_0(self, proj):
        assert _q(proj, "-mg", "*", "-tf", "--subtype", "arrow_function").returncode == 0

    def test_subtype_arrow_function_returns_results(self, proj):
        results = _lines(proj, "-mg", "*", "-tf", "--subtype", "arrow_function")
        assert len(results) > 0, "Expected at least one arrow_function symbol"

    def test_subtype_arrow_function_only_arrow(self, proj):
        results = _lines(proj, "-mg", "*", "-tf", "--subtype", "arrow_function")
        # arrowFunc from module.js should be here
        assert any("arrowFunc" in line for line in results)

    def test_subtype_unknown_exits_0(self, proj):
        # Unknown subtype silently returns empty
        assert _q(proj, "-mg", "*", "-tf", "--subtype", "nonexistent_type").returncode == 0

    def test_subtype_unknown_returns_empty(self, proj):
        results = _lines(proj, "-mg", "*", "-tf", "--subtype", "nonexistent_type")
        assert results == []

    def test_subtype_case_sensitive_mismatch_empty(self, proj):
        # 'Arrow_Function' != 'arrow_function'
        results = _lines(proj, "-mg", "*", "-tf", "--subtype", "Arrow_Function")
        assert results == []

    def test_subtype_combined_with_lang(self, proj):
        # arrow_function + js → only JS arrow functions
        results = _lines(proj, "-mg", "*", "-tf", "--subtype", "arrow_function", "--lang", "js")
        assert all("module.js" in line for line in results)
        assert len(results) > 0

    def test_subtype_combined_with_glob(self, proj):
        # Subtype filter composes with glob
        results = _lines(proj, "-mg", "arrow*", "-tf", "--subtype", "arrow_function")
        assert any("arrowFunc" in line for line in results)
