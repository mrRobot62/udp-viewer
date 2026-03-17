from dataclasses import dataclass

@dataclass
class VisualizerFieldConfig:
    field_name: str
    numeric: bool = True
    scale: int = 10
    plot: bool = True
    color: str = "blue"
    line_style: str = "solid"
    unit: str = ""
