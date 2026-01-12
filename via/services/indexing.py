"""
Indexing service orchestrating file discovery, parsing, and storage.

TLDR:
    Provides IndexingService that orchestrates the complete indexing pipeline:
    FileDiscovery → ParserRegistry → Parser → DatabaseStore. Supports incremental
    indexing via mtime checks, progress callbacks, resilient per-file error
    handling, and force re-index flag. Returns comprehensive IndexingStats.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Callable, List

from ..core.constants import DEFAULT_MAX_FILE_SIZE, PROGRESS_UPDATE_INTERVAL
from ..core.discovery import FileDiscovery, DiscoveredFile
from ..db.store import DatabaseStore
from ..parsers.registry import ParserRegistry
logger = logging.getLogger(__name__)
@dataclass
class IndexingStats:
    """Statistics from an indexing operation."""

    total_files: int = 0
    indexed_files: int = 0
    skipped_files: int = 0
    oversized_files: int = 0
    failed_files: int = 0
    duration_seconds: float = 0.0

    # Entity counts
    functions: int = 0
    classes: int = 0
    imports: int = 0
    globals: int = 0
class IndexingService:
    """
    High-level service for indexing code repositories.

    Orchestrates:
    1. File discovery (with .gitignore support)
    2. Parser selection and invocation
    3. Database storage
    4. Progress reporting
    5. Incremental updates
    """

    def __init__(
        self,
        db_store: DatabaseStore,
        parser_registry: ParserRegistry,
        size_limit: int = DEFAULT_MAX_FILE_SIZE,
    ):
        """
        Initialize indexing service.

        Args:
            db_store: Database store for persisting index
            parser_registry: Registry of language parsers
            size_limit: Maximum file size to parse (bytes)
        """
        self.db_store = db_store
        self.parser_registry = parser_registry
        self.size_limit = size_limit

    def index(
        self,
        root_dir: str,
        force: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> IndexingStats:
        """
        Index a directory tree.

        Args:
            root_dir: Root directory to index
            force: If True, re-index all files (ignore mtime)
            progress_callback: Optional callback(message, current, total)

        Returns:
            IndexingStats with results
        """
        start_time = time.time()
        stats = IndexingStats()

        logger.info(f"Starting index of {root_dir}")

        # Get parseable extensions from registry
        parseable_exts = self.parser_registry.get_supported_extensions()

        # Discover files
        discovery = FileDiscovery(
            root_dir=root_dir,
            parseable_extensions=parseable_exts,
            size_limit=self.size_limit,
        )

        discovered = discovery.discover()
        stats.total_files = len(discovered)

        logger.info(f"Discovered {stats.total_files} files")

        if progress_callback:
            progress_callback("Discovering files", 0, stats.total_files)

        # Begin database transaction for batch operations
        self.db_store.begin_transaction()

        try:
            # Index each file
            for idx, file_info in enumerate(discovered):
                try:
                    # Check if file needs indexing
                    if not force and not self._should_index_file(file_info):
                        stats.skipped_files += 1
                        logger.debug(f"Skipping unchanged file: {file_info.path}")
                        continue

                    # Check if oversized
                    if file_info.is_oversized:
                        self._store_oversized_file(file_info)
                        stats.oversized_files += 1
                        logger.debug(f"Oversized file: {file_info.path}")
                        continue

                    # Check if parseable
                    if not file_info.is_parseable:
                        # Store as unparsed file
                        self._store_unparsed_file(file_info)
                        stats.skipped_files += 1
                        continue

                    # Index the file
                    file_stats = self._index_file(file_info)
                    stats.indexed_files += 1
                    stats.functions += file_stats['functions']
                    stats.classes += file_stats['classes']
                    stats.imports += file_stats['imports']
                    stats.globals += file_stats['globals']

                    logger.debug(f"Indexed: {file_info.path}")

                except Exception as e:
                    logger.error(f"Failed to index {file_info.path}: {e}")
                    stats.failed_files += 1

                # Progress callback
                if progress_callback and (idx + 1) % PROGRESS_UPDATE_INTERVAL == 0:
                    progress_callback(
                        f"Indexing files", idx + 1, stats.total_files
                    )

            # Commit transaction
            self.db_store.commit_transaction()
            logger.info("Index committed successfully")

        except Exception as e:
            # Rollback on error
            self.db_store.rollback_transaction()
            logger.error(f"Index failed, rolling back: {e}")
            raise

        stats.duration_seconds = time.time() - start_time

        logger.info(
            f"Indexing complete: {stats.indexed_files} files indexed, "
            f"{stats.skipped_files} skipped, {stats.failed_files} failed "
            f"in {stats.duration_seconds:.2f}s"
        )

        return stats

    def _should_index_file(self, file_info: DiscoveredFile) -> bool:
        """
        Check if file needs indexing based on mtime.

        Args:
            file_info: Discovered file information

        Returns:
            True if file should be indexed
        """
        # Check if file exists in database
        existing = self.db_store.get_file_by_path(file_info.path)

        if not existing:
            # New file, needs indexing
            return True

        # Check if file was modified since last index
        return file_info.mtime > existing.get('mtime', 0)

    def _index_file(self, file_info: DiscoveredFile) -> dict:
        """
        Index a single file.

        Args:
            file_info: File to index

        Returns:
            Dict with entity counts
        """
        # Get appropriate parser
        parser = self.parser_registry.get_parser(file_info.path)

        if not parser:
            logger.warning(f"No parser found for {file_info.path}")
            self._store_unparsed_file(file_info)
            return {'functions': 0, 'classes': 0, 'imports': 0, 'globals': 0}

        # Read file content
        with open(file_info.path, 'rb') as f:
            content = f.read()

        # Parse file
        parse_result = parser.parse(file_info.path, content)

        # Check for parse errors
        if parse_result.parse_error:
            logger.warning(f"Parse error in {file_info.path}: {parse_result.parse_error}")
            # Store as parsed with error
            self._store_file_with_error(file_info, parse_result.parse_error)
            return {'functions': 0, 'classes': 0, 'imports': 0, 'globals': 0}

        # Store in database
        return self._store_parsed_file(file_info, parse_result)

    def _store_parsed_file(self, file_info: DiscoveredFile, parse_result) -> dict:
        """
        Store parsed file and entities in database.

        Args:
            file_info: File information
            parse_result: Parse result with entities

        Returns:
            Dict with entity counts
        """
        # Check if file already exists
        existing = self.db_store.get_file_by_path(file_info.path)

        if existing:
            # Update existing file
            file_id = existing['id']

            # Delete old entities (will be replaced)
            self.db_store.delete_functions_by_file(file_id)
            self.db_store.delete_classes_by_file(file_id)
            self.db_store.delete_imports_by_file(file_id)
            self.db_store.delete_globals_by_file(file_id)

            # Update file record
            self.db_store.update_file(
                file_id=file_id,
                language=parse_result.language,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=True,
            )
        else:
            # Insert new file
            file_id = self.db_store.insert_file(
                path=file_info.path,
                language=parse_result.language,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=True,
            )

        # Store classes first (needed for method linking)
        class_id_map = {}  # Map class name to class_id
        for cls in parse_result.classes:
            class_id = self.db_store.insert_class(
                file_id=file_id,
                name=cls.name,
                line_start=cls.line_start,
                line_end=cls.line_end,
                byte_offset=cls.byte_offset,
                byte_length=cls.byte_length,
                bases=cls.bases,
                decorators=cls.decorators,
                docstring=cls.docstring,
            )
            class_id_map[cls.name] = class_id

            # Store methods
            for method in cls.methods:
                self.db_store.insert_function(
                    file_id=file_id,
                    class_id=class_id,
                    name=method.name,
                    line_start=method.line_start,
                    line_end=method.line_end,
                    byte_offset=method.byte_offset,
                    byte_length=method.byte_length,
                    args=method.args,
                    decorators=method.decorators,
                    docstring=method.docstring,
                )

        # Store top-level functions
        for func in parse_result.functions:
            self.db_store.insert_function(
                file_id=file_id,
                name=func.name,
                line_start=func.line_start,
                line_end=func.line_end,
                byte_offset=func.byte_offset,
                byte_length=func.byte_length,
                args=func.args,
                decorators=func.decorators,
                docstring=func.docstring,
            )

        # Store imports
        for imp in parse_result.imports:
            self.db_store.insert_import(
                file_id=file_id,
                module=imp.module,
                name=imp.name,
                alias=imp.alias,
                line_number=imp.line_number,
                byte_offset=imp.byte_offset,
                byte_length=imp.byte_length,
            )

        # Store globals
        for glob in parse_result.globals:
            self.db_store.insert_global(
                file_id=file_id,
                name=glob.name,
                value=glob.value,
                type_hint=glob.type_hint,
                line_number=glob.line_number,
                byte_offset=glob.byte_offset,
                byte_length=glob.byte_length,
            )

        return {
            'functions': len(parse_result.functions) + sum(len(c.methods) for c in parse_result.classes),
            'classes': len(parse_result.classes),
            'imports': len(parse_result.imports),
            'globals': len(parse_result.globals),
        }

    def _store_unparsed_file(self, file_info: DiscoveredFile) -> None:
        """Store file as unparsed."""
        existing = self.db_store.get_file_by_path(file_info.path)

        if existing:
            self.db_store.update_file(
                file_id=existing['id'],
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=False,
            )
        else:
            self.db_store.insert_file(
                path=file_info.path,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=False,
            )

    def _store_oversized_file(self, file_info: DiscoveredFile) -> None:
        """Store file marked as oversized."""
        existing = self.db_store.get_file_by_path(file_info.path)

        if existing:
            self.db_store.update_file(
                file_id=existing['id'],
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
            )
        else:
            self.db_store.insert_file(
                path=file_info.path,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                oversized=True,
            )

    def _store_file_with_error(self, file_info: DiscoveredFile, error: str) -> None:
        """Store file that had a parse error."""
        existing = self.db_store.get_file_by_path(file_info.path)

        # For now, just store as unparsed
        # Could add error field to schema in future
        if existing:
            self.db_store.update_file(
                file_id=existing['id'],
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=False,
            )
        else:
            self.db_store.insert_file(
                path=file_info.path,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=False,
            )
