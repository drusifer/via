"""
Commands package for VIA CLI.

TLDR:
    Re-exports the two CLI command classes: IndexCommand for indexing a codebase
    (including watch mode) and StatsCommand for reporting symbol counts and
    per-type breakdowns from the index database.

"""

from .index import IndexCommand
from .stats import StatsCommand

__all__ = ['StatsCommand', 'IndexCommand']
