"""
T3.4.2 parser robustness test for CSV_TEMP input variants.

Usage:
    python tests/test_visualizer_csv_temp_parser_variants.py
"""

from udp_log_viewer.data_visualizer.visualizer_manager import VisualizerManager


def main() -> None:
    manager = VisualizerManager()
    manager.load_configs()

    lines = [
        # Variant A: strict CSV
        "20260323-22:32:19.277;[CSV_CLIENT_PLOT];0;0;1207;0;0;517;1;1;2",
        # Variant B: spaces around delimiter
        "20260323-22:32:19.403 ; [CSV_CLIENT_PLOT] ; 0 ; 0 ; 1213 ; 0 ; 0 ; 518 ; 1 ; 1 ; 2",
        # Variant C: timestamp and filter in first field
        "20260323-22:32:19.528 [CSV_CLIENT_PLOT];0;0;1218;0;0;521;1;1;2",
        # Variant D: no timestamp field
        "[CSV_CLIENT_PLOT];0;0;1231;0;0;523;1;1;2",
        # Negative case: wrong filter
        "20260323-22:32:19.652;[CSV_OTHER];0;0;1235;0;0;524;1;1;2",
        # Negative case: wrong field count
        "20260323-22:32:19.777;[CSV_CLIENT_PLOT];0;0;1240;0;0;527;1;1",
    ]

    for line in lines:
        accepted = manager.process_log_line(line)
        print("LINE:", line)
        print("ACCEPTED:", accepted)
        print()

    window = manager.get_window(0)
    print("WINDOW EXISTS:", window is not None)
    print("BUFFERED SAMPLES:", 0 if window is None else len(window.samples))
    if window is not None and window.samples:
        print("LAST SAMPLE:", window.samples[-1].values_by_name)


if __name__ == "__main__":
    main()
