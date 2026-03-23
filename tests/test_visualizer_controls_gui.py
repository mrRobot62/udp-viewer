"""
T3.4.3 GUI smoke test for refresh + screenshot controls.

Usage:
    python tests/test_visualizer_controls_gui.py
"""

import sys
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager


def main() -> int:
    app = QApplication(sys.argv)
    screenshot_dir = Path.cwd() / "test_screenshots"

    manager = VisualizerManager(screenshot_dir=screenshot_dir)
    manager.load_configs()
    manager.show_window(0)

    samples = [
        "[CSV_TEMP];0;0;1207;0;0;517;1;1;2",
        "[CSV_TEMP];0;0;1213;0;0;518;1;1;2",
        "[CSV_TEMP];0;0;1218;0;0;521;1;1;2",
    ]

    def feed() -> None:
        if samples:
            manager.process_log_line(samples.pop(0))
            return

        window = manager.get_window(0)
        if window is not None:
            path = window.save_screenshot()
            print("SCREENSHOT:", path)
            window.clear_samples()
            print("BUFFER AFTER CLEAR:", len(window.samples))
        timer.stop()

    timer = QTimer()
    timer.timeout.connect(feed)
    timer.start(300)

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
