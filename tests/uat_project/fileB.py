"""
UAT test fixture providing child classes and cross-file call relationships for relationship tests.

TLDR:
    Test fixture file (fileB) used by tests/uat/test_sprint5_uat.py and related UAT suites.
    Exercises single and multiple inheritance from fileA, and cross-file function calls.
    Key classes: ChildClass(BaseClass), MultiChild(BaseClass, AnotherBase), ClassB(BaseClass).
    Key functions: func_b (calls func_a from fileA — primary cross-file call target),
    uses_deprecated / another_deprecated_user (callers of deprecated_func),
    process_data (calls func_a and helper_util).
    Consumed by: fileC, my_service — both import ChildClass and func_b from here.
    Depends on: fileA (BaseClass, AnotherBase, func_a, helper_util, deprecated_func, MY_CONSTANT).
"""
import os
import sys
from pathlib import Path
from typing import Optional

from fileA import (
    CONFIG_KEY,
    MY_CONSTANT,
    AnotherBase,
    BaseClass,
    deprecated_func,
    func_a,
    helper_util,
)


class ChildClass(BaseClass):
    """A child class that inherits from BaseClass."""

    def child_method(self):
        """Child-specific method."""
        # Calls parent method
        result = self.base_method()
        return f"child: {result}"

    def uses_constant(self):
        """Method that references MY_CONSTANT."""
        return MY_CONSTANT * 2


class MultiChild(BaseClass, AnotherBase):
    """A class with multiple inheritance."""

    def multi_method(self):
        """Method in multi-inheritance class."""
        self.base_method()
        self.another_method()
        return "multi"


def func_b():
    """A function that calls func_a from fileA (cross-file call)."""
    result = func_a()
    helper_util()
    return f"func_b called {result}"


def uses_deprecated():
    """A function that uses the deprecated function."""
    # This should be refactored!
    return deprecated_func()


def another_deprecated_user():
    """Another function using deprecated_func."""
    value = deprecated_func()
    return value + " processed"


def process_data():
    """Process data using various helpers."""
    func_a()
    helper_util()
    return CONFIG_KEY


class ClassB(BaseClass):
    """Another class inheriting from BaseClass."""
    pass
