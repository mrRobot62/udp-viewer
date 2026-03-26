from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSettings
import pytest

from udp_log_viewer.rule_slots import PatternSlot
from udp_log_viewer.settings_store import SettingsStore
from udp_log_viewer.ui_state import UiState


def test_settings_store_roundtrips_ui_state(tmp_path: Path) -> None:
    qsettings_path = tmp_path / "settings.ini"
    qsettings = QSettings(str(qsettings_path), QSettings.IniFormat)
    store = SettingsStore(qsettings, tmp_path / "config.ini")

    state = UiState(
        bind_ip="127.0.0.1",
        port=9999,
        autoscroll=False,
        timestamp_enabled=True,
        max_lines=1234,
    )
    store.save_ui_state(state)
    loaded = store.load_ui_state(UiState())

    assert loaded.bind_ip == "127.0.0.1"
    assert loaded.port == 9999
    assert loaded.autoscroll is False
    assert loaded.timestamp_enabled is True
    assert loaded.max_lines == 1234


def test_settings_store_roundtrips_rule_slots(tmp_path: Path) -> None:
    qsettings_path = tmp_path / "settings.ini"
    qsettings = QSettings(str(qsettings_path), QSettings.IniFormat)
    config_path = tmp_path / "config.ini"
    store = SettingsStore(qsettings, config_path)

    slots = [PatternSlot(pattern="ERROR", mode="Substring", color="Red")]
    store.save_rule_slots(
        slots,
        ini_section="rules",
        ini_key="filter_slots_json",
        qsettings_key="filter/slots_json",
    )

    loaded = store.load_rule_slots(
        ini_section="rules",
        ini_key="filter_slots_json",
        qsettings_key="filter/slots_json",
        slot_count=5,
    )

    assert loaded[0].pattern == "ERROR"
    assert loaded[0].color == "Red"
    assert config_path.exists()


def test_settings_store_falls_back_to_qsettings_when_ini_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    qsettings_path = tmp_path / "settings.ini"
    qsettings = QSettings(str(qsettings_path), QSettings.IniFormat)
    store = SettingsStore(qsettings, tmp_path / "config.ini")

    monkeypatch.setattr(store, "ini_set", lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError()))

    store.save_rule_slots(
        [PatternSlot(pattern="OVEN", mode="Substring", color="Green")],
        ini_section="rules",
        ini_key="filter_slots_json",
        qsettings_key="filter/slots_json",
    )

    assert qsettings.value("filter/slots_json", "", type=str).startswith('[{"pattern": "OVEN"')
