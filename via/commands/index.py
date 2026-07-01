"""Command handler for indexing and watch mode triggers.

TLDR:
    Implements the 'via index' CLI command.
    Key class: IndexCommandHandler (drives indexing using IndexingService and
    starts watch mode triggers using WatchService).
    Role: Triggers indexing and watch mode. Consumed by __main__.py.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
import argparse
import sys
import logging
from pathlib import Path

from .base import CommandHandlerABC
from ..core.constants import DEFAULT_INDEX_DIR, DEFAULT_DB_NAME, EXIT_ERROR, EXIT_SUCCESS, EXIT_KEYBOARD_INTERRUPT
from ..db.store import DatabaseStore
from ..parsers.registry import ParserRegistry
from ..parsers.python_parser import PythonParser
from ..parsers.markdown_parser import MarkdownParser
from ..parsers.javascript_parser import JavaScriptParser
from ..parsers.dart_parser import DartParser
from ..services.indexing import IndexingService
from .stats import StatsCommand


class IndexCommandHandler(CommandHandlerABC):
    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "directory",
            nargs="?",
            default=".",
            help="Directory to index (default: current directory)",
        )
        parser.add_argument(
            "-w",
            "--watch",
            action="store_true",
            help="Watch for file changes and re-index automatically",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-index of all files (ignore mtime checks)",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            metavar="PATTERN",
            help="Additional patterns to exclude (can be specified multiple times)",
        )
        parser.add_argument(
            "--db",
            metavar="PATH",
            help="Database path (default: <dir>/.via/index.db)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=7891,
            metavar="PORT",
            help="Web UI port when using --watch (default: 7891)",
        )
        parser.add_argument(
            "--no-web",
            action="store_true",
            help="Disable the web UI when using --watch",
        )

    @classmethod
    def get_help(cls) -> str:
        return "Index a directory tree, respecting .gitignore rules."

    def run(self, args: argparse.Namespace) -> int:
        # Resolve directory
        target_dir = Path(args.directory).resolve()

        if not target_dir.exists():
            print(f"Error: Directory does not exist: {target_dir}", file=sys.stderr)
            return EXIT_ERROR

        if not target_dir.is_dir():
            print(f"Error: Not a directory: {target_dir}", file=sys.stderr)
            return EXIT_ERROR

        # Determine database path
        if args.db:
            db_path = Path(args.db)
        else:
            index_dir = target_dir / DEFAULT_INDEX_DIR
            index_dir.mkdir(exist_ok=True)
            db_path = index_dir / DEFAULT_DB_NAME

        logging.info(f"Indexing directory: {target_dir}")
        logging.info(f"Database path: {db_path}")

        # Handle --exclude patterns
        exclude_patterns = args.exclude or []

        # Watch mode
        if args.watch:
            return self._run_watch(
                db_path, target_dir, exclude_patterns,
                port=getattr(args, 'port', 7891),
                no_web=getattr(args, 'no_web', False),
            )

        if exclude_patterns:
            logging.info(f"Additional exclusion patterns: {exclude_patterns}")

        try:
            # Initialize database with context manager
            with DatabaseStore(str(db_path), str(target_dir)) as db_store:
                # Initialize schema
                db_store.initialize_schema()

                # Initialize parser registry and register parsers
                parser_registry = ParserRegistry()
                parser_registry.register(PythonParser())
                parser_registry.register(MarkdownParser())
                parser_registry.register(JavaScriptParser())
                parser_registry.register(DartParser())

                # Initialize indexing service
                indexing_service = IndexingService(db_store, parser_registry)

                # Run indexing
                print(f"Indexing {target_dir}...")
                stats = indexing_service.index(
                    str(target_dir),
                    force=args.force,
                    progress_callback=self._progress_callback,
                )

                # Print newline after progress
                print()

                # Print summary
                print("\n" + "=" * 60)
                print("INDEXING COMPLETE")
                print("=" * 60)
                print(f"Total files discovered:  {stats.total_files}")
                print(f"Files indexed:           {stats.indexed_files}")
                print(f"Files skipped:           {stats.skipped_files}")
                print(f"Oversized files:         {stats.oversized_files}")
                print(f"Failed files:            {stats.failed_files}")
                print(f"Duration:                {stats.duration_seconds:.2f}s")
                print()
                print(f"Entities extracted:")
                print(f"  Functions:             {stats.functions}")
                print(f"  Classes:               {stats.classes}")
                print(f"  Methods:               {getattr(stats, 'methods', 0)}")
                print(f"  Imports:               {stats.imports}")
                print(f"  Globals:               {stats.globals}")
                print(f"  Headers:               {getattr(stats, 'headers', 0)}")
                print("=" * 60)

                if stats.failed_files > 0:
                    print(f"\nWarning: {stats.failed_files} files failed to index", file=sys.stderr)

                # After indexing, run stats command for normalized output
                print("\nVIA STATS (normalized):")
                stats_cmd = StatsCommand(db_store)
                print(stats_cmd.execute(verbose=0, as_json=False))

            return EXIT_SUCCESS

        except KeyboardInterrupt:
            print("\n\nIndexing interrupted by user", file=sys.stderr)
            return EXIT_KEYBOARD_INTERRUPT

        except Exception as e:
            logging.exception("Indexing failed with exception")
            print(f"\nError: Indexing failed: {e}", file=sys.stderr)
            return EXIT_ERROR

    def _run_watch(
        self,
        db_path: Path,
        target_dir: Path,
        exclude_patterns: list,
        port: int = 7891,
        no_web: bool = False,
    ) -> int:
        """Start index watch mode."""
        from via.services.watch import WatchService
        watch_logger = logging.getLogger('via.services.watch')
        watch_logger.setLevel(logging.INFO)
        for handler in logging.root.handlers:
            if handler.level > logging.INFO:
                handler.setLevel(logging.INFO)
        with DatabaseStore(str(db_path), str(target_dir)) as db_store:
            db_store.initialize_schema()
            parser_registry = ParserRegistry()
            parser_registry.register(PythonParser())
            parser_registry.register(MarkdownParser())
            parser_registry.register(JavaScriptParser())
            parser_registry.register(DartParser())
            indexing_service = IndexingService(db_store, parser_registry)
            watch_service = WatchService(
                indexing_service=indexing_service,
                db_store=db_store,
                root_dir=str(target_dir),
                exclude_patterns=exclude_patterns,
            )
            web_server = None
            if not no_web:
                from via.web import WebServer
                web_server = WebServer(port=port, db_path=str(db_path), index_root=str(target_dir))
                watch_service.add_reindex_listener(web_server.notify_reindex)
                web_server.start()
                print(f"Web UI: http://localhost:{web_server.port}")
            try:
                watch_service.start()
            finally:
                if web_server:
                    web_server.stop()
        return EXIT_SUCCESS

    def _progress_callback(self, message: str, current: int, total: int) -> None:
        """Print indexing progress."""
        if total > 0:
            percent = (current / total) * 100
            print(f"\r{message}: {current}/{total} ({percent:.1f}%)", end="", flush=True)
        else:
            print(f"\r{message}: {current}", end="", flush=True)


# Keep legacy alias for backward compatibility
IndexCommand = IndexCommandHandler
