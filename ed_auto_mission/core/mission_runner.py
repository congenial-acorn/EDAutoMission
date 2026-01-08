"""Mission runner - orchestrates the mission collection loop."""

from __future__ import annotations

import logging
from time import localtime, sleep
from typing import Callable, Optional

from ed_auto_mission.core.types import GameInteraction, MissionRule, RunnerConfig
from ed_auto_mission.core.mission_registry import MissionRegistry

logger = logging.getLogger(__name__)

DISCORD_LEVEL = logging.INFO + 5


class MissionRunner:
    def __init__(
        self,
        game_interaction: GameInteraction,
        registry: MissionRegistry,
        config: RunnerConfig | None = None,
        should_stop: Callable[[], bool] | None = None,
    ):
        self.game = game_interaction
        self.registry = registry
        self.config = config or RunnerConfig()
        self._should_stop = should_stop or (lambda: False)

    def _accept_matching_missions(self, mission_text: str, category: str) -> int:
        accepted = 0
        credit_value = self._extract_credit_value(mission_text)

        rules_for_category = self.registry.get_rules_for_category(category)
        for rule in rules_for_category:
            if self._should_accept_mission(rule, mission_text, credit_value):
                logger.info("%s mission detected. Accepting...", rule.primary_label)

                if not self.config.dry_run:
                    self.game.accept_mission()

                self._notify_acceptance(rule, credit_value)
                accepted += 1

        return accepted

    def _notify_acceptance(self, rule: MissionRule, credit_value: Optional[int]) -> None:
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
        if not rule.matches(mission_text):
            return False

        if rule.wing:
            try:
                wing_result = self.game.check_wing_mission()
                logger.debug("Wing check result: %s", wing_result)
                if not wing_result:
                    return False
            except NotImplementedError:
                logger.debug("Wing check requested but not implemented for this game mode")
                return False

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

    def _scan_category(self, category: str) -> int:
        missions_accepted = 0
        logger.info("Scanning category: %s", category)

        if self.config.dry_run:
            logger.info("[DRY RUN] Would navigate to category: %s", category)
        else:
            self.game.navigate_to_category(category)

        while not self.game.at_bottom():
            if self._should_stop():
                raise InterruptedError("Stop requested")

            mission_text = self.game.ocr_mission()
            missions_accepted += self._accept_matching_missions(mission_text, category)

            if self.config.dry_run:
                logger.info("[DRY RUN] Would move to next mission")
            else:
                self.game.next_mission()

        return missions_accepted

    def run_once(self) -> int:
        missions_accepted = 0
        categories = self.registry.get_unique_categories()

        if not categories:
            logger.warning("No categories found in mission rules")
            return 0

        logger.info("Checking missions across %d categories: %s", len(categories), categories)

        if self.config.dry_run:
            logger.info("[DRY RUN] Would open missions board")
        else:
            self.game.open_missions_board()

        try:
            for i, category in enumerate(categories):
                if self._should_stop():
                    raise InterruptedError("Stop requested")

                missions_accepted += self._scan_category(category)

                is_last_category = i == len(categories) - 1
                if not is_last_category:
                    if self.config.dry_run:
                        logger.info("[DRY RUN] Would return to categories")
                    else:
                        self.game.return_to_categories()

        except InterruptedError:
            logger.info("Scan interrupted. Returning to starport...")
            if not self.config.dry_run:
                self.game.return_to_starport()
            raise

        if self.config.dry_run:
            logger.info("[DRY RUN] Would return to starport")
        else:
            self.game.return_to_starport()

        logger.info("Mission check complete. Accepted %d missions.", missions_accepted)
        return missions_accepted

    def run_until_full(self, existing_missions: int = 0) -> int:
        total_missions = existing_missions + self.run_once()

        if self._should_stop():
            return total_missions

        logger.info(
            "Script will now run every %s minutes, on the %s minute mark (e.g. %s:%02d)",
            self.config.poll_interval_minutes,
            self.config.poll_offset_minutes,
            localtime()[3],
            (round(localtime()[4], -1) + self.config.poll_offset_minutes) % 60,
        )

        mission_count_updated = True
        while total_missions < self.config.max_missions:
            if self._should_stop():
                logger.info("Stop requested")
                break

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
