from .visualizer_config import VisualizerConfig


class ConfigStore:
    DEFAULT_VISUALIZER_COUNT = 5

    def load_visualizer_configs(self) -> list[VisualizerConfig]:
        return [VisualizerConfig() for _ in range(self.DEFAULT_VISUALIZER_COUNT)]

    def save_visualizer_configs(self, configs: list[VisualizerConfig]) -> None:
        # Persistence will be implemented in a later step.
        _ = configs
