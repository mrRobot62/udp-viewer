#!/usr/bin/env bash
set -euo pipefail

# Build macOS .app bundle and .dmg using cx_Freeze.
# Requires: source venv activated, cx_Freeze + dmgbuild installed.
#
# Usage:
#   ./build_dmg.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$BUILD_PYTHON" ]]; then
    echo "Fehler: Python der Projektumgebung fehlt: $BUILD_PYTHON" >&2
    exit 1
fi

cd "$PROJECT_DIR"

"$BUILD_PYTHON" - <<'PY'
import sys
from importlib.metadata import PackageNotFoundError, version

print(f"Build-Interpreter: {sys.executable}")
print(f"Python-Version: {sys.version}")

for package in ("cx-Freeze", "dmgbuild", "PyQt5", "matplotlib"):
    try:
        print(f"{package}: {version(package)}")
    except PackageNotFoundError:
        raise SystemExit(f"Fehler: {package} fehlt in der Projektumgebung.")
PY

"$BUILD_PYTHON" freeze_setup.py bdist_dmg

echo "App und DMG wurden erfolgreich gebaut."
echo "Build-Ausgabe: $PROJECT_DIR/build"