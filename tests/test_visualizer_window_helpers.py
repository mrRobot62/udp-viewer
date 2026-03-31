from __future__ import annotations

from udp_log_viewer.data_visualizer.visualizer_window import _build_staggered_label_offsets


class _FakeAxisTransform:
    def transform(self, point: tuple[float, float]) -> tuple[float, float]:
        x_value, y_value = point
        return (x_value * 10.0, y_value * 10.0)


class _FakeAxis:
    def __init__(self) -> None:
        self.transData = _FakeAxisTransform()


def test_staggered_label_offsets_separate_close_values() -> None:
    axis = _FakeAxis()
    series = [
        {"axis": axis, "latest": 10.0, "latest_index": 4},
        {"axis": axis, "latest": 10.4, "latest_index": 4},
        {"axis": axis, "latest": 10.7, "latest_index": 4},
    ]

    offsets = _build_staggered_label_offsets(series, axis)

    assert offsets[id(series[0])] == 0
    assert offsets[id(series[1])] != 0
    assert offsets[id(series[2])] != offsets[id(series[1])]


def test_staggered_label_offsets_ignore_other_axes() -> None:
    axis_a = _FakeAxis()
    axis_b = _FakeAxis()
    series = [
        {"axis": axis_a, "latest": 12.0, "latest_index": 2},
        {"axis": axis_b, "latest": 12.1, "latest_index": 2},
    ]

    offsets_a = _build_staggered_label_offsets(series, axis_a)
    offsets_b = _build_staggered_label_offsets(series, axis_b)

    assert offsets_a == {id(series[0]): 0}
    assert offsets_b == {id(series[1]): 0}
