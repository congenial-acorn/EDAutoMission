"""Window focus management (Windows-specific)."""

from __future__ import annotations

import logging
import re
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class WindowFocusError(Exception):
    """Raised when a window cannot be focused."""

    pass


if sys.platform == "win32":
    import win32gui

    def _enum_windows_callback(hwnd: int, results: list[tuple[int, str]]) -> bool:
        """Callback for EnumWindows to collect window handles and titles."""
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                results.append((hwnd, title))
        return True

    def find_window(pattern: str) -> Optional[int]:
        """
        Find a window handle by title pattern (regex).

        Args:
            pattern: Regex pattern to match window title

        Returns:
            Window handle if found, None otherwise
        """
        results: list[tuple[int, str]] = []
        win32gui.EnumWindows(_enum_windows_callback, results)

        for hwnd, title in results:
            logger.debug("Checking window: %s", title)
            if re.match(pattern, title):
                return hwnd

        return None

    def focus_window(pattern: str) -> None:
        """
        Bring a window to the foreground.

        Args:
            pattern: Regex pattern to match window title

        Raises:
            WindowFocusError: If window not found or cannot be focused
        """
        hwnd = find_window(pattern)

        if hwnd is None:
            raise WindowFocusError(f"No window matching pattern: {pattern}")

        try:
            title = win32gui.GetWindowText(hwnd)
            logger.debug("Focusing window: %s", title)
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            raise WindowFocusError(f"Failed to focus window: {e}") from e

    def focus_elite_dangerous() -> bool:
        """
        Focus the Elite Dangerous game window.

        Returns:
            True if successful, False if window not found
        """
        try:
            focus_window(r"Elite.+Dangerous.+CLIENT")
            return True
        except WindowFocusError:
            logger.debug("Elite Dangerous window not found")
            return False

else:
    # Non-Windows platforms
    def find_window(pattern: str) -> Optional[int]:
        """Window finding not supported on this platform."""
        logger.warning("Window finding not supported on %s", sys.platform)
        return None

    def focus_window(pattern: str) -> None:
        """Window focusing not supported on this platform."""
        logger.warning("Window focusing not supported on %s", sys.platform)

    def focus_elite_dangerous() -> bool:
        """Window focusing not supported on this platform."""
        logger.info("Window focusing not available on %s - switch manually", sys.platform)
        return False
