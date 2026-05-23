"""GUI interface for ED Auto Mission."""

from ed_auto_mission.gui.display import enable_dpi_awareness

enable_dpi_awareness()

from ed_auto_mission.gui.app import EDAutoMissionApp, run_gui

__all__ = ["EDAutoMissionApp", "run_gui"]
