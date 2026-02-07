"""
FileC - Grandchild classes and deeper hierarchy.

Contains classes that inherit from fileB (grandchildren of fileA).
"""
from typing import List
from dataclasses import dataclass

from fileB import ChildClass, MultiChild, func_b
from fileA import helper_util, BaseClass


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
