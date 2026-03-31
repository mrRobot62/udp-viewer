from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSettings

from udp_log_viewer.preferences import AppPreferences
from udp_log_viewer.settings_store import SettingsStore


def test_preferences_are_persisted_in_config_ini(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    store = SettingsStore(QSettings("LocalTools", "UdpLogViewerTest"), config_path)
    prefs = AppPreferences(
        language="en",
        autoscroll_default=False,
        timestamp_default=False,
        max_lines_default=12345,
        log_path=str(tmp_path / "logs"),
        visualizer_presets=(100, 150, 200, 300),
        plot_sliding_window_default=False,
        plot_window_size_default=150,
        logic_sliding_window_default=True,
        logic_window_size_default=100,
    )

    store.save_preferences(prefs)
    loaded = store.load_preferences()

    assert loaded.language == "en"
    assert loaded.autoscroll_default is False
    assert loaded.timestamp_default is False
    assert loaded.max_lines_default == 12345
    assert loaded.log_path == str(tmp_path / "logs")
    assert loaded.visualizer_presets == (100, 150, 200, 300)
    assert loaded.plot_sliding_window_default is False
    assert loaded.plot_window_size_default == 150
    assert loaded.logic_sliding_window_default is True
    assert loaded.logic_window_size_default == 100
