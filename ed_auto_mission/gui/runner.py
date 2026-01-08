"""Background runner thread for mission automation."""

from __future__ import annotations

import logging
import threading
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ed_auto_mission.core.mission_registry import MissionRegistry
    from ed_auto_mission.core.config import AppConfig
    from ed_auto_mission.core.types import GameInteraction

logger = logging.getLogger(__name__)


class RunnerThread(threading.Thread):
    """Background thread for running the mission automation loop."""

    def __init__(
        self,
        game: GameInteraction,
        registry: MissionRegistry,
        config: AppConfig,
        initial_missions: int = 0,
        on_complete: Callable[[int], None] | None = None,
    ):
        super().__init__(daemon=True)
        self.game = game
        self.registry = registry
        self.config = config
        self.initial_missions = initial_missions
        self.on_complete = on_complete
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Signal the thread to stop."""
        self._stop_event.set()

    def run(self) -> None:
        """Run the mission automation loop."""
        total = 0
        try:
            total = self._run_automation()
        except Exception as e:
            logger.error("Runner error: %s", e, exc_info=True)
        finally:
            if self.on_complete:
                self.on_complete(total)

    def _run_automation(self) -> int:
        """Execute the automation logic."""
        from ed_auto_mission.core.types import RunnerConfig
        from ed_auto_mission.core.mission_runner import MissionRunner
        from ed_auto_mission.services.discord import setup_discord_logging

        setup_discord_logging(self.config.discord_webhook_url)

        runner_config = RunnerConfig(
            max_missions=self.config.max_missions,
            poll_interval_minutes=self.config.poll_interval_minutes,
            poll_offset_minutes=self.config.poll_offset_minutes,
            loop_sleep_seconds=self.config.loop_sleep_seconds,
            dry_run=self.config.dry_run,
        )

        runner = MissionRunner(self.game, self.registry, runner_config)

        return self._run_with_stop_check(runner, self.initial_missions)

    def _run_with_stop_check(self, runner, initial: int) -> int:
        """Run the mission loop with periodic stop checks."""
        from time import localtime
        from ed_auto_mission.services.timing import sleep

        total_missions = initial + runner.run_once()

        if self._stop_event.is_set():
            return total_missions

        logger.info(
            "Will poll every %d minutes on the %d minute mark",
            runner.config.poll_interval_minutes,
            runner.config.poll_offset_minutes,
        )

        while total_missions < runner.config.max_missions:
            # Check for stop signal
            if self._stop_event.is_set():
                logger.info("Runner stopped by user")
                break

            # Check if it's time to poll
            poll_check = (
                localtime()[4] + runner.config.poll_offset_minutes
            ) % runner.config.poll_interval_minutes

            if poll_check == 0:
                if self._stop_event.is_set():
                    break
                total_missions += runner.run_once()
                logger.info("%d missions in depot", total_missions)

            # Sleep in small increments to check stop signal
            for _ in range(runner.config.loop_sleep_seconds):
                if self._stop_event.is_set():
                    break
                sleep(1)

        if total_missions >= runner.config.max_missions:
            logger.info("Mission depot full with %d missions", total_missions)

        return total_missions
