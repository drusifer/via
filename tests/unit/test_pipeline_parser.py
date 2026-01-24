"""Unit tests for pipeline parser (Task 1.1)."""
import pytest
from via.pipeline.types import StageType, PipelineStage
from via.pipeline.parser import PipelineParser, PipelineParseError


class TestSplitOnVia:
    """Test _split_on_via() method."""

    def test_single_stage_no_via(self):
        """Single stage with no --via flag."""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc']
        segments = parser._split_on_via(argv)
        assert len(segments) == 1
        assert segments[0] == ['-mg', '*', '-tc']

    def test_two_stages_with_via(self):
        """Two stages separated by --via (for filtering)."""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc', '--via', '-mr', '__*', '-tm']
        segments = parser._split_on_via(argv)
        assert len(segments) == 2
        assert segments[0] == ['-mg', '*', '-tc']
        assert segments[1] == ['-mr', '__*', '-tm']

    def test_three_stages_with_via(self):
        """Three stages separated by --via flags (for multi-level filtering)."""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc', '--via', '-mr', '__*__', '-tm', '--via', '-mg', 'test*', '-tf']
        segments = parser._split_on_via(argv)
        assert len(segments) == 3
        assert segments[0] == ['-mg', '*', '-tc']
        assert segments[1] == ['-mr', '__*__', '-tm']
        assert segments[2] == ['-mg', 'test*', '-tf']

    def test_empty_argv(self):
        """Empty argv returns empty list."""
        parser = PipelineParser()
        argv = []
        segments = parser._split_on_via(argv)
        assert len(segments) == 0

    def test_via_at_start_ignored(self):
        """--via at start creates empty first segment (filtered out)."""
        parser = PipelineParser()
        argv = ['--via', '-mg', '*', '-tc']
        segments = parser._split_on_via(argv)
        # Empty segments should be filtered
        assert len(segments) == 1
        assert segments[0] == ['-mg', '*', '-tc']


class TestParseMatchStage:
    """Test parsing match stages."""

    def test_shorthand_glob_class(self):
        """Parse shorthand: -mg '*' -tc"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'class'
        assert stage.args.pattern == '*'

    def test_longform_match(self):
        """Parse long form: match --match-glob '*' --type-class"""
        parser = PipelineParser()
        stage = parser._parse_stage(['match', '--match-glob', '*', '--type-class'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'class'
        assert stage.args.pattern == '*'

    def test_match_with_regex(self):
        """Parse regex match: -mr '__*__' -tm"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mr', '__*__', '-tm'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'method'
        assert stage.args.pattern == '__*__'

    def test_match_with_case_insensitive(self):
        """Parse case-insensitive match: -mg 'user*' -tc -I"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', 'user*', '-tc', '-I'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.case_insensitive is True

    def test_match_with_limit(self):
        """Parse match with limit: -mg '*' -tc -n 20"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-n', '20'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.limit == 20

    def test_match_function_type(self):
        """Parse function match: -mg 'calc*' -tf"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', 'calc*', '-tf'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'function'

    def test_multiple_type_flags_or(self):
        """Parse multiple type flags (OR'd together): -mg '*' -tc -tf"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-tf'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_types == ['class', 'function']
        # When multiple types, symbol_type should be None
        assert stage.args.symbol_type is None

    def test_single_type_flag_also_sets_symbol_types(self):
        """Single type flag sets both symbol_type and symbol_types: -mg '*' -tc"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_types == ['class']
        assert stage.args.symbol_type == 'class'

    def test_three_type_flags_or(self):
        """Parse three type flags (OR'd): -mg '*' -tc -tf -tm"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-tf', '-tm'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_types == ['class', 'function', 'method']
        assert stage.args.symbol_type is None


class TestMatchWithOutput:
    """Test parsing match stages with integrated output flags.

    In the new design, output flags (-oL, -oT, -oR, etc.) are part of
    the match stage, not separate render stages.
    """

    def test_match_with_table_output(self):
        """Parse match with table output: -mg '*' -tc -oT -fm"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-oT', '-fm'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.pattern == '*'
        assert stage.args.symbol_type == 'class'
        assert stage.args.render_type == 'table'
        assert stage.args.format == 'md'

    def test_match_with_list_output(self):
        """Parse match with list output: -mg '*' -tc -oL"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-oL'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.render_type == 'list'

    def test_match_with_raw_context(self):
        """Parse match with raw output and context: -mg '*' -tf -oR -C 5"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tf', '-oR', '-C', '5'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.render_type == 'raw'
        assert stage.args.context == 5

    def test_match_with_before_after_context(self):
        """Parse match with -A and -B: -mg '*' -tf -oR -A 3 -B 2"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tf', '-oR', '-A', '3', '-B', '2'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.after_context == 3
        assert stage.args.before_context == 2

    def test_match_with_theme(self):
        """Parse match with theme: -mg '*' -tc -oF --theme monokai"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-oF', '--theme', 'monokai'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.render_type == 'formatted'
        assert stage.args.theme == 'monokai'


class TestParseMultiStage:
    """Test parsing multi-stage pipelines.

    In the new design, --via chains additional match filters.
    Output flags are part of the match stage, not separate.
    """

    def test_single_stage_with_output(self):
        """Parse single stage with output: -mg '*' -tc -oT"""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc', '-oT']
        stages = parser.parse(argv)
        assert len(stages) == 1
        assert stages[0].stage_type == StageType.MATCH
        assert stages[0].args.render_type == 'table'

    def test_two_stage_filter_pipeline(self):
        """Parse two-stage filter pipeline: -mg '*' -tc --via -mr '__*' -tm"""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc', '--via', '-mr', '__*', '-tm']
        stages = parser.parse(argv)
        assert len(stages) == 2
        assert stages[0].stage_type == StageType.MATCH
        assert stages[0].args.symbol_type == 'class'
        assert stages[1].stage_type == StageType.MATCH
        assert stages[1].args.symbol_type == 'method'

    def test_two_stage_filter_with_output(self):
        """Parse filter pipeline with output on last stage: -mg '*' -tc --via -mr '__*' -tm -oD"""
        parser = PipelineParser()
        argv = ['-mg', '*', '-tc', '--via', '-mr', '__*', '-tm', '-oD']
        stages = parser.parse(argv)
        assert len(stages) == 2
        assert stages[0].stage_type == StageType.MATCH
        assert stages[0].args.symbol_type == 'class'
        assert stages[1].stage_type == StageType.MATCH
        assert stages[1].args.symbol_type == 'method'
        assert stages[1].args.render_type == 'diagram'


class TestInvalidFlags:
    """Test error handling for invalid flags."""

    def test_mutually_exclusive_glob_and_regex(self):
        """Can't use -mg and -mr together."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser._parse_stage(['-mg', 'pattern', '-mr', 'other'])

    def test_empty_stage(self):
        """Empty stage raises error."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError, match="Empty pipeline stage"):
            parser._parse_stage([])

    def test_unknown_stage_type(self):
        """Unknown command raises error."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError, match="Unknown stage type"):
            parser._parse_stage(['unknown', 'command'])

    def test_invalid_match_flag(self):
        """Invalid match flag raises error."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser._parse_stage(['-mg', '*', '--invalid-flag'])


class TestStatsStage:
    """Test parsing stats stages."""

    def test_basic_stats(self):
        """Parse basic stats: stats"""
        parser = PipelineParser()
        stage = parser._parse_stage(['stats'])
        assert stage.stage_type == StageType.STATS
        assert stage.args.verbose == 0
        assert stage.args.json is False

    def test_stats_verbose(self):
        """Parse stats with verbose: stats -v"""
        parser = PipelineParser()
        stage = parser._parse_stage(['stats', '-v'])
        assert stage.stage_type == StageType.STATS
        assert stage.args.verbose == 1

    def test_stats_very_verbose(self):
        """Parse stats with -vv: stats -vv"""
        parser = PipelineParser()
        stage = parser._parse_stage(['stats', '-vv'])
        assert stage.stage_type == StageType.STATS
        assert stage.args.verbose == 2

    def test_stats_json(self):
        """Parse stats with JSON: stats --json"""
        parser = PipelineParser()
        stage = parser._parse_stage(['stats', '--json'])
        assert stage.stage_type == StageType.STATS
        assert stage.args.json is True
