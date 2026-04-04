from __future__ import annotations

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager
from udp_log_viewer.data_visualizer.visualizer_slot import VisualizerSlotId


class _DummyWindow:
    def __init__(self) -> None:
        self.closed = False
        self.project_name = None
        self.output_dir = None

    def close(self) -> None:
        self.closed = True

    def update_runtime_context(self, *, project_name, output_dir) -> None:
        self.project_name = project_name
        self.output_dir = output_dir


def test_close_all_windows_closes_and_clears_registry() -> None:
    manager = VisualizerManager()
    first = _DummyWindow()
    second = _DummyWindow()
    manager.windows_by_slot = {
        VisualizerSlotId("plot", 0): first,
        VisualizerSlotId("logic", 1): second,
    }  # type: ignore[assignment]

    manager.close_all_windows()

    assert first.closed is True
    assert second.closed is True
    assert manager.windows_by_slot == {}


def test_set_runtime_context_keeps_open_windows() -> None:
    manager = VisualizerManager()
    window = _DummyWindow()
    slot_id = VisualizerSlotId("plot", 0)
    manager.windows_by_slot = {slot_id: window}  # type: ignore[assignment]

    manager.set_runtime_context(project_name="Demo", output_dir="/tmp/demo")

    assert window.closed is False
    assert window.project_name == "Demo"
    assert str(window.output_dir) == "/tmp/demo"
    assert manager.windows_by_slot == {slot_id: window}
