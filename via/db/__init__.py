"""
Database package for via — provides SQLite-backed persistent index storage.

TLDR:
    Namespace package grouping the database schema and store modules used by
    the via indexing pipeline. Contains no logic of its own; its role is to
    make the db sub-tree importable as `via.db`.
    Key modules: schema (DDL and table definitions), store (ViaStore — the
    CRUD interface consumed by the indexing service and CLI commands).
    Depends on nothing inside via at package-init time; consumed by
    via.services.indexing and via.commands.
"""
