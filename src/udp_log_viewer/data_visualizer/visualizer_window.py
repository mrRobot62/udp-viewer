from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample


class VisualizerWindow:
    def __init__(self, config: VisualizerConfig) -> None:
        self.config = config
        self.samples: list[VisualizerSample] = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index: int | None = None
        self.refresh_request_count = 0
        self.rebuild_request_count = 0

    def append_sample(self, sample: VisualizerSample) -> None:
        self.samples.append(sample)
        self._trim_samples_if_needed()

        if self.auto_refresh_enabled:
            self.refresh_plot()

    def set_auto_refresh(self, enabled: bool) -> None:
        self.auto_refresh_enabled = enabled

        if enabled:
            self.freeze_sample_index = None
            self.rebuild_plot()
            return

        self.freeze_sample_index = len(self.samples)

    def refresh_plot(self) -> None:
        self.refresh_request_count += 1

    def rebuild_plot(self) -> None:
        self.rebuild_request_count += 1

    def _trim_samples_if_needed(self) -> None:
        max_samples = self.config.max_samples
        if len(self.samples) <= max_samples:
            return

        overflow = len(self.samples) - max_samples
        del self.samples[:overflow]

        if self.freeze_sample_index is not None:
            self.freeze_sample_index = max(0, self.freeze_sample_index - overflow)
