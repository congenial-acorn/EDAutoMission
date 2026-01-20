"""Keyboard and mouse input service."""

from __future__ import annotations

import logging
import sys
from typing import Literal

if sys.platform == "win32":
    import pydirectinput as _input_backend
else:
    import pyautogui as _input_backend

from ed_auto_mission.services.timing import slight_random_time, sleep

logger = logging.getLogger(__name__)


class InputService:
    """Service for sending keyboard and mouse input to the game."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize the input service.

        Args:
            dry_run: If True, log inputs but don't send them
        """
        self._dry_run = dry_run

    def press(
        self,
        key: str,
        presses: int = 1,
        interval: float | None = None,
    ) -> None:
        """
        Press a key one or more times.

        Args:
            key: Key to press (e.g., 'space', 'a', 'enter')
            presses: Number of times to press the key
            interval: Delay between presses (default: random 0.2-0.5s)
        """
        if interval is None:
            interval = slight_random_time(0.2)

        if self._dry_run:
            logger.info(
                "[DRY RUN] Press '%s' x%d (interval: %.2fs)", key, presses, interval
            )
            return

        logger.debug("Pressing '%s' x%d", key, presses)
        _input_backend.press(key, presses=presses, interval=interval)

    def press_with_delay(
        self,
        key: str,
        delay_after: float = 0.3,
    ) -> None:
        """
        Press a key and wait afterward.

        Args:
            key: Key to press
            delay_after: Seconds to wait after pressing
        """
        self.press(key)
        sleep(delay_after)

    def navigate_menu(
        self,
        direction: Literal["up", "down", "left", "right"],
        steps: int = 1,
        interval: float | None = None,
    ) -> None:
        """
        Navigate a menu using arrow keys or WASD.

        Args:
            direction: Direction to move
            steps: Number of steps
            interval: Delay between steps
        """
        key_map = {
            "up": "w",
            "down": "s",
            "left": "a",
            "right": "d",
        }
        self.press(key_map[direction], presses=steps, interval=interval)

    def select(self) -> None:
        """Press the selection key (space)."""
        self.press("space")

    def back(self, times: int = 1) -> None:
        """Press the back key (backspace)."""
        self.press("backspace", presses=times, interval=slight_random_time(2))

    def open_panel(self, panel_number: int) -> None:
        """
        Open a numbered panel (1-4).

        Args:
            panel_number: Panel number to open
        """
        if not 1 <= panel_number <= 4:
            raise ValueError(f"Panel number must be 1-4, got {panel_number}")
        self.press(str(panel_number))

    def escape(self) -> None:
        """Press escape key."""
        self.press("esc")
