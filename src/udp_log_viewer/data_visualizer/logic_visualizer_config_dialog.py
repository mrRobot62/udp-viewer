from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class LogicVisualizerConfigDialog(QDialog):
    COLOR_OPTIONS = ("red", "blue", "green", "orange", "purple", "black", "gray")

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logic Visualizer Config")
        self.config = config
        self.resize(980, 620)

        layout = QVBoxLayout()

        form = QFormLayout()

        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(config.enabled)

        self.ed_title = QLineEdit(config.title)
        self.ed_filter = QLineEdit(config.filter_string)

        self.sb_max = QSpinBox()
        self.sb_max.setRange(100, 100000)
        self.sb_max.setValue(config.max_samples)

        self.ed_x_label = QLineEdit(config.x_axis.label)

        self.chk_x_continuous = QCheckBox()
        self.chk_x_continuous.setChecked(config.x_axis.continuous)

        self.sb_x_max = QSpinBox()
        self.sb_x_max.setRange(10, 100000)
        self.sb_x_max.setValue(int(config.x_axis.max_value or 300))

        form.addRow("Enabled", self.chk_enabled)
        form.addRow("Title", self.ed_title)
        form.addRow("Filter", self.ed_filter)
        form.addRow("Max Samples", self.sb_max)
        form.addRow("X Label", self.ed_x_label)
        form.addRow("X Continuous", self.chk_x_continuous)
        form.addRow("X Max", self.sb_x_max)

        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Field Name",
            "Active",
            "Plot",
            "Color",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)

        for field in config.fields[:8]:
            self.add_row(field.field_name, field.active, field.plot, field.color)

        while self.table.rowCount() < 8:
            self.add_row(f"ch{self.table.rowCount()}", False, True, "gray")

        layout.addWidget(QLabel("Logic Channels (max 8)"))
        layout.addWidget(self.table)

        buttons_row = QHBoxLayout()

        self.btn_up = QPushButton("UP")
        self.btn_down = QPushButton("DOWN")

        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)

        buttons_row.addWidget(self.btn_up)
        buttons_row.addWidget(self.btn_down)
        buttons_row.addStretch(1)

        layout.addLayout(buttons_row)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout.addWidget(btns)
        self.setLayout(layout)

    def add_row(self, field_name: str, active: bool, plot: bool, color: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(field_name))

        active_combo = QComboBox()
        active_combo.addItems(["yes", "no"])
        active_combo.setCurrentText("yes" if active else "no")
        self.table.setCellWidget(row, 1, active_combo)

        plot_combo = QComboBox()
        plot_combo.addItems(["yes", "no"])
        plot_combo.setCurrentText("yes" if plot else "no")
        self.table.setCellWidget(row, 2, plot_combo)

        color_combo = QComboBox()
        color_combo.addItems(list(self.COLOR_OPTIONS))
        color_combo.setCurrentText(color if color in self.COLOR_OPTIONS else "gray")
        self.table.setCellWidget(row, 3, color_combo)

    def apply(self):
        self.config.enabled = self.chk_enabled.isChecked()
        self.config.title = self.ed_title.text().strip()
        self.config.filter_string = self.ed_filter.text().strip()
        self.config.max_samples = self.sb_max.value()
        self.config.graph_type = "logic"

        self.config.x_axis.label = self.ed_x_label.text().strip()
        self.config.x_axis.continuous = self.chk_x_continuous.isChecked()
        self.config.x_axis.max_value = float(self.sb_x_max.value())

        # logic view uses fixed logical y-range
        self.config.y1_axis.label = "Logic"
        self.config.y1_axis.min_value = 0.0
        self.config.y1_axis.max_value = 1.0

        new_fields = []
        for row in range(self.table.rowCount()):
            field_name = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            if not field_name:
                continue

            active = self.table.cellWidget(row, 1).currentText() == "yes"
            plot = self.table.cellWidget(row, 2).currentText() == "yes"
            color = self.table.cellWidget(row, 3).currentText()

            base = None
            for existing in self.config.fields:
                if existing.field_name == field_name:
                    base = existing
                    break

            if base is None:
                from .visualizer_field_config import VisualizerFieldConfig
                base = VisualizerFieldConfig(
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
            else:
                base.field_name = field_name
                base.active = active
                base.plot = plot
                base.color = color
                base.axis = "Y1"
                base.render_style = "Step"
                base.scale = 1
                base.numeric = True
                base.line_style = "solid"
                base.unit = ""

            new_fields.append(base)

        self.config.fields = new_fields[:8]


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
            "color": self.table.cellWidget(row, 3).currentText(),
        }

    def _set_row_values(self, row: int, values: dict):
        self.table.item(row, 0).setText(values["field_name"])
        self.table.cellWidget(row, 1).setCurrentText(values["active"])
        self.table.cellWidget(row, 2).setCurrentText(values["plot"])
        self.table.cellWidget(row, 3).setCurrentText(values["color"])