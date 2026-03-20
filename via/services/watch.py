"""
WatchService: filesystem watcher that auto-reindexes changed files.

TLDR:
    Wraps watchdog to monitor a directory tree. On file change/create/delete,
    debounces (500ms default) and delegates to IndexingService. Prints terse
    terminal feedback. Graceful SIGINT shutdown.

Sprint 6 - Watch Mode
"""

import logging
import os
import signal
import sys
import threading
from io import IOBase
from pathlib import Path
from typing import IO, Dict, List, Optional, Tuple

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from via.core.discovery import FileDiscovery
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
        output: IO = sys.stdout,
    ) -> None:
        self.indexing_service = indexing_service
        self.db_store = db_store
        self.root_dir = str(Path(root_dir).resolve())
        self.debounce_seconds = debounce_seconds
        self.output = output

        self._observer: Optional[Observer] = None
        self._stop_event = threading.Event()
        self._pending: Dict[str, Tuple[str, threading.Timer]] = {}
        self._lock = threading.Lock()

        # Build discovery for exclusion checks (gitignore + custom patterns)
        extra = exclude_patterns or []
        self._discovery = FileDiscovery(
            root_dir=self.root_dir,
            parseable_extensions=WATCHED_EXTENSIONS,
        )
        # Merge extra exclude patterns into the gitignore spec
        if extra:
            import pathspec
            extra_spec = pathspec.PathSpec.from_lines('gitignore', extra)
            self._extra_spec = extra_spec
        else:
            self._extra_spec = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Run initial index, start observer, block until stop() or SIGINT."""
        print(f"Indexing {self.root_dir}...", file=self.output)
        self.indexing_service.index(self.root_dir)

        self._observer = Observer()
        self._observer.schedule(_ViaEventHandler(self), self.root_dir, recursive=True)
        self._observer.start()

        print(f"Watching {self.root_dir} for changes... (Ctrl-C to stop)", file=self.output)

        original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_sigint)

        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.1)
        finally:
            self._shutdown()
            signal.signal(signal.SIGINT, original_sigint)
            print("Watch mode stopped.", file=self.output)

    def stop(self) -> None:
        """Signal the service to stop (safe to call before start)."""
        self._stop_event.set()
        self._shutdown()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _handle_sigint(self, signum, frame) -> None:
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
        except Exception as e:
            logger.error("Error processing %s: %s", path, e)

    def _is_watched_file(self, path: str) -> bool:
        """Return True if path has a watched extension and is not excluded."""
        ext = Path(path).suffix.lower()
        if ext not in WATCHED_EXTENSIONS:
            return False

        # Check gitignore + default excludes
        if not self._discovery._should_include_file(path):
            return False

        # Check extra exclude patterns
        if self._extra_spec:
            rel = os.path.relpath(path, self.root_dir)
            if self._extra_spec.match_file(rel):
                return False

        return True

    def _reindex_file(self, path: str) -> None:
        """Re-index a single file and print feedback."""
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
            file_stats = self.indexing_service._index_file(file_info)
            n_symbols = sum(file_stats.values())
        except Exception as e:
            logger.error("Failed to index %s: %s", path, e)
            n_symbols = 0

        rel = os.path.relpath(path, self.root_dir)
        print(f"Re-indexed: {rel} ({n_symbols} symbols)", file=self.output)

    def _remove_file(self, path: str) -> None:
        """Remove a file and its symbols from the index."""
        try:
            self.db_store.delete_relationships_for_file(path)
        except Exception:
            pass
        try:
            self.db_store.delete_symbols_by_file(path)
        except Exception:
            pass
        try:
            self.db_store.delete_file_by_path(path)
        except Exception:
            pass

        rel = os.path.relpath(path, self.root_dir)
        print(f"Removed: {rel}", file=self.output)
