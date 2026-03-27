from __future__ import annotations

from pathlib import Path

from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.data_visualizer.logic_visualizer_window import LogicVisualizerWindow
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

    store.save_visualizer_configs([config])
    loaded = store.load_visualizer_configs()[0]

    assert loaded.sliding_window_enabled is False
    assert loaded.default_window_size == 123


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
