"""Unit tests for CLI relationship flag parsing (Sprint 5, updated Sprint 13).

TLDR:
    Tests that PipelineParser correctly parses relationship query syntax.
    Key test classes: TestRelationshipFlagParsing (long-form --via TYPE flags),
    TestRelationshipVShortFlag (-V TYPE short form), TestSansFlag (--sans/-S
    negative relationship flags), TestRelationshipWithOptions (combined
    limit/case/output options), TestRelationshipEdgeCases (unknown types,
    missing objects).
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
        assert rel.is_negative is False

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


class TestRelationshipVShortFlag:
    """Test -V TYPE short form relationship flags."""

    def test_parse_V_inherits_from(self):
        """Test -V inherits-from."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', 'Child*', '-tc',
            '-V', 'inherits-from',
            '-mg', '*Base*', '-tc'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.INHERITS_FROM

    def test_parse_V_calls(self):
        """Test -V calls."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tf',
            '-V', 'calls',
            '-mg', 'helper*', '-tf'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.CALLS

    def test_parse_V_imports(self):
        """Test -V imports."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tF',
            '-V', 'imports',
            '-mg', 'json', '-ti'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.IMPORTS

    def test_parse_V_references(self):
        """Test -V references."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tm',
            '-V', 'references',
            '-mg', 'self.*', '-tg'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.relationship_type == RelationshipType.REFERENCES


class TestSansFlag:
    """Test --sans / -S flag for negative relationship filtering."""

    def test_sans_long_form_sets_is_negative(self):
        """Test --sans flag sets is_negative=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '--sans', 'inherits-from',
            '-mg', 'MyClass', '-tc',
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.is_negative is True

    def test_S_short_form_sets_is_negative(self):
        """Test -S short form sets is_negative=True."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-S', 'calls',
            '-mg', 'helper*', '-tc',
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.is_negative is True

    def test_no_sans_is_negative_false_by_default(self):
        """Test is_negative is False by default (--via / -V)."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-V', 'inherits-from',
            '-mg', 'Base', '-tc'
        ])

        subject = stages[0]
        rel = subject.args.relationship
        assert rel.is_negative is False


class TestRelationshipWithOptions:
    """Test relationship queries with additional options."""

    def test_relationship_with_limit(self):
        """Test limit option with relationship query."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc', '-n', '5',
            '-V', 'inherits-from',
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
            '-V', 'inherits-from',
            '-mg', 'base*', '-tc'
        ])

        subject = stages[0]
        assert subject.args.case_insensitive is True

    def test_relationship_with_output_format(self):
        """Test output format with relationship query."""
        parser = PipelineParser()
        stages = parser.parse([
            '-mg', '*', '-tc',
            '-V', 'inherits-from',
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
            '-V', 'calls',
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
            '-V', 'calls',
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
                '-V', 'inherits-from'
                # Missing object query
            ])


