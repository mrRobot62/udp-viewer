#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/common.env"

echo "[BOOTSTRAP] UDP Log Viewer"
echo "[BOOTSTRAP] Repo root: ${REPO_ROOT}"
echo "[BOOTSTRAP] Venv path: ${UDP_VIEWER_VENV}"

PY="${UDP_VIEWER_PYTHON}"

if ! command -v "${PY}" >/dev/null; then
  echo "[ERROR] Python not found: ${PY}"
  exit 1
fi

mkdir -p "$(dirname "${UDP_VIEWER_VENV}")"

if [[ ! -d "${UDP_VIEWER_VENV}" ]]; then
  echo "[BOOTSTRAP] Creating venv..."
  "${PY}" -m venv "${UDP_VIEWER_VENV}"
else
  echo "[BOOTSTRAP] Using existing venv"
fi

source "${UDP_VIEWER_VENV}/bin/activate"

echo "[BOOTSTRAP] Python version:"
python -V

echo "[BOOTSTRAP] Upgrade pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

echo "[BOOTSTRAP] Installing project editable + dev extras"
cd "${REPO_ROOT}"
python -m pip install -e "${UDP_VIEWER_PIP_EXTRAS}"

echo
echo "[BOOTSTRAP] SUCCESS"
echo
echo "Run app:"
echo "  source ${UDP_VIEWER_VENV}/bin/activate"
echo "  udp-log-viewer"
echo
echo "Run tests:"
echo "  python -m pytest"