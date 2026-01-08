"""Centralized configuration management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """Application configuration with environment variable support."""

    # Mission settings
    max_missions: int = 20
    poll_interval_minutes: int = 10
    poll_offset_minutes: int = 5
    loop_sleep_seconds: int = 20

    # Feature flags
    dry_run: bool = False
    debug_ocr: bool = False
    interactive: bool = True

    # Discord integration
    discord_webhook_url: Optional[str] = None

    # Tesseract path (platform-specific defaults handled in setup)
    tesseract_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create configuration from environment variables with sensible defaults."""
        return cls(
            max_missions=int(os.getenv("ED_MAX_MISSIONS", "20")),
            poll_interval_minutes=int(os.getenv("ED_POLL_INTERVAL", "10")),
            poll_offset_minutes=int(os.getenv("ED_POLL_OFFSET", "5")),
            loop_sleep_seconds=int(os.getenv("ED_LOOP_SLEEP", "20")),
            dry_run=os.getenv("ED_DRY_RUN", "").lower() in ("1", "true", "yes"),
            debug_ocr=os.getenv("ED_DEBUG_OCR", "").lower() in ("1", "true", "yes"),
            interactive=os.getenv("ED_INTERACTIVE", "1").lower() not in ("0", "false", "no"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            tesseract_path=os.getenv("TESSERACT_PATH"),
        )

    def prompt_missing_values(self) -> None:
        """Interactively prompt for missing configuration values if interactive mode enabled."""
        if not self.interactive:
            return

        if not self.discord_webhook_url:
            try:
                webhook = input(
                    "Enter Discord webhook URL (leave blank to disable): "
                ).strip()
                if webhook:
                    self.discord_webhook_url = webhook
                    os.environ["DISCORD_WEBHOOK_URL"] = webhook
            except EOFError:
                pass
