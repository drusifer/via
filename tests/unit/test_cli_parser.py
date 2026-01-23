"""
Unit tests for CLI argument parsing.

TLDR:
    Tests the argument parser for the `via` CLI tool. Verifies correct parsing
    of flags, subcommands, defaults, and error handling. Tests cover --version,
    verbosity levels, index command with all flags, and edge cases.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0
"""

import pytest
import sys
import io
from via.__main__ import _create_parser, _safe_print
from via.core.constants import EXIT_SUCCESS


class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_create_parser_has_index_subcommand(self):
        """Verify parser has index subcommand."""
        parser = _create_parser()

        # Parse index command
        args = parser.parse_args(['index'])
        assert args.command == 'index'

    def test_version_flag(self):
        """Test --version flag."""
        parser = _create_parser()

        # --version should cause SystemExit
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])

        # Should exit with success code
        assert exc_info.value.code == 0

    def test_verbosity_levels(self):
        """Test -v, -vv, -vvv, -vvvv flags."""
        parser = _create_parser()

        # No verbosity flag
        args = parser.parse_args(['index'])
        assert args.verbosity == 0

        # -v
        args = parser.parse_args(['-v', 'index'])
        assert args.verbosity == 1

        # -vv
        args = parser.parse_args(['-vv', 'index'])
        assert args.verbosity == 2

        # -vvv
        args = parser.parse_args(['-vvv', 'index'])
        assert args.verbosity == 3

        # -vvvv
        args = parser.parse_args(['-vvvv', 'index'])
        assert args.verbosity == 4

    def test_index_default_directory(self):
        """Test index command defaults to current directory."""
        parser = _create_parser()

        args = parser.parse_args(['index'])
        assert args.directory == '.'

    def test_index_with_directory(self):
        """Test index command with specified directory."""
        parser = _create_parser()

        args = parser.parse_args(['index', '/path/to/project'])
        assert args.directory == '/path/to/project'

    def test_force_flag(self):
        """Test --force flag."""
        parser = _create_parser()

        # Without flag
        args = parser.parse_args(['index'])
        assert args.force is False

        # With flag
        args = parser.parse_args(['index', '--force'])
        assert args.force is True

    def test_watch_flag(self):
        """Test -w/--watch flag."""
        parser = _create_parser()

        # Without flag
        args = parser.parse_args(['index'])
        assert args.watch is False

        # With -w
        args = parser.parse_args(['index', '-w'])
        assert args.watch is True

        # With --watch
        args = parser.parse_args(['index', '--watch'])
        assert args.watch is True

    def test_exclude_pattern_single(self):
        """Test single --exclude pattern."""
        parser = _create_parser()

        args = parser.parse_args(['index', '--exclude', '*.pyc'])
        assert args.exclude == ['*.pyc']

    def test_exclude_patterns_multiple(self):
        """Test multiple --exclude patterns."""
        parser = _create_parser()

        args = parser.parse_args([
            'index',
            '--exclude', '*.pyc',
            '--exclude', '__pycache__',
            '--exclude', 'build/'
        ])
        assert args.exclude == ['*.pyc', '__pycache__', 'build/']

    def test_exclude_without_patterns(self):
        """Test that exclude defaults to None."""
        parser = _create_parser()

        args = parser.parse_args(['index'])
        assert args.exclude is None

    def test_custom_db_path(self):
        """Test --db flag for custom database path."""
        parser = _create_parser()

        # Without flag
        args = parser.parse_args(['index'])
        assert args.db is None

        # With flag
        args = parser.parse_args(['index', '--db', '/tmp/custom.db'])
        assert args.db == '/tmp/custom.db'

    def test_no_command_shows_help(self):
        """Test that no command shows help."""
        parser = _create_parser()

        args = parser.parse_args([])
        assert args.command is None

    def test_combined_flags(self):
        """Test combining multiple flags."""
        parser = _create_parser()

        args = parser.parse_args([
            '-vvv',
            'index',
            '/my/project',
            '--force',
            '--exclude', '*.pyc',
            '--exclude', 'build/',
            '--db', '/tmp/test.db'
        ])

        assert args.verbosity == 3
        assert args.command == 'index'
        assert args.directory == '/my/project'
        assert args.force is True
        assert args.exclude == ['*.pyc', 'build/']
        assert args.db == '/tmp/test.db'

    def test_help_flag(self):
        """Test -h/--help flag."""
        parser = _create_parser()

        # --help should cause SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(['--help'])

        # index --help should also work
        with pytest.raises(SystemExit):
            parser.parse_args(['index', '--help'])


class TestSafePrint:
    """Tests for Unicode-safe printing."""

    def test_safe_print_ascii_text(self):
        """Test _safe_print with plain ASCII text."""
        output = io.StringIO()
        _safe_print("Hello, world!", file=output)
        assert output.getvalue() == "Hello, world!\n"

    def test_safe_print_unicode_text(self):
        """Test _safe_print with Unicode characters."""
        output = io.StringIO()
        _safe_print("Hello ✅ world 🌍", file=output)
        assert "Hello" in output.getvalue()
        assert "world" in output.getvalue()

    def test_safe_print_with_emoji_in_header(self):
        """Test _safe_print with emoji (like in markdown headers)."""
        output = io.StringIO()
        text = "header:/path/to/file.md:10:Section ✅ Complete:@100+50"
        _safe_print(text, file=output)
        assert "header:" in output.getvalue()
        assert "/path/to/file.md" in output.getvalue()

    def test_safe_print_latin1_fallback(self):
        """Test _safe_print handles encoding errors gracefully."""
        # Create a mock file with latin-1 encoding that will fail on emoji
        class Latin1File:
            encoding = 'latin-1'
            def __init__(self):
                self.content = ""
            def write(self, text):
                # Simulate latin-1 encoding behavior
                self.content += text.encode('latin-1', errors='replace').decode('latin-1')

        mock_file = Latin1File()
        # This should not raise an error
        _safe_print("Test ✅ emoji", file=mock_file)
        assert "Test" in mock_file.content

    def test_safe_print_empty_string(self):
        """Test _safe_print with empty string."""
        output = io.StringIO()
        _safe_print("", file=output)
        assert output.getvalue() == "\n"

    def test_safe_print_multiline(self):
        """Test _safe_print with multiline text."""
        output = io.StringIO()
        _safe_print("Line 1\nLine 2\nLine 3", file=output)
        result = output.getvalue()
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
