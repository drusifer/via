"""
GET /api/status handler for the via Web UI.

TLDR:
    get_status() aggregates index stats from DatabaseStore and re-index
    event state from WebServer into the JSON payload for /api/status.
    A fresh DatabaseStore connection is opened per call (Sprint 6 thread-
    safety lesson: never share a SQLite connection across threads).

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from via.db.store import DatabaseStore
    from via.web.server import WebServer


def get_status(db_store: "DatabaseStore", web_server: "WebServer") -> dict:
    """Build the /api/status response payload.

    Args:
        db_store: Connected DatabaseStore instance.
        web_server: Running WebServer instance (provides reindex_state).

    Returns:
        dict suitable for JSON serialisation.
    """
    counts = db_store.get_counts()
    last_indexed = db_store.get_last_indexed_iso()
    reindex = web_server.reindex_state

    return {
        "directory": db_store.index_root,
        "file_count": counts["files"],
        "symbol_count": counts["symbols"],
        "last_indexed": last_indexed,
        "watching": True,
        "last_reindex_count": reindex["count"],
        "last_reindex_files": reindex["last_count"],
        "last_reindex_time": reindex["last_time"],
    }
