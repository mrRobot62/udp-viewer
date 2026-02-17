#!/usr/bin/env bash
set -euo pipefail

# Minimal dependency install for packaging.
# Safe to run multiple times.

python -m pip install --upgrade pip
python -m pip install cx_Freeze dmgbuild

echo "OK"
