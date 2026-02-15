#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="udp-log-viewer"
VENV_DIR="udp"

echo "==> Creating project folder: ${PROJECT_DIR}"
mkdir -p "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

echo "==> Creating folders"
mkdir -p src/udp_log_viewer
mkdir -p data/logs
mkdir -p packaging/macos packaging/windows packaging/linux
mkdir -p build dist
mkdir -p scripts
mkdir -p .vscode

echo "==> Creating pyproject.toml"
cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "udp-log-viewer"
version = "0.1.0"
description = "Lightweight UDP log viewer (PyQt5) for ESP32 text logs."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "PyQt5>=5.15",
]

[project.scripts]
udp-log-viewer = "udp_log_viewer.main:main"
EOF

echo "==> Creating README.md"
cat > README.md <<'EOF'
# UDP Log Viewer

Lightweight PyQt5 UDP log viewer for ESP32 text logs.

## Setup (macOS/Linux)
```bash
python3 --version  # must be >= 3.12
python3 -m venv udp
source udp/bin/activate
python -m pip install -U pip
python -m pip install -e .
udp-log-viewer