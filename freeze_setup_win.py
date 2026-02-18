from __future__ import annotations

import os
import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# -----------------------------
# Project metadata
# -----------------------------
APP_NAME = "UDPLogViewer"
APP_VERSION = "0.14.0"  # keep SemVer here (PEP 440 compatible)

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# IMPORTANT:
# Use a top-level entry script (not src/udp_log_viewer/main.py) so frozen builds don't
# hit "attempted relative import with no known parent package".
ENTRY_SCRIPT = str(ROOT / "freeze_entry.py")

# Icon (Windows only)
WIN_ICON = str(ROOT / "packaging" / "windows" / "app.ico")

# -----------------------------
# Build options
# -----------------------------
includes: list[str] = []
packages: list[str] = [
    "PyQt5",
    "udp_log_viewer",
]

excludes: list[str] = [
    "tkinter",
    "unittest",
    "pytest",
]

include_files: list[tuple[str, str]] = []

# If you ship a default config.ini template later, add it here, e.g.:
# include_files.append(("packaging/default_config.ini", "default_config.ini"))

build_exe_options = {
    "packages": packages,
    "includes": includes,
    "excludes": excludes,
    "include_files": include_files,
    "include_msvcr": True if sys.platform.startswith("win") else False,
    # "zip_include_packages": ["*"],  # optional (slower startup vs. files on disk)
    # "zip_exclude_packages": [],
}

# Windows GUI base (no console window)
base = None
if sys.platform.startswith("win"):
    base = "Win32GUI"

executables = [
    Executable(
        script=ENTRY_SCRIPT,
        base=base,
        target_name=f"{APP_NAME}.exe" if sys.platform.startswith("win") else APP_NAME,
        icon=WIN_ICON if sys.platform.startswith("win") and os.path.exists(WIN_ICON) else None,
    )
]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="UDP Log Viewer (PyQt5)",
    options={"build_exe": build_exe_options},
    executables=executables,
)
