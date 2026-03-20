"""
User Acceptance Tests for Sprint 2 - Match Command.

TLDR:
    Captures the 12 acceptance criteria from SPRINT_2_USER_STORIES.md as automated
    regression tests. These tests verify end-to-end functionality of the match
    command against real indexed data using subprocess invocation of the via CLI.
    Key fixtures: uat_project (module-scoped, builds a real indexed project tree);
    run_via (helper to invoke the CLI and capture stdout/stderr).
    Key classes: TestAC1_GlobPatterns, TestAC2_SQLLikePatterns,
    TestAC3_EntityTypeFiltering, TestAC6_ResultLimiting, TestAC7_CaseSensitivity,
    TestAC8_OutputFormat, TestAC9_StreamingOutput, TestErrorHandling.
    Consumed by: pytest acceptance suite; depends on via CLI, DatabaseStore.

Author: Drew Gutstein
------------------------------------------------------------------------------
$Id$

License: GPL-3.0

Acceptance Criteria from SPRINT_2_USER_STORIES.md:
1. Users can search by glob patterns
2. Users can search by SQL LIKE patterns
3. Users can filter by entity type (method, class, function, import, global)
4. Users can filter by multiple types with OR logic (single -t per query)
5. Users can filter by file path (DEFERRED)
6. Users can limit results
7. Users can toggle case sensitivity
8. Output shows: type, file_path, line_number, qualified_name
9. Results stream for piping to less, grep, etc.
10. All P0 stories have tests (47+ tests)
11. Test coverage > 80%
12. Documentation updated
"""

import subprocess
import sys
from pathlib import Path

import pytest
from via.core.types import MatchOp, SymbolType
from via.db.store import DatabaseStore


@pytest.fixture(scope="module")
def uat_project(tmp_path_factory):
    """Create a realistic test project for UAT validation.

    This fixture creates a project with various Python constructs
    to test all acceptance criteria comprehensively.
    """
    project_dir = tmp_path_factory.mktemp("uat_project")

    # Create models module
    models_dir = project_dir / "models"
    models_dir.mkdir()

    (models_dir / "__init__.py").write_text("")

    (models_dir / "user.py").write_text('''
"""User model module."""
import json
from dataclasses import dataclass

MAX_NAME_LENGTH = 100
DEFAULT_ROLE = "user"

@dataclass
class User:
    """User entity class."""

    def __init__(self, name: str, email: str):
        """Initialize user."""
        self.name = name
        self.email = email

    def save(self):
        """Save user to database."""
        pass

    def delete(self):
        """Delete user from database."""
        pass

    def ToString(self):
        """Convert user to string."""
        return f"{self.name} <{self.email}>"


def create_user(name: str, email: str) -> User:
    """Factory function to create users."""
    return User(name, email)


def find_user_by_email(email: str) -> User:
    """Find user by email address."""
    pass
''')

    (models_dir / "post.py").write_text('''
"""Post model module."""
import datetime
from typing import Optional

POST_STATUS_DRAFT = "draft"
POST_STATUS_PUBLISHED = "published"

class Post:
    """Blog post entity."""

    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content

    def publish(self):
        """Publish the post."""
        pass

    def ToString(self):
        """Convert post to string."""
        return self.title


def get_recent_posts(limit: int = 10):
    """Get recent posts."""
    pass
''')

    # Create utils module
    utils_dir = project_dir / "utils"
    utils_dir.mkdir()

    (utils_dir / "__init__.py").write_text("")

    (utils_dir / "helpers.py").write_text('''
"""Helper utilities."""
import os
import re

DEBUG_MODE = False
LOG_LEVEL = "INFO"

def calculate_hash(data: str) -> str:
    """Calculate hash of data."""
    pass

def format_date(timestamp: float) -> str:
    """Format timestamp to date string."""
    pass

class CacheManager:
    """Simple cache manager."""

    def get(self, key: str):
        """Get value from cache."""
        pass

    def set(self, key: str, value: str):
        """Set value in cache."""
        pass
''')

    # Index the project
    via_dir = project_dir / ".via"
    via_dir.mkdir()
    db_path = via_dir / "index.db"

    # Create database and populate
    with DatabaseStore(str(db_path), str(project_dir)) as db:
        db.initialize_schema()

        # User model symbols
        db.insert_symbol('User', 'class', 'models/user.py', 10, 'models.user.User', 200, 400, None)
        db.insert_symbol('__init__', 'method', 'models/user.py', 14, 'models.user.User.__init__', 250, 100, 'User')
        db.insert_symbol('save', 'method', 'models/user.py', 19, 'models.user.User.save', 360, 50, 'User')
        db.insert_symbol('delete', 'method', 'models/user.py', 23, 'models.user.User.delete', 420, 60, 'User')
        db.insert_symbol('ToString', 'method', 'models/user.py', 27, 'models.user.User.ToString', 490, 80, 'User')
        db.insert_symbol('create_user', 'function', 'models/user.py', 32, 'models.user.create_user', 580, 100, None)
        db.insert_symbol('find_user_by_email', 'function', 'models/user.py', 37, 'models.user.find_user_by_email', 690, 60, None)
        db.insert_symbol('json', 'import', 'models/user.py', 3, 'json', 30, 11, None)
        db.insert_symbol('dataclass', 'import', 'models/user.py', 4, 'dataclasses.dataclass', 42, 28, None)
        db.insert_symbol('MAX_NAME_LENGTH', 'global', 'models/user.py', 6, 'models.user.MAX_NAME_LENGTH', 72, 20, None)
        db.insert_symbol('DEFAULT_ROLE', 'global', 'models/user.py', 7, 'models.user.DEFAULT_ROLE', 93, 21, None)
        db.insert_symbol('user.py', 'filename', 'models/user.py', 0, 'models/user.py', None, None, None)
        db.insert_symbol('models/user.py', 'filepath', 'models/user.py', 0, 'models/user.py', None, None, None)

        # Post model symbols
        db.insert_symbol('Post', 'class', 'models/post.py', 10, 'models.post.Post', 200, 300, None)
        db.insert_symbol('__init__', 'method', 'models/post.py', 14, 'models.post.Post.__init__', 250, 80, 'Post')
        db.insert_symbol('publish', 'method', 'models/post.py', 19, 'models.post.Post.publish', 340, 50, 'Post')
        db.insert_symbol('ToString', 'method', 'models/post.py', 23, 'models.post.Post.ToString', 400, 60, 'Post')
        db.insert_symbol('get_recent_posts', 'function', 'models/post.py', 28, 'models.post.get_recent_posts', 470, 50, None)
        db.insert_symbol('datetime', 'import', 'models/post.py', 3, 'datetime', 30, 15, None)
        db.insert_symbol('Optional', 'import', 'models/post.py', 4, 'typing.Optional', 46, 24, None)
        db.insert_symbol('POST_STATUS_DRAFT', 'global', 'models/post.py', 6, 'models.post.POST_STATUS_DRAFT', 72, 26, None)
        db.insert_symbol('POST_STATUS_PUBLISHED', 'global', 'models/post.py', 7, 'models.post.POST_STATUS_PUBLISHED', 99, 34, None)
        db.insert_symbol('post.py', 'filename', 'models/post.py', 0, 'models/post.py', None, None, None)
        db.insert_symbol('models/post.py', 'filepath', 'models/post.py', 0, 'models/post.py', None, None, None)

        # Helpers module symbols
        db.insert_symbol('CacheManager', 'class', 'utils/helpers.py', 12, 'utils.helpers.CacheManager', 200, 200, None)
        db.insert_symbol('get', 'method', 'utils/helpers.py', 15, 'utils.helpers.CacheManager.get', 250, 60, 'CacheManager')
        db.insert_symbol('set', 'method', 'utils/helpers.py', 19, 'utils.helpers.CacheManager.set', 320, 70, 'CacheManager')
        db.insert_symbol('calculate_hash', 'function', 'utils/helpers.py', 8, 'utils.helpers.calculate_hash', 100, 50, None)
        db.insert_symbol('format_date', 'function', 'utils/helpers.py', 12, 'utils.helpers.format_date', 160, 50, None)
        db.insert_symbol('os', 'import', 'utils/helpers.py', 3, 'os', 30, 9, None)
        db.insert_symbol('re', 'import', 'utils/helpers.py', 4, 're', 40, 9, None)
        db.insert_symbol('DEBUG_MODE', 'global', 'utils/helpers.py', 6, 'utils.helpers.DEBUG_MODE', 50, 18, None)
        db.insert_symbol('LOG_LEVEL', 'global', 'utils/helpers.py', 7, 'utils.helpers.LOG_LEVEL', 69, 17, None)
        db.insert_symbol('helpers.py', 'filename', 'utils/helpers.py', 0, 'utils/helpers.py', None, None, None)
        db.insert_symbol('utils/helpers.py', 'filepath', 'utils/helpers.py', 0, 'utils/helpers.py', None, None, None)

    yield project_dir


def run_via(args, project_dir):
    """Execute via with pipeline syntax.

    Args:
        args: Pipeline arguments (e.g., ['-mg', '*', '-tc'])
        project_dir: Project directory to run from (uses cwd)

    Returns:
        CompletedProcess result
    """
    cmd = [sys.executable, '-m', 'via'] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_dir))


class TestAC1_GlobPatterns:
    """AC1: Users can search by glob patterns."""

    def test_glob_asterisk_wildcard(self, uat_project):
        """Test glob * wildcard matches multiple characters."""
        result = run_via(['-mg', '*ToString*', '-tm'], uat_project)
        assert result.returncode == 0
        assert 'ToString' in result.stdout
        # Should find User.ToString and Post.ToString
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 2

    def test_glob_question_wildcard(self, uat_project):
        """Test glob ? wildcard matches single character."""
        result = run_via(['-mg', 'sav?', '-tm'], uat_project)
        assert result.returncode == 0
        assert 'save' in result.stdout

    def test_glob_prefix_match(self, uat_project):
        """Test glob prefix matching."""
        result = run_via(['-mg', 'create_*', '-tf'], uat_project)
        assert result.returncode == 0
        assert 'create_user' in result.stdout

    def test_glob_suffix_match(self, uat_project):
        """Test glob suffix matching."""
        result = run_via(['-mg', '*_hash', '-tf'], uat_project)
        assert result.returncode == 0
        assert 'calculate_hash' in result.stdout


class TestAC2_SQLLikePatterns:
    """AC2: Users can search by SQL LIKE patterns."""

    def test_like_percent_wildcard(self, uat_project):
        """Test SQL LIKE % wildcard."""
        result = run_via(['-ms', '%save%', '-tm'], uat_project)
        assert result.returncode == 0
        assert 'save' in result.stdout

    def test_like_underscore_wildcard(self, uat_project):
        """Test SQL LIKE _ wildcard for single character."""
        result = run_via(['-ms', 'sav_', '-tm'], uat_project)
        assert result.returncode == 0
        assert 'save' in result.stdout

    def test_like_prefix_search(self, uat_project):
        """Test SQL LIKE prefix matching."""
        result = run_via(['-ms', 'find_%', '-tf'], uat_project)
        assert result.returncode == 0
        assert 'find_user_by_email' in result.stdout


class TestAC3_EntityTypeFiltering:
    """AC3: Users can filter by entity type."""

    def test_filter_methods(self, uat_project):
        """Test filtering by method type."""
        result = run_via(['-mg', '*', '-tm'], uat_project)
        assert result.returncode == 0
        lines = result.stdout.strip().split('\n')
        assert all('method:' in l for l in lines if l)

    def test_filter_classes(self, uat_project):
        """Test filtering by class type."""
        result = run_via(['-mg', '*', '-tc'], uat_project)
        assert result.returncode == 0
        assert 'User' in result.stdout
        assert 'Post' in result.stdout
        assert 'CacheManager' in result.stdout

    def test_filter_functions(self, uat_project):
        """Test filtering by function type."""
        result = run_via(['-mg', '*', '-tf'], uat_project)
        assert result.returncode == 0
        assert 'function:' in result.stdout

    def test_filter_imports(self, uat_project):
        """Test filtering by import type."""
        result = run_via(['-mg', '*', '-ti'], uat_project)
        assert result.returncode == 0
        assert 'json' in result.stdout
        assert 'datetime' in result.stdout

    def test_filter_globals(self, uat_project):
        """Test filtering by global type."""
        result = run_via(['-mg', '*', '-tg'], uat_project)
        assert result.returncode == 0
        assert 'MAX_NAME_LENGTH' in result.stdout
        assert 'DEBUG_MODE' in result.stdout


class TestAC6_ResultLimiting:
    """AC6: Users can limit results."""

    def test_limit_results(self, uat_project):
        """Test -n flag limits results."""
        result = run_via(['-mg', '*', '-tm', '-n', '3'], uat_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 3

    def test_limit_one(self, uat_project):
        """Test limit of 1 returns exactly one result."""
        result = run_via(['-mg', '*', '-tc', '-n', '1'], uat_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 1

    def test_limit_greater_than_total(self, uat_project):
        """Test limit greater than total results returns all."""
        result = run_via(['-mg', '*', '-tc', '-n', '100'], uat_project)
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == 3  # User, Post, CacheManager


class TestAC7_CaseSensitivity:
    """AC7: Users can toggle case sensitivity."""

    def test_case_sensitive_no_match(self, uat_project):
        """Test case-sensitive search doesn't match wrong case."""
        result = run_via(['-mg', 'user', '-tc'], uat_project)
        assert result.returncode == 0
        # Should not find 'User' with lowercase search
        assert 'User' not in result.stdout

    def test_case_insensitive_match(self, uat_project):
        """Test -I flag enables case-insensitive matching."""
        result = run_via(['-mg', 'user', '-tc', '-I'], uat_project)
        assert result.returncode == 0
        assert 'User' in result.stdout

    def test_case_insensitive_uppercase_pattern(self, uat_project):
        """Test case-insensitive with uppercase pattern."""
        result = run_via(['-mg', 'TOSTRING', '-tm', '-I'], uat_project)
        assert result.returncode == 0
        assert 'ToString' in result.stdout


class TestAC8_OutputFormat:
    """AC8: Output shows type, file_path, line_number, qualified_name."""

    def test_output_contains_all_fields(self, uat_project):
        """Test output format includes all required fields."""
        result = run_via(['-mg', 'save', '-tm', '-n', '1'], uat_project)
        assert result.returncode == 0
        line = result.stdout.strip()
        parts = line.split(':')
        # Format: type:file:line:qualified:@byte+len
        assert parts[0] == 'method'  # type
        assert 'user.py' in parts[1]  # file_path
        assert parts[2].isdigit()  # line_number
        assert 'save' in parts[3]  # qualified_name

    def test_output_includes_byte_position(self, uat_project):
        """Test output includes byte position for methods."""
        result = run_via(['-mg', 'save', '-tm', '-n', '1'], uat_project)
        assert result.returncode == 0
        # Should have @offset+length
        assert '@' in result.stdout
        assert '+' in result.stdout

    def test_output_no_byte_position_for_files(self, uat_project):
        """Test filename output doesn't have byte position."""
        result = run_via(['-mg', 'user.py', '-tN'], uat_project)
        assert result.returncode == 0
        # Filename entries should not have @offset+length format
        # (or have None values)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.startswith('filename:'):
                # Either no @ or @None+None
                assert ':@' not in line or 'None' in line


class TestAC9_StreamingOutput:
    """AC9: Results stream for piping."""

    def test_output_pipeable(self, uat_project):
        """Test output can be piped to wc."""
        result = run_via(['-mg', '*', '-tm'], uat_project)
        assert result.returncode == 0
        # Verify clean output (no headers/footers)
        assert '===' not in result.stdout
        assert 'COMPLETE' not in result.stdout.upper()

    def test_output_grepable(self, uat_project):
        """Test output can be piped to grep."""
        result = run_via(['-mg', '*', '-tm'], uat_project)
        assert result.returncode == 0
        # Each line should be greppable
        lines = result.stdout.strip().split('\n')
        assert all(':' in l for l in lines if l)


class TestErrorHandling:
    """Test error handling for edge cases."""

    def test_database_not_found(self, tmp_path):
        """Test helpful error when database doesn't exist."""
        result = run_via(['-mg', '*', '-tm'], tmp_path)
        assert result.returncode != 0
        assert 'Database not found' in result.stderr
        assert 'via index' in result.stderr

    def test_no_matches_graceful(self, uat_project):
        """Test no matches returns empty output gracefully."""
        result = run_via(['-mg', 'nonexistent_xyz_123', '-tm'], uat_project)
        assert result.returncode == 0
        assert result.stdout.strip() == '' or result.stdout.strip() == ''
