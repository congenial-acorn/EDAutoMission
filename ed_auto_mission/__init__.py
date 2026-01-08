"""
ED Auto Mission - Elite Dangerous mission automation tool.

Automatically accepts missions matching configured criteria from the mission board.
"""

__version__ = "2.0.0"
__author__ = "congenial-acorn"

from ed_auto_mission.core.types import MissionRule, RunnerConfig
from ed_auto_mission.core.mission_registry import MissionRegistry, default_registry
from ed_auto_mission.core.mission_runner import MissionRunner

__all__ = [
    "MissionRule",
    "MissionRegistry",
    "MissionRunner",
    "RunnerConfig",
    "default_registry",
]
