from dataclasses import dataclass, field

@dataclass
class VisualizerSample:
    timestamp_raw: str
    filter_string: str
    sample_index: int
    values_by_name: dict[str, float | None] = field(default_factory=dict)
