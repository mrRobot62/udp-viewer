from __future__ import annotations

from pathlib import Path

from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.data_visualizer.logic_visualizer_window import (
    LogicVisualizerWindow,
    build_logic_measurement,
    choose_measurement_label_anchor,
    format_measurement_duration,
    parse_visualizer_timestamp,
)
from udp_log_viewer.data_visualizer.visualizer_sample import VisualizerSample
from udp_log_viewer.data_visualizer.visualizer_window import VisualizerWindow


def _sample(index: int) -> VisualizerSample:
    return VisualizerSample(
        timestamp_raw=f"20260327-12:00:{index:02d}.000",
        sample_index=index,
        filter_string="[CSV_TEMP]",
        values_by_name={"value": float(index)},
    )


def test_config_store_persists_sliding_window_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    store = ConfigStore(config_path=config_path)
    config = ConfigStore._build_default_csv_temp_config()
    config.sliding_window_enabled = False
    config.default_window_size = 123
    config.show_legend = False
    config.y1_axis.major_tick_step = 10.0

    store.save_visualizer_configs([config])
    loaded = store.load_visualizer_configs()[0]

    assert loaded.sliding_window_enabled is False
    assert loaded.default_window_size == 123
    assert loaded.show_legend is False
    assert loaded.y1_axis.major_tick_step == 10.0


def test_default_temperature_tick_step_is_10() -> None:
    config = ConfigStore._build_default_csv_temp_config()
    assert config.y1_axis.major_tick_step == 10.0


def test_config_store_loads_legacy_x_axis_window_as_fallback(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    config_path.write_text(
        "\n".join(
            [
                "[visualizer_1]",
                "enabled = true",
                "title = Legacy",
                "filter_string = [CSV_TEMP]",
                "graph_type = plot",
                "max_samples = 600",
                "x_continuous = false",
                "x_max = 222",
                "field_count = 1",
                "field_0_name = value",
                "field_0_active = true",
                "field_0_numeric = true",
                "field_0_scale = 1",
                "field_0_plot = true",
                "field_0_axis = Y1",
                "field_0_render_style = Line",
                "field_0_color = blue",
                "field_0_line_style = solid",
                "field_0_unit = ",
            ]
        ),
        encoding="utf-8",
    )

    loaded = ConfigStore(config_path=config_path).load_visualizer_configs()[0]

    assert loaded.sliding_window_enabled is False
    assert loaded.default_window_size == 222


def test_plot_window_uses_runtime_sliding_window() -> None:
    config = ConfigStore._build_default_csv_temp_config()
    window = VisualizerWindow(config)
    window.samples = [_sample(index) for index in range(10)]
    window.set_runtime_window_size(4)

    assert [s.sample_index for s in window.get_visible_samples_for_test()] == [6, 7, 8, 9]

    window.set_runtime_sliding_window_enabled(False)

    assert [s.sample_index for s in window.get_visible_samples_for_test()] == list(range(10))


def test_logic_window_uses_runtime_sliding_window() -> None:
    config = ConfigStore._build_default_logic_config()
    window = LogicVisualizerWindow(config)
    window.samples = [_sample(index) for index in range(8)]
    window.set_runtime_window_size(3)

    assert [s.sample_index for s in window.get_visible_samples_for_test()] == [5, 6, 7]


def test_logic_window_reset_restores_config_defaults() -> None:
    config = ConfigStore._build_default_logic_config()
    window = LogicVisualizerWindow(config)

    window.set_runtime_sliding_window_enabled(False)
    window.set_runtime_window_size(100)
    window.reset_runtime_window()

    assert window.runtime_sliding_window_enabled is True
    assert window.runtime_window_size == config.default_window_size


def test_plot_window_runtime_size_is_clamped_to_1_and_5000() -> None:
    config = ConfigStore._build_default_csv_temp_config()
    config.max_samples = 20000
    window = VisualizerWindow(config)

    window.set_runtime_window_size(0)
    assert window.runtime_window_size == config.default_window_size

    window.set_runtime_window_size(6000)
    assert window.runtime_window_size == 5000


def test_logic_window_runtime_size_is_clamped_to_1_and_5000() -> None:
    config = ConfigStore._build_default_logic_config()
    config.max_samples = 20000
    window = LogicVisualizerWindow(config)

    window.set_runtime_window_size(1)
    assert window.runtime_window_size == 1

    window.set_runtime_window_size(9999)
    assert window.runtime_window_size == 5000


def test_logic_measurement_uses_next_edge() -> None:
    samples = [
        VisualizerSample("20260331-12:00:00.000", "[CSV_LOGIC]", 0, {"sig": 0.0}),
        VisualizerSample("20260331-12:00:00.100", "[CSV_LOGIC]", 1, {"sig": 0.0}),
        VisualizerSample("20260331-12:00:00.200", "[CSV_LOGIC]", 2, {"sig": 1.0}),
        VisualizerSample("20260331-12:00:00.350", "[CSV_LOGIC]", 3, {"sig": 1.0}),
        VisualizerSample("20260331-12:00:00.500", "[CSV_LOGIC]", 4, {"sig": 0.0}),
    ]

    measurement = build_logic_measurement(samples, "sig", 0, same_edge_only=False)

    assert measurement is not None
    assert measurement.start_index == 2
    assert measurement.start_edge == "rising"
    assert measurement.end_index == 4
    assert measurement.end_edge == "falling"
    assert measurement.mode == "edge"


def test_logic_measurement_shift_mode_uses_next_same_edge() -> None:
    samples = [
        VisualizerSample("20260331-12:00:00.000", "[CSV_LOGIC]", 0, {"sig": 0.0}),
        VisualizerSample("20260331-12:00:00.100", "[CSV_LOGIC]", 1, {"sig": 1.0}),
        VisualizerSample("20260331-12:00:00.200", "[CSV_LOGIC]", 2, {"sig": 1.0}),
        VisualizerSample("20260331-12:00:00.300", "[CSV_LOGIC]", 3, {"sig": 0.0}),
        VisualizerSample("20260331-12:00:00.400", "[CSV_LOGIC]", 4, {"sig": 0.0}),
        VisualizerSample("20260331-12:00:00.500", "[CSV_LOGIC]", 5, {"sig": 1.0}),
    ]

    measurement = build_logic_measurement(samples, "sig", 0, same_edge_only=True)

    assert measurement is not None
    assert measurement.start_index == 1
    assert measurement.start_edge == "rising"
    assert measurement.end_index == 5
    assert measurement.end_edge == "rising"
    assert measurement.mode == "period"


def test_measurement_duration_formats_minutes_seconds_and_milliseconds() -> None:
    start_time = parse_visualizer_timestamp("20260331-12:00:00.125")
    end_time = parse_visualizer_timestamp("20260331-12:01:02.375")

    assert format_measurement_duration(start_time, end_time) == "01:02.250"


def test_measurement_label_stays_centered_when_span_is_large_enough() -> None:
    label_x, align = choose_measurement_label_anchor(10, 20, "EDGE 00:00.100")

    assert label_x == 15.0
    assert align == "center"


def test_measurement_label_moves_right_of_end_marker_when_span_is_too_small() -> None:
    label_x, align = choose_measurement_label_anchor(10, 12, "EDGE 00:00.100")

    assert label_x > 12
    assert align == "left"
