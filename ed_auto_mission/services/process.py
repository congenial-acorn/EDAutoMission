"""Game process detection utilities."""

from __future__ import annotations

import logging

from psutil import process_iter

logger = logging.getLogger(__name__)

# Process name patterns for Elite Dangerous
ED_PROCESS_NAMES = {
    "elitedangerous",
    "elitedangerous64",
}

ED_LAUNCHER_NAMES = {
    "edlaunch",
    "edmclient",
}


def is_game_running() -> bool:
    """
    Check if Elite Dangerous is currently running.

    Returns:
        True if the game process is detected
    """
    for process in process_iter():
        try:
            name = process.name().lower()
            if any(ed_name in name for ed_name in ED_PROCESS_NAMES):
                logger.debug("Found game process: %s", process.name())
                return True
            if any(launcher in name for launcher in ED_LAUNCHER_NAMES):
                logger.debug("Found launcher process: %s", process.name())
        except (PermissionError, OSError):
            # Process access denied or process terminated
            continue

    return False


def ensure_game_running() -> None:
    """
    Verify that Elite Dangerous is running.

    Raises:
        RuntimeError: If the game is not detected
    """
    if not is_game_running():
        raise RuntimeError("Elite: Dangerous not running. Please start the game first.")
