"""Core domain logic - pure Python, no I/O dependencies."""

from ed_auto_mission.core.types import (
    GameInteraction,
    MissionRule,
    RunnerConfig,
    ScreenRegion,
    ScreenContext,
)
from ed_auto_mission.core.mission_registry import MissionRegistry, default_registry
from ed_auto_mission.core.mission_runner import MissionRunner

__all__ = [
    "GameInteraction",
    "MissionRule",
    "MissionRegistry",
    "MissionRunner",
    "RunnerConfig",
    "ScreenRegion",
    "ScreenContext",
    "default_registry",
]
