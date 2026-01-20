"""Core types and protocols for ED Auto Mission."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ScreenRegion:
    """A rectangular region on screen, defined at a reference resolution."""

    x: int
    y: int
    width: int
    height: int
    ref_width: int = 3840
    ref_height: int = 2160

    def scaled(
        self, screen_width: int, screen_height: int
    ) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) scaled to the given screen dimensions."""
        scale_x = screen_width / self.ref_width
        scale_y = screen_height / self.ref_height
        return (
            int(self.x * scale_x),
            int(self.y * scale_y),
            int(self.width * scale_x),
            int(self.height * scale_y),
        )

    def as_tuple(
        self, screen_width: int, screen_height: int
    ) -> tuple[int, int, int, int]:
        """Alias for scaled() for pyautogui region parameter."""
        return self.scaled(screen_width, screen_height)


@dataclass
class ScreenContext:
    """Current screen dimensions and scaling context."""

    width: int
    height: int
    ref_width: int = 3840
    ref_height: int = 2160

    def scale_x(self, value: int) -> int:
        """Scale an x-coordinate from reference to current resolution."""
        return int(value * self.width / self.ref_width)

    def scale_y(self, value: int) -> int:
        """Scale a y-coordinate from reference to current resolution."""
        return int(value * self.height / self.ref_height)

    def scale_region(self, region: ScreenRegion) -> tuple[int, int, int, int]:
        """Scale a ScreenRegion to current screen dimensions."""
        return region.scaled(self.width, self.height)


@dataclass(frozen=True)
class MissionRule:
    """
    Describes how to detect and label a mission.

    - needles: list of needle groups (AND across groups, OR within each group)
    - label: display/logging label
    - wing: whether this is a wing mission
    - value: minimum credit value threshold
    - categories: list of category names this mission belongs to
    """

    needles: list[list[str]]
    label: str
    wing: bool = False
    value: int = 0
    categories: tuple[str, ...] = field(default_factory=tuple)

    def matches(self, text: str) -> bool:
        """
        Return True when each group has at least one needle contained in the OCR text.
        (AND across groups, OR within each group)
        """
        upper_text = text.upper()
        for group in self.needles:
            if not any(needle.upper() in upper_text for needle in group):
                return False
        return True

    @property
    def primary_label(self) -> str:
        """Return the display label for this mission rule."""
        return self.label


@dataclass
class RunnerConfig:
    """Configuration for the mission runner loop."""

    max_missions: int = 20
    poll_interval_minutes: int = 10
    poll_offset_minutes: int = 5
    loop_sleep_seconds: int = 20
    dry_run: bool = False


@runtime_checkable
class GameInteraction(Protocol):
    """Protocol defining game-specific interactions for mission automation."""

    def open_missions_board(self) -> None:
        """Navigate to and open the missions board."""
        ...

    def at_bottom(self) -> bool:
        """Return True if the mission list has been scrolled to the bottom."""
        ...

    def ocr_mission(self) -> str:
        """Read the currently highlighted mission text via OCR."""
        ...

    def accept_mission(self) -> None:
        """Accept the currently highlighted mission."""
        ...

    def next_mission(self) -> None:
        """Move selection to the next mission in the list."""
        ...

    def return_to_starport(self) -> None: ...

    def return_to_categories(self) -> None: ...

    def navigate_to_category(self, category: str) -> None: ...

    def check_missions_accepted(self) -> int:
        """Return the count of currently accepted missions."""
        ...

    def check_wing_mission(self) -> bool:
        """Return True if the current mission is a wing mission."""
        ...

    def reset_state(self) -> None:
        """Reset any internal state for a fresh mission scan."""
        ...
