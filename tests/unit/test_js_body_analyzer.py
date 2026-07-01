"""Unit tests for JS/TS function-body AST analyzers.

Verifies that _CallBodyAnalyzer, _HttpCallBodyAnalyzer, and _StringConstantBodyAnalyzer
correctly walk tree-sitter AST nodes and extract calls, http calls, and strings,
while respecting nested function boundaries.
"""

import pytest
from via.parsers.javascript_parser import JavaScriptParser
from via.parsers._js_body import (
    _CallBodyAnalyzer,
    _HttpCallBodyAnalyzer,
    _StringConstantBodyAnalyzer,
)


@pytest.fixture(scope="module")
def ts_parser():
    """Returns a tree-sitter Parser for javascript."""
    parser_instance = JavaScriptParser()
    # Ensure it's initialized
    ts_parser, _ = parser_instance._get_parser('javascript')
    return ts_parser


def test_call_body_analyzer(ts_parser):
    """Test _CallBodyAnalyzer extracts method and function calls, respecting boundaries."""
    js_code = b"""
    function processData(x) {
        validate(x);
        const y = format.clean(x);
        console.log(y);

        function nestedHelper() {
            // Should be ignored by parent analyzer
            nestedCall();
        }

        const arrow = () => {
            // Should be ignored by parent analyzer
            arrowCall();
        };
    }
    """
    tree = ts_parser.parse(js_code)
    root = tree.root_node
    
    # Locate the statement block of processData
    # Find the function_declaration and get its body (statement_block)
    func_node = next(n for n in root.children if n.type == 'function_declaration')
    body_node = func_node.child_by_field_name('body')
    assert body_node is not None

    analyzer = _CallBodyAnalyzer()
    entities = analyzer.collect(
        body_node,
        js_code,
        caller_name="processData",
        caller_type="function",
        caller_parent=None,
    )

    callees = [e.callee_name for e in entities]
    # 'validate', 'format.clean', and 'console.log' should be found.
    assert "validate" in callees
    assert "format.clean" in callees
    assert "console.log" in callees
    
    # 'nestedCall' and 'arrowCall' must not be found because they cross function boundaries.
    assert "nestedCall" not in callees
    assert "arrowCall" not in callees

    # Verify attributes of a collected entity
    validate_entity = next(e for e in entities if e.callee_name == "validate")
    assert validate_entity.caller_name == "processData"
    assert validate_entity.caller_type == "function"
    assert validate_entity.caller_parent is None
    assert validate_entity.line_number == 3  # validate(x) is on line 3


def test_http_call_body_analyzer(ts_parser):
    """Test _HttpCallBodyAnalyzer extracts HTTP URLs/paths, respecting boundaries."""
    js_code = b"""
    async function syncData() {
        const response1 = await fetch('/api/v1/users');
        const response2 = await axios.get("/api/v1/posts");
        const response3 = await axios.post(`/api/v1/create`);
        
        // This fetch is inside an arrow function callback, should be ignored
        const helper = () => fetch('/api/v1/ignored');
        
        // Non-fetch calls should not be captured
        doSomething('/api/v1/not-http');
    }
    """
    tree = ts_parser.parse(js_code)
    root = tree.root_node
    
    func_node = next(n for n in root.children if n.type == 'lexical_declaration' or n.type == 'function_declaration')
    # If async function is at top level
    body_node = func_node.child_by_field_name('body')
    assert body_node is not None

    analyzer = _HttpCallBodyAnalyzer()
    entities = analyzer.collect(
        body_node,
        js_code,
        caller_name="syncData",
        caller_type="function",
        caller_parent=None,
    )

    targets = [e.callee_name for e in entities]
    assert "/api/v1/users" in targets
    assert "/api/v1/posts" in targets
    assert "/api/v1/create" in targets
    assert "/api/v1/ignored" not in targets
    assert "/api/v1/not-http" not in targets


def test_string_constant_body_analyzer(ts_parser):
    """Test _StringConstantBodyAnalyzer extracts string constants, respecting boundaries."""
    js_code = b"""
    function main() {
        const title = 'User Dashboard';
        const msg = "Welcome back!";
        const tpl = `Items: ${count}`;

        function sub() {
            const inner = "hidden-string";
        }
    }
    """
    tree = ts_parser.parse(js_code)
    root = tree.root_node
    
    func_node = next(n for n in root.children if n.type == 'function_declaration')
    body_node = func_node.child_by_field_name('body')
    assert body_node is not None

    analyzer = _StringConstantBodyAnalyzer()
    entities = analyzer.collect(
        body_node,
        js_code,
        caller_name="main",
        caller_type="function",
        caller_parent=None,
    )

    values = [e.value for e in entities]
    assert "User Dashboard" in values
    assert "Welcome back!" in values
    assert "Items: ${count}" in values
    assert "hidden-string" not in values
