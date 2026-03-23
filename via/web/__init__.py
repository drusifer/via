"""
Web UI module for via — serves a browser-based query interface.

TLDR:
    Exports WebServer, which starts a ThreadingHTTPServer in a daemon thread
    alongside via index -w or via mcp serve. The UI is served at
    http://localhost:<port> (default 7891).

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from .server import WebServer

__all__ = ["WebServer"]
