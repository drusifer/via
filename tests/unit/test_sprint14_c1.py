"""Sprint 14 Cycle 1 unit tests — JS/TS calls relationship extraction.

TLDR:
    Verifies JavaScriptParser._extract_all_calls() populates ParseResult.calls
    with CallEntity records for named functions, arrow functions, class methods,
    and exported functions/classes in JS and TS fixtures.
"""

import pytest

from via.parsers.javascript_parser import JavaScriptParser
from via.parsers.base import CallEntity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JS_CALLS_FIXTURE = b"""
import { logger } from './logger';

function greet(name) {
    const msg = formatMessage(name);
    logger.info(msg);
    return msg;
}

function formatMessage(name) {
    return 'Hello, ' + name;
}

const processUser = (user) => {
    validate(user);
    return greet(user.name);
};

class UserService {
    load(id) {
        return fetchUser(id);
    }
    save(user) {
        validate(user);
        this.persist(user);
    }
}

export function exportedHelper(x) {
    return compute(x);
}
"""

TS_CALLS_FIXTURE = b"""
class DataService {
    fetch(id: number): void {
        const data = loadData(id);
        transform(data);
    }
}

const handler = (event: Event): void => {
    dispatch(event);
};
"""

JS_NO_CALLS_FIXTURE = b"""
function noCallsHere() {
    const x = 1 + 2;
    return x;
}
"""

JS_INHERITANCE_FIXTURE = b"""
class Animal {
    speak() { return 'sound'; }
}

class Dog extends Animal {
    speak() {
        const s = makeSound('woof');
        return s;
    }
}
"""


@pytest.fixture
def parser():
    return JavaScriptParser()


@pytest.fixture
def js_calls_result(parser):
    return parser.parse('service.js', JS_CALLS_FIXTURE)


@pytest.fixture
def ts_calls_result(parser):
    return parser.parse('data.service.ts', TS_CALLS_FIXTURE)


# ---------------------------------------------------------------------------
# Named function calls
# ---------------------------------------------------------------------------

class TestNamedFunctionCalls:

    def test_calls_populated(self, js_calls_result):
        assert len(js_calls_result.calls) > 0

    def test_named_function_caller(self, js_calls_result):
        callers = {c.caller_name for c in js_calls_result.calls}
        assert 'greet' in callers

    def test_callee_identifier(self, js_calls_result):
        greet_calls = [c for c in js_calls_result.calls if c.caller_name == 'greet']
        callees = {c.callee_name for c in greet_calls}
        assert 'formatMessage' in callees

    def test_member_expression_callee(self, js_calls_result):
        greet_calls = [c for c in js_calls_result.calls if c.caller_name == 'greet']
        callees = {c.callee_name for c in greet_calls}
        assert 'logger.info' in callees

    def test_caller_type_is_function(self, js_calls_result):
        greet_calls = [c for c in js_calls_result.calls if c.caller_name == 'greet']
        assert all(c.caller_type == 'function' for c in greet_calls)

    def test_caller_parent_is_none_for_function(self, js_calls_result):
        greet_calls = [c for c in js_calls_result.calls if c.caller_name == 'greet']
        assert all(c.caller_parent is None for c in greet_calls)


# ---------------------------------------------------------------------------
# Arrow function calls
# ---------------------------------------------------------------------------

class TestArrowFunctionCalls:

    def test_arrow_function_caller(self, js_calls_result):
        callers = {c.caller_name for c in js_calls_result.calls}
        assert 'processUser' in callers

    def test_arrow_function_callee(self, js_calls_result):
        arrow_calls = [c for c in js_calls_result.calls if c.caller_name == 'processUser']
        callees = {c.callee_name for c in arrow_calls}
        assert 'validate' in callees
        assert 'greet' in callees


# ---------------------------------------------------------------------------
# Class method calls
# ---------------------------------------------------------------------------

class TestMethodCalls:

    def test_method_caller(self, js_calls_result):
        callers = {c.caller_name for c in js_calls_result.calls}
        assert 'load' in callers
        assert 'save' in callers

    def test_method_caller_type(self, js_calls_result):
        method_calls = [c for c in js_calls_result.calls if c.caller_name == 'load']
        assert all(c.caller_type == 'method' for c in method_calls)

    def test_method_caller_parent(self, js_calls_result):
        load_calls = [c for c in js_calls_result.calls if c.caller_name == 'load']
        assert all(c.caller_parent == 'UserService' for c in load_calls)

    def test_method_callee(self, js_calls_result):
        load_calls = [c for c in js_calls_result.calls if c.caller_name == 'load']
        callees = {c.callee_name for c in load_calls}
        assert 'fetchUser' in callees


# ---------------------------------------------------------------------------
# Exported function calls
# ---------------------------------------------------------------------------

class TestExportedFunctionCalls:

    def test_exported_function_caller(self, js_calls_result):
        callers = {c.caller_name for c in js_calls_result.calls}
        assert 'exportedHelper' in callers

    def test_exported_function_callee(self, js_calls_result):
        helper_calls = [c for c in js_calls_result.calls if c.caller_name == 'exportedHelper']
        callees = {c.callee_name for c in helper_calls}
        assert 'compute' in callees


# ---------------------------------------------------------------------------
# TypeScript calls
# ---------------------------------------------------------------------------

class TestTypeScriptCalls:

    def test_ts_method_caller(self, ts_calls_result):
        callers = {c.caller_name for c in ts_calls_result.calls}
        assert 'fetch' in callers

    def test_ts_method_callee(self, ts_calls_result):
        fetch_calls = [c for c in ts_calls_result.calls if c.caller_name == 'fetch']
        callees = {c.callee_name for c in fetch_calls}
        assert 'loadData' in callees
        assert 'transform' in callees

    def test_ts_arrow_function_calls(self, ts_calls_result):
        callers = {c.caller_name for c in ts_calls_result.calls}
        assert 'handler' in callers


# ---------------------------------------------------------------------------
# No calls case
# ---------------------------------------------------------------------------

class TestNoCalls:

    def test_no_calls_returns_empty(self, parser):
        result = parser.parse('noop.js', JS_NO_CALLS_FIXTURE)
        # noCallsHere has no function calls
        assert all(c.caller_name != 'noCallsHere' for c in result.calls)


# ---------------------------------------------------------------------------
# Inheritance (confirms inherits-from already works for JS)
# ---------------------------------------------------------------------------

class TestJSInheritance:

    def test_subclass_bases_populated(self, parser):
        result = parser.parse('animals.js', JS_INHERITANCE_FIXTURE)
        dog = next((c for c in result.classes if c.name == 'Dog'), None)
        assert dog is not None
        assert dog.bases == 'Animal'

    def test_method_calls_in_subclass(self, parser):
        result = parser.parse('animals.js', JS_INHERITANCE_FIXTURE)
        speak_calls = [c for c in result.calls if c.caller_name == 'speak'
                       and c.caller_parent == 'Dog']
        callees = {c.callee_name for c in speak_calls}
        assert 'makeSound' in callees


# ---------------------------------------------------------------------------
# CallEntity field types
# ---------------------------------------------------------------------------

class TestCallEntityFields:

    def test_call_entity_has_line_number(self, js_calls_result):
        for call in js_calls_result.calls:
            assert isinstance(call.line_number, int)
            assert call.line_number > 0

    def test_call_entity_has_byte_offset(self, js_calls_result):
        for call in js_calls_result.calls:
            assert isinstance(call.byte_offset, int)
            assert call.byte_offset >= 0

    def test_call_entity_has_byte_length(self, js_calls_result):
        for call in js_calls_result.calls:
            assert isinstance(call.byte_length, int)
            assert call.byte_length > 0
