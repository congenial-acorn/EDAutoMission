"""Timing utilities for human-like delays."""

from __future__ import annotations

import random
import threading
from time import sleep as _sleep
from typing import Callable

_stop_check: Callable[[], bool] | None = None
_stop_check_lock = threading.Lock()


def set_stop_check(check_fn: Callable[[], bool] | None) -> None:
    global _stop_check
    with _stop_check_lock:
        _stop_check = check_fn


def clear_stop_check() -> None:
    set_stop_check(None)


def is_stop_requested() -> bool:
    with _stop_check_lock:
        if _stop_check is not None:
            return _stop_check()
    return False


def slight_random_time(base: float) -> float:
    return random.random() + base


def random_delay(
    min_seconds: float = 0.1,
    max_seconds: float = 0.5,
) -> float:
    return random.uniform(min_seconds, max_seconds)


def sleep_with_jitter(
    base_seconds: float,
    jitter: float = 1.0,
) -> None:
    sleep(base_seconds + random.random() * jitter)


def sleep(seconds: float) -> None:
    """
    Sleep for the specified duration, checking for stop every 0.1 seconds.
    Raises InterruptedError if stop is requested.
    """
    remaining = seconds
    while remaining > 0:
        if is_stop_requested():
            raise InterruptedError("Stop requested")
        chunk = min(0.1, remaining)
        _sleep(chunk)
        remaining -= chunk
