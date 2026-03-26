from __future__ import annotations

import configparser
from pathlib import Path

from PyQt5.QtCore import QSettings

from .rule_slots import PatternSlot, slots_from_json, slots_to_json
from .ui_state import UiState


class SettingsStore:
    def __init__(self, settings: QSettings, config_path: Path) -> None:
        self._settings = settings
        self._config_path = config_path

    def load_ui_state(self, default_state: UiState) -> UiState:
        return UiState(
            bind_ip=self._settings.value("net/bind_ip", default_state.bind_ip, type=str),
            port=self._settings.value("net/port", default_state.port, type=int),
            autoscroll=self._settings.value("ui/autoscroll", default_state.autoscroll, type=bool),
            timestamp_enabled=self._settings.value(
                "ui/timestamp", default_state.timestamp_enabled, type=bool
            ),
            max_lines=self._settings.value("log/max_lines", default_state.max_lines, type=int),
        )

    def save_ui_state(self, state: UiState) -> None:
        self._settings.setValue("net/bind_ip", state.bind_ip)
        self._settings.setValue("net/port", int(state.port))
        self._settings.setValue("ui/autoscroll", bool(state.autoscroll))
        self._settings.setValue("ui/timestamp", bool(state.timestamp_enabled))
        self._settings.setValue("log/max_lines", int(state.max_lines))
        self._settings.sync()

    def load_rule_slots(
        self,
        *,
        ini_section: str,
        ini_key: str,
        qsettings_key: str,
        slot_count: int,
    ) -> list[PatternSlot]:
        raw = self.ini_get(ini_section, ini_key, "")
        slots = slots_from_json(raw, slot_count)
        if all(not slot.pattern.strip() for slot in slots):
            raw_qsettings = self._settings.value(qsettings_key, "", type=str)
            if raw_qsettings:
                slots = slots_from_json(raw_qsettings, slot_count)
        return slots

    def save_rule_slots(
        self,
        slots: list[PatternSlot],
        *,
        ini_section: str,
        ini_key: str,
        qsettings_key: str,
    ) -> None:
        payload = slots_to_json(slots)
        self._settings.setValue(qsettings_key, payload)
        self._settings.sync()
        try:
            self.ini_set(ini_section, ini_key, payload)
        except Exception:
            # QSettings is the reliability fallback when config.ini is not writable.
            pass

    def ini_read(self) -> dict:
        parser = configparser.ConfigParser()
        try:
            if self._config_path.exists():
                parser.read(self._config_path, encoding="utf-8")
        except Exception:
            return {}
        return {section: dict(parser.items(section)) for section in parser.sections()}

    def ini_get(self, section: str, key: str, default: str = "") -> str:
        parser = configparser.ConfigParser()
        try:
            if self._config_path.exists():
                parser.read(self._config_path, encoding="utf-8")
            return parser.get(section, key, fallback=default)
        except Exception:
            return default

    def ini_set(self, section: str, key: str, value: str) -> None:
        parser = configparser.ConfigParser()
        if self._config_path.exists():
            try:
                parser.read(self._config_path, encoding="utf-8")
            except Exception:
                parser = configparser.ConfigParser()
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, value)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8", newline="\n") as handle:
            parser.write(handle)
