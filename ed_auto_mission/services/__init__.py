"""Infrastructure services - OCR, screen capture, input, notifications.

Services are imported lazily to avoid triggering pyautogui/X11 at module load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Lazy imports - only resolve when actually accessed
if TYPE_CHECKING:
    from ed_auto_mission.services.screen import ScreenService, get_screen_context
    from ed_auto_mission.services.ocr import OCRService, setup_tesseract
    from ed_auto_mission.services.discord import (
        DiscordWebhookHandler,
        setup_discord_logging,
    )
    from ed_auto_mission.services.timing import slight_random_time, random_delay
    from ed_auto_mission.services.process import is_game_running
    from ed_auto_mission.services.input import InputService
    from ed_auto_mission.services.window import focus_window, WindowFocusError


def __getattr__(name: str):
    """Lazy import handler."""
    if name in ("ScreenService", "get_screen_context"):
        from ed_auto_mission.services.screen import ScreenService, get_screen_context

        return ScreenService if name == "ScreenService" else get_screen_context

    if name in ("OCRService", "setup_tesseract"):
        from ed_auto_mission.services.ocr import OCRService, setup_tesseract

        return OCRService if name == "OCRService" else setup_tesseract

    if name in ("DiscordWebhookHandler", "setup_discord_logging"):
        from ed_auto_mission.services.discord import (
            DiscordWebhookHandler,
            setup_discord_logging,
        )

        return (
            DiscordWebhookHandler
            if name == "DiscordWebhookHandler"
            else setup_discord_logging
        )

    if name in ("slight_random_time", "random_delay"):
        from ed_auto_mission.services.timing import slight_random_time, random_delay

        return slight_random_time if name == "slight_random_time" else random_delay

    if name == "is_game_running":
        from ed_auto_mission.services.process import is_game_running

        return is_game_running

    if name == "InputService":
        from ed_auto_mission.services.input import InputService

        return InputService

    if name in ("focus_window", "WindowFocusError"):
        from ed_auto_mission.services.window import focus_window, WindowFocusError

        return focus_window if name == "focus_window" else WindowFocusError

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ScreenService",
    "get_screen_context",
    "OCRService",
    "setup_tesseract",
    "DiscordWebhookHandler",
    "setup_discord_logging",
    "slight_random_time",
    "random_delay",
    "is_game_running",
    "InputService",
    "focus_window",
    "WindowFocusError",
]
