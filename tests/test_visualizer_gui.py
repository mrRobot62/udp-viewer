import sys
import random

from PyQt5.QtWidgets import QApplication

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig


def build_visualizer():
    cfg = VisualizerConfig()

    cfg.enabled = True
    cfg.title = "Temperature Test"
    cfg.filter_string = "CSV-TEMP"

    cfg.fields = [
        VisualizerFieldConfig("hot_deg", scale=10, plot=True, color="red", unit="°C"),
        VisualizerFieldConfig("chamber_deg", scale=10, plot=True, color="blue", unit="°C"),
    ]

    return cfg


def main():

    app = QApplication(sys.argv)

    manager = VisualizerManager()
    manager.set_visualizers([build_visualizer()])

    window = None

    for i in range(100):

        hot = 1000 + random.randint(-50, 50)
        chamber = 300 + random.randint(-20, 20)

        line = f"20260316-21:04:{i:02d}.000;CSV-TEMP;{hot};{chamber}"

        manager.process_log_line(line)

        if window is None:
            window = manager.get_window(0)
            if window:
                window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()