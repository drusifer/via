"""
Constants for VIA application.

TLDR:
    Centralizes all application constants including file size limits, default
    paths, verbosity levels, and exit codes. Provides single source of truth
    for configuration values used across the VIA indexing system.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

# Version
VERSION = "0.1.0"

# File size limits
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MB = 1024 * 1024

# Default paths
DEFAULT_INDEX_DIR = ".via"
DEFAULT_DB_NAME = "index.db"
DEFAULT_LOG_DIR = ".via/logs"

# Database
SCHEMA_VERSION = 1

# Supported file extensions
PYTHON_EXTENSIONS = {'.py', '.pyx', '.pyi'}
MARKDOWN_EXTENSIONS = {'.md', '.markdown'}

# Default exclusions (always excluded during file discovery)
DEFAULT_EXCLUDES = [
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git/',
    '.svn/',
    '.hg/',
    '.via/',  # Exclude VIA's own index directory
]

# Worker pool configuration
DEFAULT_WORKER_COUNT = None  # None means unbounded (1 per subfolder)

# Progress reporting
PROGRESS_UPDATE_INTERVAL = 100  # Report progress every N files

# Verbosity levels
VERBOSITY_QUIET = 0    # Warnings and errors only
VERBOSITY_NORMAL = 1   # -v: Info level
VERBOSITY_VERBOSE = 2  # -vv: Debug level
VERBOSITY_DEBUG = 3    # -vvv: Detailed debug
VERBOSITY_TRACE = 4    # -vvvv: Very detailed debug

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_KEYBOARD_INTERRUPT = 130
