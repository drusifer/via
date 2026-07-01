"""Abstract base class for all CLI command handlers.

TLDR:
    Defines the standard interface for implementing CLI command executors.
    Key class: CommandHandlerABC (defines run() method returning exit codes).
    Role: Base class for CLI subcommands. Consumed by command registration.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""

import argparse
from abc import ABC, abstractmethod
from ..core.interfaces import ArgumentProvider, HelpProvider


class CommandHandlerABC(ArgumentProvider, HelpProvider, ABC):
    """Abstract base class for all CLI command handlers."""

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Execute the command using the parsed arguments.

        Args:
            args: The parsed command-line arguments.

        Returns:
            Exit code (0 for success, non-zero for error).
        """
        pass
