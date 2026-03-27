from __future__ import annotations

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager


class _DummyWindow:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_close_all_windows_closes_and_clears_registry() -> None:
    manager = VisualizerManager()
    first = _DummyWindow()
    second = _DummyWindow()
    manager.windows_by_index = {0: first, 1: second}  # type: ignore[assignment]

    manager.close_all_windows()

    assert first.closed is True
    assert second.closed is True
    assert manager.windows_by_index == {}
