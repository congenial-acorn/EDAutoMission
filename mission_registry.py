# mission_registry.py
# By congenial-acorn
# Shared mission management utilities.

from dataclasses import dataclass
from threading import RLock
from typing import Iterable, List


@dataclass(frozen=True)
class MissionRule:
    """
    Describes how to detect and label a mission.

    - needles: list of needle groups (list of lists of strings)
    - label: display/logging label
    - wing: whether this is a wing mission
    - value: integer score/value for prioritization
    """

    needles: list[list[str]]
    label: str
    wing: bool = False
    value: int = 0

    def matches(self, text: str) -> bool:
        """
        Return True when each group has at least one needle contained in the OCR text.
        (AND across groups, OR within each group)
        """
        upper_text = text.upper()
        for group in self.needles:
            if not any(needle.upper() in upper_text for needle in group):
                return False
        return True

    @property
    def primary_label(self) -> str:
        return self.label


class MissionRegistry:
    """
    Thread-safe registry for missions we care about.

    Designed so external controllers (CLI, future tooling) can mutate mission preferences safely.
    """

    def __init__(self, missions: Iterable[MissionRule] | None = None):
        self._missions: List[MissionRule] = []
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
    ) -> MissionRule:
        rule = MissionRule(
            needles=needles,
            label=label.strip(),
            wing=wing,
            value=int(value),
        )
        with self._lock:
            self._missions.append(rule)
        return rule

    def add_many(self, missions: Iterable[MissionRule]) -> list[MissionRule]:
        """Add many missions provided as MissionRule instances."""
        added: list[MissionRule] = []
        for mission in missions:
            with self._lock:
                self._missions.append(mission)
            added.append(mission)
        return added

    def remove(self, mission: MissionRule | str) -> bool:
        """Remove by MissionRule instance, label, or needle. Returns True when removed."""
        with self._lock:
            for idx, existing in enumerate(self._missions):
                if existing == mission:
                    self._missions.pop(idx)
                    return True

                if isinstance(mission, str):
                    if mission == existing.label or mission.upper() in existing.needles:
                        self._missions.pop(idx)
                        return True

                if mission in existing.needles:  # type: ignore[operator]
                    self._missions.pop(idx)
                    return True
        return False

    def all(self) -> list[MissionRule]:
        with self._lock:
            return list(self._missions)


DEFAULT_MISSIONS: list[MissionRule] = [
    MissionRule([["MINE", "MINING", "BLAST"],["BERT"]], "Bertrandite", wing=True, value=49000000),
    MissionRule([["MINE", "MINING", "BLAST"],["GOLD"]], "Gold", wing=True, value=40000000),
    MissionRule([["MINE", "MINING", "BLAST"],["SILVER"]], "Silver", wing=True, value=49000000),
    MissionRule([["MINE", "MINING", "BLAST"],["INDITE"]], "Indite", wing=True, value=39000000),
]

# Shared instance used by main.py (and any external controllers).
mission_registry = MissionRegistry(DEFAULT_MISSIONS)
