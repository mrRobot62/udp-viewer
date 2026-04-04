from __future__ import annotations

from pathlib import Path

from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig


def test_config_store_persists_field_statistic_flag(tmp_path: Path) -> None:
    config_path = tmp_path / "config.ini"
    store = ConfigStore(config_path=config_path)
    config = VisualizerConfig(
        graph_type="plot",
        enabled=True,
        filter_string="[CSV_CLIENT_PLOT]",
        fields=[
            VisualizerFieldConfig("visible_stat", statistic=True),
            VisualizerFieldConfig("hidden_stat", statistic=False),
        ],
    )

    store.save_slot_configs({"plot": [config], "logic": []})
    loaded = store.load_slot_configs()["plot"][0]

    assert loaded.fields[0].statistic is True
    assert loaded.fields[1].statistic is False

