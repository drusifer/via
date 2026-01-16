"""
Database schema definitions for VIA index.

TLDR:
    Schema v2 uses denormalized symbols table for fast matching (eliminates JOINs).
    Legacy tables (functions, classes, imports, globals) retained for backward compat.
    New tables: symbols (denormalized), references (for future relationship queries).
    Files table retained for metadata only.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

# Schema version for migrations
SCHEMA_VERSION = 2

# SQL statements for creating tables
CREATE_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

CREATE_SCHEMA_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL,
    description TEXT
);
"""

CREATE_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    language TEXT,
    size_bytes INTEGER,
    mtime REAL,
    indexed_at REAL,
    parsed BOOLEAN DEFAULT 0,
    oversized BOOLEAN DEFAULT 0
);
"""

CREATE_FUNCTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    class_id INTEGER,
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    args TEXT,
    decorators TEXT,
    docstring TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
);
"""

CREATE_CLASSES_TABLE = """
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    bases TEXT,
    decorators TEXT,
    docstring TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""

CREATE_IMPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    name TEXT,
    alias TEXT,
    line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""

CREATE_GLOBALS_TABLE = """
CREATE TABLE IF NOT EXISTS globals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    value TEXT,
    type_hint TEXT,
    line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""

CREATE_LOG_STATEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS log_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    line_number INTEGER,
    call_name TEXT NOT NULL,
    message TEXT,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""

CREATE_MARKDOWN_HEADINGS_TABLE = """
CREATE TABLE IF NOT EXISTS markdown_headings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    text TEXT NOT NULL,
    line_number INTEGER,
    byte_offset INTEGER NOT NULL,
    byte_length INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
"""

# Schema v2: Denormalized symbols table for fast matching
CREATE_SYMBOLS_TABLE = """
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_name TEXT NOT NULL,
    symbol_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    byte_offset INTEGER,
    byte_length INTEGER,
    qualified_name TEXT NOT NULL,
    parent_name TEXT
);
"""

# Schema v2: Symbol references table for relationship queries (future)
CREATE_REFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS symbol_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_symbol_id INTEGER NOT NULL,
    to_symbol_id INTEGER NOT NULL,
    reference_type TEXT NOT NULL,
    line_number INTEGER,
    FOREIGN KEY (from_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    FOREIGN KEY (to_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
);
"""

# Index definitions for performance
CREATE_INDEXES = [
    # v1 indexes (legacy tables)
    "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);",
    "CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);",
    "CREATE INDEX IF NOT EXISTS idx_files_parsed ON files(parsed);",
    "CREATE INDEX IF NOT EXISTS idx_functions_name ON functions(name);",
    "CREATE INDEX IF NOT EXISTS idx_functions_file_id ON functions(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_functions_class_id ON functions(class_id);",
    "CREATE INDEX IF NOT EXISTS idx_classes_name ON classes(name);",
    "CREATE INDEX IF NOT EXISTS idx_classes_file_id ON classes(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_imports_module ON imports(module);",
    "CREATE INDEX IF NOT EXISTS idx_imports_file_id ON imports(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_globals_name ON globals(name);",
    "CREATE INDEX IF NOT EXISTS idx_globals_file_id ON globals(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_log_statements_file_id ON log_statements(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_markdown_headings_file_id ON markdown_headings(file_id);",

    # v2 indexes (symbols and symbol_references tables)
    "CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(symbol_name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_type_name ON symbols(symbol_type, symbol_name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_from ON symbol_references(from_symbol_id);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_to ON symbol_references(to_symbol_id);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_type ON symbol_references(reference_type);",
]

# All table creation statements in dependency order
ALL_TABLES = [
    CREATE_METADATA_TABLE,
    CREATE_SCHEMA_MIGRATIONS_TABLE,
    CREATE_FILES_TABLE,
    CREATE_CLASSES_TABLE,  # Must come before functions due to foreign key
    CREATE_FUNCTIONS_TABLE,
    CREATE_IMPORTS_TABLE,
    CREATE_GLOBALS_TABLE,
    CREATE_LOG_STATEMENTS_TABLE,
    CREATE_MARKDOWN_HEADINGS_TABLE,
    # v2 tables
    CREATE_SYMBOLS_TABLE,
    CREATE_REFERENCES_TABLE,
]
