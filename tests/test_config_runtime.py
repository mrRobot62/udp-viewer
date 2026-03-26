from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSettings

from udp_log_viewer.config_runtime import normalize_config_selection, resolve_config_path


def test_normalize_config_selection_adds_ini_suffix(tmp_path: Path) -> None:
    suggested = tmp_path / "config.ini"
    selected = normalize_config_selection(str(tmp_path / "custom"), suggested)

    assert selected.name == "custom.ini"


def test_resolve_config_path_uses_existing_writable_candidate(tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    config_path = tmp_path / "config.ini"
    config_path.write_text("[app]\n", encoding="utf-8")

    resolved = resolve_config_path(
        settings,
        settings_key="config/selected_path",
        default_path=config_path,
        prompt_callback=lambda suggested: suggested,
    )

    assert resolved == config_path
