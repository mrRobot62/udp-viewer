from __future__ import annotations

from copy import deepcopy
from typing import Callable

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .config_store import ConfigStore
from .color_selection_widget import ColorSelectionWidget
from .slot_copy_dialog import SlotCopyDialog
from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig
from .visualizer_slot import SLOT_COUNT
from ..preferences import FooterStatusPreset


class LogicVisualizerConfigDialog(QDialog):
    def __init__(
        self,
        configs: list[VisualizerConfig],
        current_slot: int = 0,
        footer_status_presets: tuple[FooterStatusPreset, ...] = (),
        on_apply: Callable[[list[VisualizerConfig], int], None] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Logic Visualizer Config")
        self.resize(980, 620)
        self._configs = [ConfigStore.clone_config(config) for config in configs[:SLOT_COUNT]]
        while len(self._configs) < SLOT_COUNT:
            self._configs.append(VisualizerConfig(graph_type="logic"))
        self._current_slot = max(0, min(current_slot, SLOT_COUNT - 1))
        self._footer_status_presets = tuple(preset for preset in footer_status_presets if preset.scope in ("all", "logic"))
        self._on_apply = on_apply
        self._loaded_form_config = ConfigStore.clone_config(self._configs[self._current_slot])
        self._switch_guard = False

        layout = QVBoxLayout()

        self.sb_slot = QSpinBox()
        self.sb_slot.setRange(1, SLOT_COUNT)
        self.sb_slot.setValue(self._current_slot + 1)
        self.sb_slot.setToolTip("Choose which logic visualizer slot you want to configure.")
        self.sb_slot.valueChanged.connect(self._on_slot_changed)
        self.btn_copy = QPushButton("COPY")
        self.btn_clear = QPushButton("CLEAR")
        self.btn_copy.setToolTip("Copy another slot configuration into the selected logic slot.")
        self.btn_clear.setToolTip("Reset the selected logic slot to its default configuration.")
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_clear.clicked.connect(self._on_clear)

        self.chk_enabled = QCheckBox("Slot Active")
        self.chk_enabled.setToolTip("Enable this slot so matching data can be routed into the logic visualizer.")

        self.ed_title = QLineEdit()
        self.ed_title.setToolTip("Window title shown for this logic visualizer slot.")
        self.ed_filter = QLineEdit()
        self.ed_filter.setMinimumWidth(420)
        self.ed_filter.setToolTip("Only log lines matching this filter are routed into this logic slot.")
        self.ed_footer_format = QLineEdit()
        self.ed_footer_format.setToolTip(
            "Optional footer format. Use {samples}, {start}, {end}, {duration}, or channel names like {ch0}. "
            "Use \\n for a line break."
        )
        self.cb_footer_preset = QComboBox()
        self.cb_footer_preset.addItem("Custom", "")
        for preset in self._footer_status_presets:
            self.cb_footer_preset.addItem(preset.name, preset.format)
        self.cb_footer_preset.setToolTip("Apply one of the reusable footer format presets.")
        self.cb_footer_preset.currentIndexChanged.connect(self._on_footer_preset_changed)
        self.ed_footer_format.textChanged.connect(self._sync_footer_preset_combo)
        self.chk_show_legend = QCheckBox()
        self.chk_show_legend.setToolTip("Show or hide the legend by default in the logic visualizer window.")

        self.sb_max = QSpinBox()
        self.sb_max.setRange(100, 100000)
        self.sb_max.setToolTip("Maximum number of samples retained in memory for this slot.")
        self.chk_sliding_default = QCheckBox()
        self.chk_sliding_default.setToolTip("Enable the sliding window by default when the logic window opens.")
        self.sb_window_default = QSpinBox()
        self.sb_window_default.setRange(1, 5000)
        self.sb_window_default.setToolTip("Number of samples shown by default when the sliding window is enabled.")

        self.ed_x_label = QLineEdit()
        self.ed_x_label.setToolTip("Label shown on the X axis of the logic visualizer.")

        slot_row = QHBoxLayout()
        slot_row.addWidget(QLabel("Slot"))
        slot_row.addWidget(self.sb_slot)
        slot_row.addWidget(self.btn_copy)
        slot_row.addWidget(self.btn_clear)
        slot_row.addWidget(self.chk_enabled)
        slot_row.addStretch(1)
        layout.addLayout(slot_row)

        identity_row = QHBoxLayout()
        identity_row.addWidget(QLabel("Title"))
        identity_row.addWidget(self.ed_title, 1)
        identity_row.addWidget(QLabel("Filter"))
        identity_row.addWidget(self.ed_filter, 1)
        layout.addLayout(identity_row)

        footer_row = QHBoxLayout()
        footer_row.addWidget(QLabel("Preset"))
        footer_row.addWidget(self.cb_footer_preset)
        footer_row.addWidget(QLabel("Footer Format"))
        footer_row.addWidget(self.ed_footer_format, 1)
        layout.addLayout(footer_row)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Show Legend"))
        options_row.addWidget(self.chk_show_legend)
        options_row.addWidget(QLabel("Max Samples"))
        options_row.addWidget(self.sb_max)
        options_row.addWidget(QLabel("Sliding Window Default"))
        options_row.addWidget(self.chk_sliding_default)
        options_row.addWidget(QLabel("Default Window Size"))
        options_row.addWidget(self.sb_window_default)
        options_row.addWidget(QLabel("X Label"))
        options_row.addWidget(self.ed_x_label, 1)
        options_row.addStretch(1)
        layout.addLayout(options_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Field Name",
            "Active",
            "Plot",
            "Color",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setToolTip("Configure the logic channels, activation state, plotting, and colors for this slot.")

        layout.addWidget(QLabel("Logic Channels (max 8)"))
        layout.addWidget(self.table)

        buttons_row = QHBoxLayout()

        self.btn_up = QPushButton("UP")
        self.btn_down = QPushButton("DOWN")
        self.btn_up.setToolTip("Move the selected logic channel row up.")
        self.btn_down.setToolTip("Move the selected logic channel row down.")

        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)

        buttons_row.addWidget(self.btn_up)
        buttons_row.addWidget(self.btn_down)
        buttons_row.addStretch(1)

        layout.addLayout(buttons_row)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self._cancel_button = QPushButton("CANCEL")
        self._cancel_button.setToolTip("Close the dialog without saving the current changes.")
        self._cancel_button.clicked.connect(self.reject)
        self._apply_button = QPushButton("APPLY")
        self._apply_button.setToolTip("Apply the current slot changes without closing the dialog.")
        self._apply_button.clicked.connect(self._on_apply_clicked)
        self._save_button = QPushButton("SAVE")
        self._save_button.setToolTip("Save the current slot changes and close the dialog.")
        self._save_button.clicked.connect(self._on_save_clicked)
        buttons_row.addWidget(self._cancel_button)
        buttons_row.addWidget(self._apply_button)
        buttons_row.addWidget(self._save_button)

        layout.addLayout(buttons_row)
        self.setLayout(layout)
        self._load_slot_into_form(self._current_slot)

    def result_configs(self) -> list[VisualizerConfig]:
        self._configs[self._current_slot] = self._read_form_config()
        return [ConfigStore.clone_config(config) for config in self._configs]

    def current_slot(self) -> int:
        return self._current_slot

    def _persist_current_config(self) -> list[VisualizerConfig]:
        configs = self.result_configs()
        self._loaded_form_config = ConfigStore.clone_config(self._configs[self._current_slot])
        if self._on_apply is not None:
            self._on_apply(configs, self._current_slot)
        return configs

    def _on_apply_clicked(self) -> None:
        self._persist_current_config()

    def _on_save_clicked(self) -> None:
        self._persist_current_config()
        self.accept()

    def _load_slot_into_form(self, slot_index: int) -> None:
        config = ConfigStore.clone_config(self._configs[slot_index])
        self._switch_guard = True
        self.chk_enabled.setChecked(config.enabled)
        self.ed_title.setText(config.title)
        self.ed_filter.setText(config.filter_string)
        self.ed_footer_format.setText(config.footer_status_format)
        self._sync_footer_preset_combo(config.footer_status_format)
        self.chk_show_legend.setChecked(getattr(config, "show_legend", True))
        self.sb_max.setValue(config.max_samples)
        self.chk_sliding_default.setChecked(config.sliding_window_enabled)
        self.sb_window_default.setValue(config.default_window_size)
        self.sb_window_default.setRange(1, max(1, config.max_samples))
        self.sb_window_default.setToolTip(
            f"Number of samples shown by default when the sliding window is enabled. Allowed range: 1 to {max(1, config.max_samples)}."
        )
        self.ed_x_label.setText(config.x_axis.label)
        self.table.setRowCount(0)
        for field in config.fields[:8]:
            self.add_row(field.field_name, field.active, field.plot, field.color)
        while self.table.rowCount() < 8:
            self.add_row("", False, True, "gray")
        self._switch_guard = False
        self._loaded_form_config = self._read_form_config()

    def _read_form_config(self) -> VisualizerConfig:
        new_fields = []
        for row in range(self.table.rowCount()):
            field_name = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            if not field_name:
                continue

            active = self.table.cellWidget(row, 1).currentText() == "yes"
            plot = self.table.cellWidget(row, 2).currentText() == "yes"
            color_widget = self.table.cellWidget(row, 3)
            color = color_widget.color_code() if isinstance(color_widget, ColorSelectionWidget) else "gray"

            new_fields.append(
                VisualizerFieldConfig(
                    field_name=field_name,
                    active=active,
                    numeric=True,
                    scale=1,
                    plot=plot,
                    axis="Y1",
                    render_style="Step",
                    color=color,
                    line_style="solid",
                    unit="",
                )
            )

        return VisualizerConfig(
            enabled=self.chk_enabled.isChecked(),
            title=self.ed_title.text().strip(),
            filter_string=self.ed_filter.text().strip(),
            footer_status_format=self.ed_footer_format.text().strip(),
            show_legend=self.chk_show_legend.isChecked(),
            max_samples=self.sb_max.value(),
            sliding_window_enabled=self.chk_sliding_default.isChecked(),
            default_window_size=self.sb_window_default.value(),
            window_geometry=self._configs[self._current_slot].window_geometry,
            graph_type="logic",
            x_axis=VisualizerAxisConfig(
                label=self.ed_x_label.text().strip(),
                continuous=deepcopy(self._configs[self._current_slot].x_axis.continuous),
                min_value=deepcopy(self._configs[self._current_slot].x_axis.min_value),
                max_value=deepcopy(self._configs[self._current_slot].x_axis.max_value),
            ),
            y1_axis=VisualizerAxisConfig(label="Logic", min_value=0.0, max_value=1.0),
            y2_axis=VisualizerAxisConfig(label="Y2", min_value=0.0, max_value=1.0),
            fields=new_fields[:8],
        )

    def _has_unsaved_changes(self) -> bool:
        return self._read_form_config() != self._loaded_form_config

    def _confirm_slot_change(self) -> str:
        if not self._has_unsaved_changes():
            return "keep"
        box = QMessageBox(self)
        box.setWindowTitle("Unsaved Changes")
        box.setIcon(QMessageBox.Question)
        box.setText("Save changes before switching to another slot?")
        save_button = box.addButton("Speichern", QMessageBox.AcceptRole)
        discard_button = box.addButton("Verwerfen", QMessageBox.DestructiveRole)
        cancel_button = box.addButton("Abbrechen", QMessageBox.RejectRole)
        box.setDefaultButton(save_button)
        box.exec_()
        clicked = box.clickedButton()
        if clicked == save_button:
            return "save"
        if clicked == discard_button:
            return "discard"
        return "cancel"

    def _change_slot(self, next_slot: int) -> None:
        self._current_slot = next_slot
        self._load_slot_into_form(next_slot)

    def _reset_slot_spin(self) -> None:
        self._switch_guard = True
        self.sb_slot.setValue(self._current_slot + 1)
        self._switch_guard = False

    def _save_and_switch_slot(self, next_slot: int) -> None:
        self._persist_current_config()
        self._change_slot(next_slot)

    def _discard_and_switch_slot(self, next_slot: int) -> None:
        self._configs[self._current_slot] = ConfigStore.clone_config(self._loaded_form_config)
        self._change_slot(next_slot)

    def _on_slot_changed(self, value: int) -> None:
        if self._switch_guard:
            return
        next_slot = value - 1
        if next_slot == self._current_slot:
            return
        decision = self._confirm_slot_change()
        if decision == "cancel":
            self._reset_slot_spin()
            return
        if decision == "save":
            self._save_and_switch_slot(next_slot)
            return
        if decision == "discard":
            self._discard_and_switch_slot(next_slot)
            return
        self._change_slot(next_slot)

    def add_row(self, field_name: str, active: bool, plot: bool, color: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(field_name))

        active_combo = QComboBox()
        active_combo.addItems(["yes", "no"])
        active_combo.setCurrentText("yes" if active else "no")
        active_combo.setToolTip("Choose whether this logic channel is active.")
        self.table.setCellWidget(row, 1, active_combo)

        plot_combo = QComboBox()
        plot_combo.addItems(["yes", "no"])
        plot_combo.setCurrentText("yes" if plot else "no")
        plot_combo.setToolTip("Choose whether this logic channel is drawn in the logic visualizer.")
        self.table.setCellWidget(row, 2, plot_combo)

        self.table.setCellWidget(row, 3, ColorSelectionWidget(color))

    def _on_copy(self) -> None:
        self._configs[self._current_slot] = self._read_form_config()
        dialog = SlotCopyDialog(self._current_slot, parent=self)
        if dialog.exec_() != dialog.Accepted:
            return
        source_slot = dialog.source_slot()
        target_slot = dialog.target_slot()
        self._configs[target_slot] = ConfigStore.clone_config(self._configs[source_slot])
        if target_slot == self._current_slot:
            self._load_slot_into_form(self._current_slot)

    def _on_clear(self) -> None:
        self._configs[self._current_slot] = VisualizerConfig(graph_type="logic")
        self._load_slot_into_form(self._current_slot)

    def _move_up(self):
        row = self.table.currentRow()
        if row <= 0:
            return
        self._swap_rows(row, row - 1)
        self.table.selectRow(row - 1)

    def _move_down(self):
        row = self.table.currentRow()
        if row < 0 or row >= self.table.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self.table.selectRow(row + 1)

    def _on_footer_preset_changed(self) -> None:
        preset_format = self.cb_footer_preset.currentData()
        if not preset_format:
            return
        self.ed_footer_format.blockSignals(True)
        self.ed_footer_format.setText(str(preset_format))
        self.ed_footer_format.blockSignals(False)
        self._sync_footer_preset_combo(self.ed_footer_format.text())

    def _sync_footer_preset_combo(self, current_text: str) -> None:
        text = (current_text or "").strip()
        self.cb_footer_preset.blockSignals(True)
        index = 0
        for current_index in range(1, self.cb_footer_preset.count()):
            if str(self.cb_footer_preset.itemData(current_index) or "").strip() == text:
                index = current_index
                break
        self.cb_footer_preset.setCurrentIndex(index)
        self.cb_footer_preset.blockSignals(False)

    def _swap_rows(self, row_a: int, row_b: int):
        values_a = self._row_values(row_a)
        values_b = self._row_values(row_b)
        self._set_row_values(row_a, values_b)
        self._set_row_values(row_b, values_a)

    def _row_values(self, row: int) -> dict:
        return {
            "field_name": self.table.item(row, 0).text() if self.table.item(row, 0) else "",
            "active": self.table.cellWidget(row, 1).currentText(),
            "plot": self.table.cellWidget(row, 2).currentText(),
            "color": self.table.cellWidget(row, 3).color_code(),
        }

    def _set_row_values(self, row: int, values: dict):
        self.table.item(row, 0).setText(values["field_name"])
        self.table.cellWidget(row, 1).setCurrentText(values["active"])
        self.table.cellWidget(row, 2).setCurrentText(values["plot"])
        color_widget = self.table.cellWidget(row, 3)
        if isinstance(color_widget, ColorSelectionWidget):
            color_widget.set_color(values["color"])
