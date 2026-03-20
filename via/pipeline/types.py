"""
Core type definitions shared across the pipeline subsystem.

TLDR:
    Defines the fundamental data structures used to represent a parsed via
    command as a sequence of executable stages. StageType is an enum
    enumerating the three recognized stage kinds (MATCH, RENDER, STATS), and
    PipelineStage is a lightweight dataclass that pairs a StageType with the
    argparse Namespace produced by PipelineParser for that stage.

Author: Drew Gutstein
------------------------------------------------------------------------------

License: GPL-3.0
"""
from argparse import Namespace
from dataclasses import dataclass
from enum import Enum


class StageType(Enum):
    """Types of pipeline stages."""
    MATCH = 'match'
    RENDER = 'render'
    STATS = 'stats'


@dataclass
class PipelineStage:
    """Single stage in the pipeline.

    Attributes:
        stage_type: Type of stage (MATCH, RENDER, STATS)
        args: Parsed arguments from argparse as Namespace object
    """
    stage_type: StageType
    args: Namespace
