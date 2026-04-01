from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .config_store import ConfigStore
from .slot_copy_dialog import SlotCopyDialog
from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig
from .visualizer_slot import SLOT_COUNT


class VisualizerConfigDialog(QDialog):
    SCALE_OPTIONS = ("1", "10", "100", "1000")
    AXIS_OPTIONS = ("Y1", "Y2")
    RENDER_STYLE_OPTIONS = ("Line", "Step")
    COLOR_OPTIONS = ("black", "gray", "red", "blue", "green", "orange", "purple")
    LINESTYLE_OPTIONS = ("solid", "dashed", "dotted", "dashdot")

    def __init__(
        self,
        configs: list[VisualizerConfig],
        current_slot: int = 0,
        on_apply: Callable[[list[VisualizerConfig], int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._configs = [ConfigStore.clone_config(config) for config in configs[:SLOT_COUNT]]
        while len(self._configs) < SLOT_COUNT:
            self._configs.append(VisualizerConfig(graph_type="plot"))
        self._current_slot = max(0, min(current_slot, SLOT_COUNT - 1))
        self._on_apply = on_apply
        self._loaded_form_config = ConfigStore.clone_config(self._configs[self._current_slot])
        self._switch_guard = False
        self.setWindowTitle("Plot Visualizer Config")
        self.setModal(True)
        self.resize(1260, 720)

        root = QVBoxLayout(self)
        self._slot_spin = QSpinBox()
        self._slot_spin.setRange(1, SLOT_COUNT)
        self._slot_spin.setValue(self._current_slot + 1)
        self._slot_spin.valueChanged.connect(self._on_slot_changed)
        self._copy_button = QPushButton("COPY")
        self._copy_button.clicked.connect(self._on_copy)
        self._clear_button = QPushButton("CLEAR")
        self._clear_button.clicked.connect(self._on_clear)

        self._enabled = QCheckBox("Slot Active")
        self._title = QLineEdit()
        self._filter = QLineEdit()
        self._filter.setMinimumWidth(420)
        self._show_legend = QCheckBox("Show Legend")
        self._max_samples = QSpinBox()
        self._max_samples.setRange(50, 100000)
        self._sliding_window_enabled = QCheckBox("Sliding Window Enabled by Default")
        self._default_window_size = QSpinBox()
        self._default_window_size.setRange(1, 5000)
        self._default_window_size.setToolTip("Minimum: 1, Maximum: 5000.")

        slot_row = QHBoxLayout()
        slot_row.addWidget(QLabel("Slot"))
        slot_row.addWidget(self._slot_spin)
        slot_row.addWidget(self._copy_button)
        slot_row.addWidget(self._clear_button)
        slot_row.addWidget(self._enabled)
        slot_row.addStretch(1)
        root.addLayout(slot_row)

        identity_row = QHBoxLayout()
        identity_row.addWidget(QLabel("Title"))
        identity_row.addWidget(self._title, 1)
        identity_row.addWidget(QLabel("Filter"))
        identity_row.addWidget(self._filter, 1)
        root.addLayout(identity_row)

        options_row = QHBoxLayout()
        options_row.addWidget(self._show_legend)
        options_row.addWidget(QLabel("Max Samples"))
        options_row.addWidget(self._max_samples)
        options_row.addWidget(self._sliding_window_enabled)
        options_row.addWidget(QLabel("Default Window Size"))
        options_row.addWidget(self._default_window_size)
        options_row.addStretch(1)
        root.addLayout(options_row)

        axes_layout = QGridLayout()

        self._x_label = QLineEdit()

        self._y1_label = QLineEdit()
        self._y1_log = QCheckBox("Y1 Logarithmic")
        self._y1_min = self._build_float_spin(None)
        self._y1_max = self._build_float_spin(None)
        self._y1_major_tick_step = self._build_float_spin(None)
        self._y1_max.valueChanged.connect(self._sync_tick_step_ranges)

        self._y2_label = QLineEdit()
        self._y2_log = QCheckBox("Y2 Logarithmic")
        self._y2_min = self._build_float_spin(None)
        self._y2_max = self._build_float_spin(None)
        self._y2_major_tick_step = self._build_float_spin(None)
        self._y2_max.valueChanged.connect(self._sync_tick_step_ranges)

        axes_layout.addWidget(QLabel("X Label"), 0, 0)
        axes_layout.addWidget(self._x_label, 0, 1)
        axes_layout.addWidget(QLabel("Y1 Label"), 1, 0)
        axes_layout.addWidget(self._y1_label, 1, 1)
        axes_layout.addWidget(self._y1_log, 1, 2)
        axes_layout.addWidget(QLabel("Y1 Min"), 2, 0)
        axes_layout.addWidget(self._y1_min, 2, 1)
        axes_layout.addWidget(QLabel("Y1 Max"), 2, 2)
        axes_layout.addWidget(self._y1_max, 2, 3)
        axes_layout.addWidget(QLabel("Y1 Tick Step"), 2, 4)
        axes_layout.addWidget(self._y1_major_tick_step, 2, 5)

        axes_layout.addWidget(QLabel("Y2 Label"), 3, 0)
        axes_layout.addWidget(self._y2_label, 3, 1)
        axes_layout.addWidget(self._y2_log, 3, 2)
        axes_layout.addWidget(QLabel("Y2 Min"), 4, 0)
        axes_layout.addWidget(self._y2_min, 4, 1)
        axes_layout.addWidget(QLabel("Y2 Max"), 4, 2)
        axes_layout.addWidget(self._y2_max, 4, 3)
        axes_layout.addWidget(QLabel("Y2 Tick Step"), 4, 4)
        axes_layout.addWidget(self._y2_major_tick_step, 4, 5)

        root.addLayout(axes_layout)

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            ["Field Name", "Active", "Numeric", "Scale", "Plot", "Axis", "Render", "Color", "Line Style", "Unit"]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(self._table.SelectRows)
        self._table.setSelectionMode(self._table.SingleSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self._table, 1)

        buttons_row = QHBoxLayout()
        for text, handler in (("ADD", self._on_add), ("UP", self._on_up), ("DOWN", self._on_down), ("DEL", self._on_delete)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            buttons_row.addWidget(button)
        buttons_row.addStretch(1)
        root.addLayout(buttons_row)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        self._cancel_button = QPushButton("CANCEL")
        self._cancel_button.clicked.connect(self.reject)
        self._apply_button = QPushButton("APPLY")
        self._apply_button.clicked.connect(self._on_apply_clicked)
        self._save_button = QPushButton("SAVE")
        self._save_button.clicked.connect(self._on_save_clicked)
        buttons_row.addWidget(self._cancel_button)
        buttons_row.addWidget(self._apply_button)
        buttons_row.addWidget(self._save_button)
        root.addLayout(buttons_row)

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
        self._enabled.setChecked(config.enabled)
        self._title.setText(config.title)
        self._filter.setText(config.filter_string)
        self._show_legend.setChecked(config.show_legend)
        self._max_samples.setValue(config.max_samples)
        self._sliding_window_enabled.setChecked(config.sliding_window_enabled)
        self._default_window_size.setValue(config.default_window_size)
        self._x_label.setText(config.x_axis.label)
        self._y1_label.setText(config.y1_axis.label)
        self._y1_log.setChecked(config.y1_axis.logarithmic)
        self._y1_min.setValue(config.y1_axis.min_value if config.y1_axis.min_value is not None else 0)
        self._y1_max.setValue(config.y1_axis.max_value if config.y1_axis.max_value is not None else 0)
        self._y1_major_tick_step.setValue(
            config.y1_axis.major_tick_step if config.y1_axis.major_tick_step is not None else 10
        )
        self._y2_label.setText(config.y2_axis.label)
        self._y2_log.setChecked(config.y2_axis.logarithmic)
        self._y2_min.setValue(config.y2_axis.min_value if config.y2_axis.min_value is not None else 0)
        self._y2_max.setValue(config.y2_axis.max_value if config.y2_axis.max_value is not None else 0)
        self._y2_major_tick_step.setValue(
            config.y2_axis.major_tick_step if config.y2_axis.major_tick_step is not None else 10
        )
        self._sync_tick_step_ranges()
        self._table.setRowCount(0)
        for field in config.fields:
            self._append_row(field)
        self._switch_guard = False
        self._loaded_form_config = self._read_form_config()

    def _read_form_config(self) -> VisualizerConfig:
        fields = []
        for row in range(self._table.rowCount()):
            field_name = self._table.item(row, 0).text().strip() if self._table.item(row, 0) else ""
            if not field_name:
                continue
            fields.append(
                VisualizerFieldConfig(
                    field_name=field_name,
                    active=self._combo_text(row, 1).lower() == "yes",
                    numeric=self._combo_text(row, 2).lower() == "yes",
                    scale=int(self._combo_text(row, 3) or "10"),
                    plot=self._combo_text(row, 4).lower() == "yes",
                    axis=self._combo_text(row, 5),
                    render_style=self._combo_text(row, 6),
                    color=self._combo_text(row, 7),
                    line_style=self._combo_text(row, 8),
                    unit=self._table.item(row, 9).text().strip() if self._table.item(row, 9) else "",
                )
            )

        return VisualizerConfig(
            enabled=self._enabled.isChecked(),
            title=self._title.text().strip(),
            filter_string=self._filter.text().strip(),
            show_legend=self._show_legend.isChecked(),
            max_samples=int(self._max_samples.value()),
            sliding_window_enabled=self._sliding_window_enabled.isChecked(),
            default_window_size=int(self._default_window_size.value()),
            window_geometry=self._configs[self._current_slot].window_geometry,
            graph_type="plot",
            x_axis=VisualizerAxisConfig(
                label=self._x_label.text().strip(),
                continuous=self._configs[self._current_slot].x_axis.continuous,
                min_value=self._configs[self._current_slot].x_axis.min_value,
                max_value=self._configs[self._current_slot].x_axis.max_value,
            ),
            y1_axis=VisualizerAxisConfig(
                label=self._y1_label.text().strip(),
                logarithmic=self._y1_log.isChecked(),
                min_value=self._spin_value_or_none(self._y1_min),
                max_value=self._spin_value_or_none(self._y1_max),
                major_tick_step=self._positive_spin_value_or_none(self._y1_major_tick_step),
            ),
            y2_axis=VisualizerAxisConfig(
                label=self._y2_label.text().strip(),
                logarithmic=self._y2_log.isChecked(),
                min_value=self._spin_value_or_none(self._y2_min),
                max_value=self._spin_value_or_none(self._y2_max),
                major_tick_step=self._positive_spin_value_or_none(self._y2_major_tick_step),
            ),
            fields=fields,
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
        self._slot_spin.setValue(self._current_slot + 1)
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

    def _append_row(self, field: VisualizerFieldConfig) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(field.field_name))
        self._table.setCellWidget(row, 1, self._build_combo(("yes", "no"), "yes" if field.active else "no"))
        self._table.setCellWidget(row, 2, self._build_combo(("yes", "no"), "yes" if field.numeric else "no"))
        self._table.setCellWidget(row, 3, self._build_combo(self.SCALE_OPTIONS, str(field.scale)))
        self._table.setCellWidget(row, 4, self._build_combo(("yes", "no"), "yes" if field.plot else "no"))
        self._table.setCellWidget(row, 5, self._build_combo(self.AXIS_OPTIONS, field.axis))
        self._table.setCellWidget(row, 6, self._build_combo(self.RENDER_STYLE_OPTIONS, field.render_style))
        self._table.setCellWidget(row, 7, self._build_combo(self.COLOR_OPTIONS, field.color))
        self._table.setCellWidget(row, 8, self._build_combo(self.LINESTYLE_OPTIONS, field.line_style))
        self._table.setItem(row, 9, QTableWidgetItem(field.unit))

    def _build_combo(self, values: tuple[str, ...], current: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(list(values))
        combo.setCurrentText(current if current in values else values[0])
        return combo

    def _build_float_spin(self, value: float | None) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 99999.0)
        spin.setDecimals(2)
        spin.setSpecialValueText("")
        spin.setValue(value if value is not None else 0)
        return spin

    @staticmethod
    def _spin_value_or_none(spin: QDoubleSpinBox) -> float | None:
        return None if spin.value() <= 0 else float(spin.value())

    @staticmethod
    def _positive_spin_value_or_none(spin: QDoubleSpinBox) -> float | None:
        value = VisualizerConfigDialog._spin_value_or_none(spin)
        if value is None or value <= 0:
            return None
        return value

    def _sync_tick_step_ranges(self) -> None:
        self._sync_single_tick_step_range(self._y1_max, self._y1_major_tick_step)
        self._sync_single_tick_step_range(self._y2_max, self._y2_major_tick_step)

    @staticmethod
    def _sync_single_tick_step_range(max_spin: QDoubleSpinBox, step_spin: QDoubleSpinBox) -> None:
        max_value = VisualizerConfigDialog._spin_value_or_none(max_spin)
        max_step = max(1.0, (max_value / 5.0) if max_value is not None and max_value > 0 else 100.0)
        step_spin.blockSignals(True)
        step_spin.setRange(-99999.0, max_step)
        current_value = step_spin.value()
        if current_value != -99999.0:
            step_spin.setValue(min(max(1.0, current_value), max_step))
        step_spin.blockSignals(False)

    def _combo_text(self, row: int, col: int) -> str:
        combo = self._table.cellWidget(row, col)
        return combo.currentText().strip() if combo is not None else ""

    def _on_add(self) -> None:
        self._append_row(VisualizerFieldConfig("new_field", True, True, 10, False, "Y1", "Line", "gray", "solid", ""))

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
        self._configs[self._current_slot] = VisualizerConfig(graph_type="plot")
        self._load_slot_into_form(self._current_slot)

    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    def _on_up(self) -> None:
        row = self._table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            self._table.selectRow(row - 1)

    def _on_down(self) -> None:
        row = self._table.currentRow()
        if 0 <= row < self._table.rowCount() - 1:
            self._swap_rows(row, row + 1)
            self._table.selectRow(row + 1)

    def _swap_rows(self, row_a: int, row_b: int) -> None:
        values_a = self._row_values(row_a)
        values_b = self._row_values(row_b)
        self._set_row_values(row_a, values_b)
        self._set_row_values(row_b, values_a)

    def _row_values(self, row: int) -> dict[str, str]:
        return {
            "field_name": self._table.item(row, 0).text() if self._table.item(row, 0) else "",
            "active": self._combo_text(row, 1),
            "numeric": self._combo_text(row, 2),
            "scale": self._combo_text(row, 3),
            "plot": self._combo_text(row, 4),
            "axis": self._combo_text(row, 5),
            "render_style": self._combo_text(row, 6),
            "color": self._combo_text(row, 7),
            "line_style": self._combo_text(row, 8),
            "unit": self._table.item(row, 9).text() if self._table.item(row, 9) else "",
        }

    def _set_row_values(self, row: int, values: dict[str, str]) -> None:
        self._table.item(row, 0).setText(values["field_name"])
        self._table.cellWidget(row, 1).setCurrentText(values["active"])
        self._table.cellWidget(row, 2).setCurrentText(values["numeric"])
        self._table.cellWidget(row, 3).setCurrentText(values["scale"])
        self._table.cellWidget(row, 4).setCurrentText(values["plot"])
        self._table.cellWidget(row, 5).setCurrentText(values["axis"])
        self._table.cellWidget(row, 6).setCurrentText(values["render_style"])
        self._table.cellWidget(row, 7).setCurrentText(values["color"])
        self._table.cellWidget(row, 8).setCurrentText(values["line_style"])
        self._table.item(row, 9).setText(values["unit"])
