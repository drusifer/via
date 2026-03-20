"""
UAT test fixture providing a duplicate function name for ambiguous-symbol resolution tests.

TLDR:
    Test fixture file (fileD) used by tests/uat/test_sprint5_uat.py and related UAT suites.
    Intentionally defines do_work() with the same name as fileC.do_work() to exercise
    the ambiguous-resolution edge case (UAT-5.3).
    Key functions: do_work() (duplicate of fileC's — triggers ambiguity),
    calls_both_do_works() (additional caller referencing helper_util).
    Depends on: fileA (helper_util).
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
