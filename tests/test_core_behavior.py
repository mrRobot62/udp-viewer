from __future__ import annotations

from udp_log_viewer import __display_version__, __version__
from udp_log_viewer.preferences import AppPreferences
from udp_log_viewer.data_visualizer.csv_log_parser import CsvLogParser
from udp_log_viewer.data_visualizer.config_store import ConfigStore
from udp_log_viewer.udp_log_utils import compile_patterns, match_exclude, match_include


def test_package_version_is_consistent() -> None:
    assert __version__ == "0.15.0"
    assert __display_version__.startswith(__version__)


def test_csv_temp_parser_accepts_variant_with_spaces() -> None:
    parser = CsvLogParser()
    config = ConfigStore._build_default_csv_temp_config()

    sample = parser.parse_line(
        "20260323-22:32:19.403 ; [CSV_TEMP] ; 0 ; 0 ; 1213 ; 0 ; 0 ; 518 ; 1 ; 1 ; 2",
        config,
        sample_index=7,
    )

    assert sample is not None
    assert sample.sample_index == 7
    assert sample.filter_string == "[CSV_TEMP]"
    assert sample.values_by_name["Thot"] == 121.3
    assert sample.values_by_name["Tch"] == 51.8
    assert sample.values_by_name["heater_on"] == 1.0
    assert sample.values_by_name["state"] == 2.0


def test_csv_temp_parser_rejects_wrong_field_count() -> None:
    parser = CsvLogParser()
    config = ConfigStore._build_default_csv_temp_config()

    sample = parser.parse_line(
        "20260323-22:32:19.777;[CSV_TEMP];0;0;1240;0;0;527;1;1",
        config,
        sample_index=1,
    )

    assert sample is None


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
