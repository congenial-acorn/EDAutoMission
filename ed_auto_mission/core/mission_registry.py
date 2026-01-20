"""Mission registry for managing detection rules."""

from __future__ import annotations

from threading import RLock
from typing import Iterable

from ed_auto_mission.core.types import MissionRule


class MissionRegistry:
    """
    Thread-safe registry for mission detection rules.

    Designed so external controllers (CLI, future tooling) can mutate mission
    preferences safely.
    """

    def __init__(self, missions: Iterable[MissionRule] | None = None):
        self._missions: list[MissionRule] = []
        self._lock = RLock()
        if missions:
            for mission in missions:
                self._missions.append(mission)

    def add(
        self,
        needles: list[list[str]],
        label: str,
        wing: bool = False,
        value: int = 0,
        categories: list[str] | None = None,
    ) -> MissionRule:
        rule = MissionRule(
            needles=needles,
            label=label.strip(),
            wing=wing,
            value=int(value),
            categories=tuple(categories) if categories else (),
        )
        with self._lock:
            self._missions.append(rule)
        return rule

    def add_rule(self, rule: MissionRule) -> MissionRule:
        with self._lock:
            self._missions.append(rule)
        return rule

    def add_many(self, missions: Iterable[MissionRule]) -> list[MissionRule]:
        added: list[MissionRule] = []
        with self._lock:
            for mission in missions:
                self._missions.append(mission)
                added.append(mission)
        return added

    def remove(self, mission: MissionRule | str) -> bool:
        with self._lock:
            for idx, existing in enumerate(self._missions):
                if existing == mission:
                    self._missions.pop(idx)
                    return True

                if isinstance(mission, str):
                    if mission == existing.label:
                        self._missions.pop(idx)
                        return True

        return False

    def all(self) -> list[MissionRule]:
        with self._lock:
            return list(self._missions)

    def get_unique_categories(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        with self._lock:
            for mission in self._missions:
                for category in mission.categories:
                    if category not in seen:
                        seen.add(category)
                        result.append(category)
        return result

    def get_rules_for_category(self, category: str) -> list[MissionRule]:
        with self._lock:
            return [m for m in self._missions if category in m.categories]

    def clear(self) -> None:
        with self._lock:
            self._missions.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._missions)

    def __iter__(self):
        return iter(self.all())


# Default mission configurations for common mining commodities
DEFAULT_MISSIONS: list[MissionRule] = [
    MissionRule(
        needles=[["MINE", "MINING", "BLAST"], ["BERT"]],
        label="Bertrandite",
        wing=True,
        value=49_000_000,
        categories=("transport",),
    ),
    MissionRule(
        needles=[["MINE", "MINING", "BLAST"], ["GOLD"]],
        label="Gold",
        wing=True,
        value=40_000_000,
        categories=("transport",),
    ),
    MissionRule(
        needles=[["MINE", "MINING", "BLAST"], ["SILVER"]],
        label="Silver",
        wing=True,
        value=49_000_000,
        categories=("transport",),
    ),
    MissionRule(
        needles=[["MINE", "MINING", "BLAST"], ["INDITE"]],
        label="Indite",
        wing=True,
        value=39_000_000,
        categories=("transport",),
    ),
]

# Shared instance for backward compatibility
default_registry = MissionRegistry(DEFAULT_MISSIONS)
