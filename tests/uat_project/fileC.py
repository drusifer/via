"""
UAT test fixture providing grandchild classes for deep inheritance and ambiguous-name tests.

TLDR:
    Test fixture file (fileC) used by tests/uat/test_sprint5_uat.py and related UAT suites.
    Exercises multi-level (grandchild) inheritance and provides one of two do_work() definitions
    for the ambiguous-symbol resolution edge case (UAT-5.3).
    Key classes: GrandChildClass(ChildClass), AnotherGrandChild(ChildClass),
    DataChild(ChildClass) — a dataclass child.
    Key functions: do_work() — same name as fileD.do_work(), used to test ambiguous resolution.
    Depends on: fileA (BaseClass, helper_util), fileB (ChildClass, MultiChild, func_b).
"""
from dataclasses import dataclass
from typing import List

from fileA import BaseClass, helper_util
from fileB import ChildClass, MultiChild, func_b


class GrandChildClass(ChildClass):
    """A grandchild class (inherits from ChildClass which inherits from BaseClass)."""

    def grandchild_method(self):
        """Grandchild-specific method."""
        # Calls parent and grandparent methods
        self.child_method()
        self.base_method()
        return "grandchild"


class AnotherGrandChild(ChildClass):
    """Another grandchild of BaseClass via ChildClass."""

    def another_gc_method(self):
        """Another grandchild method."""
        func_b()
        helper_util()
        return "another_gc"


def do_work():
    """A function named do_work in fileC."""
    helper_util()
    return "work from C"


@dataclass
class DataChild(ChildClass):
    """A dataclass that also inherits from ChildClass."""
    extra_field: str = "default"

    def data_method(self):
        """Method in dataclass child."""
        return self.extra_field
