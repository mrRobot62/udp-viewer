from __future__ import annotations

from pathlib import Path

from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.data_visualizer.logic_visualizer_window import (
    LogicVisualizerWindow,
    _LogicVisualizerWindowWidget,
    build_logic_measurement,
    choose_measurement_label_anchor,
    format_measurement_duration,
    parse_visualizer_timestamp,
)
from udp_log_viewer.data_visualizer.visualizer_sample import VisualizerSample
from udp_log_viewer.data_visualizer.visualizer_window import (
    VisualizerWindow,
    PlotMeasurement,
    _VisualizerWindowWidget,
    advance_plot_measurement,
    choose_plot_measurement_label_anchor,
    format_plot_measurement_duration,
    parse_plot_timestamp,
)


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


def test_plot_measurement_duration_formats_minutes_seconds_and_hundredths() -> None:
    start_time = parse_plot_timestamp("20260331-12:00:00.125")
    end_time = parse_plot_timestamp("20260331-12:01:02.375")

    assert format_plot_measurement_duration(start_time, end_time) == "01:02.25"


def test_plot_measurement_click_cycle_restarts_after_completed_measurement() -> None:
    measurement = advance_plot_measurement(None, 4)
    measurement = advance_plot_measurement(measurement, 9)
    measurement = advance_plot_measurement(measurement, 2)

    assert measurement == PlotMeasurement(start_index=2, end_index=None)


def test_plot_measurement_label_moves_right_of_later_marker_when_span_is_too_small() -> None:
    label_x, align = choose_plot_measurement_label_anchor(12, 10, "A-B 00:00.10")

    assert label_x > 12
    assert align == "left"


def test_plot_measurement_pause_and_resume_force_auto_refresh() -> None:
    class _DummyController:
        def __init__(self) -> None:
            self.auto_refresh_enabled = True
            self.freeze_sample_index = None
            self.samples = [_sample(index) for index in range(3)]
            self.calls: list[bool] = []

        def set_auto_refresh(self, enabled: bool) -> None:
            self.calls.append(enabled)
            self.auto_refresh_enabled = enabled
            self.freeze_sample_index = None if enabled else len(self.samples)

    class _DummyWidget:
        def __init__(self) -> None:
            self._controller = _DummyController()
            self._measurement = PlotMeasurement(start_index=0, end_index=1)
            self.rendered = False
            self.checkbox_states: list[bool] = []

        def _render_plot(self) -> None:
            self.rendered = True

        def _set_auto_refresh_checkbox_state(self, enabled: bool) -> None:
            self.checkbox_states.append(enabled)

    widget = _DummyWidget()

    _VisualizerWindowWidget._pause_for_measurement(widget)
    assert widget._controller.calls == [False]
    assert widget._controller.auto_refresh_enabled is False
    assert widget.checkbox_states == [False]

    _VisualizerWindowWidget._clear_measurement(widget, resume=True)
    assert widget._controller.calls == [False, True]
    assert widget._controller.auto_refresh_enabled is True
    assert widget.checkbox_states == [False, True]


def test_plot_sync_runtime_controls_updates_auto_refresh_checkbox() -> None:
    class _DummyCheckbox:
        def __init__(self) -> None:
            self.checked = None
            self.block_calls: list[bool] = []

        def blockSignals(self, value: bool) -> None:
            self.block_calls.append(value)

        def setChecked(self, value: bool) -> None:
            self.checked = value

    class _DummySpin:
        def __init__(self) -> None:
            self.block_calls: list[bool] = []
            self.range_values = None
            self.value = None
            self.enabled = None

        def blockSignals(self, value: bool) -> None:
            self.block_calls.append(value)

        def setRange(self, minimum: int, maximum: int) -> None:
            self.range_values = (minimum, maximum)

        def setValue(self, value: int) -> None:
            self.value = value

        def setEnabled(self, enabled: bool) -> None:
            self.enabled = enabled

    class _DummyController:
        def __init__(self) -> None:
            self.auto_refresh_enabled = True
            self.runtime_sliding_window_enabled = False
            self.runtime_show_legend = True
            self.runtime_window_size = 123
            self.config = type("Cfg", (), {"max_samples": 500})()

    class _DummyWidget:
        def __init__(self) -> None:
            self._controller = _DummyController()
            self._auto_refresh_checkbox = _DummyCheckbox()
            self._sliding_window_checkbox = _DummyCheckbox()
            self._legend_checkbox = _DummyCheckbox()
            self._window_size_spin = _DummySpin()

    widget = _DummyWidget()

    _VisualizerWindowWidget._sync_runtime_controls(widget)

    assert widget._auto_refresh_checkbox.checked is True
    assert widget._auto_refresh_checkbox.block_calls == [True, False]


def test_plot_measurement_checkbox_state_updates_immediately() -> None:
    class _DummyCheckbox:
        def __init__(self) -> None:
            self.checked = None
            self.block_calls: list[bool] = []

        def blockSignals(self, value: bool) -> None:
            self.block_calls.append(value)

        def setChecked(self, value: bool) -> None:
            self.checked = value

    class _DummyController:
        def __init__(self) -> None:
            self.auto_refresh_enabled = True
            self.freeze_sample_index = None
            self.samples = [_sample(index) for index in range(2)]

        def set_auto_refresh(self, enabled: bool) -> None:
            self.auto_refresh_enabled = enabled
            self.freeze_sample_index = None if enabled else len(self.samples)

    class _DummyWidget:
        def __init__(self) -> None:
            self._controller = _DummyController()
            self._auto_refresh_checkbox = _DummyCheckbox()
            self._measurement = PlotMeasurement(start_index=0, end_index=1)

        def _set_auto_refresh_checkbox_state(self, enabled: bool) -> None:
            _VisualizerWindowWidget._set_auto_refresh_checkbox_state(self, enabled)

    widget = _DummyWidget()

    _VisualizerWindowWidget._pause_for_measurement(widget)
    assert widget._auto_refresh_checkbox.checked is False

    _VisualizerWindowWidget._clear_measurement(widget, resume=True)
    assert widget._auto_refresh_checkbox.checked is True


def test_plot_measurement_escape_shortcut_clears_active_measurement() -> None:
    class _DummyWidget:
        def __init__(self) -> None:
            self._measurement = PlotMeasurement(start_index=1, end_index=None)
            self.resume_calls: list[bool] = []

        def _clear_measurement(self, *, resume: bool) -> None:
            self.resume_calls.append(resume)

    widget = _DummyWidget()

    _VisualizerWindowWidget._on_escape_shortcut(widget)

    assert widget.resume_calls == [True]


def test_plot_space_shortcut_toggles_auto_refresh_checkbox() -> None:
    class _DummyCheckbox:
        def __init__(self, checked: bool) -> None:
            self._checked = checked

        def isChecked(self) -> bool:
            return self._checked

        def setChecked(self, value: bool) -> None:
            self._checked = value

    class _DummyWidget:
        def __init__(self) -> None:
            self._auto_refresh_checkbox = _DummyCheckbox(True)

    widget = _DummyWidget()

    _VisualizerWindowWidget._on_space_shortcut(widget)
    assert widget._auto_refresh_checkbox.isChecked() is False

    _VisualizerWindowWidget._on_space_shortcut(widget)
    assert widget._auto_refresh_checkbox.isChecked() is True


def test_logic_measurement_pause_and_resume_force_auto_refresh() -> None:
    class _DummyController:
        def __init__(self) -> None:
            self.auto_refresh_enabled = True
            self.freeze_sample_index = None
            self.samples = [_sample(index) for index in range(3)]
            self.calls: list[bool] = []

        def set_auto_refresh(self, enabled: bool) -> None:
            self.calls.append(enabled)
            self.auto_refresh_enabled = enabled
            self.freeze_sample_index = None if enabled else len(self.samples)

    class _DummyWidget:
        def __init__(self) -> None:
            self._controller = _DummyController()
            self._measurement = object()
            self.checkbox_states: list[bool] = []

        def _set_auto_refresh_checkbox_state(self, enabled: bool) -> None:
            self.checkbox_states.append(enabled)

    widget = _DummyWidget()

    _LogicVisualizerWindowWidget._pause_for_measurement(widget)
    assert widget._controller.calls == [False]
    assert widget.checkbox_states == [False]

    _LogicVisualizerWindowWidget._clear_measurement(widget, resume=True)
    assert widget._controller.calls == [False, True]
    assert widget.checkbox_states == [False, True]


def test_logic_sync_runtime_controls_updates_auto_refresh_checkbox() -> None:
    class _DummyCheckbox:
        def __init__(self) -> None:
            self.checked = None
            self.block_calls: list[bool] = []

        def blockSignals(self, value: bool) -> None:
            self.block_calls.append(value)

        def setChecked(self, value: bool) -> None:
            self.checked = value

    class _DummySpin:
        def __init__(self) -> None:
            self.block_calls: list[bool] = []
            self.range_values = None
            self.value = None
            self.enabled = None

        def blockSignals(self, value: bool) -> None:
            self.block_calls.append(value)

        def setRange(self, minimum: int, maximum: int) -> None:
            self.range_values = (minimum, maximum)

        def setValue(self, value: int) -> None:
            self.value = value

        def setEnabled(self, enabled: bool) -> None:
            self.enabled = enabled

    class _DummyController:
        def __init__(self) -> None:
            self.auto_refresh_enabled = True
            self.runtime_sliding_window_enabled = False
            self.runtime_show_legend = True
            self.runtime_window_size = 123
            self.config = type("Cfg", (), {"max_samples": 500})()

    class _DummyWidget:
        def __init__(self) -> None:
            self._controller = _DummyController()
            self._auto_refresh_checkbox = _DummyCheckbox()
            self._sliding_window_checkbox = _DummyCheckbox()
            self._legend_checkbox = _DummyCheckbox()
            self._window_size_spin = _DummySpin()

    widget = _DummyWidget()

    _LogicVisualizerWindowWidget._sync_runtime_controls(widget)

    assert widget._auto_refresh_checkbox.checked is True
    assert widget._auto_refresh_checkbox.block_calls == [True, False]


def test_logic_escape_shortcut_clears_active_measurement() -> None:
    class _DummyWidget:
        def __init__(self) -> None:
            self._measurement = object()
            self.resume_calls: list[bool] = []

        def _clear_measurement(self, *, resume: bool) -> None:
            self.resume_calls.append(resume)

    widget = _DummyWidget()

    _LogicVisualizerWindowWidget._on_escape_shortcut(widget)

    assert widget.resume_calls == [True]


def test_logic_space_shortcut_toggles_auto_refresh_checkbox() -> None:
    class _DummyCheckbox:
        def __init__(self, checked: bool) -> None:
            self._checked = checked

        def isChecked(self) -> bool:
            return self._checked

        def setChecked(self, value: bool) -> None:
            self._checked = value

    class _DummyWidget:
        def __init__(self) -> None:
            self._auto_refresh_checkbox = _DummyCheckbox(True)

    widget = _DummyWidget()

    _LogicVisualizerWindowWidget._on_space_shortcut(widget)
    assert widget._auto_refresh_checkbox.isChecked() is False

    _LogicVisualizerWindowWidget._on_space_shortcut(widget)
    assert widget._auto_refresh_checkbox.isChecked() is True
