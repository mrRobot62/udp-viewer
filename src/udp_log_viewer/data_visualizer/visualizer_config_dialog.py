from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig


class VisualizerConfigDialog(QDialog):
    SCALE_OPTIONS = ("1", "10", "100", "1000")
    COLOR_OPTIONS = ("black", "gray", "red", "blue", "green", "orange", "purple")
    LINESTYLE_OPTIONS = ("solid", "dashed", "dotted", "dashdot")

    def __init__(self, config: VisualizerConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("CSV_TEMP Visualizer Config")
        self.setModal(True)
        self.resize(980, 620)

        root = QVBoxLayout(self)
        self._enabled = QCheckBox("Enabled")
        self._enabled.setChecked(config.enabled)
        self._title = QLineEdit(config.title)
        self._filter = QLineEdit(config.filter_string)
        self._max_samples = QSpinBox()
        self._max_samples.setRange(50, 100000)
        self._max_samples.setValue(config.max_samples)

        form = QFormLayout()
        form.addRow(self._enabled)
        form.addRow("Title", self._title)
        form.addRow("Filter", self._filter)
        form.addRow("Max Samples", self._max_samples)
        root.addLayout(form)

        axes_layout = QGridLayout()
        self._x_label = QLineEdit(config.x_axis.label)
        self._x_continuous = QCheckBox("Continuous X")
        self._x_continuous.setChecked(config.x_axis.continuous)
        self._x_min = self._build_float_spin(config.x_axis.min_value)
        self._x_max = self._build_float_spin(config.x_axis.max_value)
        self._y_label = QLineEdit(config.y_axis.label)
        self._y_log = QCheckBox("Logarithmic Y")
        self._y_log.setChecked(config.y_axis.logarithmic)
        self._y_min = self._build_float_spin(config.y_axis.min_value)
        self._y_max = self._build_float_spin(config.y_axis.max_value)

        axes_layout.addWidget(QLabel("X Label"), 0, 0)
        axes_layout.addWidget(self._x_label, 0, 1)
        axes_layout.addWidget(self._x_continuous, 0, 2)
        axes_layout.addWidget(QLabel("X Min"), 1, 0)
        axes_layout.addWidget(self._x_min, 1, 1)
        axes_layout.addWidget(QLabel("X Max"), 1, 2)
        axes_layout.addWidget(self._x_max, 1, 3)
        axes_layout.addWidget(QLabel("Y Label"), 2, 0)
        axes_layout.addWidget(self._y_label, 2, 1)
        axes_layout.addWidget(self._y_log, 2, 2)
        axes_layout.addWidget(QLabel("Y Min"), 3, 0)
        axes_layout.addWidget(self._y_min, 3, 1)
        axes_layout.addWidget(QLabel("Y Max"), 3, 2)
        axes_layout.addWidget(self._y_max, 3, 3)
        root.addLayout(axes_layout)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Field Name", "Numeric", "Scale", "Plot", "Color", "Line Style", "Unit"]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(self._table.SelectRows)
        self._table.setSelectionMode(self._table.SingleSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        for field in config.fields:
            self._append_row(field)
        root.addWidget(self._table, 1)

        buttons_row = QHBoxLayout()
        for text, handler in (("ADD", self._on_add), ("UP", self._on_up), ("DOWN", self._on_down), ("DEL", self._on_delete)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            buttons_row.addWidget(button)
        buttons_row.addStretch(1)
        root.addLayout(buttons_row)

        dlg_buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self)
        dlg_buttons.accepted.connect(self.accept)
        dlg_buttons.rejected.connect(self.reject)
        root.addWidget(dlg_buttons)

    def result_config(self) -> VisualizerConfig:
        fields = []
        for row in range(self._table.rowCount()):
            field_name = self._table.item(row, 0).text().strip() if self._table.item(row, 0) else ""
            if not field_name:
                continue
            fields.append(
                VisualizerFieldConfig(
                    field_name=field_name,
                    numeric=self._combo_text(row, 1).lower() == "yes",
                    scale=int(self._combo_text(row, 2) or "10"),
                    plot=self._combo_text(row, 3).lower() == "yes",
                    color=self._combo_text(row, 4),
                    line_style=self._combo_text(row, 5),
                    unit=self._table.item(row, 6).text().strip() if self._table.item(row, 6) else "",
                )
            )

        return VisualizerConfig(
            enabled=self._enabled.isChecked(),
            title=self._title.text().strip(),
            filter_string=self._filter.text().strip(),
            max_samples=int(self._max_samples.value()),
            window_geometry=self._config.window_geometry,
            x_axis=VisualizerAxisConfig(
                label=self._x_label.text().strip(),
                continuous=self._x_continuous.isChecked(),
                min_value=self._spin_value_or_none(self._x_min),
                max_value=self._spin_value_or_none(self._x_max),
            ),
            y_axis=VisualizerAxisConfig(
                label=self._y_label.text().strip(),
                logarithmic=self._y_log.isChecked(),
                min_value=self._spin_value_or_none(self._y_min),
                max_value=self._spin_value_or_none(self._y_max),
            ),
            fields=fields,
        )

    def _append_row(self, field: VisualizerFieldConfig) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(field.field_name))
        self._table.setCellWidget(row, 1, self._build_combo(("yes", "no"), "yes" if field.numeric else "no"))
        self._table.setCellWidget(row, 2, self._build_combo(self.SCALE_OPTIONS, str(field.scale)))
        self._table.setCellWidget(row, 3, self._build_combo(("yes", "no"), "yes" if field.plot else "no"))
        self._table.setCellWidget(row, 4, self._build_combo(self.COLOR_OPTIONS, field.color))
        self._table.setCellWidget(row, 5, self._build_combo(self.LINESTYLE_OPTIONS, field.line_style))
        self._table.setItem(row, 6, QTableWidgetItem(field.unit))

    def _build_combo(self, values: tuple[str, ...], current: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(list(values))
        combo.setCurrentText(current if current in values else values[0])
        return combo

    def _build_float_spin(self, value: float | None) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-99999.0, 99999.0)
        spin.setDecimals(2)
        spin.setSpecialValueText("")
        spin.setValue(value if value is not None else -99999.0)
        return spin

    @staticmethod
    def _spin_value_or_none(spin: QDoubleSpinBox) -> float | None:
        return None if spin.value() <= -99999.0 else float(spin.value())

    def _combo_text(self, row: int, col: int) -> str:
        combo = self._table.cellWidget(row, col)
        return combo.currentText().strip() if combo is not None else ""

    def _on_add(self) -> None:
        self._append_row(VisualizerFieldConfig("new_field", True, 10, False, "gray", "solid", ""))

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
            "numeric": self._combo_text(row, 1),
            "scale": self._combo_text(row, 2),
            "plot": self._combo_text(row, 3),
            "color": self._combo_text(row, 4),
            "line_style": self._combo_text(row, 5),
            "unit": self._table.item(row, 6).text() if self._table.item(row, 6) else "",
        }

    def _set_row_values(self, row: int, values: dict[str, str]) -> None:
        self._table.item(row, 0).setText(values["field_name"])
        self._table.cellWidget(row, 1).setCurrentText(values["numeric"])
        self._table.cellWidget(row, 2).setCurrentText(values["scale"])
        self._table.cellWidget(row, 3).setCurrentText(values["plot"])
        self._table.cellWidget(row, 4).setCurrentText(values["color"])
        self._table.cellWidget(row, 5).setCurrentText(values["line_style"])
        self._table.item(row, 6).setText(values["unit"])
