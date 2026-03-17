from dataclasses import dataclass, field
from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_field_config import VisualizerFieldConfig

@dataclass
class VisualizerConfig:
    enabled: bool = False
    title: str = ""
    filter_string: str = ""
    max_samples: int = 2000
    window_geometry: str | None = None

    x_axis: VisualizerAxisConfig = field(default_factory=VisualizerAxisConfig)
    y_axis: VisualizerAxisConfig = field(default_factory=VisualizerAxisConfig)

    fields: list[VisualizerFieldConfig] = field(default_factory=list)
