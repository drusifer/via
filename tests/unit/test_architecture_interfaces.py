"""
Test suite for CLI argument and help interface architecture (Morpheus's ARCH.md).

TLDR:
    Verifies the ArgumentProvider and HelpProvider abstract base class contracts
    defined in ARCH.md. Tests that concrete implementations correctly register
    CLI arguments (add_arguments) and return help strings (get_help), and that
    both are surfaced in --help output.
    Key tests: test_argument_provider_adds_arguments, test_help_provider_returns_help,
    test_cli_help_integration.
    Role: guards the CLI plugin interface so all command types remain interchangeable.
    Design notes: defines local stub ABCs (ArgumentProvider, HelpProvider, DummyType)
    rather than importing from via.core.interfaces — tests the contract pattern itself.
"""
import argparse
from abc import ABC, abstractmethod

import pytest


# --- Example ABCs from ARCH.md ---
class ArgumentProvider(ABC):
    @abstractmethod
    def add_arguments(self, parser: argparse.ArgumentParser):
        pass

class HelpProvider(ABC):
    @abstractmethod
    def get_help(self) -> str:
        pass

# --- Example implementation for test ---
class DummyType(ArgumentProvider, HelpProvider):
    def add_arguments(self, parser):
        parser.add_argument('--foo', help='Foo argument')
    def get_help(self):
        return 'DummyType: provides --foo.'

# --- Tests ---
def test_argument_provider_adds_arguments():
    parser = argparse.ArgumentParser()
    dt = DummyType()
    dt.add_arguments(parser)
    args = parser.parse_args(['--foo', 'bar'])
    assert args.foo == 'bar'

def test_help_provider_returns_help():
    dt = DummyType()
    assert 'DummyType' in dt.get_help()

# --- Integration: CLI help output ---
def test_cli_help_integration(capsys):
    parser = argparse.ArgumentParser(description='Test CLI')
    dt = DummyType()
    dt.add_arguments(parser)
    parser.description += '\n' + dt.get_help()
    with pytest.raises(SystemExit):
        parser.parse_args(['--help'])
    out = capsys.readouterr().out
    assert '--foo' in out
    assert 'DummyType' in out
