from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class LogicVisualizerConfigDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logic Visualizer Config")

        self.config = config

        layout = QVBoxLayout()
        form = QFormLayout()

        self.ed_title = QLineEdit(config.title)
        self.ed_filter = QLineEdit(config.filter_string)

        self.sb_max = QSpinBox()
        self.sb_max.setRange(100, 100000)
        self.sb_max.setValue(config.max_samples)

        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(config.enabled)

        form.addRow("Enabled", self.chk_enabled)
        form.addRow("Title", self.ed_title)
        form.addRow("Filter", self.ed_filter)
        form.addRow("Max Samples", self.sb_max)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout.addWidget(btns)
        self.setLayout(layout)

    def apply(self):
        self.config.enabled = self.chk_enabled.isChecked()
        self.config.title = self.ed_title.text()
        self.config.filter_string = self.ed_filter.text()
        self.config.max_samples = self.sb_max.value()
