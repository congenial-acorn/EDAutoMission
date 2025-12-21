# mission_runner.py
# By congenial-acorn
# Core mission runner classes and protocol definitions.

import logging
from dataclasses import dataclass
from time import localtime, sleep
from typing import Optional, Protocol

from mission_registry import MissionRegistry, MissionRule


class GameInteraction(Protocol):
    def open_missions_board(self) -> None: ...
    def at_bottom(self) -> bool: ...
    def ocr_mission(self) -> str: ...
    def accept_mission(self) -> None: ...
    def next_mission(self) -> None: ...
    def return_to_starport(self) -> None: ...
    def check_missions_accepted(self) -> int: ...
    # Optional: Only implemented in OdysseyHelper today
    def check_wing_mission(self) -> bool: ...


@dataclass
class RunnerConfig:
    max_missions: int = 20
    poll_interval_minutes: int = 10
    poll_offset_minutes: int = 5
    loop_sleep_seconds: int = 20


class MissionRunner:
    """Runs the core mission-collection loop for a given game interaction layer."""

    def __init__(
        self,
        game_interaction: GameInteraction,
        registry: MissionRegistry,
        config: RunnerConfig | None = None
    ):
        self.game_interaction = game_interaction
        self.registry = registry
        self.config = config or RunnerConfig()
    
    def _accept_matching_missions(self, mission_text: str) -> int:
        accepted = 0
        for mission in self.registry.all():
            if self._should_accept_mission(mission, mission_text):
                logging.info("%s mission detected. Accepting...", mission.primary_label)
                self.game_interaction.accept_mission()
                accepted += 1
        return accepted

    def _should_accept_mission(self, mission_rule: MissionRule, mission_text: str) -> bool:
        """Apply mission_rule filters (needles AND, optional wing check, value threshold)."""
        # 1) All needle groups must match
        if not mission_rule.matches(mission_text):
            return False

        # 2) Wing mission check (optional)
        if mission_rule.wing:
            wing_checker = getattr(self.game_interaction, "check_wing_mission", None)
            if not callable(wing_checker):
                logging.debug("Wing check requested but game interaction lacks check_wing_mission")
                return False
            wing_result = wing_checker()
            logging.debug("Wing check result: %s", wing_result)
            if not wing_result:
                return False

        # 3) Credit value check based on text ending with 'CR'
        credit_value = self._extract_credit_value(mission_text)
        logging.debug("Extracted credit value: %s", credit_value)
        if credit_value is None:
            return False
        if credit_value <= mission_rule.value:
            logging.debug("Credit value %s did not exceed rule threshold %s", credit_value, mission_rule.value)
            return False

        return True

    @staticmethod
    def _extract_credit_value(mission_text: str) -> Optional[int]:
        """
        Find the numeric value immediately preceding 'CR', scanning backwards through digits/commas.
        """
        upper_text = mission_text.upper()
        idx = upper_text.find("CR")
        if idx == -1:
            return None

        i = idx - 1
        digits: list[str] = []
        while i >= 0 and (mission_text[i].isdigit() or mission_text[i] == ","):
            digits.append(mission_text[i])
            i -= 1

        if not digits:
            return None

        num_str = "".join(reversed(digits)).replace(",", "")
        if not num_str:
            return None

        try:
            return int(num_str)
        except ValueError:
            return None
        
    def run_once(self) -> int:
        """Perform a single scan of the mission board."""
        missions = 0
        logging.info("Checking missions...")

        self.game_interaction.open_missions_board()
        while not self.game_interaction.at_bottom():
            mission_text = self.game_interaction.ocr_mission()
            missions += self._accept_matching_missions(mission_text)
            self.game_interaction.next_mission()

        self.game_interaction.return_to_starport()
        logging.info("Mission check complete.")
        return missions
    
    def run_until_full(self, existing_missions: int = 0) -> int:
        """
        Continuously check for missions until the depot is full.

        :param existing_missions: Missions already present when the loop begins.
        :return: Total missions detected once the depot is full.
        """
        missions = existing_missions + self.run_once()
        logging.info(
            "Script will now be run every %s minutes, on the %s minute mark (e.g. %s:%s)",
            self.config.poll_interval_minutes,
            self.config.poll_offset_minutes,
            int(localtime()[3]),
            int(round(localtime()[4], -1)) + self.config.poll_offset_minutes,
        )

        mission_count_update = True
        while missions < self.config.max_missions:
            logging.debug("Current minute reading is: %s", localtime()[4])

            if ((localtime()[4] + self.config.poll_offset_minutes) % self.config.poll_interval_minutes) == 0:
                missions += self.run_once()
                mission_count_update = True

            if mission_count_update:
                mission_count_update = False
                logging.info("%s missions in depot.", missions)
                logging.info(
                    "Next update at %s:%s",
                    int(localtime()[3]),
                    int(round(localtime()[4], -1)) + self.config.poll_offset_minutes,
                )

            sleep(self.config.loop_sleep_seconds)

        return missions
