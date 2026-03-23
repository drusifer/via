"""Sprint 11 Cycle 1 unit tests — JS/TS discovery + node_modules excludes.

TLDR:
    Verifies that node_modules/, dist/, .next/, and related JS directories are
    excluded by PathFilter.DEFAULT_EXCLUDES, and that JavaScriptParser is
    registered with the correct extensions so .ts and .jsx files are discovered
    as parseable after via index.
"""

import os
import tempfile

import pytest

from via.core.path_filter import PathFilter
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.registry import ParserRegistry


# ---------------------------------------------------------------------------
# S11-5: node_modules and JS directory exclusion
# ---------------------------------------------------------------------------

class TestJSDefaultExcludes:
    """PathFilter.DEFAULT_EXCLUDES includes JS-specific directories."""

    def _make_filter(self, tmpdir: str) -> PathFilter:
        return PathFilter(root_dir=tmpdir, respect_gitignore=False)

    def test_node_modules_excluded(self, tmp_path):
        nm = tmp_path / "node_modules"
        nm.mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), "node_modules")

    def test_dist_excluded(self, tmp_path):
        (tmp_path / "dist").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), "dist")

    def test_next_excluded(self, tmp_path):
        (tmp_path / ".next").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), ".next")

    def test_nuxt_excluded(self, tmp_path):
        (tmp_path / ".nuxt").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), ".nuxt")

    def test_svelte_kit_excluded(self, tmp_path):
        (tmp_path / ".svelte-kit").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), ".svelte-kit")

    def test_coverage_excluded(self, tmp_path):
        (tmp_path / "coverage").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), "coverage")

    def test_turbo_excluded(self, tmp_path):
        (tmp_path / ".turbo").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(tmp_path), ".turbo")

    def test_src_not_excluded(self, tmp_path):
        """Normal source directories are NOT excluded."""
        (tmp_path / "src").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert pf.should_include_dir(str(tmp_path), "src")

    def test_nested_node_modules_excluded(self, tmp_path):
        """node_modules nested inside a package is also excluded."""
        pkg = tmp_path / "packages" / "foo"
        pkg.mkdir(parents=True)
        (pkg / "node_modules").mkdir()
        pf = self._make_filter(str(tmp_path))
        assert not pf.should_include_dir(str(pkg), "node_modules")

    def test_node_modules_files_not_discovered(self, tmp_path):
        """Files inside node_modules are not returned by FileDiscovery."""
        from via.core.discovery import FileDiscovery

        nm = tmp_path / "node_modules" / "react"
        nm.mkdir(parents=True)
        excluded_file = nm / "index.js"
        excluded_file.write_text("module.exports = {};")
        included_file = tmp_path / "app.js"
        included_file.write_text("import React from 'react';")

        registry = ParserRegistry()
        registry.register(JavaScriptParser())
        fd = FileDiscovery(
            root_dir=str(tmp_path),
            parseable_extensions=registry.get_supported_extensions(),
        )
        paths = [f.path for f in fd.discover()]
        assert str(excluded_file) not in paths
        assert str(included_file) in paths


# ---------------------------------------------------------------------------
# S11-1: JavaScriptParser extensions + auto-registration
# ---------------------------------------------------------------------------

class TestJavaScriptParserExtensions:
    """JavaScriptParser reports correct extensions."""

    def setup_method(self):
        self.parser = JavaScriptParser()

    def test_supported_extensions_js(self):
        exts = self.parser.get_supported_extensions()
        assert '.js' in exts
        assert '.mjs' in exts
        assert '.cjs' in exts
        assert '.jsx' in exts

    def test_supported_extensions_ts(self):
        exts = self.parser.get_supported_extensions()
        assert '.ts' in exts
        assert '.tsx' in exts

    def test_can_parse_js(self):
        assert self.parser.can_parse("index.js")
        assert self.parser.can_parse("server.mjs")
        assert self.parser.can_parse("Button.jsx")

    def test_can_parse_ts(self):
        assert self.parser.can_parse("app.ts")
        assert self.parser.can_parse("Component.tsx")

    def test_cannot_parse_python(self):
        assert not self.parser.can_parse("main.py")

    def test_cannot_parse_css(self):
        assert not self.parser.can_parse("styles.css")

    def test_language_for_js_files(self):
        assert self.parser._language_for_path("app.js") == "javascript"
        assert self.parser._language_for_path("Button.jsx") == "javascript"

    def test_language_for_ts_files(self):
        assert self.parser._language_for_path("app.ts") == "typescript"
        assert self.parser._language_for_path("Component.tsx") == "typescript"


class TestJavaScriptParserRegistration:
    """JavaScriptParser integrates with ParserRegistry."""

    def test_registry_resolves_js(self):
        reg = ParserRegistry()
        reg.register(JavaScriptParser())
        parser = reg.get_parser("src/index.js")
        assert parser is not None
        assert isinstance(parser, JavaScriptParser)

    def test_registry_resolves_tsx(self):
        reg = ParserRegistry()
        reg.register(JavaScriptParser())
        parser = reg.get_parser("src/App.tsx")
        assert parser is not None
        assert isinstance(parser, JavaScriptParser)

    def test_registry_extensions_include_js_ts(self):
        reg = ParserRegistry()
        reg.register(JavaScriptParser())
        exts = reg.get_supported_extensions()
        assert '.js' in exts
        assert '.ts' in exts
        assert '.jsx' in exts
        assert '.tsx' in exts

    def test_discovery_marks_ts_parseable(self, tmp_path):
        """FileDiscovery marks .ts files as parseable when JavaScriptParser is registered."""
        from via.core.discovery import FileDiscovery

        (tmp_path / "app.ts").write_text("const x = 1;")
        (tmp_path / "style.css").write_text("body {}")

        reg = ParserRegistry()
        reg.register(JavaScriptParser())
        fd = FileDiscovery(
            root_dir=str(tmp_path),
            parseable_extensions=reg.get_supported_extensions(),
        )
        discovered = {os.path.basename(f.path): f for f in fd.discover()}
        assert "app.ts" in discovered
        assert discovered["app.ts"].is_parseable is True
        assert "style.css" in discovered
        assert discovered["style.css"].is_parseable is False

    def test_discovery_marks_jsx_parseable(self, tmp_path):
        """FileDiscovery marks .jsx files as parseable."""
        from via.core.discovery import FileDiscovery

        (tmp_path / "Button.jsx").write_text("export default function Button() {}")

        reg = ParserRegistry()
        reg.register(JavaScriptParser())
        fd = FileDiscovery(
            root_dir=str(tmp_path),
            parseable_extensions=reg.get_supported_extensions(),
        )
        discovered = {os.path.basename(f.path): f for f in fd.discover()}
        assert "Button.jsx" in discovered
        assert discovered["Button.jsx"].is_parseable is True
