"""Category navigation for mission board categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ed_auto_mission.services.timing import sleep, slight_random_time

if TYPE_CHECKING:
    from ed_auto_mission.services.input import InputService


class CategoryNavigator:
    def __init__(self, input_service: InputService):
        self._input = input_service
        self._category_handlers: dict[str, Callable[[], None]] = {
            "all": self.navigate_to_all,
            "combat": self.navigate_to_combat,
            "transport": self.navigate_to_transport,
            "freelance": self.navigate_to_freelance,
            "operations": self.navigate_to_operations,
            "support": self.navigate_to_support,
            "thargoid": self.navigate_to_thargoid,
        }

    def navigate_to_category(self, category: str) -> bool:
        handler = self._category_handlers.get(category.lower())
        if handler is None:
            return False
        handler()
        sleep(5)
        return True

    def get_supported_categories(self) -> list[str]:
        return list(self._category_handlers.keys())

    def navigate_to_all(self) -> None:
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_combat(self) -> None:
        self._input.press("d", presses=1, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_transport(self) -> None:
        self._input.press("d", presses=2, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_freelance(self) -> None:
        self._input.press("d", presses=3, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_operations(self) -> None:
        self._input.press("s", presses=1, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_support(self) -> None:
        self._input.press("s", presses=1, interval=slight_random_time(0.3))
        self._input.press("d", presses=1, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))

    def navigate_to_thargoid(self) -> None:
        self._input.press("s", presses=1, interval=slight_random_time(0.3))
        self._input.press("d", presses=2, interval=slight_random_time(0.3))
        self._input.press("space", interval=slight_random_time(0.3))
