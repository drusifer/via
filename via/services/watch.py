"""
Filesystem watch service that triggers incremental re-indexing on file changes.

TLDR:
    WatchService wraps the watchdog library to observe a directory tree for
    create/modify/delete/move events on .py, .pyx, .pyi, and .md files. Events
    are debounced (default 500 ms) to coalesce rapid saves, then dispatched to
    IndexingService for incremental re-index or symbol removal. The internal
    _ViaEventHandler class bridges watchdog callbacks to WatchService._schedule.
    Runs until Ctrl-C (SIGINT), prints terse per-file feedback to stdout.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""

import logging
import os
import signal
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from via.core.path_filter import PathFilter
from via.db.store import DatabaseStore
from via.services.indexing import IndexingService

logger = logging.getLogger(__name__)

WATCHED_EXTENSIONS = {'.py', '.pyx', '.pyi', '.md'}


class _ViaEventHandler(FileSystemEventHandler):
    """Watchdog event handler that delegates to WatchService."""

    def __init__(self, svc: 'WatchService') -> None:
        self._svc = svc

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._svc._schedule(event.src_path, 'modified')

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._svc._schedule(event.src_path, 'created')

    def on_deleted(self, event) -> None:
        if not event.is_directory:
            self._svc._schedule(event.src_path, 'deleted')

    def on_moved(self, event) -> None:
        if not event.is_directory:
            self._svc._schedule(event.src_path, 'deleted')
            self._svc._schedule(event.dest_path, 'modified')


class WatchService:
    """
    Watches a directory tree and reindexes files on change.

    Usage:
        svc = WatchService(indexing_service, db_store, root_dir)
        svc.start()  # blocks until Ctrl-C
    """

    def __init__(
        self,
        indexing_service: IndexingService,
        db_store: DatabaseStore,
        root_dir: str,
        exclude_patterns: Optional[List[str]] = None,
        debounce_seconds: float = 0.5,
        handle_signals: bool = True,
    ) -> None:
        self.indexing_service = indexing_service
        self.db_store = db_store
        self.root_dir = str(Path(root_dir).resolve())
        self.debounce_seconds = debounce_seconds
        self.handle_signals = handle_signals

        self._observer: Optional[Observer] = None
        self._handler: Optional[_ViaEventHandler] = None
        self._stop_event = threading.Event()
        self._pending: Dict[str, Tuple[str, threading.Timer]] = {}
        self._lock = threading.Lock()

        # Build path filter for exclusion checks (gitignore + custom patterns)
        extra = exclude_patterns or []
        self._filter = PathFilter(self.root_dir, extra_patterns=extra)

        # Re-index listeners: called with files_changed count after each batch
        self._reindex_listeners: List[Any] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Run initial index, start observer, block until stop() or SIGINT."""
        logger.info("Indexing %s...", self.root_dir)
        self.indexing_service.index(self.root_dir)

        self._observer = Observer()
        self._handler = _ViaEventHandler(self)
        self._schedule_dir_watches()
        self._observer.start()

        logger.info("Watching %s for changes... (Ctrl-C to stop)", self.root_dir)

        if self.handle_signals:
            original_sigint = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self._handle_sigint)

        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.1)
        finally:
            self._shutdown()
            if self.handle_signals:
                signal.signal(signal.SIGINT, original_sigint)
            logger.info("Watch mode stopped.")

    def stop(self) -> None:
        """Signal the service to stop (safe to call before start)."""
        self._stop_event.set()
        self._shutdown()

    def add_reindex_listener(self, callback: Callable[[int], None]) -> None:
        """Register a callback to be called after each re-index batch.

        Args:
            callback: Callable receiving files_changed count (int). Exceptions
                      raised by the callback are caught and logged so they
                      cannot crash the watcher.
        """
        self._reindex_listeners.append(callback)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _notify_reindex_listeners(self, files_changed: int) -> None:
        """Fire all registered re-index listeners, swallowing exceptions.

        Args:
            files_changed: Number of files processed in this batch.
        """
        for cb in self._reindex_listeners:
            try:
                cb(files_changed)
            except Exception:
                logger.exception("Re-index listener raised an exception")

    def _handle_sigint(self, _signum, _frame) -> None:
        self._stop_event.set()

    def _shutdown(self) -> None:
        """Stop observer and cancel pending timers."""
        # Cancel pending debounce timers
        with self._lock:
            for _, (_, timer) in self._pending.items():
                timer.cancel()
            self._pending.clear()

        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)

    def _schedule_dir_watches(self) -> None:
        self._observer.schedule(self._handler, self.root_dir, recursive=True)

    def _schedule(self, path: str, action: str) -> None:
        """Debounce a file event and schedule execution."""
        if not self._is_watched_file(path):
            return

        with self._lock:
            existing = self._pending.get(path)
            if existing:
                existing[1].cancel()

            timer = threading.Timer(
                self.debounce_seconds,
                self._execute,
                args=(path, action),
            )
            self._pending[path] = (action, timer)
            timer.start()

    def _execute(self, path: str, action: str) -> None:
        """Execute the debounced action for a file."""
        with self._lock:
            self._pending.pop(path, None)

        try:
            if action == 'deleted':
                self._remove_file(path)
            else:
                self._reindex_file(path)
                self._notify_reindex_listeners(1)
        except Exception as e:
            logger.error("Error processing %s: %s", path, e)

    def _is_watched_file(self, path: str) -> bool:
        """Return True if path has a watched extension and is not excluded."""
        ext = Path(path).suffix.lower()
        if ext not in WATCHED_EXTENSIONS:
            return False

        # Check gitignore + default excludes + extra patterns
        if not self._filter.should_include_file(path):
            return False

        return True

    def _reindex_file(self, path: str) -> None:
        """Re-index a single file and log feedback."""
        from via.core.discovery import DiscoveredFile

        # If file is gone, remove it instead
        try:
            stat = os.stat(path)
        except FileNotFoundError:
            self._remove_file(path)
            return

        ext = Path(path).suffix.lower()
        file_info = DiscoveredFile(
            path=path,
            size_bytes=stat.st_size,
            mtime=stat.st_mtime,
            is_parseable=ext in WATCHED_EXTENSIONS,
            is_oversized=stat.st_size > self.indexing_service.size_limit,
        )

        try:
            file_stats = self.indexing_service.reindex_file(file_info)
            n_symbols = sum(file_stats.values())
        except Exception as e:
            logger.error("Failed to index %s: %s", path, e)
            n_symbols = 0

        rel = os.path.relpath(path, self.root_dir)
        logger.info("Re-indexed: %s (%d symbols)", rel, n_symbols)

    def _remove_file(self, path: str) -> None:
        """Remove a file and its symbols from the index atomically."""
        try:
            self.db_store.delete_file_completely(path)
        except Exception as e:
            logger.error("Failed to remove %s: %s", path, e)

        rel = os.path.relpath(path, self.root_dir)
        logger.info("Removed: %s", rel)
