from dataclasses import dataclass, field


@dataclass(slots=True)
class VisualizerSample:
    timestamp_raw: str
    filter_string: str
    sample_index: int
    values_by_name: dict[str, float | None] = field(default_factory=dict)

    @property
    def has_any_value(self) -> bool:
        return any(value is not None for value in self.values_by_name.values())
