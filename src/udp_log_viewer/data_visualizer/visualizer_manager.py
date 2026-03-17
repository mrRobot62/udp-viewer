from .config_store import ConfigStore
from .csv_log_parser import CsvLogParser
from .visualizer_config import VisualizerConfig
from .visualizer_window import VisualizerWindow


class VisualizerManager:
    def __init__(self) -> None:
        self.parser = CsvLogParser()
        self.config_store = ConfigStore()

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

    def _get_or_create_window(self, index: int, config: VisualizerConfig) -> VisualizerWindow:
        existing_window = self.windows_by_index.get(index)
        if existing_window is not None:
            return existing_window

        window = VisualizerWindow(config)
        self.windows_by_index[index] = window
        return window
