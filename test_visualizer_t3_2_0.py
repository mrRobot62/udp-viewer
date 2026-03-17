from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig


def build_temp_visualizer():
    cfg = VisualizerConfig()
    cfg.enabled = True
    cfg.title = "Temperature"
    cfg.filter_string = "CSV-TEMP"

    cfg.fields = [
        VisualizerFieldConfig("hotspot_raw", scale=1),
        VisualizerFieldConfig("chamber_raw", scale=1),
        VisualizerFieldConfig("hot_deg", scale=10),
        VisualizerFieldConfig("chamber_deg", scale=10),
        VisualizerFieldConfig("state", scale=1),
    ]

    return cfg


def build_power_visualizer():
    cfg = VisualizerConfig()
    cfg.enabled = True
    cfg.title = "Power"
    cfg.filter_string = "CSV-POWER"

    cfg.fields = [
        VisualizerFieldConfig("voltage", scale=10),
        VisualizerFieldConfig("current", scale=100),
        VisualizerFieldConfig("power", scale=1),
    ]

    return cfg


def main():

    manager = VisualizerManager()

    # Zwei unterschiedliche Visualizer konfigurieren
    manager.set_visualizers([
        build_temp_visualizer(),
        build_power_visualizer(),
    ])

    test_lines = [

        # PASS: Temperaturdatensatz
        "20260316-21:04:35.328;CSV-TEMP;12325;6525;1010;323;1",

        # PASS: Powerdatensatz
        "20260316-21:04:36.000;CSV-POWER;2305;1250;287",

        # FAIL: falscher Filter
        "20260316-21:04:36.500;CSV-OTHER;1;2;3",

        # FAIL: falsche Feldanzahl
        "20260316-21:04:37.000;CSV-TEMP;1;2",

        # PASS: Temperaturdatensatz mit leeren Feldern
        "20260316-21:04:38.000;CSV-TEMP;12000;;950;310;1",

        # PASS: Powerdatensatz mit Skalierung
        "20260316-21:04:39.000;CSV-POWER;2300;1500;345",
    ]

    for line in test_lines:

        accepted = manager.process_log_line(line)

        print()
        print("LINE:", line)
        print("ACCEPTED SAMPLES:", accepted)

    print("\n--- RESULT WINDOWS ---")

    for idx in range(2):

        window = manager.get_window(idx)

        if not window:
            print(f"Visualizer {idx}: no samples")
            continue

        print(f"\nVisualizer {idx} ({window.config.title})")
        print("samples:", len(window.samples))

        for s in window.samples:
            print(
                s.timestamp_raw,
                s.values_by_name
            )


if __name__ == "__main__":
    main()