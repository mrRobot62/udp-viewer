from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .project_runtime import RuntimeProject


class ProjectDialog(QDialog):
    def __init__(self, current_project: RuntimeProject | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project")
        self.setModal(True)
        self.resize(640, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name = QLineEdit(self)
        self._name.setMaxLength(15)
        self._name.setPlaceholderText("Project name")
        self._name.setToolTip(
            "Use 1 to 15 alphanumeric characters. The name is used for the project folder, file names, and window titles."
        )
        self._name.setValidator(QRegularExpressionValidator(QRegularExpression(r"[A-Za-z0-9]{0,15}"), self._name))
        self._name.textChanged.connect(self._update_preview)

        self._root_dir = QLineEdit(self)
        self._root_dir.setPlaceholderText("Select a root folder")
        self._root_dir.setToolTip(
            "Select the parent folder for the project, for example Downloads. Saving will automatically create a subfolder with the project name and store all project artifacts there."
        )
        self._root_dir.textChanged.connect(self._update_preview)

        self._browse = QPushButton("Browse…", self)
        self._browse.clicked.connect(self._browse_root_dir)
        root_row = QHBoxLayout()
        root_row.setContentsMargins(0, 0, 0, 0)
        root_row.addWidget(self._root_dir, 1)
        root_row.addWidget(self._browse)
        root_widget = QWidget(self)
        root_widget.setLayout(root_row)

        self._preview = QLabel(self)
        self._preview.setWordWrap(True)

        form.addRow("Project name", self._name)
        form.addRow("Root folder", root_widget)
        form.addRow("Project folder", self._preview)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._cancel = QPushButton("CANCEL", self)
        self._cancel.clicked.connect(self.reject)
        self._save = QPushButton("SAVE", self)
        self._save.clicked.connect(self.accept)
        buttons.addWidget(self._cancel)
        buttons.addWidget(self._save)
        layout.addLayout(buttons)

        if current_project is not None:
            self._name.setText(current_project.name)
            self._root_dir.setText(str(current_project.root_dir))
        self._update_preview()

    def project_name(self) -> str:
        return self._name.text().strip()

    def root_dir(self) -> Path:
        return Path(self._root_dir.text().strip()).expanduser()

    def project(self) -> RuntimeProject:
        return RuntimeProject(name=self.project_name(), root_dir=self.root_dir())

    def _browse_root_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Project Root Folder", self._root_dir.text().strip())
        if selected:
            self._root_dir.setText(selected)

    def _update_preview(self) -> None:
        project_name = self.project_name()
        root_dir = self._root_dir.text().strip()
        if not project_name or not root_dir:
            self._preview.setText("The project folder will be created after you enter both fields.")
            return
        self._preview.setText(str(Path(root_dir).expanduser() / project_name))
