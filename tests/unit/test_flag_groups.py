"""Unit tests for flag group CLI syntax in the via pipeline parser.

TLDR:
    Validates the prefix-based flag group system for the via CLI pipeline parser.
    Covers all three flag namespaces: match syntax (-mg/-mr/-ms), symbol type
    (-tc/-tf/-tm/-ti/-tg/-tF/-tN/-tH), and output format (-fa/-fm/-fh/-fp).
    Key classes: TestMatchFlags, TestTypeFlags, TestFormatFlags, TestOutputFlags,
    TestCombinedFlags (multi-flag pipelines), TestStageDetection (stage boundary logic),
    and TestOptions (-n limit, -I case-insensitive, -Q qualified name).
    Role: protects PipelineParser flag-group feature and stage-parsing logic against
    regressions; depends on PipelineParser and PipelineParseError.

"""
import pytest
from via.pipeline.parser import PipelineParseError, PipelineParser


class TestMatchFlags:
    """Test match syntax flags (-m<X>)."""

    def test_match_glob_flag(self):
        """Test -mg flag for glob patterns."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*Match*', '-tc'])
        assert stages[0].args.pattern == '*Match*'
        assert stages[0].args.match_syntax == 'g'

    def test_match_glob_long_flag(self):
        """Test --match-glob long form."""
        parser = PipelineParser()
        stages = parser.parse(['--match-glob', '*Match*', '-tc'])
        assert stages[0].args.pattern == '*Match*'
        assert stages[0].args.match_syntax == 'g'

    def test_match_regex_flag(self):
        """Test -mr flag for regex patterns."""
        parser = PipelineParser()
        stages = parser.parse(['-mr', '^test.*', '-tf'])
        assert stages[0].args.pattern == '^test.*'
        assert stages[0].args.match_syntax == 'r'

    def test_match_regex_long_flag(self):
        """Test --match-regex long form."""
        parser = PipelineParser()
        stages = parser.parse(['--match-regex', '^test.*', '-tf'])
        assert stages[0].args.pattern == '^test.*'
        assert stages[0].args.match_syntax == 'r'

    def test_match_sql_flag(self):
        """Test -ms flag for SQL LIKE patterns."""
        parser = PipelineParser()
        stages = parser.parse(['-ms', 'test%', '-tf'])
        assert stages[0].args.pattern == 'test%'
        assert stages[0].args.match_syntax == 's'

    def test_match_sql_long_flag(self):
        """Test --match-sql long form."""
        parser = PipelineParser()
        stages = parser.parse(['--match-sql', 'test%', '-tf'])
        assert stages[0].args.pattern == 'test%'
        assert stages[0].args.match_syntax == 's'


class TestTypeFlags:
    """Test symbol type flags (-t<X>)."""

    def test_type_class_flag(self):
        """Test -tc flag for classes."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc'])
        assert stages[0].args.symbol_type == 'class'

    def test_type_class_long_flag(self):
        """Test --type-class long form."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '--type-class'])
        assert stages[0].args.symbol_type == 'class'

    def test_type_function_flag(self):
        """Test -tf flag for functions."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tf'])
        assert stages[0].args.symbol_type == 'function'

    def test_type_method_flag(self):
        """Test -tm flag for methods."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tm'])
        assert stages[0].args.symbol_type == 'method'

    def test_type_import_flag(self):
        """Test -ti flag for imports."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-ti'])
        assert stages[0].args.symbol_type == 'import'

    def test_type_global_flag(self):
        """Test -tg flag for globals."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tg'])
        assert stages[0].args.symbol_type == 'global'

    def test_type_filepath_flag(self):
        """Test -tF flag for file paths."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tF'])
        assert stages[0].args.symbol_type == 'filepath'

    def test_type_filename_flag(self):
        """Test -tN flag for file names."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tN'])
        assert stages[0].args.symbol_type == 'filename'

    def test_type_header_flag(self):
        """Test -tH flag for markdown headers."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tH'])
        assert stages[0].args.symbol_type == 'header'


class TestFormatFlags:
    """Test output format flags (-f<X>)."""

    def test_format_ascii_flag(self):
        """Test -fa flag for ASCII/terminal format."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oT', '-fa'])
        assert stages[1].args.format == 'ascii'

    def test_format_markdown_flag(self):
        """Test -fm flag for markdown format."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oT', '-fm'])
        assert stages[1].args.format == 'md'

    def test_format_html_flag(self):
        """Test -fh flag for HTML format."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oT', '-fh'])
        assert stages[1].args.format == 'html'

    def test_format_png_flag(self):
        """Test -fp flag for PNG format."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oD', '-fp'])
        assert stages[1].args.format == 'png'


class TestOutputFlags:
    """Test output type flags (-o<X>) - should still work."""

    def test_output_list_flag(self):
        """Test -oL flag for list output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oL'])
        assert stages[1].args.render_type == 'list'

    def test_output_table_flag(self):
        """Test -oT flag for table output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oT'])
        assert stages[1].args.render_type == 'table'

    def test_output_diagram_flag(self):
        """Test -oD flag for diagram output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '--via', '-oD'])
        assert stages[1].args.render_type == 'diagram'

    def test_output_usage_flag(self):
        """Test -oU flag for usage output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tf', '--via', '-oU'])
        assert stages[1].args.render_type == 'usage'

    def test_output_raw_flag(self):
        """Test -oR flag for raw output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tf', '--via', '-oR'])
        assert stages[1].args.render_type == 'raw'

    def test_output_formatted_flag(self):
        """Test -oF flag for formatted output."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tf', '--via', '-oF'])
        assert stages[1].args.render_type == 'formatted'


class TestCombinedFlags:
    """Test combinations of new flag groups."""

    def test_match_type_output_format(self):
        """Test full command with all flag groups."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*Match*', '-tc', '--via', '-oT', '-fm'])
        # Match stage
        assert stages[0].args.pattern == '*Match*'
        assert stages[0].args.match_syntax == 'g'
        assert stages[0].args.symbol_type == 'class'
        # Render stage
        assert stages[1].args.render_type == 'table'
        assert stages[1].args.format == 'md'

    def test_regex_function_raw(self):
        """Test regex match with function type and raw output."""
        parser = PipelineParser()
        stages = parser.parse(['-mr', '^test_.*', '-tf', '--via', '-oR'])
        assert stages[0].args.pattern == '^test_.*'
        assert stages[0].args.match_syntax == 'r'
        assert stages[0].args.symbol_type == 'function'
        assert stages[1].args.render_type == 'raw'

    def test_sql_header_table_html(self):
        """Test SQL match with header type, table output, HTML format."""
        parser = PipelineParser()
        stages = parser.parse(['-ms', 'API%', '-tH', '--via', '-oT', '-fh'])
        assert stages[0].args.pattern == 'API%'
        assert stages[0].args.match_syntax == 's'
        assert stages[0].args.symbol_type == 'header'
        assert stages[1].args.render_type == 'table'
        assert stages[1].args.format == 'html'


class TestStageDetection:
    """Test that new flags are detected as match stages."""

    def test_mg_detected_as_match(self):
        """Test -mg is detected as match stage."""
        parser = PipelineParser()
        assert parser._is_match_stage(['-mg', '*'])

    def test_mr_detected_as_match(self):
        """Test -mr is detected as match stage."""
        parser = PipelineParser()
        assert parser._is_match_stage(['-mr', '^test'])

    def test_ms_detected_as_match(self):
        """Test -ms is detected as match stage."""
        parser = PipelineParser()
        assert parser._is_match_stage(['-ms', 'test%'])

    def test_tc_detected_as_match(self):
        """Test -tc is detected as match stage."""
        parser = PipelineParser()
        assert parser._is_match_stage(['-tc'])

    def test_tf_detected_as_match(self):
        """Test -tf is detected as match stage."""
        parser = PipelineParser()
        assert parser._is_match_stage(['-tf'])


class TestOptions:
    """Test that options still work with new flags."""

    def test_limit_option(self):
        """Test -n limit option."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '-n', '5'])
        assert stages[0].args.limit == 5

    def test_case_insensitive_option(self):
        """Test -I case insensitive option."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '-I'])
        assert stages[0].args.case_insensitive is True

    def test_qualified_option(self):
        """Test -Q qualified option."""
        parser = PipelineParser()
        stages = parser.parse(['-mg', '*', '-tc', '-Q'])
        assert stages[0].args.match_qualified is True
