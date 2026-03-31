from __future__ import annotations

from dataclasses import dataclass


DEFAULT_VISUALIZER_PRESETS = (100, 150, 200, 300)


@dataclass(slots=True)
class AppPreferences:
    language: str = "de"
    autoscroll_default: bool = True
    timestamp_default: bool = True
    max_lines_default: int = 20000
    log_path: str = ""
    visualizer_presets: tuple[int, int, int, int] = DEFAULT_VISUALIZER_PRESETS
    plot_sliding_window_default: bool = True
    plot_window_size_default: int = 200
    logic_sliding_window_default: bool = True
    logic_window_size_default: int = 150

    def __post_init__(self) -> None:
        self.language = (self.language or "de").strip().lower() or "de"
        self.max_lines_default = self._normalize_positive_int(self.max_lines_default, fallback=20000, minimum=1000)
        self.log_path = self._normalize_log_path(self.log_path)
        self.visualizer_presets = self._normalize_presets(self.visualizer_presets)
        self.plot_window_size_default = self._normalize_positive_int(
            self.plot_window_size_default,
            fallback=200,
            minimum=10,
        )
        self.logic_window_size_default = self._normalize_positive_int(
            self.logic_window_size_default,
            fallback=150,
            minimum=10,
        )

    @staticmethod
    def _normalize_positive_int(value: int | str | None, *, fallback: int, minimum: int) -> int:
        try:
            parsed = int(value) if value is not None else fallback
        except (TypeError, ValueError):
            parsed = fallback
        return max(minimum, parsed)

    @staticmethod
    def _normalize_log_path(value: str | None) -> str:
        return (value or "").strip()

    @classmethod
    def _normalize_presets(
        cls,
        values: tuple[int, int, int, int] | list[int] | str | None,
    ) -> tuple[int, int, int, int]:
        if isinstance(values, str):
            raw_parts = [part.strip() for part in values.split(",")]
        elif values is None:
            raw_parts = []
        else:
            raw_parts = [str(part).strip() for part in values]

        parsed: list[int] = []
        for part in raw_parts:
            if not part:
                continue
            try:
                value = int(part)
            except ValueError:
                continue
            if value > 0:
                parsed.append(value)

        if len(parsed) != 4:
            return DEFAULT_VISUALIZER_PRESETS

        parsed = sorted(parsed)
        return tuple(parsed)  # type: ignore[return-value]

    def presets_as_ini(self) -> str:
        return ",".join(str(value) for value in self.visualizer_presets)
