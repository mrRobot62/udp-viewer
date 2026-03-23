"""
T3.5.0 headless test for dual-axis config model and persistence.

Usage:
    python tests/test_visualizer_dual_axis_config_headless.py
"""

from pathlib import Path
import tempfile

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.ini"

        manager = VisualizerManager(config_path=config_path)
        manager.load_configs()

        config = manager.visualizers[0]
        print("DEFAULT Y1 LABEL:", config.y1_axis.label)
        print("DEFAULT Y2 LABEL:", config.y2_axis.label)
        print("DEFAULT AXES:", [field.axis for field in config.fields])

        config.y1_axis.label = "Temperature"
        config.y1_axis.min_value = 0.0
        config.y1_axis.max_value = 160.0

        config.y2_axis.label = "State"
        config.y2_axis.min_value = -0.1
        config.y2_axis.max_value = 3.1

        config.fields[2].axis = "Y1"  # Thot
        config.fields[5].axis = "Y1"  # Tch
        config.fields[6].axis = "Y2"  # heater_on
        config.fields[7].axis = "Y2"  # door_open
        config.fields[8].axis = "Y2"  # state

        manager.save_configs()

        reloaded_manager = VisualizerManager(config_path=config_path)
        reloaded_manager.load_configs()
        reloaded = reloaded_manager.visualizers[0]

        print("RELOADED Y1 LABEL:", reloaded.y1_axis.label)
        print("RELOADED Y2 LABEL:", reloaded.y2_axis.label)
        print("RELOADED Y1 RANGE:", reloaded.y1_axis.min_value, reloaded.y1_axis.max_value)
        print("RELOADED Y2 RANGE:", reloaded.y2_axis.min_value, reloaded.y2_axis.max_value)
        print("RELOADED AXES:", [field.axis for field in reloaded.fields])


if __name__ == "__main__":
    main()
