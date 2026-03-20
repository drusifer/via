"""Pipeline module for internal command chaining.

TLDR:
    Public surface of the pipeline subsystem. Re-exports the four symbols
    most commonly imported by callers: PipelineStage and StageType (the data
    structures that represent a parsed command), PipelineParser (the parser
    that turns raw argv into a list of PipelineStages), and PipelineParseError
    (the exception raised on invalid input). Actual execution logic lives in
    pipeline/executor.py and is not re-exported here.

"""
from via.pipeline.parser import PipelineParseError, PipelineParser
from via.pipeline.types import PipelineStage, StageType

__all__ = ['StageType', 'PipelineStage', 'PipelineParser', 'PipelineParseError']
