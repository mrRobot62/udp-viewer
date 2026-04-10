from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from .footer_format import normalize_footer_status_format


DEFAULT_VISUALIZER_PRESETS = (100, 150, 200, 300)
FOOTER_PRESET_NAME_MAX_LENGTH = 12
FooterPresetScope = Literal["all", "plot", "logic"]


@dataclass(slots=True, frozen=True)
class FooterStatusPreset:
    name: str
    scope: FooterPresetScope
    format: str


DEFAULT_FOOTER_STATUS_PRESETS = (
    FooterStatusPreset("Compact", "all", "Samples:{samples}  Dauer:{duration}"),
    FooterStatusPreset("Two Lines", "all", "Start:{start} End:{end}\\nSamples:{samples} Dauer:{duration}"),
    FooterStatusPreset("Temperatures", "plot", "Samples:{samples}\\nThot:{Thot}  Tch:{Tch}"),
    FooterStatusPreset("Logic 4", "logic", "Samples:{samples}\\nCH0:{ch0}; CH1:{ch1}; CH2:{ch2}; CH3:{ch3}"),
)


@dataclass(slots=True)
class AppPreferences:
    language: str = "de"
    autoscroll_default: bool = True
    timestamp_default: bool = True
    max_lines_default: int = 20000
    log_path: str = ""
    project_root: str = ""
    visualizer_presets: tuple[int, int, int, int] = DEFAULT_VISUALIZER_PRESETS
    footer_status_presets: tuple[FooterStatusPreset, ...] = DEFAULT_FOOTER_STATUS_PRESETS
    plot_sliding_window_default: bool = True
    plot_window_size_default: int = 200
    logic_sliding_window_default: bool = True
    logic_window_size_default: int = 150

    def __post_init__(self) -> None:
        self.language = (self.language or "de").strip().lower() or "de"
        self.max_lines_default = self._normalize_positive_int(self.max_lines_default, fallback=20000, minimum=1000)
        self.log_path = self._normalize_log_path(self.log_path)
        self.project_root = self._normalize_log_path(self.project_root)
        self.visualizer_presets = self._normalize_presets(self.visualizer_presets)
        self.footer_status_presets = self._normalize_footer_presets(self.footer_status_presets)
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

    @classmethod
    def _normalize_footer_presets(
        cls,
        values: tuple[FooterStatusPreset, ...] | list[FooterStatusPreset] | list[dict[str, str]] | str | None,
    ) -> tuple[FooterStatusPreset, ...]:
        raw_items: list[FooterStatusPreset | dict[str, str]] = []
        if isinstance(values, str):
            try:
                parsed = json.loads(values)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list):
                raw_items = [item for item in parsed if isinstance(item, dict)]
        elif values is not None:
            raw_items = list(values)

        normalized: list[FooterStatusPreset] = []
        seen_names: set[str] = set()
        for item in raw_items:
            if isinstance(item, FooterStatusPreset):
                name = cls._normalize_footer_preset_name(item.name)
                scope = cls._normalize_footer_preset_scope(item.scope)
                fmt = cls._normalize_footer_preset_format(item.format)
            else:
                name = cls._normalize_footer_preset_name(item.get("name", ""))
                scope = cls._normalize_footer_preset_scope(item.get("scope", "all"))
                fmt = cls._normalize_footer_preset_format(item.get("format", ""))
            if not name or not fmt:
                continue
            key = name.casefold()
            if key in seen_names:
                continue
            seen_names.add(key)
            normalized.append(FooterStatusPreset(name=name, scope=scope, format=fmt))

        if not normalized:
            return DEFAULT_FOOTER_STATUS_PRESETS
        return tuple(normalized)

    @staticmethod
    def _normalize_footer_preset_name(value: str | None) -> str:
        return (value or "").strip()[:FOOTER_PRESET_NAME_MAX_LENGTH]

    @staticmethod
    def _normalize_footer_preset_scope(value: str | None) -> FooterPresetScope:
        normalized = (value or "all").strip().lower()
        if normalized not in ("all", "plot", "logic"):
            return "all"
        return normalized  # type: ignore[return-value]

    @staticmethod
    def _normalize_footer_preset_format(value: str | None) -> str:
        raw = str(value or "").strip()
        if raw in {"Start:{start}\\n{stats}", "Start:{start}  Dauer:{duration}\\n{stats}"}:
            return "Start:{start}\\nDauer:{duration}"
        return normalize_footer_status_format(raw)

    def footer_presets_as_ini(self) -> str:
        return json.dumps(
            [{"name": preset.name, "scope": preset.scope, "format": preset.format} for preset in self.footer_status_presets],
            ensure_ascii=True,
        )
