"""Display helpers for stable Tk rendering."""

from __future__ import annotations

import ctypes
import platform
import tkinter as tk
import tkinter.font as tkfont
from typing import ClassVar, cast


def enable_dpi_awareness() -> None:
    """Opt the process into Windows DPI awareness before Tk creates windows."""
    if platform.system() != "Windows":
        return

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except (AttributeError, OSError):
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


class DisplayStabilizer:
    """Keep Tk text metrics stable across focus/display changes."""

    _FONT_NAMES: ClassVar[tuple[str, ...]] = (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    )

    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.scaling: float = float(cast(str, root.tk.call("tk", "scaling")))
        self.font_sizes: dict[str, int] = self._read_font_sizes()
        self.scale: float = 1.0

    def apply(self) -> None:
        _ = self.root.tk.call("tk", "scaling", self.scaling * self.scale)
        for name, size in self.font_sizes.items():
            scaled_size = max(6, round(size * self.scale))
            _ = tkfont.nametofont(name).configure(size=scaled_size)

    def adjust_scale(self, delta: float) -> None:
        self.scale = min(1.6, max(0.8, self.scale + delta))
        self.apply()

    def reset_scale(self) -> None:
        self.scale = 1.0
        self.apply()

    def bind(self) -> None:
        _ = self.root.bind("<FocusIn>", self._restore, add="+")
        _ = self.root.bind("<Map>", self._restore, add="+")

    def _restore(self, _event: tk.Event) -> None:
        self.root.after_idle(self.apply)

    def _read_font_sizes(self) -> dict[str, int]:
        sizes: dict[str, int] = {}
        for name in self._FONT_NAMES:
            try:
                sizes[name] = int(tkfont.nametofont(name).cget("size"))
            except tk.TclError:
                pass
        return sizes
