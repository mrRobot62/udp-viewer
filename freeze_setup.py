from __future__ import annotations

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# -----------------------------------------------------------------------------
# UDPLogViewer - cx_Freeze build script
#
# Targets:
#   - build_exe      -> folder build/exe.* (fast local test run)
#   - bdist_mac      -> .app bundle
#   - bdist_dmg      -> .dmg installer (creates .app first, then packages)
#
# Notes:
#   - We intentionally exclude QtQml/QtQuick to avoid QML hook issues on some
#     PyQt5 installations (e.g. KeyError: 'QmlImportsPath').
#   - Entry-point is a small bootstrap script so that package relative imports
#     work reliably when frozen.
# -----------------------------------------------------------------------------

APP_NAME = "UDPLogViewer"
APP_VERSION = "0.14.0"

ROOT = Path(__file__).resolve().parent

# Icons (we reuse placeholders for now; user can replace later)
MAC_ICON = ROOT / "packaging" / "macos" / "app.icns"
WIN_ICON = ROOT / "packaging" / "windows" / "app.ico"

executables = [
    Executable(
        script="run_udp_log_viewer.py",
        base="gui",
        target_name=APP_NAME,
        icon=str(MAC_ICON) if MAC_ICON.exists() else None,
    )
]

build_exe_options = {
    "packages": ["udp_log_viewer", "PyQt5"],
    "excludes": [
        # avoid QML-related hook issues (not needed for our app)
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.QtQuickWidgets",
        "PyQt5.QtQmlModels",
    ],
    "include_files": [
        # Keep package data if added later (e.g., assets)
        ("src/udp_log_viewer", "udp_log_viewer"),
    ],
    "zip_include_packages": ["PyQt5", "udp_log_viewer"],
    "zip_exclude_packages": [],
}

bdist_mac_options = {
    "bundle_name": APP_NAME,
    # set CFBundleIdentifier via Info.plist entries (works across cx_Freeze variants)
    "plist_items": [
        ("CFBundleIdentifier", "localtools.udplogviewer"),
        ("CFBundleName", APP_NAME),
        ("CFBundleDisplayName", APP_NAME),
    ],
    # optional (later): icon
    # "iconfile": "packaging/macos/app.icns",
}

bdist_dmg_options = {
    "volume_label": APP_NAME,
    "applications_shortcut": True,
    # Finder window layout (coordinates in pixels)
    "icon_locations": {
        f"{APP_NAME}.app": (140, 170),
        "Applications": (420, 170),
    },
    "default_view": "icon-view",
    "icon_size": 128,
    # Optional background (set later when you have a png/svg)
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
