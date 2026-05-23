# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ED Auto Mission.

Builds a --onedir distribution with bundled Tesseract OCR.

Usage:
    pyinstaller ed_auto_mission.spec              # Build with system Tesseract
    TESSERACT_DIR=/path/to/tesseract pyinstaller ed_auto_mission.spec  # Custom Tesseract

Output:
    dist/EDAutoMission/EDAutoMission.exe  (+ _internal/ dependencies)
"""

import os
import sys
from pathlib import Path

# --- Project paths ---
project_root = Path(SPECPATH)

# --- Tesseract bundling ---
# Defaults to Chocolatey install location on Windows.
# Override with TESSERACT_DIR env var for CI or local builds.
tesseract_dir = Path(os.environ.get("TESSERACT_DIR", r"C:\Program Files\Tesseract-OCR"))

tesseract_binaries: list[tuple[str, str]] = []
tesseract_datas: list[tuple[str, str]] = []

if tesseract_dir.is_dir():
    for f in tesseract_dir.glob("*.exe"):
        tesseract_binaries.append((str(f), "."))
    for f in tesseract_dir.glob("*.dll"):
        tesseract_binaries.append((str(f), "."))

    tessdata_dir = tesseract_dir / "tessdata"
    if tessdata_dir.is_dir():
        for f in tessdata_dir.glob("*.traineddata"):
            tesseract_datas.append((str(f), "tessdata"))

    print(f"[spec] Tesseract: {tesseract_dir} ({len(tesseract_binaries)} binaries, {len(tesseract_datas)} tessdata)")
else:
    print(f"[spec] WARNING: Tesseract not found at {tesseract_dir}")
    print("[spec]        Set TESSERACT_DIR to your Tesseract installation directory.")

# --- Application data files ---
app_datas: list[tuple[str, str]] = [
    (str(project_root / "wingicon.png"), "."),
]

# --- Runtime hook (sets TESSERACT_PATH + TESSDATA_PREFIX in frozen mode) ---
runtime_hooks = [str(project_root / "packaging" / "runtime_hook.py")]

# --- Analysis ---
a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[
        *tesseract_binaries,
    ],
    datas=[
        *app_datas,
        *tesseract_datas,
    ],
    hiddenimports=[
        # Direct dependencies
        "pyautogui",
        "pydirectinput",
        "pytesseract",
        "numpy",
        "PIL",
        "matplotlib",
        "schedule",
        "psutil",
        # pywin32 (required by pydirectinput / screen capture)
        "win32api",
        "win32con",
        "win32gui",
        "win32process",
        "pywintypes",
        "pythoncom",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[
        # Trim unused stdlib modules to reduce size
        "tkinter.test",
        "unittest",
        "email",
        "html",
        "xmlrpc",
        "pydoc",
        "doctest",
        "difflib",
        "lib2to3",
        "multiprocessing",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EDAutoMission",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="EDAutoMission",
)
