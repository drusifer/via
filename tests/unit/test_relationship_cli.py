"""Unit tests for CLI relationship flag parsing (result-first semantics).

Tests that PipelineParser correctly parses relationship query syntax with
both forward and inverse relationship types.
"""
import pytest
from via.core.relationship_types import RelationshipType
from via.pipeline.parser import PipelineParseError, PipelineParser
from via.pipeline.types import StageType


class TestRelationshipFlagParsing:
    """Test parsing of relationship CLI flags."""

    def test_parse_via_inherits_from_long_form(self):
        """Test --via inherits-from creates relationship stage."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--via', 'inherits-from',
            '-mg', 'BaseClass', '-tc'
        ])

        assert len(stages) >= 1
        result = stages[0]
        assert result.stage_type == StageType.MATCH
        assert result.args.pattern == '*'

        rel = result.args.relationship
        assert rel is not None
        assert rel.relationship_type.value == RelationshipType.INHERITS_FROM.value
        assert rel.filter_pattern == 'BaseClass'
        assert 'class' in rel.filter_types
        assert rel.is_negative is False
        assert rel.inverted is False

    def test_parse_via_calls_long_form(self):
        """Test --via calls relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--via', 'calls',
            '-mg', 'connect', '-tf'
        ])

        result = stages[0]
        rel = result.args.relationship
        assert rel.relationship_type.value == RelationshipType.CALLS.value
        assert rel.filter_pattern == 'connect'
        assert rel.inverted is False

    def test_parse_via_imports_long_form(self):
        """Test --via imports relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '--via', 'imports',
            '-mg', 'os', '-ti'
        ])

        result = stages[0]
        rel = result.args.relationship
        assert rel.relationship_type.value == RelationshipType.IMPORTS.value
        assert rel.filter_pattern == 'os'

    def test_parse_via_references_long_form(self):
        """Test --via references relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--via', 'references',
            '-mg', 'CONFIG*', '-tg'
        ])

        result = stages[0]
        rel = result.args.relationship
        assert rel.relationship_type.value == RelationshipType.REFERENCES.value

    def test_parse_via_called_by_inverse(self):
        """Test --via called-by sets inverted=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--via', 'called-by',
            '-mg', 'main_func', '-tf'
        ])

        result = stages[0]
        rel = result.args.relationship
        assert rel.relationship_type.value == RelationshipType.CALLS.value
        assert rel.filter_pattern == 'main_func'
        assert rel.inverted is True
        assert rel.is_negative is False

    def test_parse_via_inherited_by_inverse(self):
        """Test --via inherited-by sets inverted=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--via', 'inherited-by',
            '-mg', 'ChildClass', '-tc'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.INHERITS_FROM.value
        assert rel.inverted is True

    def test_parse_via_declares_inverse(self):
        """Test --via declares sets inverted=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '--via', 'declares',
            '-mg', 'MyClass', '-tc'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.DECLARES.value
        assert rel.inverted is True

    def test_parse_via_declared_in_not_inverse(self):
        """Test --via declared-in sets inverted=False."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--via', 'declared-in',
            '-mg', 'my_file.py', '-tF'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.DECLARES.value
        assert rel.inverted is False

    def test_parse_sans_called_by_inverse(self):
        """Test --sans called-by (unused functions) sets inverted=True + is_negative=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--sans', 'called-by',
            '-mg', '*', '-tf'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.CALLS.value
        assert rel.is_negative is True
        assert rel.inverted is True


class TestRelationshipVShortFlag:
    """Test -V TYPE short form relationship flags."""

    def test_parse_V_inherits_from(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-V', 'inherits-from',
            '-mg', 'Base', '-tc'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.INHERITS_FROM.value
        assert rel.filter_pattern == 'Base'

    def test_parse_V_calls(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-V', 'calls',
            '-mg', 'helper*', '-tf'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.CALLS.value

    def test_parse_V_imports(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '-V', 'imports',
            '-mg', 'json', '-ti'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.IMPORTS.value

    def test_parse_V_references(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tm',
            '-V', 'references',
            '-mg', 'self.*', '-tg'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.REFERENCES.value

    def test_parse_V_called_by_inverse(self):
        """Inverse types work with -V short form."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-V', 'called-by',
            '-mg', 'main', '-tf'
        ])

        rel = stages[0].args.relationship
        assert rel.relationship_type.value == RelationshipType.CALLS.value
        assert rel.inverted is True


class TestSansFlag:
    """Test --sans / -S flag for negative relationship filtering."""

    def test_sans_long_form_sets_is_negative(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--sans', 'inherits-from',
            '-mg', '*', '-tc',
        ])

        rel = stages[0].args.relationship
        assert rel.is_negative is True
        assert rel.inverted is False

    def test_S_short_form_sets_is_negative(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-S', 'calls',
            '-mg', '*', '-tc',
        ])

        rel = stages[0].args.relationship
        assert rel.is_negative is True

    def test_no_sans_is_negative_false_by_default(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-V', 'inherits-from',
            '-mg', 'Base', '-tc'
        ])

        rel = stages[0].args.relationship
        assert rel.is_negative is False


class TestRelationshipWithOptions:
    """Test relationship queries with additional options."""

    def test_relationship_with_limit(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-n', '5',
            '-V', 'inherits-from',
            '-mg', 'Base*', '-tc'
        ])

        result = stages[0]
        assert result.args.limit == 5
        assert result.args.relationship is not None

    def test_relationship_with_case_insensitive(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-I',
            '-V', 'inherits-from',
            '-mg', 'base*', '-tc'
        ])

        result = stages[0]
        assert result.args.case_insensitive is True

    def test_relationship_with_output_format(self):
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-V', 'inherits-from',
            '-mg', 'Base*', '-tc',
            '-oT', '-fm'
        ])

        result = stages[0]
        assert result.args.render_type == 'table'
        assert result.args.format == 'md'


class TestRelationshipEdgeCases:
    """Test edge cases for relationship parsing."""

    def test_result_multiple_types(self):
        """Result stage with multiple symbol types (OR)."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-tf',
            '-V', 'calls',
            '-mg', 'helper*', '-tf'
        ])

        result = stages[0]
        assert 'class' in result.args.symbol_types
        assert 'function' in result.args.symbol_types

    def test_filter_multiple_types(self):
        """Filter stage with multiple symbol types."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-V', 'calls',
            '-mg', '*util*', '-tf', '-tm'
        ])

        rel = stages[0].args.relationship
        assert 'function' in rel.filter_types
        assert 'method' in rel.filter_types

    def test_multiple_relationship_filters_are_preserved_in_order(self):
        """A result stage can be narrowed by multiple relationship filters."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--via', 'calls',
            '-mg', 'connect', '-tf',
            '--sans', 'declared-in',
            '-mg', '*test*', '-tF',
        ])

        relationships = stages[0].args.relationships
        assert len(relationships) == 2
        assert stages[0].args.relationship is relationships[0]
        assert relationships[0].relationship_type.value == RelationshipType.CALLS.value
        assert relationships[0].filter_pattern == 'connect'
        assert relationships[0].is_negative is False
        assert relationships[1].relationship_type.value == RelationshipType.DECLARES.value
        assert relationships[1].filter_pattern == '*test*'
        assert relationships[1].is_negative is True
        assert relationships[1].inverted is False

    def test_unknown_relationship_type_raises(self):
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser.parse([
                '-mg', '*', '-tc',
                '--via', 'unknown-relation',
                '-mg', '*', '-tc'
            ])

    def test_relationship_without_filter_raises(self):
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser.parse([
                '-mg', '*', '-tc',
                '-V', 'inherits-from'
            ])


class TestViaFlag:
    """Tests for --via / -V relationship type flags."""

    def test_via_inherits_from(self):
        parser = PipelineParser()
        argv_V = ['-mg', '*', '-tc', '-V', 'inherits-from', '-mg', 'Base', '-tc']
        argv_via = ['-mg', '*', '-tc', '--via', 'inherits-from', '-mg', 'Base', '-tc']

        stage_V = parser._parse_stage(argv_V)
        stage_via = parser._parse_stage(argv_via)

        assert stage_V.args.relationship.relationship_type == stage_via.args.relationship.relationship_type
        assert stage_via.args.relationship.relationship_type.value == 'inherits-from'

    def test_V_calls(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'calls', '-mg', 'func', '-tm'])
        assert stage.args.relationship.relationship_type.value == 'calls'

    def test_V_imports(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-V', 'imports', '-mg', 'os'])
        assert stage.args.relationship.relationship_type.value == 'imports'

    def test_V_references(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'references', '-mg', 'X', '-tm'])
        assert stage.args.relationship.relationship_type.value == 'references'

    def test_V_declares(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'declares', '-mg', 'utils.py', '-tF'])
        assert stage.args.relationship.relationship_type.value == 'declares'

    def test_V_all_forward_types(self):
        parser = PipelineParser()
        valid_types = ['inherits-from', 'calls', 'imports', 'references']
        for rt in valid_types:
            stage = parser._parse_stage(['-mg', '*', '-tc', '-V', rt, '-mg', 'Anchor'])
            assert stage.args.relationship.relationship_type.value == rt
            assert stage.args.relationship.inverted is False

        # Test declares which is inverted=True to match DB layout
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'declares', '-mg', 'Anchor'])
        assert stage.args.relationship.relationship_type.value == 'declares'
        assert stage.args.relationship.inverted is True

    def test_V_all_inverse_types(self):
        parser = PipelineParser()
        inverse_types = {
            'called-by': 'calls',
            'inherited-by': 'inherits-from',
            'imported-by': 'imports',
            'referenced-by': 'references',
        }
        for inv_name, forward_value in inverse_types.items():
            stage = parser._parse_stage(['-mg', '*', '-tc', '-V', inv_name, '-mg', 'X'])
            assert stage.args.relationship.relationship_type.value == forward_value
            assert stage.args.relationship.inverted is True

        # Test declared-in which is inverted=False
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'declared-in', '-mg', 'X'])
        assert stage.args.relationship.relationship_type.value == 'declares'
        assert stage.args.relationship.inverted is False

    def test_V_invalid_value_raises(self):
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser._parse_stage(['-mg', '*', '-tc', '--via', 'bad-type', '-mg', '*'])

    def test_V_error_message_lists_valid_types(self):
        parser = PipelineParser()
        with pytest.raises(PipelineParseError, match="Valid:"):
            parser._parse_stage(['-mg', '*', '-V', 'bad-type', '-mg', '*'])

    def test_V_with_newerthan_on_result(self):
        parser = PipelineParser()
        stage = parser._parse_stage([
            '-mg', '*', '-tc', '--newerthan', '1h',
            '-V', 'declares',
            '-mg', 'utils.py', '-tF', '-n', '0',
        ])
        assert stage.args.relationship is not None
        assert stage.args.relationship.relationship_type.value == 'declares'
        assert stage.args.newerthan == '1h'

    def test_V_filter_pattern_and_type(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-V', 'imports', '-mg', 'test_*', '-tm'])
        rel = stage.args.relationship
        assert rel.filter_pattern == 'test_*'
        assert 'method' in rel.filter_types


class TestStaleFlag:
    """--stale flag on the filter side of a relationship query."""

    def test_stale_sets_result_stale_true(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'inherits-from', '-mg', 'Base', '-tc', '--stale'])
        assert stage.args.relationship.result_stale is True

    def test_stale_default_is_false(self):
        parser = PipelineParser()
        stage = parser._parse_stage(['-mg', '*', '-tc', '-V', 'inherits-from', '-mg', 'Base', '-tc'])
        assert stage.args.relationship.result_stale is False

    def test_stale_with_via_flag(self):
        parser = PipelineParser()
        stage = parser._parse_stage([
            '-mg', '*', '-tc', '--via', 'inherits-from', '-mg', 'Base', '-tc', '--stale'
        ])
        assert stage.args.relationship.result_stale is True
        assert stage.args.relationship.relationship_type.value == 'inherits-from'

    def test_stale_with_newerthan_on_result(self):
        parser = PipelineParser()
        stage = parser._parse_stage([
            '-mg', '*', '-tc', '--newerthan', '1h', '-V', 'inherits-from', '-mg', 'Base', '-tc', '--stale'
        ])
        assert stage.args.relationship.result_stale is True
        assert stage.args.newerthan == '1h'
