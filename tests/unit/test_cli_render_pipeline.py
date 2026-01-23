"""
Unit tests for CLI render flag parsing and pipeline detection.

TLDR:
    Tests the new render flags (-rL, -rT, -rD, -rU, -rR) and format flags (-a, -m, -h, -p)
    on the match command. Also tests --via flag detection for pipeline mode.

Author: Neo (SWE Agent)
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import argparse
import pytest
from via.commands.match import MatchCommand


class TestRenderFlagParsing:
    """Tests for render flag argument parsing in MatchCommand."""

    def test_render_list_flag_short(self):
        """Test -rL flag parses as render_type=list."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-rL', 'test_pattern'])
        assert hasattr(args, 'render_type')
        assert args.render_type == 'list'

    def test_render_table_flag_short(self):
        """Test -rT flag parses as render_type=table."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-rT', 'test_pattern'])
        assert args.render_type == 'table'

    def test_render_diagram_flag_short(self):
        """Test -rD flag parses as render_type=diagram."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-rD', 'test_pattern'])
        assert args.render_type == 'diagram'

    def test_render_usage_flag_short(self):
        """Test -rU flag parses as render_type=usage."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-rU', 'test_pattern'])
        assert args.render_type == 'usage'

    def test_render_raw_flag_short(self):
        """Test -rR flag parses as render_type=raw."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-rR', 'test_pattern'])
        assert args.render_type == 'raw'

    def test_render_list_flag_long(self):
        """Test --list flag parses as render_type=list."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['--list', 'test_pattern'])
        assert args.render_type == 'list'

    def test_render_table_flag_long(self):
        """Test --table flag parses as render_type=table."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['--table', 'test_pattern'])
        assert args.render_type == 'table'

    def test_render_diagram_flag_long(self):
        """Test --diagram flag parses as render_type=diagram."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['--diagram', 'test_pattern'])
        assert args.render_type == 'diagram'

    def test_render_usage_flag_long(self):
        """Test --usage flag parses as render_type=usage."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['--usage', 'test_pattern'])
        assert args.render_type == 'usage'

    def test_render_raw_flag_long(self):
        """Test --raw flag parses as render_type=raw."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['--raw', 'test_pattern'])
        assert args.render_type == 'raw'

    def test_no_render_flag_defaults_to_none(self):
        """Test that no render flag results in render_type=None or not set."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['test_pattern'])
        # Should either not have render_type or be None
        render_type = getattr(args, 'render_type', None)
        assert render_type is None

    def test_render_flags_mutually_exclusive(self):
        """Test that render flags are mutually exclusive."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        # Should raise error if two render flags specified
        with pytest.raises(SystemExit):
            parser.parse_args(['-rL', '-rT', 'test_pattern'])


class TestFormatFlagParsing:
    """Tests for output format flag argument parsing."""

    def test_format_ascii_flag_short(self):
        """Test -a flag parses as format=ascii."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-a', 'test_pattern'])
        assert hasattr(args, 'format')
        assert args.format == 'ascii'

    def test_format_markdown_flag_short(self):
        """Test -m flag parses as format=md."""
        parser = argparse.ArgumentParser()
        MatchCommand.add_arguments(parser)
        
        args = parser.parse_args(['-m', 'test_pattern'])
        assert args.format == 'md'

