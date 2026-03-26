from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtCore import QSettings


def is_config_path_writable(path: Path) -> bool:
    if path.exists():
        return os.access(path, os.W_OK)
    return os.access(path.parent, os.W_OK)


def resolve_config_path(
    settings: QSettings,
    *,
    settings_key: str,
    default_path: Path,
    prompt_callback,
) -> Path:
    remembered = settings.value(settings_key, "", type=str).strip()

    candidates: list[Path] = []
    if remembered:
        candidates.append(Path(remembered).expanduser())
    if default_path not in candidates:
        candidates.append(default_path)

    for candidate in candidates:
        if candidate.exists() and is_config_path_writable(candidate):
            settings.setValue(settings_key, str(candidate))
            settings.sync()
            return candidate

    selected = prompt_callback(default_path)
    settings.setValue(settings_key, str(selected))
    settings.sync()
    return selected


def normalize_config_selection(selected_path: str, suggested_path: Path) -> Path:
    if not selected_path:
        return suggested_path
    target = Path(selected_path).expanduser()
    if target.suffix.lower() != ".ini":
        target = target.with_suffix(".ini")
    return target
