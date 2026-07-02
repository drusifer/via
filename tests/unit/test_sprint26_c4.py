"""
Unit tests for Sprint 26 Cycle 4 — Class-Based Relationship Type Hierarchy.

Theme: replace the flat relationship enum with a polymorphic class hierarchy
(Relation -> Any -> UpstreamRef/DownstreamRef -> concrete leaves) so a single
--via category name (upstream-ref, downstream-ref, any-ref) can expand to a
blast-radius query spanning multiple concrete relationship types, resolved
via real issubclass/__subclasses__ polymorphism rather than a lookup table.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from via.core.relationship_types import (
    Any,
    CalledBy,
    Calls,
    DownstreamRef,
    UpstreamRef,
    execute_relation,
    get_relation_names,
    is_category,
    resolve_relation,
)
from via.pipeline.parser import PipelineParseError, PipelineParser


def _run(cwd, *args):
    return subprocess.run(
        [sys.executable, "-m", "via", *args],
        capture_output=True, text=True, timeout=60, cwd=str(cwd),
    )


class TestRelationHierarchy:
    """Unit tests for via/core/relationship_types.py directly."""

    def test_leaf_resolves_to_itself(self):
        assert resolve_relation("calls") is Calls
        assert Calls.leaves() == [Calls]
        assert Calls.is_category() is False

    def test_category_resolves_to_multiple_leaves_via_subclasses(self):
        leaves = resolve_relation("upstream-ref").leaves()
        assert Calls in leaves
        assert CalledBy not in leaves  # CalledBy is DownstreamRef, not UpstreamRef
        assert len(leaves) > 1
        assert UpstreamRef.is_category() is True

    def test_any_ref_includes_both_directions(self):
        leaves = resolve_relation("any-ref").leaves()
        assert Calls in leaves
        assert CalledBy in leaves

    def test_issubclass_relationships_are_real(self):
        """Genuine polymorphism: leaves are actual subclasses, not just dict entries."""
        assert issubclass(Calls, UpstreamRef)
        assert issubclass(Calls, Any)
        assert not issubclass(Calls, DownstreamRef)
        assert issubclass(CalledBy, DownstreamRef)
        assert not issubclass(CalledBy, UpstreamRef)

    def test_get_relation_names_includes_categories_and_leaves(self):
        names = get_relation_names()
        assert "calls" in names
        assert "upstream-ref" in names
        assert "downstream-ref" in names
        assert "any-ref" in names

    def test_resolve_relation_unknown_name_raises(self):
        with pytest.raises(KeyError):
            resolve_relation("not-a-real-relationship")

    def test_is_category_handles_plain_reference_type(self):
        """Older ReferenceType enum members (web API, ViaQueryBuilder) never
        produce categories — is_category must accept them safely."""
        from via.core.relationship_types import ReferenceType
        assert is_category(ReferenceType.CALLS) is False

    def test_execute_relation_runs_once_for_a_leaf(self):
        calls = []

        def run_leaf(leaf_cls):
            calls.append(leaf_cls)
            return ["result"]

        result = execute_relation(Calls, run_leaf)
        assert calls == [Calls]
        assert result == ["result"]

    def test_execute_relation_fans_out_for_a_category(self):
        calls = []

        def run_leaf(leaf_cls):
            calls.append(leaf_cls)
            return []

        execute_relation(UpstreamRef, run_leaf)
        assert set(calls) == set(UpstreamRef.leaves())
        assert len(calls) > 1


class TestParserCategoryResolution:
    """Unit tests for parser.py resolving category names."""

    def test_via_upstream_ref_parses_to_category_class(self):
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '--via', 'upstream-ref', '-mg', 'helper'])
        rel = stages[0].args.relationship
        assert rel.relationship_type is UpstreamRef
        assert rel.relationship_type.is_category()

    def test_sans_with_category_raises_clear_error(self):
        parser = PipelineParser()
        with pytest.raises(PipelineParseError, match="does not support relationship categories"):
            parser.parse(['-mg', '*', '--sans', 'upstream-ref', '-mg', 'helper'])

    def test_via_leaf_name_still_parses_to_leaf_class(self):
        """Existing single-relationship-type syntax is unaffected."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '--via', 'calls', '-mg', 'helper'])
        rel = stages[0].args.relationship
        assert rel.relationship_type is Calls
        assert rel.relationship_type.is_category() is False


class TestBlastRadiusEndToEnd:
    """Real end-to-end CLI queries against an indexed project."""

    @pytest.fixture
    def project(self, tmp_path):
        src = tmp_path / "app.py"
        src.write_text(
            "def helper():\n"
            "    return 1\n\n"
            "def caller():\n"
            "    return helper()\n\n"
            "class Base:\n"
            "    pass\n\n"
            "class Child(Base):\n"
            "    pass\n"
        )
        index = _run(tmp_path, "index", str(tmp_path))
        assert index.returncode == 0, index.stderr
        return tmp_path

    def test_upstream_ref_finds_callers(self, project):
        """upstream-ref of helper = who depends on helper = caller."""
        result = _run(project, "-mg", "*", "-tf", "--via", "upstream-ref", "-mg", "helper", "-oJ")
        assert result.returncode == 0, result.stderr
        names = [r["symbol_name"] for r in json.loads(result.stdout)]
        assert names == ["caller"]

    def test_downstream_ref_finds_callees(self, project):
        """downstream-ref of caller = what caller depends on = helper."""
        result = _run(project, "-mg", "*", "-tf", "--via", "downstream-ref", "-mg", "caller", "-oJ")
        assert result.returncode == 0, result.stderr
        names = [r["symbol_name"] for r in json.loads(result.stdout)]
        assert names == ["helper"]

    def test_any_ref_finds_both_directions(self, project):
        """any-ref of Base = both its subclasses (upstream) and parents (downstream, none here)."""
        result = _run(project, "-mg", "*", "-tc", "--via", "any-ref", "-mg", "Base", "-oJ")
        assert result.returncode == 0, result.stderr
        names = [r["symbol_name"] for r in json.loads(result.stdout)]
        assert names == ["Child"]

    def test_category_fan_out_suppresses_a_single_leaf_error(self, project, monkeypatch):
        """If one leaf under a category raises ValueError (e.g. a future leaf
        with its own type-applicability constraint, like Declares had before
        it was removed from the categories), the category query must still
        succeed with the other leaves' results — not abort entirely. A
        direct single-relationship query with the same error must still
        raise normally (see test_direct_declares_invalid_container_still_raises)."""
        from via.db.store import DatabaseStore

        real_query_relationships = DatabaseStore.query_relationships

        def flaky_query_relationships(self, relationship_type, **kwargs):
            if relationship_type == 'references':
                raise ValueError("synthetic per-leaf failure for this test")
            return real_query_relationships(self, relationship_type, **kwargs)

        monkeypatch.setattr(DatabaseStore, "query_relationships", flaky_query_relationships)

        result = _run(project, "-mg", "*", "-tf", "--via", "upstream-ref", "-mg", "helper", "-oJ")
        assert result.returncode == 0, result.stderr
        names = [r["symbol_name"] for r in json.loads(result.stdout)]
        assert names == ["caller"]  # Calls leaf's result still comes through

    def test_direct_declares_invalid_container_still_raises(self, project):
        """A direct (non-category) --via declares query keeps its normal,
        clear validation error — only category fan-out suppresses it."""
        result = _run(project, "-mg", "*", "-tf", "--via", "declares", "-mg", "helper", "-tf", "-oJ")
        assert result.returncode != 0
        assert "not a valid container type for declares" in result.stderr

    def test_chained_category_query_rejected(self, project):
        """Categories aren't yet supported when chaining multiple relationship
        filters in one query — explicit error, not silent wrong results."""
        result = _run(
            project, "-mg", "*", "-tf",
            "--via", "upstream-ref", "-mg", "helper",
            "--via", "calls", "-mg", "*",
            "-oJ",
        )
        assert result.returncode != 0
        assert "not yet" in result.stderr.lower() or "not yet" in result.stdout.lower()


class TestBlastCannedQuery:
    """The 'blast' canned query (design doc section 4)."""

    def test_blast_expands_to_any_ref(self):
        from via.canned import expand_canned_query
        argv = expand_canned_query(".", "blast", "symbol=helper", [])
        assert argv == ["-mg", "*", "--via", "any-ref", "-mg", "helper"]

    def test_blast_canned_query_runs_end_to_end(self, tmp_path):
        src = tmp_path / "app.py"
        src.write_text(
            "def helper():\n    return 1\n\n"
            "def caller():\n    return helper()\n"
        )
        index = _run(tmp_path, "index", str(tmp_path))
        assert index.returncode == 0, index.stderr

        result = _run(tmp_path, "--canned", "blast", "--args", "symbol=helper", "-oJ")
        assert result.returncode == 0, result.stderr
        names = [r["symbol_name"] for r in json.loads(result.stdout)]
        assert "caller" in names
