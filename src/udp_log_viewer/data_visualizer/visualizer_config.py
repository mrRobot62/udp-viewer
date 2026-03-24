from dataclasses import dataclass, field

from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_field_config import VisualizerFieldConfig


@dataclass(slots=True)
class VisualizerConfig:
    enabled: bool = False
    title: str = ""
    filter_string: str = ""
    max_samples: int = 2000
    window_geometry: str | None = None
    graph_type: str = "plot"  # NEW: "plot" | "logic"

    x_axis: VisualizerAxisConfig = field(default_factory=VisualizerAxisConfig)
    y1_axis: VisualizerAxisConfig = field(default_factory=VisualizerAxisConfig)
    y2_axis: VisualizerAxisConfig = field(default_factory=lambda: VisualizerAxisConfig(label="Y2"))

    fields: list[VisualizerFieldConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = (self.title or "").strip()
        self.filter_string = (self.filter_string or "").strip()
        self.max_samples = self._normalize_max_samples(self.max_samples)

    @property
    def is_routable(self) -> bool:
        return self.enabled and bool(self.filter_string) and bool(self.fields)

    @property
    def y_axis(self) -> VisualizerAxisConfig:
        """Backward-compatible alias for existing single-axis code paths."""
        return self.y1_axis

    @staticmethod
    def _normalize_max_samples(value: int | str | None) -> int:
        try:
            parsed = int(value) if value is not None else 2000
        except (TypeError, ValueError):
            return 2000
        if parsed <= 0:
            return 2000
        return parsed
