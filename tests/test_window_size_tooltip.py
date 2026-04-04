from __future__ import annotations

from udp_log_viewer.data_visualizer.logic_visualizer_window import _build_window_size_tooltip as build_logic_tooltip
from udp_log_viewer.data_visualizer.visualizer_window import _build_window_size_tooltip as build_plot_tooltip


def test_plot_window_size_tooltip_uses_runtime_max_samples() -> None:
    tooltip = build_plot_tooltip(275)

    assert "1 to 275" in tooltip
    assert "5000" not in tooltip


def test_logic_window_size_tooltip_caps_large_runtime_max_samples() -> None:
    tooltip = build_logic_tooltip(200000)

    assert "1 to 5000" in tooltip
