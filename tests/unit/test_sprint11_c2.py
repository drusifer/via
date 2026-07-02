"""Sprint 11 Cycle 2 unit tests — JavaScriptParser AST + schema migrations.

TLDR:
    Verifies JavaScriptParser extracts correct FunctionEntity, ClassEntity,
    ImportEntity, and GlobalEntity from JS and TS fixtures. Also tests schema
    migration v6 adds language and symbol_subtype columns to an existing DB.
"""

import sqlite3
import tempfile

import pytest

from via.parsers.javascript_parser import JavaScriptParser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JS_FIXTURE = b"""
import React from 'react';
import { useState, useEffect } from 'react';
import * as lodash from 'lodash';

const BASE_URL = 'https://api.example.com';

const fetchUser = async (id) => {
    return fetch(BASE_URL + id);
};

class UserList extends React.Component {
    render() {
        return null;
    }
    componentDidMount() {}
}

function formatName(first, last) {
    return first + ' ' + last;
}

export default UserList;
"""

TS_FIXTURE = b"""
import { Injectable } from '@angular/core';

interface User {
    id: number;
    name: string;
}

type UserId = string | number;

enum Role { Admin = 'admin', Guest = 'guest' }

class UserService {
    getUser(id: UserId): User {
        return { id: 1, name: 'test' };
    }
}

const createUser = (name: string): User => ({ id: 0, name });
"""

SYNTAX_ERROR_FIXTURE = b"""
function goodFunction() { return 1; }
const broken = {{{;
class GoodClass {}
"""


@pytest.fixture
def js_parser():
    return JavaScriptParser()


@pytest.fixture
def js_result(js_parser):
    return js_parser.parse('Button.jsx', JS_FIXTURE)


@pytest.fixture
def ts_result(js_parser):
    return js_parser.parse('user.service.ts', TS_FIXTURE)


# ---------------------------------------------------------------------------
# S11-2: JavaScript parsing — functions
# ---------------------------------------------------------------------------

class TestJSFunctions:

    def test_named_function_extracted(self, js_result):
        names = [f.name for f in js_result.functions]
        assert 'formatName' in names

    def test_arrow_function_extracted(self, js_result):
        names = [f.name for f in js_result.functions]
        assert 'fetchUser' in names

    def test_arrow_function_subtype_set(self, js_result):
        fn = next(f for f in js_result.functions if f.name == 'fetchUser')
        assert fn.symbol_subtype == 'arrow_function'

    def test_named_function_subtype_none(self, js_result):
        fn = next(f for f in js_result.functions if f.name == 'formatName')
        assert fn.symbol_subtype is None

    def test_function_line_numbers_correct(self, js_result):
        fn = next(f for f in js_result.functions if f.name == 'formatName')
        assert fn.line_start > 0
        assert fn.line_end >= fn.line_start

    def test_function_byte_offset_set(self, js_result):
        fn = next(f for f in js_result.functions if f.name == 'formatName')
        assert fn.byte_offset is not None
        assert fn.byte_length is not None
        assert fn.byte_length > 0

    def test_no_parse_error_on_valid_js(self, js_result):
        assert js_result.parse_error is None


# ---------------------------------------------------------------------------
# S11-2: JavaScript parsing — classes + inheritance
# ---------------------------------------------------------------------------

class TestJSClasses:

    def test_class_extracted(self, js_result):
        names = [c.name for c in js_result.classes]
        assert 'UserList' in names

    def test_class_inheritance_captured(self, js_result):
        cls = next(c for c in js_result.classes if c.name == 'UserList')
        assert cls.bases == 'React.Component'

    def test_class_methods_extracted(self, js_result):
        cls = next(c for c in js_result.classes if c.name == 'UserList')
        method_names = [m.name for m in cls.methods]
        assert 'render' in method_names
        assert 'componentDidMount' in method_names

    def test_class_line_numbers(self, js_result):
        cls = next(c for c in js_result.classes if c.name == 'UserList')
        assert cls.line_start > 0
        assert cls.line_end >= cls.line_start


# ---------------------------------------------------------------------------
# S11-2: JavaScript parsing — imports
# ---------------------------------------------------------------------------

class TestJSImports:

    def test_default_import_extracted(self, js_result):
        imports = [(i.module, i.name) for i in js_result.imports]
        assert ('react', 'React') in imports

    def test_named_imports_one_per_specifier(self, js_result):
        react_imports = [i for i in js_result.imports if i.module == 'react' and i.name in ('useState', 'useEffect')]
        assert len(react_imports) == 2

    def test_namespace_import_extracted(self, js_result):
        lodash = next((i for i in js_result.imports if i.module == 'lodash'), None)
        assert lodash is not None
        assert lodash.alias == 'lodash'

    def test_import_line_number_set(self, js_result):
        for imp in js_result.imports:
            assert imp.line_number > 0


# ---------------------------------------------------------------------------
# S11-2: JavaScript parsing — globals
# ---------------------------------------------------------------------------

class TestJSGlobals:

    def test_module_level_const_extracted(self, js_result):
        names = [g.name for g in js_result.globals]
        assert 'BASE_URL' in names

    def test_arrow_function_not_in_globals(self, js_result):
        # Arrow functions should be in functions, not globals
        global_names = [g.name for g in js_result.globals]
        assert 'fetchUser' not in global_names


# ---------------------------------------------------------------------------
# S11-2: TypeScript parsing — interfaces, enums, type aliases
# ---------------------------------------------------------------------------

class TestTSParsing:

    def test_ts_interface_extracted_as_class(self, ts_result):
        names = [c.name for c in ts_result.classes]
        assert 'User' in names

    def test_ts_interface_subtype_set(self, ts_result):
        cls = next(c for c in ts_result.classes if c.name == 'User')
        assert cls.symbol_subtype == 'interface'

    def test_ts_enum_extracted_as_class(self, ts_result):
        names = [c.name for c in ts_result.classes]
        assert 'Role' in names

    def test_ts_enum_subtype_set(self, ts_result):
        cls = next(c for c in ts_result.classes if c.name == 'Role')
        assert cls.symbol_subtype == 'enum'

    def test_ts_class_extracted(self, ts_result):
        names = [c.name for c in ts_result.classes]
        assert 'UserService' in names

    def test_ts_class_subtype_none(self, ts_result):
        cls = next(c for c in ts_result.classes if c.name == 'UserService')
        assert cls.symbol_subtype is None

    def test_ts_type_alias_extracted_as_global(self, ts_result):
        names = [g.name for g in ts_result.globals]
        assert 'UserId' in names

    def test_ts_method_extracted(self, ts_result):
        svc = next(c for c in ts_result.classes if c.name == 'UserService')
        assert any(m.name == 'getUser' for m in svc.methods)

    def test_ts_language_set(self, ts_result):
        assert ts_result.language == 'typescript'

    def test_ts_arrow_function_extracted(self, ts_result):
        names = [f.name for f in ts_result.functions]
        assert 'createUser' in names


# ---------------------------------------------------------------------------
# S11-2: Partial parse on syntax error
# ---------------------------------------------------------------------------

class TestPartialParse:

    def test_syntax_error_sets_parse_error(self, js_parser):
        result = js_parser.parse('broken.js', SYNTAX_ERROR_FIXTURE)
        assert result.parse_error is not None

    def test_valid_symbols_returned_despite_error(self, js_parser):
        result = js_parser.parse('broken.js', SYNTAX_ERROR_FIXTURE)
        names = [f.name for f in result.functions] + [c.name for c in result.classes]
        assert 'goodFunction' in names or 'GoodClass' in names

    def test_size_limit_respected(self, js_parser):
        huge = b'x' * (11 * 1024 * 1024)
        result = js_parser.parse('huge.js', huge)
        assert result.parse_error is not None
        assert 'limit' in result.parse_error.lower()


# ---------------------------------------------------------------------------
# S11-2: Schema migration v6 — language + symbol_subtype columns
# ---------------------------------------------------------------------------

class TestSchemaMigrationV6:

    def test_fresh_db_has_language_column(self, tmp_path):
        from via.db.store import DatabaseStore
        db_path = str(tmp_path / 'index.db')
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()
        cols = {row[1] for row in store.conn.execute("PRAGMA table_info(symbols)")}
        assert 'language' in cols
        assert 'symbol_subtype' in cols
        store.close()

    def test_existing_db_migrates_to_v6(self, tmp_path):
        """A v5 DB without language/symbol_subtype gets both columns added."""
        db_path = str(tmp_path / 'index.db')

        # Build a v5 DB manually (full files table, symbols without language/symbol_subtype)
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at REAL NOT NULL, description TEXT)")
        conn.execute("""CREATE TABLE files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL, language TEXT,
            size_bytes INTEGER, mtime REAL, indexed_at REAL,
            parsed BOOLEAN DEFAULT 0, oversized BOOLEAN DEFAULT 0
        )""")
        conn.execute("""CREATE TABLE symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol_name TEXT NOT NULL, symbol_type TEXT NOT NULL,
            file_path TEXT NOT NULL, line_number INTEGER NOT NULL,
            byte_offset INTEGER, byte_length INTEGER,
            qualified_name TEXT NOT NULL, parent_name TEXT, mtime REAL
        )""")
        conn.execute("""CREATE TABLE symbol_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_symbol_id INTEGER NOT NULL, to_symbol_id INTEGER NOT NULL,
            reference_type TEXT NOT NULL, line_number INTEGER,
            FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
            FOREIGN KEY (to_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
        )""")
        conn.execute("""CREATE TABLE pending_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL, target_name TEXT NOT NULL, rel_type TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES symbols(id) ON DELETE CASCADE
        )""")
        conn.execute("""CREATE TABLE line_offsets (
            file_id INTEGER NOT NULL, line_number INTEGER NOT NULL,
            byte_offset INTEGER NOT NULL, byte_length INTEGER NOT NULL,
            PRIMARY KEY (file_id, line_number)
        )""")
        conn.execute("INSERT INTO metadata VALUES ('schema_version', '5')")
        conn.commit()
        conn.close()

        from via.db.store import DatabaseStore
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()

        cols = {row[1] for row in store.conn.execute("PRAGMA table_info(symbols)")}
        assert 'language' in cols, "language column missing after v6 migration"
        assert 'symbol_subtype' in cols, "symbol_subtype column missing after v6 migration"

        version = store.get_metadata("schema_version")
        assert version == "7"
        store.close()

    def test_language_populated_on_insert(self, tmp_path):
        """insert_symbol stores language on the symbols row."""
        from via.db.store import DatabaseStore
        db_path = str(tmp_path / 'index.db')
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()

        sym_id = store.insert_symbol(
            symbol_name='fetchUser',
            symbol_type='function',
            file_path='src/api.js',
            line_number=5,
            qualified_name='src/api.js.fetchUser',
            language='javascript',
        )
        row = store.conn.execute(
            "SELECT language FROM symbols WHERE id = ?", (sym_id,)
        ).fetchone()
        assert row[0] == 'javascript'
        store.close()

    def test_symbol_subtype_stored(self, tmp_path):
        """insert_symbol stores symbol_subtype on the symbols row."""
        from via.db.store import DatabaseStore
        db_path = str(tmp_path / 'index.db')
        store = DatabaseStore(db_path, str(tmp_path))
        store.connect()
        store.initialize_schema()

        sym_id = store.insert_symbol(
            symbol_name='User',
            symbol_type='class',
            file_path='src/types.ts',
            line_number=3,
            qualified_name='src/types.ts.User',
            language='typescript',
            symbol_subtype='interface',
        )
        row = store.conn.execute(
            "SELECT language, symbol_subtype FROM symbols WHERE id = ?", (sym_id,)
        ).fetchone()
        assert row[0] == 'typescript'
        assert row[1] == 'interface'
        store.close()
