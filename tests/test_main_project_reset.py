from __future__ import annotations

from pathlib import Path

from udp_log_viewer.main import MainWindow
from udp_log_viewer.project_runtime import RuntimeProject


class _DummySettingsStore:
    def __init__(self) -> None:
        self.saved_preferences = None
        self.ini_calls: list[tuple[str, str, str]] = []

    def save_preferences(self, preferences) -> None:
        self.saved_preferences = preferences

    def ini_set(self, section: str, key: str, value: str) -> None:
        self.ini_calls.append((section, key, value))


class _DummyVisualizerManager:
    def __init__(self) -> None:
        self.runtime_contexts: list[tuple[str | None, Path | None]] = []

    def set_runtime_context(self, *, project_name, output_dir) -> None:
        self.runtime_contexts.append((project_name, output_dir))


class _DummyWindow:
    def __init__(self) -> None:
        self._active_project = RuntimeProject(name="Demo", root_dir=Path("/tmp/projects"))
        self._preferences = type("Prefs", (), {"project_root": "/tmp/projects"})()
        self._settings_store = _DummySettingsStore()
        self._paths_cfg = type("Paths", (), {"project_root": Path("/tmp/projects")})()
        self._visualizer_manager = _DummyVisualizerManager()
        self.updated_title = False

    def _project_name(self) -> str | None:
        return self._active_project.name if self._active_project is not None else None

    def _project_output_dir(self) -> Path | None:
        if self._active_project is None:
            return None
        return self._active_project.output_dir

    def _update_window_title(self) -> None:
        self.updated_title = True

    def _sync_runtime_context(self) -> None:
        MainWindow._sync_runtime_context(self)


def test_reset_active_project_restores_defaults(monkeypatch) -> None:
    window = _DummyWindow()
    default_root = Path("/tmp/default-project-root")

    monkeypatch.setattr("udp_log_viewer.main.get_default_project_root_dir", lambda: default_root)

    MainWindow._reset_active_project(window)

    assert window._active_project is None
    assert window._preferences.project_root == ""
    assert window._paths_cfg.project_root == default_root
    assert window._settings_store.ini_calls[-1] == ("paths", "project_root", str(default_root))
    assert window._visualizer_manager.runtime_contexts[-1] == (None, None)
    assert window.updated_title is True

