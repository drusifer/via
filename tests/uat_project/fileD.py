"""
FileD - Additional utilities.

Contains another do_work function to test ambiguous resolution.
"""
from fileA import helper_util


def do_work():
    """A function named do_work in fileD (same name as in fileC)."""
    helper_util()
    return "work from D"


def calls_both_do_works():
    """Function that might call do_work."""
    helper_util()
    return "calls both"
