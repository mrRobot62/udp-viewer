from __future__ import annotations

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# -----------------------------------------------------------------------------
# UDPLogViewer - cx_Freeze build script (macOS + Windows)
#
# Targets:
#   - build_exe      -> build/exe.* folder
#   - bdist_mac      -> .app bundle (macOS)
#   - bdist_dmg      -> .dmg installer (macOS; uses cx_Freeze bdist_dmg)
#
# Notes:
#   - We exclude QtQml/QtQuick to avoid QML hook issues (e.g. KeyError: 'QmlImportsPath')
#   - Entry-point uses freeze_entry.py to make package-relative imports work when frozen
# -----------------------------------------------------------------------------

APP_NAME = "UDPLogViewer"
APP_VERSION = "0.14.0"  # keep PEP 440 compliant here

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"

ENTRY_SCRIPT = str(ROOT / "freeze_entry.py")

MAC_ICON = ROOT / "packaging" / "macos" / "app.icns"
WIN_ICON = ROOT / "packaging" / "windows" / "app.ico"

# --- Executable (platform-specific settings) ---
if sys.platform.startswith("win"):
    executables = [
        Executable(
            script=ENTRY_SCRIPT,
            base="Win32GUI",
            target_name=f"{APP_NAME}.exe",
            icon=str(WIN_ICON) if WIN_ICON.exists() else None,
        )
    ]
else:
    # macOS/Linux: GUI base works fine for a Qt app
    executables = [
        Executable(
            script=ENTRY_SCRIPT,
            base="gui",
            target_name=APP_NAME,
            icon=str(MAC_ICON) if MAC_ICON.exists() else None,
        )
    ]

# --- build_exe options (shared) ---
build_exe_options = {
    # Let cx_Freeze discover most things, but keep it stable:
    "packages": ["udp_log_viewer", "PyQt5"],
    "excludes": [
        # avoid QML-related hook issues (not needed for our app)
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.QtQuickWidgets",
        "PyQt5.QtQmlModels",
    ],
    "include_files": [
        # Ensure our package code is included (src layout)
        (str(SRC_DIR / "udp_log_viewer"), "udp_log_viewer"),
    ],
    "zip_include_packages": ["PyQt5", "udp_log_viewer"],
    "zip_exclude_packages": [],
    "include_msvcr": True if sys.platform.startswith("win") else False,
    "path": [str(SRC_DIR)] + sys.path,
}

# --- macOS bundle options ---
bdist_mac_options = {
    "bundle_name": APP_NAME,
    # Use plist_items (portable) instead of bundle_identifier option
    "plist_items": [
        ("CFBundleIdentifier", "localtools.udplogviewer"),
        ("CFBundleName", APP_NAME),
        ("CFBundleDisplayName", APP_NAME),
        ("CFBundleShortVersionString", APP_VERSION),
    ],
    "iconfile": "packaging/macos/app.icns",

}

# --- DMG options (cx_Freeze bdist_dmg) ---
bdist_dmg_options = {
    "volume_label": APP_NAME,
    "applications_shortcut": True,
    "icon_locations": {
        f"{APP_NAME}.app": (140, 170),
        "Applications": (420, 170),
    },
    "default_view": "icon-view",
    "icon_size": 128,
    # optional later:
    # "background": "packaging/macos/dmg_background.png",
}

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="UDP log viewer for ESP32 devices (PyQt5)",
    options={
        "build_exe": build_exe_options,
        "bdist_mac": bdist_mac_options,
        "bdist_dmg": bdist_dmg_options,
    },
    executables=executables,
)