"""Unit tests for pipeline parser (Task 1.1)."""
import pytest
from via.pipeline.types import StageType, PipelineStage
from via.pipeline.parser import PipelineParser, PipelineParseError


class TestSplitOnVia:
    """Test _split_on_via() method."""

    def test_single_stage_no_via(self):
        """Single stage with no --via flag."""
        parser = PipelineParser()
        argv = ['-mg', '-c', '*']
        segments = parser._split_on_via(argv)
        assert len(segments) == 1
        assert segments[0] == ['-mg', '-c', '*']

    def test_two_stages_with_via(self):
        """Two stages separated by --via."""
        parser = PipelineParser()
        argv = ['-mg', '-c', '*', '--via', '-oT']
        segments = parser._split_on_via(argv)
        assert len(segments) == 2
        assert segments[0] == ['-mg', '-c', '*']
        assert segments[1] == ['-oT']

    def test_three_stages_with_via(self):
        """Three stages separated by --via flags."""
        parser = PipelineParser()
        argv = ['-mg', '-c', '*', '--via', '-mr', '-m', '__*__', '--via', '-oDm']
        segments = parser._split_on_via(argv)
        assert len(segments) == 3
        assert segments[0] == ['-mg', '-c', '*']
        assert segments[1] == ['-mr', '-m', '__*__']
        assert segments[2] == ['-oDm']

    def test_empty_argv(self):
        """Empty argv returns empty list."""
        parser = PipelineParser()
        argv = []
        segments = parser._split_on_via(argv)
        assert len(segments) == 0

    def test_via_at_start_ignored(self):
        """--via at start creates empty first segment (filtered out)."""
        parser = PipelineParser()
        argv = ['--via', '-mg', '-c', '*']
        segments = parser._split_on_via(argv)
        # Empty segments should be filtered
        assert len(segments) == 1
        assert segments[0] == ['-mg', '-c', '*']


class TestParseMatchStage:
    """Test parsing match stages."""

    def test_shorthand_glob_class(self):
        """Parse shorthand: -mg -c '*'"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '-c', '*'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'class'
        assert stage.args.pattern == '*'

    def test_longform_match(self):
        """Parse long form: match --type class --glob '*'"""
        parser = PipelineParser()
        stage = parser._parse_stage(['match', '--type', 'class', '--glob', '*'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'class'
        assert stage.args.pattern == '*'

    def test_match_with_regex(self):
        """Parse regex match: -mr -m '__*__'"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mr', '-m', '__*__'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'method'
        assert stage.args.pattern == '__*__'

    def test_match_with_case_insensitive(self):
        """Parse case-insensitive match: -mg -I -c 'user*'"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '-I', '-c', 'user*'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.case_insensitive is True

    def test_match_with_limit(self):
        """Parse match with limit: -mg -c '*' -n 20"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '-c', '*', '-n', '20'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.limit == 20

    def test_match_function_type(self):
        """Parse function match: -mg -f 'calc*'"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '-f', 'calc*'])
        assert stage.stage_type == StageType.MATCH
        assert stage.args.symbol_type == 'function'


class TestParseRenderStage:
    """Test parsing render stages."""

    def test_render_table_markdown(self):
        """Parse render table markdown: -oTm"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-oTm'])
        assert stage.stage_type == StageType.RENDER
        assert stage.args.render_type == 'table'
        assert stage.args.format == 'md'

    def test_render_list(self):
        """Parse render list: -oL"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-oL'])
        assert stage.stage_type == StageType.RENDER
        assert stage.args.render_type == 'list'

    def test_render_with_context(self):
        """Parse render with context: -oR -C 5"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-oR', '-C', '5'])
        assert stage.stage_type == StageType.RENDER
        assert stage.args.render_type == 'raw'
        assert stage.args.context == 5

    def test_render_with_before_after_context(self):
        """Parse render with -A and -B: -oR -A 3 -B 2"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-oR', '-A', '3', '-B', '2'])
        assert stage.stage_type == StageType.RENDER
        assert stage.args.after_context == 3
        assert stage.args.before_context == 2

    def test_render_with_theme(self):
        """Parse render with theme: -oF --theme monokai"""
        parser = PipelineParser()
        stage = parser._parse_stage(['-oF', '--theme', 'monokai'])
        assert stage.stage_type == StageType.RENDER
        assert stage.args.render_type == 'formatted'
        assert stage.args.theme == 'monokai'


class TestParseMultiStage:
    """Test parsing multi-stage pipelines."""

    def test_two_stage_pipeline(self):
        """Parse two-stage pipeline: -mg -c '*' --via -oT"""
        parser = PipelineParser()
        argv = ['-mg', '-c', '*', '--via', '-oT']
        stages = parser.parse(argv)
        assert len(stages) == 2
        assert stages[0].stage_type == StageType.MATCH
        assert stages[1].stage_type == StageType.RENDER

    def test_three_stage_pipeline(self):
        """Parse three-stage pipeline: match -> match -> render"""
        parser = PipelineParser()
        argv = ['-mg', '-c', '*Match*', '--via', '-mr', '-m', '__*__', '--via', '-oDm']
        stages = parser.parse(argv)
        assert len(stages) == 3
        assert stages[0].stage_type == StageType.MATCH
        assert stages[0].args.symbol_type == 'class'
        assert stages[1].stage_type == StageType.MATCH
        assert stages[1].args.symbol_type == 'method'
        assert stages[2].stage_type == StageType.RENDER
        assert stages[2].args.render_type == 'diagram'


class TestInvalidFlags:
    """Test error handling for invalid flags."""

    def test_mutually_exclusive_glob_and_regex(self):
        """Can't use -g and -r together."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser._parse_stage(['-mg', '-r', 'pattern'])

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
            parser._parse_stage(['-mg', '--invalid-flag'])


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
