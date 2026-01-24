"""
Interfaces for argument parsing and help output (ARCH.md).

Defines ArgumentProvider and HelpProvider ABCs for CLI extensibility.
"""
import argparse


class ArgumentProvider:
    """Mixin for classes that provide CLI arguments."""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        """Register CLI arguments for this type/renderer."""
        pass


class HelpProvider:
    """Mixin for classes that provide help text."""

    @classmethod
    def get_help(cls) -> str:
        """Return help string for this type/renderer."""
        return getattr(cls, "HELP", f"{cls.__name__}: no help provided.")
