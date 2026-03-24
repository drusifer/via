"""Playwright E2E test fixture — symbols for the via web UI tests."""


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b


class ScientificCalculator(Calculator):
    """Extended calculator with scientific functions."""

    def square(self, a: float) -> float:
        return a * a


def greet(name: str) -> str:
    """Return a greeting string."""
    return f"Hello, {name}!"


MAX_VALUE = 100
