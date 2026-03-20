"""
UAT test fixture providing a service module with rich imports and inheritance for query tests.

TLDR:
    Test fixture file (my_service) used by tests/uat/test_sprint5_uat.py and related UAT suites.
    Exercises import relationship queries (stdlib + fileA/fileB cross-file imports) and
    provides a realistic inheritance + call chain for inverted call queries (UAT-3.2).
    Key classes: ServiceConfig (dataclass), MyService(BaseClass) — inherits from fileA.
    Key functions: main_entrypoint() — calls func_a, func_b, process(), save();
    primary target for "what does X call" inverted call tests.
    Depends on: fileA (MY_CONSTANT, BaseClass, func_a), fileB (ChildClass, func_b),
    plus stdlib: json, logging, os, sys, collections, dataclasses, pathlib, typing.
"""
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fileA import MY_CONSTANT, BaseClass, func_a
from fileB import ChildClass, func_b

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for the service."""
    name: str
    timeout: int = 30
    options: Dict[str, Any] = field(default_factory=dict)


class MyService(BaseClass):
    """A service class that inherits from BaseClass."""

    def __init__(self, config: ServiceConfig):
        self.config = config

    def process(self):
        """Process using imported functions."""
        result_a = func_a()
        result_b = func_b()
        return f"{result_a} + {result_b}"

    def save(self):
        """Save service state."""
        logger.info("Saving service state")
        return True

    def load(self):
        """Load service state."""
        data = json.loads("{}")
        return data


def main_entrypoint():
    """Main entry point for the service.

    Calls multiple functions for testing inverted call queries.
    """
    config = ServiceConfig(name="test")
    service = MyService(config)
    service.process()
    service.save()
    func_a()
    func_b()
    return service
