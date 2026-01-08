"""Discord webhook logging integration."""

from __future__ import annotations

import json
import logging
from urllib import request
from typing import Optional

logger = logging.getLogger(__name__)

# Custom logging level for Discord notifications
DISCORD_LEVEL = logging.INFO + 5
logging.addLevelName(DISCORD_LEVEL, "DISCORD")


class DiscordWebhookHandler(logging.Handler):
    """Logging handler that sends log records to a Discord webhook."""

    def __init__(self, webhook_url: str, level: int = DISCORD_LEVEL):
        super().__init__(level=level)
        self.webhook_url = webhook_url

    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to the Discord webhook."""
        try:
            message = self.format(record)
            payload = json.dumps({"content": message}).encode("utf-8")

            req = request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with request.urlopen(req, timeout=5):
                pass

        except Exception:
            self.handleError(record)


def setup_discord_logging(
    webhook_url: Optional[str],
    logger_instance: logging.Logger | None = None,
) -> bool:
    """
    Configure Discord webhook logging.

    Args:
        webhook_url: Discord webhook URL, or None to skip setup
        logger_instance: Logger to attach handler to (default: root logger)

    Returns:
        True if Discord logging was enabled, False otherwise
    """
    if not webhook_url:
        logger.debug("Discord webhook not configured")
        return False

    target_logger = logger_instance or logging.getLogger()

    # Check if handler already exists
    for handler in target_logger.handlers:
        if isinstance(handler, DiscordWebhookHandler):
            logger.debug("Discord handler already attached")
            return True

    handler = DiscordWebhookHandler(webhook_url)
    handler.setFormatter(logging.Formatter("%(message)s"))
    target_logger.addHandler(handler)

    logger.info("Discord webhook logging enabled")
    return True


def log_discord(message: str, logger_instance: logging.Logger | None = None) -> None:
    """
    Log a message at the DISCORD level.

    Args:
        message: Message to send to Discord
        logger_instance: Logger to use (default: root logger)
    """
    target_logger = logger_instance or logging.getLogger()
    target_logger.log(DISCORD_LEVEL, message)
