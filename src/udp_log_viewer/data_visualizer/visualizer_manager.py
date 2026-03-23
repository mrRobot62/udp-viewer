from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import QWidget

from .config_store import ConfigStore
from .csv_log_parser import CsvLogParser
from .visualizer_config import VisualizerConfig
from .visualizer_config_dialog import VisualizerConfigDialog
from .visualizer_window import VisualizerWindow


class VisualizerManager:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.parser = CsvLogParser()
        self.config_store = ConfigStore(config_path=config_path)
        self.visualizers: list[VisualizerConfig] = []
        self.windows_by_index: dict[int, VisualizerWindow] = {}
        self.sample_counters_by_index: dict[int, int] = {}

    def load_configs(self) -> None:
        self.visualizers = self.config_store.load_visualizer_configs()
        self.windows_by_index.clear()
        self.sample_counters_by_index.clear()

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

    def configure_csv_temp(self, parent: QWidget | None = None) -> bool:
        if not self.visualizers:
            self.load_configs()
        dialog = VisualizerConfigDialog(config=self.visualizers[0], parent=parent)
        if dialog.exec_() != dialog.Accepted:
            return False
        self.visualizers[0] = dialog.result_config()
        self.save_configs()
        existing_window = self.windows_by_index.pop(0, None)
        if existing_window is not None:
            existing_window.close()
        self.sample_counters_by_index[0] = 0
        return True

    def _get_or_create_window(self, index: int, config: VisualizerConfig) -> VisualizerWindow:
        existing_window = self.windows_by_index.get(index)
        if existing_window is not None:
            return existing_window
        window = VisualizerWindow(config)
        self.windows_by_index[index] = window
        return window
