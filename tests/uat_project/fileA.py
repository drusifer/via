"""
FileA - Base classes and utility functions.

Contains base classes and functions that will be inherited/called by other files.
"""
import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

# Global constants
MY_CONSTANT = 42
CONFIG_KEY = "default_config"


@dataclass
class BaseModel:
    """Base model class for all data models."""
    id: int
    name: str


class BaseClass:
    """A base class for inheritance testing."""

    def base_method(self):
        """Base method that can be overridden."""
        return "base"

    def shared_logic(self):
        """Shared logic used by children."""
        return MY_CONSTANT


class AnotherBase:
    """Another base class for multiple inheritance testing."""

    def another_method(self):
        """Another method."""
        pass


def func_a():
    """A function in fileA that will be called from fileB."""
    return "func_a result"


def helper_util():
    """A utility helper function."""
    return "helper"


def deprecated_func():
    """A deprecated function that should be refactored.

    DEPRECATED: Use new_func() instead.
    """
    return "deprecated"


def new_func():
    """The replacement for deprecated_func."""
    return "new"


class FinalClass:
    """A final class with no children."""
    pass
