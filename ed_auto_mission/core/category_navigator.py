"""Category navigation for mission board categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ed_auto_mission.services.timing import sleep, slight_random_time

if TYPE_CHECKING:
    from ed_auto_mission.services.input import InputService
    from ed_auto_mission.core.config import AppConfig


CATEGORY_KEYS: dict[str, list[tuple[str, int]]] = {
    "all": [],
    "combat": [("d", 1)],
    "transport": [("d", 2)],
    "freelance": [("d", 3)],
    "operations": [("s", 1)],
    "support": [("s", 1), ("d", 1)],
    "thargoid": [("s", 1), ("d", 2)],
}


class CategoryNavigator:
    def __init__(self, input_service: InputService, config: AppConfig):
        self._input = input_service
        self._config = config
        self._category_handlers: dict[str, Callable[[], None]] = {
            category: lambda keys=CATEGORY_KEYS[category]: self._navigate_keys(keys)
            for category in CATEGORY_KEYS
        }

    def navigate_to_category(self, category: str) -> bool:
        handler = self._category_handlers.get(category.lower())
        if handler is None:
            return False
        handler()
        sleep(self._config.navigation_delay)
        return True

    def get_supported_categories(self) -> list[str]:
        return list(self._category_handlers.keys())

    def _navigate_keys(self, keys: list[tuple[str, int]]) -> None:
        for key, presses in keys:
            self._input.press(key, presses=presses, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))
