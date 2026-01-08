"""Main entry point for ED Auto Mission."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from ed_auto_mission.core.config import AppConfig
from ed_auto_mission.core.types import RunnerConfig, MissionRule
from ed_auto_mission.core.mission_registry import MissionRegistry, default_registry
from ed_auto_mission.core.mission_runner import MissionRunner
from ed_auto_mission.services.screen import ScreenService
from ed_auto_mission.services.ocr import OCRService, setup_tesseract
from ed_auto_mission.services.discord import setup_discord_logging
from ed_auto_mission.services.input import InputService
from ed_auto_mission.services.process import ensure_game_running
from ed_auto_mission.services.window import focus_elite_dangerous
from ed_auto_mission.services.timing import sleep
from ed_auto_mission.adapters import EliteDangerousGame

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False) -> None:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def create_game(
    config: AppConfig,
    screen: ScreenService,
    ocr: OCRService,
    input_service: InputService,
) -> EliteDangerousGame:
    """
    Create the game interaction adapter.

    Args:
        config: Application configuration
        screen: Screen service
        ocr: OCR service
        input_service: Input service

    Returns:
        Game interaction adapter
    """
    logger.info("Initializing Elite Dangerous game adapter")
    return EliteDangerousGame(
        screen=screen,
        ocr=ocr,
        input_service=input_service,
        debug_output=config.debug_ocr,
    )


def get_initial_mission_count(
    config: AppConfig,
    game: EliteDangerousGame,
) -> int:
    """
    Get the initial mission count, either from OCR or user input.

    Args:
        config: Application configuration
        game: Game interaction adapter

    Returns:
        Number of currently accepted missions
    """
    try:
        user_input = input(
            "Enter number of currently accepted missions (or press Enter for auto-detect): "
        ).strip()
        if user_input:
            return int(user_input)
    except (EOFError, ValueError):
        pass


def start(
    config: AppConfig | None = None,
    registry: MissionRegistry | None = None,
) -> int:
    """
    Main entry point for running the mission loop.

    Args:
        config: Application configuration (default: from environment)
        registry: Mission registry (default: shared default registry)

    Returns:
        Total number of missions when the loop finishes
    """
    config = config or AppConfig.from_env()
    registry = registry or default_registry

    # Setup
    setup_logging(debug=config.debug_ocr)
    config.prompt_missing_values()
    setup_tesseract(config.tesseract_path)
    setup_discord_logging(config.discord_webhook_url)

    # Verify game is running
    ensure_game_running()

    # Focus game window (Windows only)
    sleep(1)
    if focus_elite_dangerous():
        sleep(4)

    # Create services
    screen = ScreenService()
    ocr = OCRService(screen, debug_output=config.debug_ocr)
    input_service = InputService(dry_run=config.dry_run)

    # Create game adapter
    game = create_game(config, screen, ocr, input_service)

    # Create runner
    runner_config = RunnerConfig(
        max_missions=config.max_missions,
        poll_interval_minutes=config.poll_interval_minutes,
        poll_offset_minutes=config.poll_offset_minutes,
        loop_sleep_seconds=config.loop_sleep_seconds,
        dry_run=config.dry_run,
    )
    runner = MissionRunner(game, registry, runner_config)
    #TODO: add categories to runner and OCR each one
    # Get initial mission count
    initial_missions = get_initial_mission_count(config, game)
    logger.info("Starting with %d missions already accepted", initial_missions)

    sleep(3)  # Brief pause before starting

    # Run the loop
    total_missions = runner.run_until_full(initial_missions)
    return total_missions


# Compatibility functions for external callers
def add_mission(
    needles: list[list[str]],
    label: str,
    wing: bool = False,
    value: int = 0,
) -> MissionRule:
    """Add a mission detection rule to the default registry."""
    return default_registry.add(needles, label, wing=wing, value=value)


def remove_mission(mission: MissionRule | str) -> bool:
    """Remove a mission detection rule from the default registry."""
    return default_registry.remove(mission)


def get_missions() -> list[MissionRule]:
    """Get all mission detection rules from the default registry."""
    return default_registry.all()


def main() -> int:
    """CLI entry point."""
    try:
        return start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
