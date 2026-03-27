from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QWidget

from .config_store import ConfigStore
from .csv_log_parser import CsvLogParser
from .visualizer_config import VisualizerConfig
from .visualizer_config_dialog import VisualizerConfigDialog
from .visualizer_window import VisualizerWindow
from .logic_visualizer_window import LogicVisualizerWindow
from .logic_visualizer_config_dialog import LogicVisualizerConfigDialog
from ..preferences import AppPreferences

class VisualizerManager:
    PLOT_SLOT_INDEX = 0
    LOGIC_SLOT_INDEX = 1

    def __init__(
        self,
        config_path: str | Path | None = None,
        screenshot_dir: str | Path | None = None,
        preferences: AppPreferences | None = None,
    ) -> None:
        self.parser = CsvLogParser()
        self.preferences = preferences or AppPreferences()
        self.config_store = ConfigStore(config_path=config_path, preferences=self.preferences)
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir is not None else None
        self.visualizers: list[VisualizerConfig] = []
        self.windows_by_index: dict[int, VisualizerWindow] = {}
        self.sample_counters_by_index: dict[int, int] = {}

    def load_configs(self) -> None:
        self.config_store = ConfigStore(config_path=self.config_store._config_path, preferences=self.preferences)
        self.visualizers = self.config_store.load_visualizer_configs()
        self.windows_by_index.clear()
        self.sample_counters_by_index.clear()

    def set_preferences(self, preferences: AppPreferences) -> None:
        self.preferences = preferences
        self.config_store = ConfigStore(config_path=self.config_store._config_path, preferences=self.preferences)

    def save_configs(self) -> None:
        self.config_store.save_visualizer_configs(self.visualizers)

    def process_log_line(self, line: str) -> int:
        accepted_samples = 0
        for index, config in enumerate(self.visualizers):
            if not config.is_routable:
                continue
            sample_index = self.sample_counters_by_index.get(index, 0)
            sample = self.parser.parse_line(line, config, sample_index)
            if sample is None:
                continue
            window = self._get_or_create_window(index, config)
            window.append_sample(sample)
            self.sample_counters_by_index[index] = sample_index + 1
            accepted_samples += 1
        return accepted_samples

    def set_visualizers(self, configs: list[VisualizerConfig]) -> None:
        self.visualizers = list(configs)
        self.windows_by_index.clear()
        self.sample_counters_by_index.clear()

    def get_window(self, index: int) -> VisualizerWindow | None:
        return self.windows_by_index.get(index)

    def show_window(self, index: int) -> None:
        if not self.visualizers:
            self.load_configs()
        if not (0 <= index < len(self.visualizers)):
            return
        window = self._get_or_create_window(index, self.visualizers[index])
        window.show()

    def close_window(self, index: int) -> None:
        window = self.windows_by_index.get(index)
        if window is not None:
            window.close()

    def close_all_windows(self) -> None:
        for window in list(self.windows_by_index.values()):
            try:
                window.close()
            except Exception:
                pass
        self.windows_by_index.clear()

    def clear_all_buffers(self) -> None:
        self.sample_counters_by_index.clear()
        for window in self.windows_by_index.values():
            window.clear_samples()

    def clear_window_buffer(self, index: int) -> None:
        self.sample_counters_by_index[index] = 0
        window = self.windows_by_index.get(index)
        if window is not None:
            window.clear_samples()

    def configure_csv_temp(self, parent: QWidget | None = None) -> bool:
        if not self.visualizers:
            self.load_configs()
        dialog = VisualizerConfigDialog(config=self.visualizers[self.PLOT_SLOT_INDEX], parent=parent)
        if dialog.exec_() != dialog.Accepted:
            return False
        self.visualizers[self.PLOT_SLOT_INDEX] = dialog.result_config()
        self.save_configs()
        existing_window = self.windows_by_index.pop(self.PLOT_SLOT_INDEX, None)
        if existing_window is not None:
            existing_window.close()
        self.sample_counters_by_index[self.PLOT_SLOT_INDEX] = 0
        return True

    def _get_or_create_window(self, index: int, config: VisualizerConfig) -> VisualizerWindow:
        existing_window = self.windows_by_index.get(index)
        if existing_window is not None:
            return existing_window
        if config.graph_type == "logic":
            window = LogicVisualizerWindow(
                config,
                screenshot_dir=self.screenshot_dir,
                window_size_presets=self.preferences.visualizer_presets,
            )
        else:
            window = VisualizerWindow(
                config,
                screenshot_dir=self.screenshot_dir,
                window_size_presets=self.preferences.visualizer_presets,
            )

        self.windows_by_index[index] = window
        return window

    def configure_logic(self, parent=None) -> bool:
        if not self.visualizers:
            self.load_configs()

        while len(self.visualizers) <= self.LOGIC_SLOT_INDEX:
            self.visualizers.append(VisualizerConfig())

        config = self.visualizers[self.LOGIC_SLOT_INDEX]

        if getattr(config, "graph_type", "plot") != "logic":
            config = self.config_store._build_default_logic_config(self.preferences)
            self.visualizers[self.LOGIC_SLOT_INDEX] = config

        dlg = LogicVisualizerConfigDialog(config, parent)
        if dlg.exec_() != dlg.Accepted:
            return False

        dlg.apply()
        self.visualizers[self.LOGIC_SLOT_INDEX] = config
        self.save_configs()

        existing_window = self.windows_by_index.pop(self.LOGIC_SLOT_INDEX, None)
        if existing_window is not None:
            existing_window.close()

        self.sample_counters_by_index[self.LOGIC_SLOT_INDEX] = 0
        return True

    def show_logic_window(self) -> None:
        if not self.visualizers:
            self.load_configs()

        while len(self.visualizers) <= self.LOGIC_SLOT_INDEX:
            self.visualizers.append(VisualizerConfig())

        config = self.visualizers[self.LOGIC_SLOT_INDEX]

        if getattr(config, "graph_type", "plot") != "logic":
            config = self.config_store._build_default_logic_config(self.preferences)
            self.visualizers[self.LOGIC_SLOT_INDEX] = config
            self.save_configs()

        window = self._get_or_create_window(self.LOGIC_SLOT_INDEX, config)
        window.show()
