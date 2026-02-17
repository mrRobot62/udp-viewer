#!/usr/bin/env bash
set -euo pipefail

# Safe to run multiple times.
mkdir -p dist build

# Activate venv if you want (optional)
# source .venv/bin/activate

# 1) Build .app via cx_Freeze
python freeze_setup.py bdist_mac

# 2) Build DMG via dmgbuild
# dmgbuild reads packaging/macos/dmg_settings.py and auto-finds the .app under ./build
python -m dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" "dist/UDPLogViewer.dmg"

echo "OK: dist/UDPLogViewer.dmg"
