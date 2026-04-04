from dataclasses import dataclass


@dataclass(slots=True)
class VisualizerFieldConfig:
    field_name: str
    numeric: bool = True
    scale: int = 10
    plot: bool = True
    statistic: bool = True
    active: bool = True
    axis: str = "Y1"
    render_style: str = "Line"
    color: str = "blue"
    line_style: str = "solid"
    unit: str = ""

    def __post_init__(self) -> None:
        self.field_name = (self.field_name or "").strip()
        self.axis = self._normalize_axis(self.axis)
        self.render_style = self._normalize_render_style(self.render_style)
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

    @staticmethod
    def _normalize_axis(value: str | None) -> str:
        normalized = (value or "Y1").strip().upper()
        if normalized not in ("Y1", "Y2"):
            return "Y1"
        return normalized

    @staticmethod
    def _normalize_render_style(value: str | None) -> str:
        normalized = (value or "Line").strip().title()
        if normalized not in ("Line", "Step"):
            return "Line"
        return normalized
