"""Mission runner - orchestrates the mission collection loop."""

from __future__ import annotations

import logging
from time import localtime, sleep
from typing import Optional

from ed_auto_mission.core.types import GameInteraction, MissionRule, RunnerConfig
from ed_auto_mission.core.mission_registry import MissionRegistry

logger = logging.getLogger(__name__)

# Custom Discord logging level
DISCORD_LEVEL = logging.INFO + 5


class MissionRunner:
    """Runs the core mission-collection loop for a given game interaction layer."""

    def __init__(
        self,
        game_interaction: GameInteraction,
        registry: MissionRegistry,
        config: RunnerConfig | None = None,
    ):
        self.game = game_interaction
        self.registry = registry
        self.config = config or RunnerConfig()

    def _accept_matching_missions(self, mission_text: str) -> int:
        """Check mission text against all rules and accept matching missions."""
        accepted = 0
        credit_value = self._extract_credit_value(mission_text)

        for rule in self.registry.all():
            if self._should_accept_mission(rule, mission_text, credit_value):
                logger.info("%s mission detected. Accepting...", rule.primary_label)

                if not self.config.dry_run:
                    self.game.accept_mission()

                self._notify_acceptance(rule, credit_value)
                accepted += 1

        return accepted

    def _notify_acceptance(self, rule: MissionRule, credit_value: Optional[int]) -> None:
        """Log mission acceptance to Discord if configured."""
        message = f"Accepted mission: {rule.primary_label}"
        if credit_value is not None:
            message += f" worth {credit_value:,} CR"
        logger.log(DISCORD_LEVEL, message)

    def _should_accept_mission(
        self,
        rule: MissionRule,
        mission_text: str,
        credit_value: Optional[int],
    ) -> bool:
        """Apply rule filters (needles AND, optional wing check, value threshold)."""
        # 1) All needle groups must match
        if not rule.matches(mission_text):
            return False

        # 2) Wing mission check (optional)
        if rule.wing:
            try:
                wing_result = self.game.check_wing_mission()
                logger.debug("Wing check result: %s", wing_result)
                if not wing_result:
                    return False
            except NotImplementedError:
                logger.debug("Wing check requested but not implemented for this game mode")
                return False

        # 3) Credit value check
        logger.debug("Extracted credit value: %s", credit_value)
        if credit_value is None:
            return False
        if credit_value <= rule.value:
            logger.debug(
                "Credit value %s did not exceed rule threshold %s",
                credit_value,
                rule.value,
            )
            return False

        return True

    @staticmethod
    def _extract_credit_value(mission_text: str) -> Optional[int]:
        """
        Find the numeric value immediately preceding 'CR', scanning backwards.
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
        missions_accepted = 0
        logger.info("Checking missions...")

        if self.config.dry_run:
            logger.info("[DRY RUN] Would open missions board")
        else:
            self.game.open_missions_board()

        while not self.game.at_bottom():
            mission_text = self.game.ocr_mission()
            missions_accepted += self._accept_matching_missions(mission_text)

            if self.config.dry_run:
                logger.info("[DRY RUN] Would move to next mission")
            else:
                self.game.next_mission()

        if self.config.dry_run:
            logger.info("[DRY RUN] Would return to starport")
        else:
            self.game.return_to_starport()

        logger.info("Mission check complete. Accepted %d missions.", missions_accepted)
        return missions_accepted

    def run_until_full(self, existing_missions: int = 0) -> int:
        """
        Continuously check for missions until the depot is full.

        Args:
            existing_missions: Missions already present when the loop begins.

        Returns:
            Total missions detected once the depot is full.
        """
        total_missions = existing_missions + self.run_once()

        logger.info(
            "Script will now run every %s minutes, on the %s minute mark (e.g. %s:%02d)",
            self.config.poll_interval_minutes,
            self.config.poll_offset_minutes,
            localtime()[3],
            (round(localtime()[4], -1) + self.config.poll_offset_minutes) % 60,
        )

        mission_count_updated = True
        while total_missions < self.config.max_missions:
            logger.debug("Current minute: %s", localtime()[4])

            poll_check = (
                localtime()[4] + self.config.poll_offset_minutes
            ) % self.config.poll_interval_minutes

            if poll_check == 0:
                total_missions += self.run_once()
                mission_count_updated = True

            if mission_count_updated:
                mission_count_updated = False
                logger.info("%s missions in depot.", total_missions)
                logger.info(
                    "Next update at %s:%02d",
                    localtime()[3],
                    (round(localtime()[4], -1) + self.config.poll_offset_minutes) % 60,
                )

            sleep(self.config.loop_sleep_seconds)

        logger.info("Mission depot full with %d missions.", total_missions)
        return total_missions
