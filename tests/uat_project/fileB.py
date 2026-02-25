"""
FileB - Child classes and calling functions.

Contains classes that inherit from fileA and functions that call fileA functions.
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
