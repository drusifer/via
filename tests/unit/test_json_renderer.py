"""
Unit tests for JsonRenderer (Sprint 7 P1).

TLDR:
    Tests RenderType.JSON enum addition, supports_render_type base class refactor,
    JsonRenderer._to_dict() field completeness, JSON validity, None serialization,
    and -oJ flag registration in OUTPUT_FLAGS / RendererFactory.

Author: Drew Gutstein
------------------------------------------------------------------------------
License: GPL-3.0
"""

import json

import pytest

from via.core.match_record import (
    ClassMatchRecord,
    FileMatchRecord,
    FunctionMatchRecord,
    GlobalMatchRecord,
    HeaderMatchRecord,
    ImportMatchRecord,
    MatchRecord,
    MethodMatchRecord,
    RenderType,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_class_record(**overrides):
    defaults = dict(
        symbol_type='class',
        symbol_name='MyClass',
        qualified_name='mymodule.MyClass',
        file_path='mymodule.py',
        line_number=10,
        byte_offset=100,
        byte_length=200,
        parent_name=None,
    )
    defaults.update(overrides)
    return ClassMatchRecord(**defaults)


def make_function_record(**overrides):
    defaults = dict(
        symbol_type='function',
        symbol_name='my_func',
        qualified_name='mymodule.my_func',
        file_path='mymodule.py',
        line_number=50,
        byte_offset=None,
        byte_length=None,
        parent_name=None,
    )
    defaults.update(overrides)
    return FunctionMatchRecord(**defaults)


# ── P1-1: RenderType.JSON ──────────────────────────────────────────────────

class TestRenderTypeJSON:
    def test_json_render_type_exists(self):
        assert RenderType.JSON.value == 'json'

    def test_json_is_member_of_render_type(self):
        assert 'JSON' in RenderType.__members__


# ── P1-2: supports_render_type refactor ───────────────────────────────────

class TestSupportsRenderTypeRefactor:
    """JSON must be universally supported by ALL MatchRecord subclasses."""

    def _all_record_types(self):
        return [
            ClassMatchRecord(
                symbol_type='class', symbol_name='C', qualified_name='m.C',
                file_path='m.py', line_number=1,
            ),
            MethodMatchRecord(
                symbol_type='method', symbol_name='m', qualified_name='m.C.m',
                file_path='m.py', line_number=2,
            ),
            FunctionMatchRecord(
                symbol_type='function', symbol_name='f', qualified_name='m.f',
                file_path='m.py', line_number=3,
            ),
            FileMatchRecord(
                symbol_type='filepath', symbol_name='m.py', qualified_name='m.py',
                file_path='m.py', line_number=0,
            ),
            ImportMatchRecord(
                symbol_type='import', symbol_name='os', qualified_name='os',
                file_path='m.py', line_number=1,
            ),
            GlobalMatchRecord(
                symbol_type='global', symbol_name='X', qualified_name='m.X',
                file_path='m.py', line_number=5,
            ),
            HeaderMatchRecord(
                symbol_type='header', symbol_name='Intro', qualified_name='Intro',
                file_path='README.md', line_number=1,
            ),
        ]

    def test_all_subclasses_support_json(self):
        for record in self._all_record_types():
            assert record.supports_render_type(RenderType.JSON), \
                f"{type(record).__name__} should support JSON"

    def test_class_still_supports_diagram(self):
        r = ClassMatchRecord(
            symbol_type='class', symbol_name='C', qualified_name='m.C',
            file_path='m.py', line_number=1,
        )
        assert r.supports_render_type(RenderType.DIAGRAM)

    def test_method_still_rejects_diagram(self):
        r = MethodMatchRecord(
            symbol_type='method', symbol_name='m', qualified_name='C.m',
            file_path='m.py', line_number=1,
        )
        assert not r.supports_render_type(RenderType.DIAGRAM)

    def test_file_still_rejects_usage(self):
        r = FileMatchRecord(
            symbol_type='filepath', symbol_name='f.py', qualified_name='f.py',
            file_path='f.py', line_number=0,
        )
        assert not r.supports_render_type(RenderType.USAGE)


# ── P1-3: JsonRenderer._to_dict ───────────────────────────────────────────

class TestJsonRendererToDict:
    def test_all_fields_present(self):
        from via.renderers.json_renderer import JsonRenderer
        record = make_class_record()
        d = JsonRenderer._to_dict(record)
        expected_keys = {
            'symbol_name', 'symbol_type', 'qualified_name',
            'file_path', 'line_number', 'byte_offset', 'byte_length', 'parent_name',
        }
        assert set(d.keys()) == expected_keys

    def test_values_correct(self):
        from via.renderers.json_renderer import JsonRenderer
        record = make_class_record()
        d = JsonRenderer._to_dict(record)
        assert d['symbol_name'] == 'MyClass'
        assert d['symbol_type'] == 'class'
        assert d['qualified_name'] == 'mymodule.MyClass'
        assert d['file_path'] == 'mymodule.py'
        assert d['line_number'] == 10
        assert d['byte_offset'] == 100
        assert d['byte_length'] == 200
        assert d['parent_name'] is None

    def test_none_fields_serialize_as_null(self):
        from via.renderers.json_renderer import JsonRenderer
        record = make_function_record()
        d = JsonRenderer._to_dict(record)
        assert d['byte_offset'] is None
        assert d['byte_length'] is None
        assert d['parent_name'] is None
        # Check JSON serialization produces null
        j = json.dumps(d)
        assert '"byte_offset": null' in j or 'null' in j


class TestJsonRendererRender:
    def test_render_returns_valid_json(self):
        from via.renderers.json_renderer import JsonRenderer
        records = [make_class_record(), make_function_record()]
        renderer = JsonRenderer()
        output = renderer.render(iter(records))
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_render_empty_returns_empty_array(self):
        from via.renderers.json_renderer import JsonRenderer
        renderer = JsonRenderer()
        output = renderer.render(iter([]))
        assert json.loads(output) == []

    def test_render_single_record(self):
        from via.renderers.json_renderer import JsonRenderer
        renderer = JsonRenderer()
        output = renderer.render(iter([make_class_record()]))
        parsed = json.loads(output)
        assert len(parsed) == 1
        assert parsed[0]['symbol_name'] == 'MyClass'


# ── P1-4: -oJ flag in OUTPUT_FLAGS ────────────────────────────────────────

class TestOutputJSONFlag:
    def test_oJ_flag_exists_in_output_flags(self):
        from via.core.flag_groups import OUTPUT_FLAGS
        shorts = [f.short for f in OUTPUT_FLAGS]
        assert '-oJ' in shorts

    def test_oJ_flag_dest_and_const(self):
        from via.core.flag_groups import OUTPUT_FLAGS
        flag = next(f for f in OUTPUT_FLAGS if f.short == '-oJ')
        assert flag.dest == 'render_type'
        assert flag.const == 'json'

    def test_oJ_long_name(self):
        from via.core.flag_groups import OUTPUT_FLAGS
        flag = next(f for f in OUTPUT_FLAGS if f.short == '-oJ')
        assert flag.long == '--output-json'


# ── P1-5: RendererFactory registers JsonRenderer ──────────────────────────

class TestRendererFactoryJSON:
    def test_factory_creates_json_renderer(self):
        from via.renderers.factory import RendererFactory
        from via.renderers.json_renderer import JsonRenderer
        renderer = RendererFactory.create(RenderType.JSON)
        assert isinstance(renderer, JsonRenderer)

    def test_factory_json_needs_no_format_type(self):
        from via.renderers.factory import RendererFactory
        # Should not raise even without format_type
        renderer = RendererFactory.create(RenderType.JSON, format_type=None)
        assert renderer is not None
