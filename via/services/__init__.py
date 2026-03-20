"""
High-level services orchestrating core functionality.

TLDR:
    Package exposing IndexingService (indexing.py) and WatchService (watch.py).
    IndexingService drives the full index pipeline; WatchService adds filesystem
    watch-mode on top of it. Consumed by via/commands/index.py and __main__.py.

"""
