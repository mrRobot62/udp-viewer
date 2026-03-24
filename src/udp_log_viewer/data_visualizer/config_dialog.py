from PyQt5.QtWidgets import QDialog, QTableWidget, QVBoxLayout, QComboBox, QTableWidgetItem
from .visualizer_config import VisualizerConfig
from .visualizer_field_config import VisualizerFieldConfig


class ConfigDialog(QDialog):
    def __init__(self, config: VisualizerConfig):
        super().__init__()
        self.config = config

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Field", "Active", "Numeric", "Scale", "Plot",
            "Axis", "Color", "Style", "Unit"
        ])

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        for f in config.fields:
            self.add_row(f)

    def add_row(self, f: VisualizerFieldConfig):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(f.field_name))
        self.table.setCellWidget(row, 1, self.combo(["yes", "no"], f.active))
        self.table.setCellWidget(row, 2, self.combo(["yes", "no"], f.numeric))
        self.table.setCellWidget(row, 3, self.combo(["1", "10", "100"], f.scale))
        self.table.setCellWidget(row, 4, self.combo(["yes", "no"], f.plot))
        self.table.setCellWidget(row, 5, self.combo(["Y1", "Y2"], f.axis))
        self.table.setCellWidget(row, 6, self.combo(["blue","red","green"], f.color))
        self.table.setCellWidget(row, 7, self.combo(["solid","dashed"], f.line_style))
        self.table.setItem(row, 8, QTableWidgetItem(f.unit))

    def combo(self, values, current):
        c = QComboBox()
        c.addItems(values)
        c.setCurrentText(str(current).lower() if isinstance(current,bool) else str(current))
        return c

    def configure_logic(self, parent=None):
        config = self._configs[0]  # oder eigener Slot später

        config.graph_type = "logic"

        dlg = LogicVisualizerConfigDialog(config, parent)
        if dlg.exec_():
            dlg.apply()
            self.save_configs()