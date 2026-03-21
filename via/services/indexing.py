"""
Indexing service orchestrating file discovery, parsing, and database storage.

TLDR:
    IndexingService drives the full pipeline: FileDiscovery → ParserRegistry
    → Parser → DatabaseStore, wrapped in a single transaction per run. It
    stores classes, methods, functions, imports, globals, filenames, filepaths,
    Markdown headers, call relationships, and inheritance relationships. Supports
    incremental re-indexing via mtime comparison, a force flag to re-index all
    files, progress callbacks, and per-file error resilience. Returns an
    IndexingStats dataclass with counts and timing.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from via.core.constants import DEFAULT_MAX_FILE_SIZE, PROGRESS_UPDATE_INTERVAL
from via.core.discovery import DiscoveredFile, FileDiscovery
from via.db.store import DatabaseStore
from via.parsers.registry import ParserRegistry

logger = logging.getLogger(__name__)


def _calculate_qualified_name(file_path: str, entity_name: str, parent_class: Optional[str] = None) -> str:
    """Calculate fully qualified name for an entity.

    Args:
        file_path: Relative path to file (e.g., 'src/models/user.py')
        entity_name: Simple entity name (e.g., 'save', 'User')
        parent_class: Parent class name for methods (None for non-methods)

    Returns:
        Fully qualified name (e.g., 'models.user.User.save')
    """
    # Convert file path to module: src/models/user.py -> models.user
    module = file_path.replace('.py', '').replace('/', '.')

    # Remove common prefixes
    if module.startswith('src.'):
        module = module[4:]

    # Build qualified name
    if parent_class:
        return f"{module}.{parent_class}.{entity_name}"
    else:
        return f"{module}.{entity_name}"
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

        logger.info("Starting index of %s", root_dir)

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

        logger.info("Discovered %d files", stats.total_files)

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
                        logger.debug("Skipping unchanged file: %s", file_info.path)
                        continue

                    # Check if oversized
                    if file_info.is_oversized:
                        self._store_oversized_file(file_info)
                        stats.oversized_files += 1
                        logger.debug("Oversized file: %s", file_info.path)
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

                    logger.debug("Indexed: %s", file_info.path)

                except Exception as e:
                    logger.error("Failed to index %s: %s", file_info.path, e)
                    stats.failed_files += 1

                # Progress callback
                if progress_callback and (idx + 1) % PROGRESS_UPDATE_INTERVAL == 0:
                    progress_callback(
                        f"Indexing files", idx + 1, stats.total_files
                    )

            # Resolve pending relationships before committing
            resolved = self.db_store.resolve_pending_relationships()
            logger.debug("Resolved %d pending relationships", resolved)

            # Commit transaction
            self.db_store.commit_transaction()
            logger.info("Index committed successfully")

        except Exception as e:
            # Rollback on error
            self.db_store.rollback_transaction()
            logger.error("Index failed, rolling back: %s", e)
            raise

        stats.duration_seconds = time.time() - start_time

        logger.info(
            "Indexing complete: %d files indexed, %d skipped, %d failed in %.2fs",
            stats.indexed_files,
            stats.skipped_files,
            stats.failed_files,
            stats.duration_seconds
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

    def reindex_file(self, file_info: DiscoveredFile) -> dict:
        """Re-index a single file — deletes existing data then indexes fresh.

        Public method used by WatchService. Wraps delete_file_completely() +
        _index_file() in a single call so callers don't need to orchestrate.

        Args:
            file_info: File to re-index

        Returns:
            Dict with entity counts from _index_file
        """
        self.db_store.delete_file_completely(file_info.path)
        return self._index_file(file_info)

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
            logger.warning("No parser found for %s", file_info.path)
            self._store_unparsed_file(file_info)
            return {'functions': 0, 'classes': 0, 'imports': 0, 'globals': 0}

        # Read file content
        with open(file_info.path, 'rb') as f:
            content = f.read()

        # Parse file
        parse_result = parser.parse(file_info.path, content)

        # Check for parse errors
        if parse_result.parse_error:
            logger.warning("Parse error in %s: %s", file_info.path, parse_result.parse_error)
            # Store as parsed with error
            self._store_file_with_error(file_info, parse_result.parse_error)
            return {'functions': 0, 'classes': 0, 'imports': 0, 'globals': 0}

        # Store in database (pass content for line offset indexing)
        return self._store_parsed_file(file_info, parse_result, content)

    def _store_parsed_file(self, file_info: DiscoveredFile, parse_result, content: bytes = b'') -> dict:
        """
        Store parsed file and entities in database.

        Args:
            file_info: File information
            parse_result: Parse result with entities
            content: Raw file bytes (used to build line offset index)

        Returns:
            Dict with entity counts
        """
        file_id = self._upsert_file(file_info, parse_result)
        self._store_symbols(file_info, parse_result)
        if content:
            self._index_line_offsets(file_id, content)

        return {
            'functions': len(parse_result.functions) + sum(len(c.methods) for c in parse_result.classes),
            'classes': len(parse_result.classes),
            'imports': len(parse_result.imports),
            'globals': len(parse_result.globals),
            'headers': len(parse_result.markdown_headings),
        }

    def _upsert_file(self, file_info: DiscoveredFile, parse_result) -> int:
        """Insert or update file record, clearing old entities if updating.

        Args:
            file_info: File information
            parse_result: Parse result with language info

        Returns:
            file_id for the inserted/updated file
        """
        existing = self.db_store.get_file_by_path(file_info.path)

        if existing:
            file_id = existing['id']
            # Delete old symbols (will be replaced)
            self.db_store.delete_symbols_by_file(file_info.path)
            # Update file record
            self.db_store.update_file(
                file_id=file_id,
                language=parse_result.language,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=True,
            )
        else:
            file_id = self.db_store.insert_file(
                path=file_info.path,
                language=parse_result.language,
                size_bytes=file_info.size_bytes,
                mtime=file_info.mtime,
                parsed=True,
            )
        return file_id


    def _store_symbols(self, file_info: DiscoveredFile, parse_result) -> None:
        """Populate symbols table (denormalized for fast matching)."""
        self._store_class_symbols(file_info, parse_result)
        self._store_function_symbols(file_info, parse_result)
        self._store_import_symbols(file_info, parse_result)
        self._store_global_symbols(file_info, parse_result)
        self._store_file_path_symbols(file_info)
        self._store_call_relationships(file_info, parse_result)
        self._store_reference_relationships(file_info, parse_result)
        self._store_markdown_headers(file_info, parse_result)

    def _store_class_symbols(self, file_info: DiscoveredFile, parse_result) -> None:
        """Insert class and method symbols."""
        for cls in parse_result.classes:
            qualified_name = _calculate_qualified_name(file_info.path, cls.name)
            class_id = self.db_store.insert_symbol(
                symbol_name=cls.name,
                symbol_type='class',
                file_path=file_info.path,
                line_number=cls.line_start,
                qualified_name=qualified_name,
                byte_offset=cls.byte_offset,
                byte_length=cls.byte_length,
                parent_name=None,
            )

            # Create pending relationships for inheritance
            if cls.bases:
                base_names = [b.strip() for b in cls.bases.split(',')]
                for base_name in base_names:
                    if base_name:
                        self.db_store.insert_pending_relationship(
                            source_id=class_id,
                            target_name=base_name,
                            rel_type='inherits-from'
                        )

            for method in cls.methods:
                qualified_name = _calculate_qualified_name(file_info.path, method.name, parent_class=cls.name)
                self.db_store.insert_symbol(
                    symbol_name=method.name,
                    symbol_type='method',
                    file_path=file_info.path,
                    line_number=method.line_start,
                    qualified_name=qualified_name,
                    byte_offset=method.byte_offset,
                    byte_length=method.byte_length,
                    parent_name=cls.name,
                )

    def _store_function_symbols(self, file_info: DiscoveredFile, parse_result) -> None:
        """Insert function symbols."""
        for func in parse_result.functions:
            qualified_name = _calculate_qualified_name(file_info.path, func.name)
            self.db_store.insert_symbol(
                symbol_name=func.name,
                symbol_type='function',
                file_path=file_info.path,
                line_number=func.line_start,
                qualified_name=qualified_name,
                byte_offset=func.byte_offset,
                byte_length=func.byte_length,
                parent_name=None,
            )

    def _store_import_symbols(self, file_info: DiscoveredFile, parse_result) -> None:
        """Insert import symbols and create import relationships."""
        for imp in parse_result.imports:
            symbol_name = imp.name if imp.name else imp.module
            qualified_name = imp.module if not imp.name else f"{imp.module}.{imp.name}"
            import_id = self.db_store.insert_symbol(
                symbol_name=symbol_name,
                symbol_type='import',
                file_path=file_info.path,
                line_number=imp.line_number,
                qualified_name=qualified_name,
                byte_offset=imp.byte_offset,
                byte_length=imp.byte_length,
                parent_name=None,
            )

            module_name = imp.module if imp.module else symbol_name
            self.db_store.insert_pending_relationship(
                source_id=import_id,
                target_name=module_name,
                rel_type='imports'
            )

    def _store_global_symbols(self, file_info: DiscoveredFile, parse_result) -> None:
        """Insert global symbols."""
        for glob in parse_result.globals:
            qualified_name = _calculate_qualified_name(file_info.path, glob.name)
            self.db_store.insert_symbol(
                symbol_name=glob.name,
                symbol_type='global',
                file_path=file_info.path,
                line_number=glob.line_number,
                qualified_name=qualified_name,
                byte_offset=glob.byte_offset,
                byte_length=glob.byte_length,
                parent_name=None,
            )

    def _store_file_path_symbols(self, file_info: DiscoveredFile) -> None:
        """Insert file path symbols (for filename and filepath matching)."""
        filename = file_info.path.split('/')[-1]
        self.db_store.insert_symbol(
            symbol_name=filename,
            symbol_type='filename',
            file_path=file_info.path,
            line_number=0,
            qualified_name=filename,
            byte_offset=None,
            byte_length=None,
            parent_name=None,
        )
        self.db_store.insert_symbol(
            symbol_name=filename,
            symbol_type='filepath',
            file_path=file_info.path,
            line_number=0,
            qualified_name=file_info.path,
            byte_offset=None,
            byte_length=None,
            parent_name=None,
        )

    def _store_call_relationships(self, file_info: DiscoveredFile, parse_result) -> None:
        """Create pending relationships for function/method calls."""
        for call in parse_result.calls:
            caller_type = 'method' if call.caller_type == 'method' else 'function'
            parent_name = call.caller_parent if call.caller_type == 'method' else None

            cursor = self.db_store.conn.execute(
                """SELECT id FROM symbols
                   WHERE symbol_name = ? AND symbol_type = ? AND file_path = ?
                   AND (parent_name = ? OR (parent_name IS NULL AND ? IS NULL))
                   LIMIT 1""",
                (call.caller_name, caller_type, file_info.path, parent_name, parent_name)
            )
            row = cursor.fetchone()

            if row:
                caller_id = row[0]
                self.db_store.insert_pending_relationship(
                    source_id=caller_id,
                    target_name=call.callee_name,
                    rel_type='calls'
                )

    def _store_reference_relationships(self, file_info: DiscoveredFile, parse_result) -> None:
        """Create pending relationships for symbol references."""
        for ref in parse_result.references:
            referencer_type = 'method' if ref.referencer_type == 'method' else 'function'
            parent_name = ref.referencer_parent if ref.referencer_type == 'method' else None

            cursor = self.db_store.conn.execute(
                """SELECT id FROM symbols
                   WHERE symbol_name = ? AND symbol_type = ? AND file_path = ?
                   AND (parent_name = ? OR (parent_name IS NULL AND ? IS NULL))
                   LIMIT 1""",
                (ref.referencer_name, referencer_type, file_info.path, parent_name, parent_name)
            )
            row = cursor.fetchone()

            if row:
                referencer_id = row[0]
                self.db_store.insert_pending_relationship(
                    source_id=referencer_id,
                    target_name=ref.referenced_name,
                    rel_type='references'
                )

    def _store_markdown_headers(self, file_info: DiscoveredFile, parse_result) -> None:
        """Insert header symbols with hierarchical qualified names."""
        header_stack = []
        for heading in parse_result.markdown_headings:
            while header_stack and header_stack[-1][0] >= heading.level:
                header_stack.pop()

            ancestors = [text for _, text in header_stack]
            ancestors.append(heading.text)
            qualified_name = ' > '.join(ancestors)

            parent_name = header_stack[-1][1] if header_stack else None
            header_stack.append((heading.level, heading.text))

            self.db_store.insert_symbol(
                symbol_name=heading.text,
                symbol_type='header',
                file_path=file_info.path,
                line_number=heading.line_number,
                qualified_name=qualified_name,
                byte_offset=heading.byte_offset,
                byte_length=heading.byte_length,
                parent_name=parent_name,
            )

    def _index_line_offsets(self, file_id: int, content: bytes) -> None:
        """Record byte offset of each line start for the given file.

        Called after symbol indexing for parsed files. O(file_size) — same
        content bytes already in memory from _index_file().

        Args:
            file_id: File ID (FK to files.id)
            content: Raw file bytes
        """
        offsets = []
        pos = 0
        for line_num, line in enumerate(content.splitlines(keepends=True), start=1):
            offsets.append((file_id, line_num, pos, len(line)))
            pos += len(line)
        self.db_store.upsert_line_offsets(file_id, offsets)

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
