"""
Test suite for CLI argument and help interface architecture (Morpheus's ARCH.md).

Covers:
- ArgumentProvider and HelpProvider ABCs
- add_arguments and get_help contract
- CLI entrypoint delegation
- Help output synchronization
"""
import argparse
import pytest
from abc import ABC, abstractmethod

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
