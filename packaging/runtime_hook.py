"""PyInstaller runtime hook for ED Auto Mission.

Runs before the application starts when launched from a frozen (packaged) bundle.
Configures environment variables so bundled Tesseract is found automatically.
"""

import os
import sys


def _setup_frozen_paths() -> None:
    if not getattr(sys, "frozen", False):
        return

    base = sys._MEIPASS

    # Point TESSERACT_PATH to bundled tesseract executable.
    # The existing setup_tesseract() checks this env var first.
    tesseract_exe = os.path.join(base, "tesseract.exe")
    if os.path.isfile(tesseract_exe):
        os.environ.setdefault("TESSERACT_PATH", tesseract_exe)

    # Tell Tesseract where to find tessdata/ relative to the bundle root.
    tessdata_dir = os.path.join(base, "tessdata")
    if os.path.isdir(tessdata_dir):
        # TESSDATA_PREFIX must be the parent of the tessdata/ directory
        os.environ.setdefault("TESSDATA_PREFIX", base + os.sep)


_setup_frozen_paths()
