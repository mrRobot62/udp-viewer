from dataclasses import dataclass


@dataclass(slots=True)
class VisualizerFieldConfig:
    field_name: str
    numeric: bool = True
    scale: int = 10
    plot: bool = True
    color: str = "blue"
    line_style: str = "solid"
    unit: str = ""

    def __post_init__(self) -> None:
        self.field_name = (self.field_name or "").strip()
        self.color = (self.color or "blue").strip() or "blue"
        self.line_style = (self.line_style or "solid").strip() or "solid"
        self.unit = (self.unit or "").strip()
        self.scale = self._normalize_scale(self.scale)

    @staticmethod
    def _normalize_scale(value: int | str | None) -> int:
        if value in (None, "", 0, "0"):
            return 1

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 1

        if parsed <= 0:
            return 1

        if parsed > 1000:
            return 1000

        return parsed
