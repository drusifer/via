"""Registry and executors for pipeline execution stages.

TLDR:
    Implements stage handlers that orchestrate execution of individual pipeline steps.
    Key classes: StageHandlerABC (handler interface), MatchStageHandler (performs database
    matching), RenderStageHandler (formats results), StatsStageHandler (displays stats),
    and StageHandlerRegistry (maps StageTypes to handlers).
    Role: Stage executor registry. Consumed by PipelineExecutor.

Author: Oracle
------------------------------------------------------------------------------
License: GPL-3.0
"""
from abc import ABC, abstractmethod
from typing import Iterator, Optional

from .types import PipelineStage, StageType
from ..core.match_record import MatchRecord


class StageHandlerABC(ABC):
    """Abstract base class for all pipeline stage handlers."""

    @abstractmethod
    def handle(
        self,
        stage: PipelineStage,
        executor,
        result_iter: Optional[Iterator[MatchRecord]]
    ) -> Optional[Iterator[MatchRecord]]:
        """Process a single pipeline stage.

        Args:
            stage: The PipelineStage to execute.
            executor: The PipelineExecutor instance.
            result_iter: Output iterator from previous stages (if any).

        Returns:
            The output iterator for the next stage, or None if terminal stage.
        """
        pass


class MatchStageHandler(StageHandlerABC):
    """Handles symbol matching and filtering stages."""

    def handle(
        self,
        stage: PipelineStage,
        executor,
        result_iter: Optional[Iterator[MatchRecord]]
    ) -> Optional[Iterator[MatchRecord]]:
        if result_iter is None:
            return executor._execute_match_stage(stage)
        else:
            return executor._execute_filter_stage(stage, result_iter)


class RenderStageHandler(StageHandlerABC):
    """Handles rendering/formatting of results (terminal stage)."""

    def handle(
        self,
        stage: PipelineStage,
        executor,
        result_iter: Optional[Iterator[MatchRecord]]
    ) -> Optional[Iterator[MatchRecord]]:
        executor._execute_render_stage(stage, result_iter)
        return None


class StatsStageHandler(StageHandlerABC):
    """Handles printing database statistics (terminal stage)."""

    def handle(
        self,
        stage: PipelineStage,
        executor,
        result_iter: Optional[Iterator[MatchRecord]]
    ) -> Optional[Iterator[MatchRecord]]:
        executor._execute_stats_stage(stage)
        return None


class StageHandlerRegistry:
    """Registry mapping StageTypes to handlers."""

    def __init__(self):
        self._handlers = {}

    def register(self, stage_type: StageType, handler: StageHandlerABC):
        self._handlers[stage_type] = handler

    def get(self, stage_type: StageType) -> Optional[StageHandlerABC]:
        return self._handlers.get(stage_type)


# Create and populate the global registry
STAGE_REGISTRY = StageHandlerRegistry()
STAGE_REGISTRY.register(StageType.MATCH, MatchStageHandler())
STAGE_REGISTRY.register(StageType.RENDER, RenderStageHandler())
STAGE_REGISTRY.register(StageType.STATS, StatsStageHandler())
