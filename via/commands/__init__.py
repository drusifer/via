"""
Commands package for VIA CLI.

TLDR:
    Re-exports the two CLI command classes: IndexCommand for indexing a codebase
    (including watch mode) and StatsCommand for reporting symbol counts and
    per-type breakdowns from the index database.

"""

from .index import IndexCommandHandler, IndexCommand
from .stats import StatsCommandHandler, StatsCommand
from .mcp import McpCommandHandler
from .install import InstallCommandHandler
from .coverage import CoverageCommandHandler
from .ask import AskCommandHandler, AskCommand

__all__ = [
    'IndexCommandHandler',
    'IndexCommand',
    'StatsCommandHandler',
    'StatsCommand',
    'McpCommandHandler',
    'InstallCommandHandler',
    'CoverageCommandHandler',
    'AskCommandHandler',
    'AskCommand',
]
