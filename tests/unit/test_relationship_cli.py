"""Unit tests for CLI relationship flag parsing (Sprint 5).

TLDR:
    Tests that PipelineParser correctly parses relationship query syntax introduced
    in Sprint 5. Key test classes: TestRelationshipFlagParsing (long-form --via
    flags), TestRelationshipShortFlags (-Vinh/-Vca/-Vimp/-Vr short forms),
    TestInvertFlag (--invert/-iv direction reversal), TestRelationshipWithOptions
    (combined limit/case/output options), TestRelationshipEdgeCases (unknown types,
    missing objects), TestRelationshipFlagDefinitions (flag registration check).
    Role: protects the CLI parsing layer in PipelineParser; consumed by the test suite.
    Dependencies: PipelineParser, PipelineParseError, RelationshipType, StageType.

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
            '-mg', 'Child*', '-tc',
            '--via', 'inherits-from',
            '-mg', '*Base*', '-tc'
        ])

        # Should have subject stage with relationship
        assert len(stages) >= 1
        subject = stages[0]
        assert subject.stage_type == StageType.MATCH
        assert subject.args.pattern == 'Child*'

        # Relationship should be attached
        assert hasattr(subject.args, 'relationship')
        rel = subject.args.relationship
        assert rel is not None
        assert rel.relationship_type == RelationshipType.INHERITS_FROM
        assert rel.object_pattern == '*Base*'
        assert 'class' in rel.object_types
        assert rel.invert is False

    def test_parse_via_calls_long_form(self):
        """Test --via calls relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', 'main*', '-tf',
            '--via', 'calls',
            '-mg', '*util*', '-tf'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.CALLS
        assert rel.object_pattern == '*util*'

    def test_parse_via_imports_long_form(self):
        """Test --via imports relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '--via', 'imports',
            '-mg', 'os', '-ti'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.IMPORTS
        assert rel.object_pattern == 'os'

    def test_parse_via_references_long_form(self):
        """Test --via references relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '--via', 'references',
            '-mg', 'CONFIG*', '-tg'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.REFERENCES


class TestRelationshipShortFlags:
    """Test short form relationship flags."""

    def test_parse_Vinh_short_flag(self):
        """Test -Vinh for inherits-from."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', 'Child*', '-tc',
            '-Vinh',
            '-mg', '*Base*', '-tc'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.INHERITS_FROM

    def test_parse_Vca_short_flag(self):
        """Test -Vca for calls."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-Vca',
            '-mg', 'helper*', '-tf'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.CALLS

    def test_parse_Vimp_short_flag(self):
        """Test -Vimp for imports."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '-Vimp',
            '-mg', 'json', '-ti'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.IMPORTS

    def test_parse_Vr_short_flag(self):
        """Test -Vr for references."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tm',
            '-Vr',
            '-mg', 'self.*', '-tg'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.REFERENCES


class TestInvertFlag:
    """Test --invert / -iv flag for relationship direction."""

    def test_invert_long_form(self):
        """Test --invert flag reverses relationship direction."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--via', 'inherits-from',
            '-mg', 'MyClass', '-tc',
            '--invert'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.invert is True

    def test_invert_short_form(self):
        """Test -iv short form for invert."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-Vinh',
            '-mg', 'Parser*', '-tc',
            '-iv'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.invert is True

    def test_no_invert_by_default(self):
        """Test invert is False by default."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-Vinh',
            '-mg', 'Base', '-tc'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.invert is False


class TestRelationshipWithOptions:
    """Test relationship queries with additional options."""

    def test_relationship_with_limit(self):
        """Test limit option with relationship query."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-n', '5',
            '-Vinh',
            '-mg', 'Base*', '-tc'
        ])

        subject = stages[0]
        assert subject.args.limit == 5
        assert subject.args.relationship is not None

    def test_relationship_with_case_insensitive(self):
        """Test case insensitive flag with relationship."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-I',
            '-Vinh',
            '-mg', 'base*', '-tc'
        ])

        subject = stages[0]
        assert subject.args.case_insensitive is True

    def test_relationship_with_output_format(self):
        """Test output format with relationship query."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-Vinh',
            '-mg', 'Base*', '-tc',
            '-oT', '-fm'
        ])

        subject = stages[0]
        # Output format should be on the query
        assert subject.args.render_type == 'table'
        assert subject.args.format == 'md'


class TestRelationshipEdgeCases:
    """Test edge cases for relationship parsing."""

    def test_subject_multiple_types(self):
        """Test subject with multiple symbol types (OR)."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-tf',  # class OR function
            '-Vca',
            '-mg', 'helper*', '-tf'
        ])

        subject = stages[0]
        assert 'class' in subject.args.symbol_types
        assert 'function' in subject.args.symbol_types

    def test_object_multiple_types(self):
        """Test object with multiple symbol types."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-Vca',
            '-mg', '*util*', '-tf', '-tm'  # function OR method
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert 'function' in rel.object_types
        assert 'method' in rel.object_types

    def test_unknown_relationship_type_raises(self):
        """Test unknown relationship type raises error."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser.parse([
                '-mg', '*', '-tc',
                '--via', 'unknown-relation',
                '-mg', '*', '-tc'
            ])

    def test_relationship_without_object_raises(self):
        """Test relationship without object query raises error."""
        parser = PipelineParser()
        with pytest.raises(PipelineParseError):
            parser.parse([
                '-mg', '*', '-tc',
                '-Vinh'
                # Missing object query
            ])


class TestRelationshipFlagDefinitions:
    """Test relationship flag definitions in flag_groups."""

    def test_relationship_flags_exist(self):
        """Test RELATIONSHIP_FLAGS are defined."""
        from via.core.flag_groups import RELATIONSHIP_FLAGS

        # Should have 4 relationship flags
        assert len(RELATIONSHIP_FLAGS) == 4

        # Check flag names
        flag_suffixes = [f.suffix for f in RELATIONSHIP_FLAGS]
        assert 'inh' in flag_suffixes
        assert 'ca' in flag_suffixes
        assert 'imp' in flag_suffixes
        assert 'r' in flag_suffixes

    def test_relationship_short_flags(self):
        """Test short flag format -V<suffix>."""
        from via.core.flag_groups import RELATIONSHIP_FLAGS

        short_flags = [f.short for f in RELATIONSHIP_FLAGS]
        assert '-Vinh' in short_flags
        assert '-Vca' in short_flags
        assert '-Vimp' in short_flags
        assert '-Vr' in short_flags

    def test_get_relationship_short_flags(self):
        """Test get_relationship_short_flags helper."""
        from via.core.flag_groups import get_relationship_short_flags

        flags = get_relationship_short_flags()
        assert '-Vinh' in flags
        assert '-Vca' in flags
        assert '-Vimp' in flags
        assert '-Vr' in flags
