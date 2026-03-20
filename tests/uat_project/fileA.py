"""
UAT test fixture providing base classes and utility functions for relationship query tests.

TLDR:
    Test fixture file (fileA) used by tests/uat/test_sprint5_uat.py and related UAT suites.
    Defines the root of the inheritance hierarchy and common callees for cross-file tests.
    Key classes: BaseModel (dataclass), BaseClass (base for single/multiple inheritance),
    AnotherBase (second base for multiple inheritance), FinalClass (leaf, no children).
    Key functions: func_a (called from fileB/my_service), helper_util (called from many files),
    deprecated_func (target for callers-of tests), new_func (replacement).
    Key globals: MY_CONSTANT, CONFIG_KEY (targets for reference queries).
    Consumed by: fileB, fileC, fileD, my_service — all in tests/uat_project/.
"""
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

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
