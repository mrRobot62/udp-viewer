from __future__ import annotations

import configparser
from copy import deepcopy
from pathlib import Path

from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig
from .visualizer_slot import SLOT_COUNT, VisualizerGraphType
from ..preferences import AppPreferences


class ConfigStore:
    DEFAULT_VISUALIZER_COUNT = SLOT_COUNT
    LEGACY_SECTION_PREFIX = "visualizer_"
    SECTION_PREFIXES: dict[VisualizerGraphType, str] = {
        "plot": "plot_visualizer_",
        "logic": "logic_visualizer_",
    }

    def __init__(
        self,
        config_path: str | Path | None = None,
        preferences: AppPreferences | None = None,
    ) -> None:
        self._config_path = Path(config_path) if config_path is not None else None
        self._preferences = preferences or AppPreferences()

    def load_slot_configs(self) -> dict[VisualizerGraphType, list[VisualizerConfig]]:
        configs = self._build_default_slot_config_map()
        parser = self._read_parser()
        if parser is None:
            return configs

        has_new_schema = False
        for graph_type, prefix in self.SECTION_PREFIXES.items():
            defaults = self._default_config_for_type(graph_type)
            for index in range(self.DEFAULT_VISUALIZER_COUNT):
                section = f"{prefix}{index + 1}"
                if not parser.has_section(section):
                    continue
                has_new_schema = True
                configs[graph_type][index] = self._load_single_config(parser, section, defaults)

        if has_new_schema:
            return configs

        legacy_configs = self._load_legacy_slot_configs(parser)
        if any(config.enabled and config.filter_string for config in legacy_configs["plot"] + legacy_configs["logic"]):
            return legacy_configs
        return configs

    def save_slot_configs(self, configs_by_type: dict[VisualizerGraphType, list[VisualizerConfig]]) -> None:
        if self._config_path is None:
            return

        parser = self._read_parser() or configparser.ConfigParser()
        self._remove_owned_sections(parser)

        for graph_type, prefix in self.SECTION_PREFIXES.items():
            slot_configs = list(configs_by_type.get(graph_type, []))
            for index, config in enumerate(slot_configs[: self.DEFAULT_VISUALIZER_COUNT]):
                if self._is_empty_config(config):
                    continue
                section = f"{prefix}{index + 1}"
                self._save_single_config(parser, section, config, graph_type=graph_type)

        self._write_parser(parser)

    def load_visualizer_configs(self) -> list[VisualizerConfig]:
        return self.load_slot_configs()["plot"]

    def save_visualizer_configs(self, configs: list[VisualizerConfig]) -> None:
        slot_configs = self.load_slot_configs()
        slot_configs["plot"] = list(configs[: self.DEFAULT_VISUALIZER_COUNT]) + [
            self._build_empty_config("plot")
            for _ in range(max(0, self.DEFAULT_VISUALIZER_COUNT - len(configs)))
        ]
        self.save_slot_configs(slot_configs)

    def _build_empty_slot_config_map(self) -> dict[VisualizerGraphType, list[VisualizerConfig]]:
        return {
            "plot": [self._build_empty_config("plot") for _ in range(self.DEFAULT_VISUALIZER_COUNT)],
            "logic": [self._build_empty_config("logic") for _ in range(self.DEFAULT_VISUALIZER_COUNT)],
        }

    def _build_default_slot_config_map(self) -> dict[VisualizerGraphType, list[VisualizerConfig]]:
        configs = self._build_empty_slot_config_map()
        configs["plot"][0] = self._build_default_csv_temp_config(self._preferences)
        configs["plot"][1] = self._build_default_csv_host_plot_config(self._preferences)
        configs["logic"][0] = self._build_default_logic_config(self._preferences)
        return configs

    def _load_legacy_slot_configs(
        self,
        parser: configparser.ConfigParser,
    ) -> dict[VisualizerGraphType, list[VisualizerConfig]]:
        configs = self._build_empty_slot_config_map()
        next_index = {"plot": 0, "logic": 0}

        for index in range(self.DEFAULT_VISUALIZER_COUNT):
            section = f"{self.LEGACY_SECTION_PREFIX}{index + 1}"
            if not parser.has_section(section):
                continue

            graph_type = parser.get(section, "graph_type", fallback="plot").strip().lower()
            if graph_type not in self.SECTION_PREFIXES:
                graph_type = "plot"
            typed_graph_type: VisualizerGraphType = graph_type  # type: ignore[assignment]
            target_index = next_index[typed_graph_type]
            if target_index >= self.DEFAULT_VISUALIZER_COUNT:
                continue

            base = self._default_config_for_type(typed_graph_type)
            configs[typed_graph_type][target_index] = self._load_single_config(parser, section, base)
            next_index[typed_graph_type] += 1

        return configs

    def _remove_owned_sections(self, parser: configparser.ConfigParser) -> None:
        for section in list(parser.sections()):
            if section.startswith(self.LEGACY_SECTION_PREFIX):
                parser.remove_section(section)
                continue
            if any(section.startswith(prefix) for prefix in self.SECTION_PREFIXES.values()):
                parser.remove_section(section)

    def _save_single_config(
        self,
        parser: configparser.ConfigParser,
        section: str,
        config: VisualizerConfig,
        *,
        graph_type: VisualizerGraphType,
    ) -> None:
        parser.add_section(section)

        parser.set(section, "enabled", str(bool(config.enabled)).lower())
        parser.set(section, "title", config.title)
        parser.set(section, "filter_string", config.filter_string)
        parser.set(section, "footer_status_format", config.footer_status_format)
        parser.set(section, "show_legend", str(bool(config.show_legend)).lower())
        parser.set(section, "graph_type", graph_type)
        parser.set(section, "max_samples", str(config.max_samples))
        parser.set(section, "sliding_window_enabled", str(bool(config.sliding_window_enabled)).lower())
        parser.set(section, "default_window_size", str(config.default_window_size))
        parser.set(section, "window_geometry", config.window_geometry or "")

        parser.set(section, "x_label", config.x_axis.label)
        parser.set(section, "x_continuous", str(bool(config.x_axis.continuous)).lower())
        parser.set(section, "x_min", "" if config.x_axis.min_value is None else str(config.x_axis.min_value))
        parser.set(section, "x_max", "" if config.x_axis.max_value is None else str(config.x_axis.max_value))

        parser.set(section, "y1_label", config.y1_axis.label)
        parser.set(section, "y1_logarithmic", str(bool(config.y1_axis.logarithmic)).lower())
        parser.set(section, "y1_min", "" if config.y1_axis.min_value is None else str(config.y1_axis.min_value))
        parser.set(section, "y1_max", "" if config.y1_axis.max_value is None else str(config.y1_axis.max_value))
        parser.set(
            section,
            "y1_major_tick_step",
            "" if config.y1_axis.major_tick_step is None else str(config.y1_axis.major_tick_step),
        )

        parser.set(section, "y2_label", config.y2_axis.label)
        parser.set(section, "y2_logarithmic", str(bool(config.y2_axis.logarithmic)).lower())
        parser.set(section, "y2_min", "" if config.y2_axis.min_value is None else str(config.y2_axis.min_value))
        parser.set(section, "y2_max", "" if config.y2_axis.max_value is None else str(config.y2_axis.max_value))
        parser.set(
            section,
            "y2_major_tick_step",
            "" if config.y2_axis.major_tick_step is None else str(config.y2_axis.major_tick_step),
        )

        parser.set(section, "field_count", str(len(config.fields)))
        for field_index, field in enumerate(config.fields):
            prefix = f"field_{field_index}_"
            parser.set(section, f"{prefix}name", field.field_name)
            parser.set(section, f"{prefix}active", str(bool(field.active)).lower())
            parser.set(section, f"{prefix}numeric", str(bool(field.numeric)).lower())
            parser.set(section, f"{prefix}scale", str(field.scale))
            parser.set(section, f"{prefix}plot", str(bool(field.plot)).lower())
            parser.set(section, f"{prefix}statistic", str(bool(field.statistic)).lower())
            parser.set(section, f"{prefix}axis", field.axis)
            parser.set(section, f"{prefix}render_style", field.render_style)
            parser.set(section, f"{prefix}color", field.color)
            parser.set(section, f"{prefix}line_style", field.line_style)
            parser.set(section, f"{prefix}unit", field.unit)

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
                    statistic=self._get_bool(parser, section, f"{prefix}statistic", default=True),
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
            major_tick_step=self._get_float_or_none(
                parser,
                section,
                "y1_major_tick_step",
                default=base_config.y1_axis.major_tick_step,
            ),
        )
        y2_axis = VisualizerAxisConfig(
            label=parser.get(section, "y2_label", fallback=base_config.y2_axis.label),
            logarithmic=self._get_bool(parser, section, "y2_logarithmic", default=base_config.y2_axis.logarithmic),
            min_value=self._get_float_or_none(parser, section, "y2_min", default=base_config.y2_axis.min_value),
            max_value=self._get_float_or_none(parser, section, "y2_max", default=base_config.y2_axis.max_value),
            major_tick_step=self._get_float_or_none(
                parser,
                section,
                "y2_major_tick_step",
                default=base_config.y2_axis.major_tick_step,
            ),
        )

        max_samples = self._get_int(parser, section, "max_samples", default=base_config.max_samples)
        legacy_sliding_enabled = self._get_bool(
            parser,
            section,
            "x_continuous",
            default=base_config.sliding_window_enabled,
        )
        legacy_window_size = self._get_int(
            parser,
            section,
            "x_max",
            default=base_config.default_window_size,
        )

        config = VisualizerConfig(
            enabled=self._get_bool(parser, section, "enabled", default=base_config.enabled),
            title=parser.get(section, "title", fallback=base_config.title),
            filter_string=parser.get(section, "filter_string", fallback=base_config.filter_string),
            footer_status_format=parser.get(section, "footer_status_format", fallback=base_config.footer_status_format),
            show_legend=self._get_bool(parser, section, "show_legend", default=base_config.show_legend),
            graph_type=parser.get(section, "graph_type", fallback=getattr(base_config, "graph_type", "plot")),
            max_samples=max_samples,
            sliding_window_enabled=self._get_bool(
                parser,
                section,
                "sliding_window_enabled",
                default=legacy_sliding_enabled,
            ),
            default_window_size=self._get_int(
                parser,
                section,
                "default_window_size",
                default=legacy_window_size,
            ),
            window_geometry=parser.get(section, "window_geometry", fallback=base_config.window_geometry or "") or None,
            x_axis=x_axis,
            y1_axis=y1_axis,
            y2_axis=y2_axis,
            fields=fields or list(base_config.fields),
        )
        return self._normalize_loaded_plot_config(config)

    @staticmethod
    def _normalize_loaded_plot_config(config: VisualizerConfig) -> VisualizerConfig:
        if config.graph_type != "plot":
            return config
        legacy_filter_aliases = {
            "[CSV_CLIENT_TEMP]": "[CSV_CLIENT_PLOT]",
            "[CSV_HOST_TEMP]": "[CSV_HOST_PLOT]",
            "CSV_CLIENT_TEMP": "CSV_CLIENT_PLOT",
            "CSV_HOST_TEMP": "CSV_HOST_PLOT",
        }
        config.filter_string = legacy_filter_aliases.get(config.filter_string, config.filter_string)
        if config.filter_string == "[CSV_HOST_PLOT]":
            field_names = [field.field_name.strip().lower() for field in config.fields]
            legacy_host_names = ["chamber", "hotspot", "target", "chamber_min", "chamber_max", "state"]
            compact_host_names = ["tch", "thot", "target", "temp_range", "state"]
            if field_names in (legacy_host_names, compact_host_names):
                config.fields = [
                    VisualizerFieldConfig("Tch", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="blue", line_style="solid", unit="°C"),
                    VisualizerFieldConfig("Thot", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="red", line_style="solid", unit="°C"),
                    VisualizerFieldConfig("target", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="green", line_style="solid", unit="°C"),
                    VisualizerFieldConfig("target_min", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="black", line_style="dashed", unit=""),
                    VisualizerFieldConfig("target_max", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="gray", line_style="solid", unit=""),
                    VisualizerFieldConfig("state", active=False, numeric=True, scale=1, plot=False, axis="Y2", render_style="Step", color="gray", line_style="dotted", unit=""),
                ]
                config.y1_axis.label = config.y1_axis.label or "Temperature"
                config.y2_axis.label = config.y2_axis.label or "State"
                if config.y2_axis.min_value is None:
                    config.y2_axis.min_value = -0.1
                if config.y2_axis.max_value is None:
                    config.y2_axis.max_value = 3.1
        return config

    def _default_config_for_type(self, graph_type: VisualizerGraphType) -> VisualizerConfig:
        if graph_type == "logic":
            return self._build_default_logic_config(self._preferences)
        return self._build_default_csv_temp_config(self._preferences)

    @staticmethod
    def _build_empty_config(graph_type: VisualizerGraphType) -> VisualizerConfig:
        return VisualizerConfig(enabled=False, graph_type=graph_type)

    @staticmethod
    def _is_empty_config(config: VisualizerConfig) -> bool:
        return (
            not config.enabled
            and not config.title
            and not config.filter_string
            and not config.footer_status_format
            and not config.window_geometry
            and not config.fields
        )

    def _read_parser(self) -> configparser.ConfigParser | None:
        if self._config_path is None or not self._config_path.exists():
            return None
        parser = configparser.ConfigParser()
        parser.read(self._config_path, encoding="utf-8")
        return parser

    def _write_parser(self, parser: configparser.ConfigParser) -> None:
        if self._config_path is None:
            return
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8", newline="\n") as handle:
            parser.write(handle)

    @staticmethod
    def clone_config(config: VisualizerConfig) -> VisualizerConfig:
        return deepcopy(config)

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
    def _build_default_csv_temp_config(preferences: AppPreferences | None = None) -> VisualizerConfig:
        prefs = preferences or AppPreferences()
        return VisualizerConfig(
            enabled=True,
            title="CSV_CLIENT_PLOT Graph",
            filter_string="[CSV_CLIENT_PLOT]",
            show_legend=True,
            graph_type="plot",
            max_samples=600,
            sliding_window_enabled=prefs.plot_sliding_window_default,
            default_window_size=prefs.plot_window_size_default,
            x_axis=VisualizerAxisConfig(
                label="Samples",
                continuous=True,
                max_value=float(prefs.plot_window_size_default),
            ),
            y1_axis=VisualizerAxisConfig(label="Temperature", min_value=0.0, max_value=160.0, major_tick_step=10.0),
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
    def _build_default_csv_host_plot_config(preferences: AppPreferences | None = None) -> VisualizerConfig:
        prefs = preferences or AppPreferences()
        return VisualizerConfig(
            enabled=True,
            title="CSV_HOST_PLOT Graph",
            filter_string="[CSV_HOST_PLOT]",
            show_legend=True,
            graph_type="plot",
            max_samples=600,
            sliding_window_enabled=prefs.plot_sliding_window_default,
            default_window_size=prefs.plot_window_size_default,
            x_axis=VisualizerAxisConfig(
                label="Samples",
                continuous=True,
                max_value=float(prefs.plot_window_size_default),
            ),
            y1_axis=VisualizerAxisConfig(label="Temperature", min_value=0.0, max_value=160.0, major_tick_step=10.0),
            y2_axis=VisualizerAxisConfig(label="State", min_value=-0.1, max_value=3.1),
            fields=[
                VisualizerFieldConfig("Tch", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="blue", line_style="solid", unit="°C"),
                VisualizerFieldConfig("Thot", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="red", line_style="solid", unit="°C"),
                VisualizerFieldConfig("target", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="green", line_style="solid", unit="°C"),
                VisualizerFieldConfig("target_min", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="black", line_style="dashed", unit=""),
                VisualizerFieldConfig("target_max", active=True, numeric=True, scale=10, plot=True, axis="Y1", render_style="Line", color="gray", line_style="solid", unit=""),
                VisualizerFieldConfig("state", active=False, numeric=True, scale=1, plot=False, axis="Y2", render_style="Step", color="green", line_style="dashdot", unit=""),
            ],
        )

    @staticmethod
    def _build_default_logic_config(preferences: AppPreferences | None = None) -> VisualizerConfig:
        prefs = preferences or AppPreferences()
        return VisualizerConfig(
            enabled=True,
            title="Logic Graph",
            filter_string="[CSV_CLIENT_LOGIC]",
            show_legend=False,
            graph_type="logic",
            max_samples=600,
            sliding_window_enabled=prefs.logic_sliding_window_default,
            default_window_size=prefs.logic_window_size_default,
            x_axis=VisualizerAxisConfig(
                label="Samples",
                continuous=True,
                max_value=float(prefs.logic_window_size_default),
            ),
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
