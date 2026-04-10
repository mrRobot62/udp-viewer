from __future__ import annotations

from udp_log_viewer.data_visualizer.logic_visualizer_window import build_logic_footer_status
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_sample import VisualizerSample
from udp_log_viewer.data_visualizer.visualizer_window import build_plot_footer_status


def test_logic_footer_status_uses_first_and_last_timestamp() -> None:
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_LOGIC]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:07.000", filter_string="[CSV_CLIENT_LOGIC]", sample_index=1),
    ]

    footer = build_logic_footer_status(samples)

    assert "Start: 10:00:00" in footer
    assert "Duration: 00:00:07" in footer


def test_logic_footer_status_supports_custom_channel_placeholders_and_newline() -> None:
    samples = [
        VisualizerSample(
            timestamp_raw="20260404-10:00:00.000",
            filter_string="[CSV_CLIENT_LOGIC]",
            sample_index=0,
            values_by_name={"ch0": 0.0, "ch1": 1.0},
        ),
        VisualizerSample(
            timestamp_raw="20260404-10:00:07.000",
            filter_string="[CSV_CLIENT_LOGIC]",
            sample_index=1,
            values_by_name={"ch0": 1.0, "ch1": 0.0},
        ),
    ]

    footer = build_logic_footer_status(samples, "Samples:{samples} Start:{start} End:{end} Dur:{duration}\\nCH0:{ch0};CH1:{ch1}")

    assert footer == "Samples:2 Start:10:00:00 End:10:00:07 Dur:00:00:07\nCH0:1;CH1:0"


def test_logic_footer_status_supports_python_format_specs() -> None:
    samples = [
        VisualizerSample(
            timestamp_raw="20260404-10:00:00.000",
            filter_string="[CSV_CLIENT_LOGIC]",
            sample_index=0,
            values_by_name={"ch0": 1.0},
        )
    ]

    footer = build_logic_footer_status(samples, "Samples:{samples:04d} CH0:{ch0:02.0f}")

    assert footer == "Samples:0001 CH0:01"


def test_plot_footer_status_includes_series_max_and_current() -> None:
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:05.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=1),
    ]
    series_metadata = [
        {
            "field_name": "hot_deg",
            "unit": "C",
            "statistic": True,
            "render_style": "Line",
            "latest": 118.2,
            "mean": 119.4,
            "max": 121.5,
        },
        {
            "field_name": "fan_pwm",
            "unit": "%",
            "statistic": True,
            "render_style": "Line",
            "latest": 45.0,
            "mean": 67.5,
            "max": 90.0,
        },
        {
            "field_name": "relay_state",
            "unit": "",
            "statistic": True,
            "render_style": "Step",
            "latest": 1.0,
            "mean": 0.5,
            "max": 1.0,
        },
    ]

    footer = build_plot_footer_status(samples, series_metadata)

    assert "Start: 10:00:00" in footer
    assert "Duration: 00:00:05" in footer
    assert "hot_deg MAX/Mean/Current:121.5 C/119.4 C/118.2 C" in footer
    assert "fan_pwm MAX/Mean/Current:90 %/67.5 %/45 %" in footer
    assert "relay_state" not in footer


def test_plot_footer_status_supports_custom_field_placeholders_and_newline() -> None:
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:05.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=1),
    ]
    series_metadata = [
        {
            "field_name": "hot_deg",
            "unit": "C",
            "statistic": True,
            "render_style": "Line",
            "latest": 118.2,
            "mean": 119.4,
            "max": 121.5,
        },
        {
            "field_name": "fan_pwm",
            "unit": "%",
            "statistic": True,
            "render_style": "Line",
            "latest": 45.0,
            "mean": 67.5,
            "max": 90.0,
        },
    ]

    footer = build_plot_footer_status(
        samples,
        series_metadata,
        "Samples:{samples} Start:{start} End:{end} Dur:{duration}\\nHot:{hot_deg} Mean:{mean:hot_deg} Fan:{max:fan_pwm}",
    )

    assert footer == "Samples:2 Start:10:00:00 End:10:00:05 Dur:00:00:05\nHot:118.2 C Mean:119.4 C Fan:90 %"


def test_plot_footer_status_supports_python_format_specs() -> None:
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:05.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=1),
    ]
    series_metadata = [
        {
            "field_name": "hot_deg",
            "unit": "C",
            "statistic": True,
            "render_style": "Line",
            "latest": 8.2,
            "mean": 7.4,
            "max": 12.5,
        },
    ]

    footer = build_plot_footer_status(
        samples,
        series_metadata,
        "Samples:{samples:04d} Hot:{hot_deg:03.1f} Mean:{mean:hot_deg:04.1f} Avg:{avg:hot_deg:04.1f}",
    )

    assert footer == "Samples:0002 Hot:8.2 C Mean:07.4 C Avg:07.4 C"


def test_plot_footer_status_removes_legacy_stats_placeholder_from_configured_format() -> None:
    config = VisualizerConfig(
        graph_type="plot",
        footer_status_format="Start:{start} Dur:{duration} {stats}\\nHot:{hot_deg}",
    )
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:05.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=1),
    ]
    series_metadata = [
        {
            "field_name": "hot_deg",
            "unit": "C",
            "statistic": True,
            "render_style": "Line",
            "latest": 118.2,
            "mean": 119.4,
            "max": 121.5,
        },
    ]

    footer = build_plot_footer_status(samples, series_metadata, config.footer_status_format)

    assert "MAX/Mean/Current" not in footer
    assert footer == "Start:10:00:00 Dur:00:00:05\nHot:118.2 C"


def test_plot_footer_status_skips_series_with_statistic_disabled() -> None:
    samples = [
        VisualizerSample(timestamp_raw="20260404-10:00:00.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=0),
        VisualizerSample(timestamp_raw="20260404-10:00:05.000", filter_string="[CSV_CLIENT_PLOT]", sample_index=1),
    ]
    series_metadata = [
        {
            "field_name": "hidden_line",
            "unit": "C",
            "statistic": False,
            "render_style": "Line",
            "latest": 50.0,
            "mean": 40.0,
            "max": 60.0,
        }
    ]

    footer = build_plot_footer_status(samples, series_metadata)

    assert "hidden_line" not in footer
