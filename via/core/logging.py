"""
Logging configuration for VIA.

TLDR:
    Provides centralized logging setup with 5 verbosity levels (0-4) mapped to
    -v flags. Supports console and file logging with customizable formats based
    on verbosity. Level 0 is warnings only, levels 1-4 add progressively more detail.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import logging
import sys
from typing import Optional
def setup_logging(verbosity: int = 0, log_file: Optional[str] = None) -> None:
    """
    Setup logging based on verbosity level.

    Verbosity levels:
    - 0: WARNING and above (default)
    - 1: INFO and above (-v)
    - 2: DEBUG and above (-vv)
    - 3: DEBUG with detailed formatting (-vvv)
    - 4: DEBUG with very detailed formatting (-vvvv)

    Args:
        verbosity: Verbosity level (0-4)
        log_file: Optional log file path
    """
    # Map verbosity to logging level
    levels = [
        logging.WARNING,  # 0: Default
        logging.INFO,     # 1: -v
        logging.DEBUG,    # 2: -vv
        logging.DEBUG,    # 3: -vvv
        logging.DEBUG,    # 4: -vvvv
    ]

    level = levels[min(verbosity, len(levels) - 1)]

    # Choose format based on verbosity
    if verbosity >= 4:
        # Very detailed format with timestamp, module, function
        log_format = '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
    elif verbosity >= 3:
        # Detailed format with module and line number
        log_format = '[%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        date_format = None
    elif verbosity >= 1:
        # Simple format with level and message
        log_format = '%(levelname)s: %(message)s'
        date_format = None
    else:
        # Minimal format - just the message for warnings/errors
        log_format = '%(levelname)s: %(message)s'
        date_format = None

    # Configure root logger
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
