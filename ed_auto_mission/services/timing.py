"""Timing utilities for human-like delays."""

from __future__ import annotations

import random
from time import sleep as _sleep


def slight_random_time(base: float) -> float:
    """
    Add slight randomness to a base time value.

    Args:
        base: Base time in seconds

    Returns:
        Base time plus a random value between 0 and 1 seconds
    """
    return random.random() + base


def random_delay(
    min_seconds: float = 0.1,
    max_seconds: float = 0.5,
) -> float:
    """
    Generate a random delay within a range.

    Args:
        min_seconds: Minimum delay
        max_seconds: Maximum delay

    Returns:
        Random delay value
    """
    return random.uniform(min_seconds, max_seconds)


def sleep_with_jitter(
    base_seconds: float,
    jitter: float = 1.0,
) -> None:
    """
    Sleep for a base duration plus random jitter.

    Args:
        base_seconds: Base sleep duration
        jitter: Maximum additional random seconds (default: 1.0)
    """
    _sleep(base_seconds + random.random() * jitter)


def sleep(seconds: float) -> None:
    """
    Sleep for the specified duration.

    Wrapper around time.sleep for consistency.
    """
    _sleep(seconds)
