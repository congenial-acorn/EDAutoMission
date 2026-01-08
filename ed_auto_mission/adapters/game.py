"""Elite Dangerous game interaction adapter."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from ed_auto_mission.core.types import GameInteraction, ScreenRegion
from ed_auto_mission.core.coordinates import UI_MAP
from ed_auto_mission.core.category_navigator import CategoryNavigator
from ed_auto_mission.services.screen import ScreenService
from ed_auto_mission.services.ocr import OCRService
from ed_auto_mission.services.input import InputService
from ed_auto_mission.services.timing import sleep, slight_random_time

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

WING_ICON_PATH = Path(__file__).parent.parent.parent / "wingicon.png"


class EliteDangerousGame:
    """
    Game interaction implementation for Elite Dangerous.

    Works with both Horizons and Odyssey versions of the game.
    Implements the GameInteraction protocol with instance-based state management.
    """

    def __init__(
        self,
        screen: ScreenService,
        ocr: OCRService,
        input_service: InputService,
        debug_output: bool = False,
    ):
        self._screen = screen
        self._ocr = ocr
        self._input = input_service
        self._debug_output = debug_output
        self._category_navigator = CategoryNavigator(input_service)

        self._missions_seen = 0
        self._back_button_original: np.ndarray | None = None

        self._wing_icon: Image.Image | None = None
        if WING_ICON_PATH.exists():
            self._wing_icon = Image.open(WING_ICON_PATH).convert("RGB")
        else:
            logger.warning("Wing icon not found at %s", WING_ICON_PATH)

    def reset_state(self) -> None:
        self._missions_seen = 0
        self._back_button_original = None

    def open_missions_board(self) -> None:
        self._input.press("space", presses=2, interval=slight_random_time(2))
        sleep(5)

    def navigate_to_category(self, category: str) -> None:
        if not self._category_navigator.navigate_to_category(category):
            logger.warning("Unknown category: %s", category)
            return
        sleep(5)

    def at_bottom(self) -> bool:
        region = UI_MAP.back_button
        scaled = region.scaled(self._screen.width, self._screen.height)

        current = np.array(self._screen.capture_region(scaled))

        if self._back_button_original is None:
            self._back_button_original = current
            return False

        mse = np.sum(
            (self._back_button_original.astype("float") - current.astype("float")) ** 2
        ) / float(self._back_button_original.shape[0] * current.shape[1])

        logger.debug("Back button MSE: %.2f", mse)

        return mse > 1

    def ocr_mission(self) -> str:
        region = UI_MAP.get_mission_region(self._missions_seen)

        filename = "ocr_debug.png" if self._debug_output else None
        text = self._ocr.read_text(region, debug_filename=filename)

        return text

    def check_wing_mission(self) -> bool:
        if self._wing_icon is None:
            logger.warning("Wing icon reference not loaded, cannot check wing status")
            return False

        region = UI_MAP.get_wing_icon_region(self._missions_seen)
        scaled = region.scaled(self._screen.width, self._screen.height)

        captured = self._screen.capture_region(scaled)

        if self._debug_output:
            captured.save("wing_debug.png")

        wing_resized = self._wing_icon.resize(
            (captured.width, captured.height)
        )

        captured_arr = np.array(captured).astype("float")
        wing_arr = np.array(wing_resized).astype("float")

        mse = np.sum((wing_arr - captured_arr) ** 2) / float(
            wing_arr.shape[0] * wing_arr.shape[1]
        )

        logger.debug("Wing mission MSE: %.2f", mse)

        return mse < 5000

    def accept_mission(self) -> None:
        self._input.press("space", presses=2, interval=slight_random_time(0.3))

    def next_mission(self) -> None:
        self._missions_seen += 1
        self._input.press("s", interval=slight_random_time(0.2))

    def return_to_categories(self) -> None:
        self.reset_state()
        self._input.press("backspace", presses=1)
        sleep(2)

    def return_to_starport(self) -> None:
        self.reset_state()
        self._input.press("backspace", presses=2, interval=slight_random_time(2))

    def check_missions_accepted(self) -> int:
        self._input.press("1", presses=1, interval=slight_random_time(0.3))
        sleep(2)

        region = UI_MAP.mission_count_region

        filename = "missions_accepted_debug.png" if self._debug_output else None
        count = self._ocr.read_digits(region, debug_filename=filename)

        self._input.press("1", presses=1, interval=slight_random_time(0.3))

        if count is None:
            logger.debug("Could not read mission count, assuming 0")
            return 0

        return count


def _check_protocol() -> None:
    interaction: GameInteraction = EliteDangerousGame(
        screen=ScreenService(),
        ocr=OCRService(ScreenService()),
        input_service=InputService(),
    )
    _ = interaction
