"""
MyService - A service module with various imports.

Used for testing import relationship queries.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from fileA import BaseClass, func_a, MY_CONSTANT
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
