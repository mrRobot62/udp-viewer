from __future__ import annotations

from pathlib import Path

from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig
from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager
from udp_log_viewer.data_visualizer.visualizer_slot import VisualizerSlotId


def _plot_config(filter_string: str) -> VisualizerConfig:
    return VisualizerConfig(
        enabled=True,
        title=filter_string,
        filter_string=filter_string,
        graph_type="plot",
        fields=[VisualizerFieldConfig("value", active=True, numeric=True, scale=1, plot=True, axis="Y1")],
    )


def _logic_config(filter_string: str) -> VisualizerConfig:
    return VisualizerConfig(
        enabled=True,
        title=filter_string,
        filter_string=filter_string,
        graph_type="logic",
        fields=[VisualizerFieldConfig("ch0", active=True, numeric=True, scale=1, plot=True, axis="Y1")],
    )


def test_config_store_migrates_legacy_sections_to_typed_slots(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    config_path.write_text(
        "\n".join(
            [
                "[visualizer_1]",
                "enabled = true",
                "title = Plot Legacy",
                "filter_string = [CSV_TEMP]",
                "graph_type = plot",
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
                "field_0_unit = C",
                "",
                "[visualizer_2]",
                "enabled = true",
                "title = Logic Legacy",
                "filter_string = [CSV_LOGIC]",
                "graph_type = logic",
                "field_count = 1",
                "field_0_name = ch0",
                "field_0_active = true",
                "field_0_numeric = true",
                "field_0_scale = 1",
                "field_0_plot = true",
                "field_0_axis = Y1",
                "field_0_render_style = Step",
                "field_0_color = red",
                "field_0_line_style = solid",
                "field_0_unit = ",
            ]
        ),
        encoding="utf-8",
    )

    slot_configs = ConfigStore(config_path=config_path).load_slot_configs()

    assert slot_configs["plot"][0].title == "Plot Legacy"
    assert slot_configs["logic"][0].title == "Logic Legacy"
    assert slot_configs["plot"][1].fields == []
    assert slot_configs["logic"][1].fields == []


def test_config_store_preserves_other_ini_sections_when_saving_slots(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    config_path.write_text("[preferences]\nlanguage = de\n", encoding="utf-8")
    store = ConfigStore(config_path=config_path)

    store.save_slot_configs(
        {
            "plot": [_plot_config("[CSV_TEMP]")] + [VisualizerConfig(graph_type="plot") for _ in range(4)],
            "logic": [_logic_config("[CSV_LOGIC]")] + [VisualizerConfig(graph_type="logic") for _ in range(4)],
        }
    )

    saved = config_path.read_text(encoding="utf-8")

    assert "[preferences]" in saved
    assert "[plot_visualizer_1]" in saved
    assert "[logic_visualizer_1]" in saved
    assert "[visualizer_1]" not in saved


class _DummyWindow:
    def __init__(self) -> None:
        self.shown = False
        self.closed = False
        self.samples = []

    def show(self) -> None:
        self.shown = True

    def close(self) -> None:
        self.closed = True

    def append_sample(self, sample) -> None:
        self.samples.append(sample)

    def clear_samples(self) -> None:
        self.samples.clear()


def test_manager_routes_to_multiple_active_slots(monkeypatch) -> None:
    manager = VisualizerManager()
    manager.configs_by_type["plot"][0] = _plot_config("[CSV_TEMP]")
    manager.configs_by_type["plot"][1] = _plot_config("[CSV_TEMP]")
    manager.configs_by_type["logic"][0] = _logic_config("[CSV_LOGIC]")

    def fake_get_or_create_window(slot_id, _config):
        existing = manager.windows_by_slot.get(slot_id)
        if existing is not None:
            return existing
        window = _DummyWindow()
        manager.windows_by_slot[slot_id] = window  # type: ignore[assignment]
        return window

    monkeypatch.setattr(manager, "_get_or_create_window", fake_get_or_create_window)

    accepted = manager.process_log_line("[CSV_TEMP];10")

    assert accepted == 2
    assert len(manager.windows_by_slot[VisualizerSlotId("plot", 0)].samples) == 1
    assert len(manager.windows_by_slot[VisualizerSlotId("plot", 1)].samples) == 1
    assert VisualizerSlotId("logic", 0) not in manager.windows_by_slot


def test_manager_show_windows_only_opens_active_slots(monkeypatch) -> None:
    manager = VisualizerManager()
    manager.configs_by_type["plot"][0] = _plot_config("[CSV_TEMP]")
    manager.configs_by_type["plot"][1] = VisualizerConfig(graph_type="plot")
    inactive_window = _DummyWindow()
    manager.windows_by_slot[VisualizerSlotId("plot", 1)] = inactive_window  # type: ignore[assignment]

    def fake_get_or_create_window(slot_id, _config):
        existing = manager.windows_by_slot.get(slot_id)
        if existing is not None:
            return existing
        window = _DummyWindow()
        manager.windows_by_slot[slot_id] = window  # type: ignore[assignment]
        return window

    monkeypatch.setattr(manager, "_get_or_create_window", fake_get_or_create_window)

    manager.show_windows("plot")

    assert manager.windows_by_slot[VisualizerSlotId("plot", 0)].shown is True
    assert inactive_window.closed is True
