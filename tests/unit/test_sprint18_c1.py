"""Sprint 18 Cycle 1 tests — polymorphic JS parser top-level handlers."""

import pytest

from via.parsers.javascript_parser import JavaScriptParser


JS_POLYMORPHIC_FIXTURE = b"""
import { readFile } from 'fs';

function greet(name) {
    return name;
}

class Service {
    load() {
        return greet('x');
    }
}

const handler = () => greet('y');

export function exportedHelper() {
    return handler();
}

export default class ExportedService {
    run() {
        return exportedHelper();
    }
}
"""


TS_POLYMORPHIC_FIXTURE = b"""
interface UserShape {
    id: string;
}

enum Status {
    Ready,
    Done,
}

type UserId = string;

const mapper = (id: UserId) => id;

export default function lookup(id: UserId): UserShape {
    return { id: mapper(id) };
}
"""


@pytest.fixture
def parser():
    return JavaScriptParser()


def test_refactor_preserves_js_top_level_symbol_extraction(parser):
    result = parser.parse("service.js", JS_POLYMORPHIC_FIXTURE)
    if result.parse_error and "tree-sitter" in result.parse_error:
        pytest.skip(result.parse_error)

    assert {imp.module for imp in result.imports} == {"fs"}
    assert {func.name for func in result.functions} == {
        "greet",
        "handler",
        "exportedHelper",
    }
    assert {cls.name for cls in result.classes} == {
        "Service",
        "ExportedService",
    }
    exported_class = next(cls for cls in result.classes if cls.name == "ExportedService")
    assert {method.name for method in exported_class.methods} == {"run"}


def test_refactor_preserves_ts_top_level_symbol_extraction(parser):
    result = parser.parse("types.ts", TS_POLYMORPHIC_FIXTURE)
    if result.parse_error and "tree-sitter" in result.parse_error:
        pytest.skip(result.parse_error)

    classes = {(cls.name, cls.symbol_subtype) for cls in result.classes}
    assert ("UserShape", "interface") in classes
    assert ("Status", "enum") in classes
    assert {func.name for func in result.functions} == {"mapper", "lookup"}
    assert {glob.name for glob in result.globals} == {"UserId"}
