#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="udp"

if [[ -d "${VENV_DIR}" ]]; then
  echo "==> venv '${VENV_DIR}' already exists."
else
  echo "==> Creating venv '${VENV_DIR}'"
  python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "==> Upgrading pip"
python -m pip install -U pip

echo "==> Installing project (editable)"
python -m pip install -e .

echo ""
echo "DONE."
echo "Python: $(which python)"
python -V