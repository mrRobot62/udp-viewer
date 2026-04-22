from __future__ import annotations

from PyQt5.QtWidgets import QApplication, QPushButton

from udp_log_viewer.data_visualizer.logic_visualizer_config_dialog import LogicVisualizerConfigDialog
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_config_dialog import VisualizerConfigDialog
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig
from udp_log_viewer.preferences import AppPreferences, FOOTER_PRESET_NAME_MAX_LENGTH, FooterStatusPreset
from udp_log_viewer.preferences_dialog import PreferencesDialog

APP: QApplication | None = None


def _app() -> QApplication:
    global APP
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    APP = app
    return APP


def test_plot_visualizer_color_widget_syncs_preset_and_hex_input() -> None:
    _app()
    config = VisualizerConfig(
        graph_type="plot",
        fields=[VisualizerFieldConfig("temp", color="blue")],
    )
    dialog = VisualizerConfigDialog([config])

    color_widget = dialog._table.cellWidget(0, 8)
    assert color_widget.line_edit.text() == "#1f77b4"

    color_widget.combo_box.setCurrentText("Orange")
    assert color_widget.line_edit.text() == "#ff7f0e"
    assert dialog._combo_text(0, 8) == "#ff7f0e"

    color_widget.line_edit.setText("#123456")
    assert color_widget.combo_box.currentText() == "Custom"
    assert dialog._combo_text(0, 8) == "#123456"

    dialog.close()


def test_logic_visualizer_color_widget_preserves_manual_hex_colors() -> None:
    _app()
    config = VisualizerConfig(
        graph_type="logic",
        fields=[VisualizerFieldConfig("ch0", color="#abcdef")],
    )
    dialog = LogicVisualizerConfigDialog([config])

    color_widget = dialog.table.cellWidget(0, 3)
    assert color_widget.line_edit.text() == "#abcdef"
    assert color_widget.combo_box.currentText() == "Custom"

    color_widget.combo_box.setCurrentText("Red")
    assert color_widget.line_edit.text() == "#d62728"

    color_widget.line_edit.setText("#654321")
    result = dialog.result_configs()[0]

    assert result.fields[0].color == "#654321"
    dialog.close()


def test_plot_visualizer_footer_preset_combo_applies_template() -> None:
    _app()
    config = VisualizerConfig(graph_type="plot", fields=[VisualizerFieldConfig("temp", color="blue")])
    dialog = VisualizerConfigDialog(
        [config],
        footer_status_presets=(
            FooterStatusPreset("Compact", "all", "Start:{start}"),
            FooterStatusPreset("Values", "plot", "Start:{start}\\nTemp:{temp}"),
            FooterStatusPreset("LogicOnly", "logic", "Start:{start}\\nCH0:{ch0}"),
        ),
    )

    dialog._footer_preset_combo.setCurrentText("Values")
    assert dialog._footer_format.text() == "Start:{start}\\nTemp:{temp}"
    assert dialog._footer_preset_combo.findText("LogicOnly") == -1

    dialog._footer_format.setText("Custom:{temp}")
    assert dialog._footer_preset_combo.currentText() == "Custom"
    dialog.close()


def test_logic_visualizer_footer_preset_combo_applies_template() -> None:
    _app()
    config = VisualizerConfig(graph_type="logic", fields=[VisualizerFieldConfig("ch0", color="#abcdef")])
    dialog = LogicVisualizerConfigDialog(
        [config],
        footer_status_presets=(
            FooterStatusPreset("PlotOnly", "plot", "Start:{start}\\nTemp:{temp}"),
            FooterStatusPreset("Logic", "logic", "Start:{start}\\nCH0:{ch0}"),
        ),
    )

    dialog.cb_footer_preset.setCurrentText("Logic")
    assert dialog.ed_footer_format.text() == "Start:{start}\\nCH0:{ch0}"
    assert dialog.cb_footer_preset.findText("PlotOnly") == -1

    dialog.ed_footer_format.setText("Free:{ch1}")
    assert dialog.cb_footer_preset.currentText() == "Custom"
    dialog.close()


def test_preferences_dialog_trims_footer_preset_names_to_max_length() -> None:
    _app()
    dialog = PreferencesDialog(AppPreferences())
    dialog._on_footer_preset_add()

    item = dialog._footer_presets_table.item(4, 0)
    item.setText("12345678901234567890")

    assert item.text() == "123456789012"[:FOOTER_PRESET_NAME_MAX_LENGTH]
    assert dialog._footer_scope_combo(4).currentData() == "all"
    dialog.close()


def test_preferences_dialog_footer_preset_table_shows_at_least_eight_rows() -> None:
    _app()
    dialog = PreferencesDialog(AppPreferences())

    row_height = dialog._footer_presets_table.verticalHeader().defaultSectionSize()
    header_height = dialog._footer_presets_table.horizontalHeader().height()

    assert dialog.width() >= 1200
    assert dialog._footer_presets_table.minimumHeight() >= header_height + (8 * row_height)
    dialog.close()


def test_preferences_dialog_footer_and_save_buttons_are_ordered() -> None:
    _app()
    dialog = PreferencesDialog(AppPreferences())

    button_labels = [button.text() for button in dialog.findChildren(QPushButton)]

    assert button_labels[button_labels.index("ADD") : button_labels.index("DOWN") + 1] == [
        "ADD",
        "DELETE",
        "UP",
        "DOWN",
    ]
    assert button_labels[button_labels.index("Cancel") : button_labels.index("Save") + 1] == [
        "Cancel",
        "Apply",
        "Save",
    ]
    assert "OK" not in button_labels
    dialog.close()


def test_preferences_dialog_multiline_footer_editor_updates_selected_preset() -> None:
    _app()
    dialog = PreferencesDialog(AppPreferences())

    dialog._footer_presets_table.selectRow(0)
    dialog._footer_format_editor.setPlainText("Samples:{samples:04d}\nTemp:{Thot:03.1f}")
    prefs = dialog.result_preferences()

    assert prefs.footer_status_presets[0].format == "Samples:{samples:04d}\nTemp:{Thot:03.1f}"
    dialog.close()
