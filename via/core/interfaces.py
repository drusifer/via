"""
Abstract base interfaces for CLI argument registration and help text.

TLDR:
    Provides two lightweight mixin ABCs used throughout the VIA command layer.
    ArgumentProvider declares add_arguments() so that symbol types and renderers
    can register their own argparse flags with a shared parser. HelpProvider
    declares get_help() so each class can expose a self-describing help string,
    falling back to a HELP class attribute when present.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
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
