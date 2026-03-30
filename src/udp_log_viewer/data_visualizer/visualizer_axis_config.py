from dataclasses import dataclass

@dataclass
class VisualizerAxisConfig:
    label: str = ""
    min_value: float | None = None
    max_value: float | None = None
    major_tick_step: float | None = None
    continuous: bool = False
    logarithmic: bool = False
