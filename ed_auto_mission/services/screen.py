"""Screen capture and dimension management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pyautogui

from ed_auto_mission.core.types import ScreenContext, ScreenRegion

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


def get_screen_context() -> ScreenContext:
    """Get the current screen dimensions as a ScreenContext."""
    width, height = pyautogui.size()
    return ScreenContext(width=width, height=height)


class ScreenService:
    """Service for screen capture and region management."""

    def __init__(self, context: ScreenContext | None = None):
        self._context = context or get_screen_context()

    @property
    def context(self) -> ScreenContext:
        """Current screen context."""
        return self._context

    @property
    def width(self) -> int:
        """Screen width in pixels."""
        return self._context.width

    @property
    def height(self) -> int:
        """Screen height in pixels."""
        return self._context.height

    def refresh(self) -> None:
        """Refresh screen dimensions (useful if resolution changed)."""
        self._context = get_screen_context()

    def capture_region(
        self,
        region: ScreenRegion | tuple[int, int, int, int],
        filename: str | None = None,
    ) -> Image.Image:
        """
        Capture a screenshot of a screen region.

        Args:
            region: ScreenRegion or (x, y, width, height) tuple
            filename: Optional path to save the screenshot

        Returns:
            PIL Image of the captured region
        """
        if isinstance(region, ScreenRegion):
            scaled = region.scaled(self.width, self.height)
        else:
            scaled = region

        logger.debug("Capturing region: %s", scaled)

        if filename:
            return pyautogui.screenshot(region=scaled, imageFilename=filename)
        return pyautogui.screenshot(region=scaled)

    def scale_x(self, value: int, ref_width: int = 3840) -> int:
        """Scale an x-coordinate from reference to current resolution."""
        return int(value * self.width / ref_width)

    def scale_y(self, value: int, ref_height: int = 2160) -> int:
        """Scale a y-coordinate from reference to current resolution."""
        return int(value * self.height / ref_height)

    def scale_region(self, region: ScreenRegion) -> tuple[int, int, int, int]:
        """Scale a ScreenRegion to current screen dimensions."""
        return region.scaled(self.width, self.height)
