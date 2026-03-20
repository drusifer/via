"""
SQL DDL constants and schema version for the VIA index database.

TLDR:
    Defines CREATE TABLE and CREATE INDEX statements for all five VIA tables:
    metadata, schema_migrations, files, symbols, symbol_references, and
    pending_relationships. The symbols table is intentionally denormalized
    (file_path stored inline) to enable zero-JOIN lookups. Pending
    relationships support the two-pass cross-file resolution strategy used
    during indexing. ALL_TABLES and CREATE_INDEXES are consumed by the
    store's initializer to bootstrap or migrate the database.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

# Schema version for migrations
SCHEMA_VERSION = 3

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

# Denormalized symbols table for fast matching
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

# Symbol references table for relationship queries
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

# Pending relationships for two-pass indexing
CREATE_PENDING_RELATIONSHIPS_TABLE = """
CREATE TABLE IF NOT EXISTS pending_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES symbols(id) ON DELETE CASCADE
);
"""

# Index definitions for performance
CREATE_INDEXES = [
    # Files indexes
    "CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);",
    "CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);",
    "CREATE INDEX IF NOT EXISTS idx_files_parsed ON files(parsed);",

    # Symbols indexes
    "CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(symbol_name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_type_name ON symbols(symbol_type, symbol_name);",
    "CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path);",

    # Symbol references indexes
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_from ON symbol_references(from_symbol_id);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_to ON symbol_references(to_symbol_id);",
    "CREATE INDEX IF NOT EXISTS idx_symbol_references_type ON symbol_references(reference_type);",

    # Pending relationships indexes
    "CREATE INDEX IF NOT EXISTS idx_pending_rel_source ON pending_relationships(source_id);",
    "CREATE INDEX IF NOT EXISTS idx_pending_rel_target ON pending_relationships(target_name);",
]

# All table creation statements in dependency order
ALL_TABLES = [
    CREATE_METADATA_TABLE,
    CREATE_SCHEMA_MIGRATIONS_TABLE,
    CREATE_FILES_TABLE,
    CREATE_SYMBOLS_TABLE,
    CREATE_REFERENCES_TABLE,
    CREATE_PENDING_RELATIONSHIPS_TABLE,
]
