# main.py
import logging
from platform import system
from time import sleep
from typing import Optional, Sequence

import helper_functions
from mission_registry import MissionRegistry, mission_registry
from mission_runner import GameInteraction, MissionRunner

if system() == "Windows":
    from pywintypes import error as PyWinError
    from tab_to import tab_to
else:
    PyWinError = Exception  # type: ignore[misc,assignment]


def focus_game_window() -> None:
    if system() != "Windows":
        return

    try:
        tab_to("Elite.+Dangerous.+CLIENT")
        sleep(1)
    except PyWinError as e:
        logging.debug("PyWinError while attempting to focus window: %s", e)


def ensure_game_running() -> None:
    if not helper_functions.game_running():
        raise RuntimeError("Elite: Dangerous not running.")


def resolve_game_interaction(game_mode: Optional[str] = None) -> GameInteraction:
    """Return the helper implementation for the detected or specified game mode."""
    #mode = (game_mode or helper_functions.game_mode()).lower()
    mode = "odyssey"  # Temporarily force Odyssey mode for testing
    if mode == "horizons":
        import horizons_helper as horizons
        logging.info("Operating in Horizons mode")
        return horizons  # type: ignore[return-value]
    if mode == "odyssey":
        from odyssey_helper import OdysseyHelper

        logging.info("Operating in Odyssey mode")
        return OdysseyHelper()
    raise ValueError(f"Unknown game mode '{mode}'")


def start(
    game_mode: Optional[str] = None,
    registry: MissionRegistry = mission_registry,
) -> int:
    """
    Entry point for running the mission loop from the CLI.

    :return: Total number of missions detected when the loop finishes.
    """
    helper_functions.module_setup()
    ensure_game_running()
    focus_game_window()

    game_interaction = resolve_game_interaction(game_mode)
    runner = MissionRunner(game_interaction, registry)

    missions = game_interaction.check_missions_accepted()
    logging.info("Detected that %s missions already accepted.", missions)

    sleep(1)  # Brief pause to prevent errors
    total_missions = runner.run_until_full(missions)
    return total_missions


def addMission(
    missionDetection: str | Sequence[str],
    missionType: str,
    wing: bool = False,
    value: int = 0,
):
    """Add mission detection configuration (compatibility shim for external callers)."""
    return mission_registry.add(missionDetection, missionType, wing=wing, value=value)


def removeMission(mission):
    """Remove mission detection configuration (compatibility shim for external callers)."""
    return mission_registry.remove(mission)


def getMissions():
    """Return all mission detection rules."""
    return mission_registry.all()


def main(game_mode: Optional[str] = None):
    try:
        start(game_mode=game_mode)
    except Exception as exc:
        logging.error("Fatal error: %s", exc)
        raise


if __name__ == "__main__":
    main()
