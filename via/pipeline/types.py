"""Pipeline types and data structures."""
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
