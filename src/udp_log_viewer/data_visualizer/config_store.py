from __future__ import annotations

import configparser
from pathlib import Path

from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig


class ConfigStore:
    DEFAULT_VISUALIZER_COUNT = 5
    SECTION_PREFIX = "visualizer_"

    def __init__(self, config_path: str | Path | None = None) -> None:
        self._config_path = Path(config_path) if config_path is not None else None

    def load_visualizer_configs(self) -> list[VisualizerConfig]:
        configs = [VisualizerConfig() for _ in range(self.DEFAULT_VISUALIZER_COUNT)]
        configs[0] = self._build_default_csv_temp_config()

        if self._config_path is None or not self._config_path.exists():
            return configs

        parser = configparser.ConfigParser()
        parser.read(self._config_path, encoding="utf-8")

        for index in range(self.DEFAULT_VISUALIZER_COUNT):
            section = f"{self.SECTION_PREFIX}{index + 1}"
            if not parser.has_section(section):
                continue
            configs[index] = self._load_single_config(parser, section, configs[index])

        return configs

    def save_visualizer_configs(self, configs: list[VisualizerConfig]) -> None:
        if self._config_path is None:
            return

        parser = configparser.ConfigParser()

        for index, config in enumerate(configs[: self.DEFAULT_VISUALIZER_COUNT]):
            section = f"{self.SECTION_PREFIX}{index + 1}"
            parser.add_section(section)

            parser.set(section, "enabled", str(bool(config.enabled)).lower())
            parser.set(section, "title", config.title)
            parser.set(section, "filter_string", config.filter_string)
            parser.set(section, "graph_type", getattr(config, "graph_type", "plot"))
            parser.set(section, "max_samples", str(config.max_samples))
            parser.set(section, "window_geometry", config.window_geometry or "")

            parser.set(section, "x_label", config.x_axis.label)
            parser.set(section, "x_continuous", str(bool(config.x_axis.continuous)).lower())
            parser.set(section, "x_min", "" if config.x_axis.min_value is None else str(config.x_axis.min_value))
            parser.set(section, "x_max", "" if config.x_axis.max_value is None else str(config.x_axis.max_value))

            parser.set(section, "y1_label", config.y1_axis.label)
            parser.set(section, "y1_logarithmic", str(bool(config.y1_axis.logarithmic)).lower())
            parser.set(section, "y1_min", "" if config.y1_axis.min_value is None else str(config.y1_axis.min_value))
            parser.set(section, "y1_max", "" if config.y1_axis.max_value is None else str(config.y1_axis.max_value))

            parser.set(section, "y2_label", config.y2_axis.label)
            parser.set(section, "y2_logarithmic", str(bool(config.y2_axis.logarithmic)).lower())
            parser.set(section, "y2_min", "" if config.y2_axis.min_value is None else str(config.y2_axis.min_value))
            parser.set(section, "y2_max", "" if config.y2_axis.max_value is None else str(config.y2_axis.max_value))

            parser.set(section, "field_count", str(len(config.fields)))
            for field_index, field in enumerate(config.fields):
                prefix = f"field_{field_index}_"
                parser.set(section, f"{prefix}name", field.field_name)
                parser.set(section, f"{prefix}active", str(bool(field.active)).lower())
                parser.set(section, f"{prefix}numeric", str(bool(field.numeric)).lower())
                parser.set(section, f"{prefix}scale", str(field.scale))
                parser.set(section, f"{prefix}plot", str(bool(field.plot)).lower())
                parser.set(section, f"{prefix}axis", field.axis)
                parser.set(section, f"{prefix}render_style", field.render_style)
                parser.set(section, f"{prefix}color", field.color)
                parser.set(section, f"{prefix}line_style", field.line_style)
                parser.set(section, f"{prefix}unit", field.unit)

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8", newline="\n") as handle:
            parser.write(handle)

    def _load_single_config(
        self,
        parser: configparser.ConfigParser,
        section: str,
        base_config: VisualizerConfig,
    ) -> VisualizerConfig:
        fields: list[VisualizerFieldConfig] = []
        field_count = self._get_int(parser, section, "field_count", default=len(base_config.fields))

        for field_index in range(field_count):
            prefix = f"field_{field_index}_"
            field_name = parser.get(section, f"{prefix}name", fallback="")
            if not field_name.strip():
                continue

            fields.append(
                VisualizerFieldConfig(
                    field_name=field_name,
                    active=self._get_bool(parser, section, f"{prefix}active", default=True),
                    numeric=self._get_bool(parser, section, f"{prefix}numeric", default=True),
                    scale=self._get_int(parser, section, f"{prefix}scale", default=10),
                    plot=self._get_bool(parser, section, f"{prefix}plot", default=True),
                    axis=parser.get(section, f"{prefix}axis", fallback="Y1"),
                    render_style=parser.get(section, f"{prefix}render_style", fallback="Line"),
                    color=parser.get(section, f"{prefix}color", fallback="blue"),
                    line_style=parser.get(section, f"{prefix}line_style", fallback="solid"),
                    unit=parser.get(section, f"{prefix}unit", fallback=""),
                )
            )

        x_axis = VisualizerAxisConfig(
            label=parser.get(section, "x_label", fallback=base_config.x_axis.label),
            continuous=self._get_bool(parser, section, "x_continuous", default=base_config.x_axis.continuous),
            min_value=self._get_float_or_none(parser, section, "x_min", default=base_config.x_axis.min_value),
            max_value=self._get_float_or_none(parser, section, "x_max", default=base_config.x_axis.max_value),
        )
        y1_axis = VisualizerAxisConfig(
            label=parser.get(section, "y1_label", fallback=base_config.y1_axis.label),
            logarithmic=self._get_bool(parser, section, "y1_logarithmic", default=base_config.y1_axis.logarithmic),
            min_value=self._get_float_or_none(parser, section, "y1_min", default=base_config.y1_axis.min_value),
            max_value=self._get_float_or_none(parser, section, "y1_max", default=base_config.y1_axis.max_value),
        )
        y2_axis = VisualizerAxisConfig(
            label=parser.get(section, "y2_label", fallback=base_config.y2_axis.label),
            logarithmic=self._get_bool(parser, section, "y2_logarithmic", default=base_config.y2_axis.logarithmic),
            min_value=self._get_float_or_none(parser, section, "y2_min", default=base_config.y2_axis.min_value),
            max_value=self._get_float_or_none(parser, section, "y2_max", default=base_config.y2_axis.max_value),
        )

        return VisualizerConfig(
            enabled=self._get_bool(parser, section, "enabled", default=base_config.enabled),
            title=parser.get(section, "title", fallback=base_config.title),
            filter_string=parser.get(section, "filter_string", fallback=base_config.filter_string),
            graph_type=parser.get(section, "graph_type", fallback=getattr(base_config, "graph_type", "plot")),
            max_samples=self._get_int(parser, section, "max_samples", default=base_config.max_samples),
            window_geometry=parser.get(section, "window_geometry", fallback=base_config.window_geometry or "") or None,
            x_axis=x_axis,
            y1_axis=y1_axis,
            y2_axis=y2_axis,
            fields=fields or list(base_config.fields),
        )

    @staticmethod
    def _get_bool(parser: configparser.ConfigParser, section: str, key: str, default: bool) -> bool:
        try:
            return parser.getboolean(section, key, fallback=default)
        except ValueError:
            return default

    @staticmethod
    def _get_int(parser: configparser.ConfigParser, section: str, key: str, default: int) -> int:
        try:
            return parser.getint(section, key, fallback=default)
        except ValueError:
            return default

    @staticmethod
    def _get_float_or_none(
        parser: configparser.ConfigParser,
        section: str,
        key: str,
        default: float | None,
    ) -> float | None:
        raw = parser.get(section, key, fallback="")
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    @staticmethod
    def _build_default_csv_temp_config() -> VisualizerConfig:
        return VisualizerConfig(
            enabled=True,
            title="CSV_TEMP Graph",
            filter_string="[CSV_TEMP]",
            graph_type="plot",
            max_samples=600,
            x_axis=VisualizerAxisConfig(label="Samples", continuous=True, max_value=300),
            y1_axis=VisualizerAxisConfig(label="Temperature", min_value=0.0, max_value=160.0),
            y2_axis=VisualizerAxisConfig(label="State", min_value=-0.1, max_value=3.1),
            fields=[
                VisualizerFieldConfig("rawHot", active=True, numeric=True, scale=1, plot=False, axis="Y1", render_style="Line", color="black", line_style="solid", unit="raw"),
                VisualizerFieldConfig("hot_mV", active=True, numeric=True, scale=1, plot=False, axis="Y1", render_style="Line", color="gray", line_style="solid", unit="mV"),
                VisualizerFieldConfig("Thot", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="red", line_style="solid", unit="°C"),
                VisualizerFieldConfig("rawChamber", active=True, numeric=True, scale=1, plot=False, axis="Y1", render_style="Line", color="black", line_style="dashed", unit="raw"),
                VisualizerFieldConfig("chamberMilliVolts", active=True, numeric=True, scale=1, plot=False, axis="Y1", render_style="Line", color="gray", line_style="dashed", unit="mV"),
                VisualizerFieldConfig("Tch", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="blue", line_style="dashed", unit="°C"),
                VisualizerFieldConfig("heater_on", active=False, numeric=True, scale=1, plot=False, axis="Y2", render_style="Step", color="orange", line_style="dotted", unit="Bool"),
                VisualizerFieldConfig("door_open", active=False, numeric=True, scale=1, plot=False, axis="Y2", render_style="Step", color="purple", line_style="dotted", unit="Bool"),
                VisualizerFieldConfig("state", active=False, numeric=True, scale=1, plot=False, axis="Y2", render_style="Step", color="green", line_style="dashdot", unit=""),
            ],
        )

    @staticmethod
    def _build_default_logic_config() -> VisualizerConfig:
        return VisualizerConfig(
            enabled=True,
            title="Logic Graph",
            filter_string="[CSV_LOGIC]",
            graph_type="logic",
            max_samples=600,
            x_axis=VisualizerAxisConfig(label="Samples", continuous=True, max_value=300),
            y1_axis=VisualizerAxisConfig(label="Logic", min_value=0.0, max_value=1.0),
            y2_axis=VisualizerAxisConfig(label="Y2", min_value=0.0, max_value=1.0),
            fields=[
                VisualizerFieldConfig("ch0", active=True, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="red", line_style="solid", unit=""),
                VisualizerFieldConfig("ch1", active=True, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="blue", line_style="solid", unit=""),
                VisualizerFieldConfig("ch2", active=True, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="green", line_style="solid", unit=""),
                VisualizerFieldConfig("ch3", active=True, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="orange", line_style="solid", unit=""),
                VisualizerFieldConfig("ch4", active=False, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="purple", line_style="solid", unit=""),
                VisualizerFieldConfig("ch5", active=False, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="black", line_style="solid", unit=""),
                VisualizerFieldConfig("ch6", active=False, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="gray", line_style="solid", unit=""),
                VisualizerFieldConfig("ch7", active=False, numeric=True, scale=1, plot=True, axis="Y1", render_style="Step", color="red", line_style="dashed", unit=""),
            ],
        )