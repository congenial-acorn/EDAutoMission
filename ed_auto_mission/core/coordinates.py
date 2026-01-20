"""UI coordinate maps for Elite Dangerous.

All coordinates are defined at 3840x2160 reference resolution and scaled at runtime.
Works with both Horizons and Odyssey versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from ed_auto_mission.core.types import ScreenRegion


@dataclass(frozen=True)
class UIMap:
    """UI element coordinates for Elite Dangerous at 3840x2160 reference resolution."""

    # Back button region for detecting end of mission list
    back_button: ScreenRegion = ScreenRegion(x=235, y=1868, width=666, height=90)

    # Mission selection regions (first 6 missions before scrolling)
    mission_regions: tuple[ScreenRegion, ...] = (
        ScreenRegion(x=235, y=888, width=1563, height=127),
        ScreenRegion(x=235, y=1040, width=1563, height=127),
        ScreenRegion(x=235, y=1184, width=1563, height=127),
        ScreenRegion(x=235, y=1336, width=1563, height=127),
        ScreenRegion(x=235, y=1481, width=1563, height=127),
        ScreenRegion(x=235, y=1627, width=1563, height=127),
        ScreenRegion(x=235, y=1683, width=1563, height=127),  # After scrolling
    )

    # Wing icon regions for detecting wing missions
    wing_icon_regions: tuple[ScreenRegion, ...] = (
        ScreenRegion(x=235, y=980, width=45, height=40),
        ScreenRegion(x=235, y=1132, width=45, height=40),
        ScreenRegion(x=235, y=1276, width=45, height=40),
        ScreenRegion(x=235, y=1428, width=45, height=40),
        ScreenRegion(x=235, y=1573, width=45, height=40),
        ScreenRegion(x=235, y=1719, width=45, height=40),
        ScreenRegion(x=235, y=1775, width=45, height=40),  # After scrolling
    )

    # Mission count display region
    mission_count_region: ScreenRegion = ScreenRegion(
        x=499, y=630, width=140, height=80
    )

    def get_mission_region(self, mission_index: int) -> ScreenRegion:
        """Get the screen region for a mission at the given index."""
        if mission_index < 6:
            return self.mission_regions[mission_index]
        return self.mission_regions[6]  # After scrolling, always use bottom position

    def get_wing_icon_region(self, mission_index: int) -> ScreenRegion:
        """Get the screen region for the wing icon at the given mission index."""
        if mission_index < 6:
            return self.wing_icon_regions[mission_index]
        return self.wing_icon_regions[6]


# Default UI map instance
UI_MAP = UIMap()
