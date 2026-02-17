#!/usr/bin/env bash
set -euo pipefail

# Build macOS .app bundle and .dmg using cx_Freeze.
# Requires: source venv activated, cx_Freeze + dmgbuild installed.
#
# Usage:
#   ./build_dmg.sh

python freeze_setup.py bdist_dmg
echo "DMG created under: dist/"
ls -la dist || true
