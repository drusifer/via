"""
Tests for Stats command.

TDD: Tests written first, then implementation.
"""

import json
from unittest.mock import MagicMock

import pytest
from via.commands.stats import StatsCommand


class TestStatsCommandBasics:
    """Test basic stats command functionality."""

    def test_stats_command_exists(self):
        """Test StatsCommand can be instantiated."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 100
        mock_db.count_files.return_value = 10

        cmd = StatsCommand(mock_db)
        assert cmd is not None

    def test_execute_returns_string(self):
        """Test execute returns a string."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 100
        mock_db.count_files.return_value = 10
        mock_db.count_by_type.return_value = {}

        cmd = StatsCommand(mock_db)
        result = cmd.execute()

        assert isinstance(result, str)


class TestStatsCommandOutput:
    def test_stats_includes_markdown_headers(self):
        """Stats output should include header (markdown) counts."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 200
        mock_db.count_files.return_value = 25
        mock_db.count_by_type.return_value = {
            'function': 100,
            'class': 50,
            'header': 30,
            'method': 10,
        }
        cmd = StatsCommand(mock_db)
        result = cmd.execute(verbose=0)
        assert 'Headers:       30' in result
        assert 'Functions:     100' in result
        assert 'Classes:       50' in result
        assert 'Methods:       10' in result

    def test_stats_includes_zero_headers(self):
        """Stats output should show zero headers if none present."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 10
        mock_db.count_files.return_value = 2
        mock_db.count_by_type.return_value = {
            'function': 5,
            'class': 5,
        }
        cmd = StatsCommand(mock_db)
        result = cmd.execute(verbose=0)
        assert 'Headers:       0' in result

    def test_basic_stats(self):
        """Test basic stats shows totals."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 150
        mock_db.count_files.return_value = 20

        cmd = StatsCommand(mock_db)
        result = cmd.execute(verbose=0)

        assert 'Total symbols: 150' in result
        assert 'Total files: 20' in result

    def test_verbose_stats(self):
        """Test verbose stats shows breakdown by type."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 150
        mock_db.count_files.return_value = 20
        mock_db.count_by_type.return_value = {
            'function': 80,
            'class': 30,
            'method': 40,
        }

        cmd = StatsCommand(mock_db)
        result = cmd.execute(verbose=1)

        assert 'function: 80' in result
        assert 'class: 30' in result
        assert 'method: 40' in result


class TestStatsCommandJsonOutput:
    """Test JSON output mode."""

    def test_json_output(self):
        """Test stats with JSON output."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 100
        mock_db.count_files.return_value = 10
        mock_db.count_by_type.return_value = {'function': 50}

        cmd = StatsCommand(mock_db)
        result = cmd.execute(as_json=True)

        # Should be valid JSON
        data = json.loads(result)
        assert data['total_symbols'] == 100
        assert data['total_files'] == 10

    def test_json_verbose_output(self):
        """Test verbose stats with JSON output."""
        mock_db = MagicMock()
        mock_db.count_symbols.return_value = 100
        mock_db.count_files.return_value = 10
        mock_db.count_by_type.return_value = {
            'function': 50,
            'class': 20,
        }

        cmd = StatsCommand(mock_db)
        result = cmd.execute(verbose=1, as_json=True)

        data = json.loads(result)
        assert 'by_type' in data
        assert data['by_type']['function'] == 50
        assert data['by_type']['class'] == 20
