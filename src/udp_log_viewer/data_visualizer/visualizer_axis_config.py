from dataclasses import dataclass

@dataclass
class VisualizerAxisConfig:
    """Configuration container for VisualizerAxis."""
    label: str = ""
    min_value: float | None = None
    max_value: float | None = None
    major_tick_step: float | None = None
    continuous: bool = False
    logarithmic: bool = False
