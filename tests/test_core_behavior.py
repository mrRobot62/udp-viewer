from __future__ import annotations

import random

from udp_log_viewer import __display_version__, __version__
from udp_log_viewer.preferences import AppPreferences
from udp_log_viewer.data_visualizer.csv_log_parser import CsvLogParser
from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.replay_simulation import (
    create_temperature_plot_simulation_state,
    next_temperature_plot_simulation_lines,
)
from udp_log_viewer.udp_log_utils import compile_patterns, match_exclude, match_include


def test_package_version_is_consistent() -> None:
    assert __version__ == "0.16.0"
    assert __display_version__.startswith(__version__)


def test_csv_temp_parser_accepts_variant_with_spaces() -> None:
    parser = CsvLogParser()
    config = ConfigStore._build_default_csv_temp_config()

    sample = parser.parse_line(
        "20260323-22:32:19.403 ; [CSV_CLIENT_PLOT] ; 0 ; 0 ; 1213 ; 0 ; 0 ; 518 ; 1 ; 1 ; 2",
        config,
        sample_index=7,
    )

    assert sample is not None
    assert sample.sample_index == 7
    assert sample.filter_string == "[CSV_CLIENT_PLOT]"
    assert sample.values_by_name["Thot"] == 121.3
    assert sample.values_by_name["Tch"] == 51.8
    assert sample.values_by_name["heater_on"] == 1.0
    assert sample.values_by_name["state"] == 2.0


def test_csv_temp_parser_rejects_wrong_field_count() -> None:
    parser = CsvLogParser()
    config = ConfigStore._build_default_csv_temp_config()

    sample = parser.parse_line(
        "20260323-22:32:19.777;[CSV_CLIENT_PLOT];0;0;1240;0;0;527;1;1",
        config,
        sample_index=1,
    )

    assert sample is None


def test_temperature_plot_simulation_keeps_host_and_client_in_sync() -> None:
    parser = CsvLogParser()
    client_config = ConfigStore._build_default_csv_temp_config()
    host_config = ConfigStore._build_default_csv_host_plot_config()
    state = create_temperature_plot_simulation_state()

    random.seed(1)
    lines = next_temperature_plot_simulation_lines(state)

    client_sample = parser.parse_line(lines[0], client_config, sample_index=0)
    host_sample = parser.parse_line(lines[1], host_config, sample_index=0)

    assert client_sample is not None
    assert host_sample is not None
    assert client_sample.values_by_name["Tch"] == host_sample.values_by_name["Tch"]
    assert client_sample.values_by_name["Thot"] == host_sample.values_by_name["Thot"]
    assert host_sample.values_by_name["target"] == 60.0
    assert host_sample.values_by_name["target_min"] == 57.0
    assert host_sample.values_by_name["target_max"] == 65.0
    assert host_sample.values_by_name["state"] == client_sample.values_by_name["state"]


def test_temperature_plot_simulation_chamber_moves_toward_target() -> None:
    parser = CsvLogParser()
    client_config = ConfigStore._build_default_csv_temp_config()
    state = create_temperature_plot_simulation_state()
    start_gap = state.target - state.chamber

    random.seed(7)
    last_client_sample = None
    for _ in range(80):
        lines = next_temperature_plot_simulation_lines(state)
        last_client_sample = parser.parse_line(lines[0], client_config, sample_index=0)

    assert last_client_sample is not None
    assert state.chamber > 50.0
    assert state.target - state.chamber < start_gap


def test_temperature_plot_simulation_cuts_heater_at_150c_hotspot() -> None:
    parser = CsvLogParser()
    client_config = ConfigStore._build_default_csv_temp_config()
    state = create_temperature_plot_simulation_state()
    state.heater_on = True
    state.hotspot = 149.8
    state.chamber = 115.0
    state.heater_ticks_remaining = 5

    random.seed(3)
    lines = next_temperature_plot_simulation_lines(state)
    client_sample = parser.parse_line(lines[0], client_config, sample_index=0)

    assert client_sample is not None
    assert state.hotspot <= 150.0
    assert state.heater_on is False
    assert client_sample.values_by_name["heater_on"] == 0.0


def test_include_and_exclude_pattern_logic() -> None:
    include_patterns = compile_patterns("[OVEN/INFO];[T11]", "Substring")
    exclude_patterns = compile_patterns("ERROR;WARN", "Substring")

    assert match_include("[OVEN/INFO] [T11] core=23.20", include_patterns) is True
    assert match_include("[OVEN/INFO] core=23.20", include_patterns) is False
    assert match_exclude("[HOST/ERROR] timeout", exclude_patterns) is True
    assert match_exclude("[HOST/INFO] ready", exclude_patterns) is False


def test_preferences_normalize_visualizer_presets() -> None:
    prefs = AppPreferences(visualizer_presets="300,100,200,150")

    assert prefs.visualizer_presets == (100, 150, 200, 300)
