from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QRegularExpression, Qt
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .project_runtime import (
    PROJECT_README_MAX_CHARS,
    RuntimeProject,
    build_project_readme_default_text,
    load_project_readme,
    normalize_project_notes,
)


class ProjectDialog(QDialog):
    def __init__(
        self,
        current_project: RuntimeProject | None = None,
        *,
        default_root_dir: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project")
        self.setModal(True)
        self.resize(760, 420)
        self._notes_max_chars = PROJECT_README_MAX_CHARS
        self._default_notes_text = ""
        self._notes_uses_default = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name = QLineEdit(self)
        self._name.setMaxLength(20)
        self._name.setMinimumWidth(260)
        self._name.setPlaceholderText("Project name")
        self._name.setToolTip(
            "Use 1 to 50 characters with letters, digits, underscores, or hyphens. The name is used for the project folder, file names, and window titles."
        )
        self._name.setValidator(QRegularExpressionValidator(QRegularExpression(r"[A-Za-z0-9_-]{0,50}"), self._name))
        self._name.textChanged.connect(self._update_preview)

        self._root_dir = QLineEdit(self)
        self._root_dir.setPlaceholderText("Select a root folder")
        self._root_dir.setMinimumWidth(440)
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

        self._preview = QLineEdit(self)
        self._preview.setReadOnly(True)
        self._preview.setMinimumWidth(440)
        self._preview.setAlignment(Qt.AlignRight)

        form.addRow("Project name", self._name)
        form.addRow("Root folder", root_widget)
        form.addRow("Project folder", self._preview)
        layout.addLayout(form)

        layout.addWidget(QLabel("Project description (Markdown)"))
        self._notes = QTextEdit(self)
        self._notes.setAcceptRichText(False)
        self._notes.setLineWrapMode(QTextEdit.WidgetWidth)
        self._notes.setPlaceholderText("Project description")
        self._notes.setMinimumHeight(self.fontMetrics().lineSpacing() * 10 + 24)
        self._notes.textChanged.connect(self._enforce_notes_limit)
        layout.addWidget(self._notes, 1)

        self._notes_info = QLabel(self)
        layout.addWidget(self._notes_info)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self._cancel = QPushButton("CANCEL", self)
        self._cancel.clicked.connect(self.reject)
        self._save = QPushButton("SAVE", self)
        self._save.setDefault(True)
        self._save.setAutoDefault(True)
        self._save.clicked.connect(self.accept)
        buttons.addWidget(self._cancel)
        buttons.addWidget(self._save)
        layout.addLayout(buttons)

        if current_project is not None:
            self._name.setText(current_project.name)
            self._root_dir.setText(str(current_project.root_dir))
            existing_notes = load_project_readme(current_project)
            if existing_notes is not None:
                self._notes.setPlainText(normalize_project_notes(existing_notes))
                self._notes_uses_default = False
        elif default_root_dir is not None:
            self._root_dir.setText(str(default_root_dir.expanduser()))
        if not self._notes.toPlainText().strip():
            self._set_default_notes_text(self.project_name())
        self._update_preview()
        self._update_notes_info()

    def project_name(self) -> str:
        return self._name.text().strip()

    def root_dir(self) -> Path:
        return Path(self._root_dir.text().strip()).expanduser()

    def project_notes(self) -> str:
        return normalize_project_notes(self._notes.toPlainText(), max_chars=self._notes_max_chars)

    def project(self) -> RuntimeProject:
        return RuntimeProject(name=self.project_name(), root_dir=self.root_dir())

    def _browse_root_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Select Project Root Folder", self._root_dir.text().strip())
        if selected:
            self._root_dir.setText(selected)

    def _update_preview(self) -> None:
        project_name = self.project_name()
        root_dir = self._root_dir.text().strip()
        if self._notes_uses_default:
            cursor = self._notes.textCursor()
            position = cursor.position()
            self._set_default_notes_text(project_name or "project")
            cursor = self._notes.textCursor()
            cursor.setPosition(min(position, len(self._notes.toPlainText())))
            self._notes.setTextCursor(cursor)
        if not project_name or not root_dir:
            self._preview.setText("The project folder will be created after you enter both fields.")
            return
        self._preview.setText(str(Path(root_dir).expanduser() / project_name))

    def _enforce_notes_limit(self) -> None:
        normalized = normalize_project_notes(self._notes.toPlainText(), max_chars=self._notes_max_chars)
        if normalized != self._notes.toPlainText():
            cursor = self._notes.textCursor()
            position = min(cursor.position(), len(normalized))
            self._notes.blockSignals(True)
            self._notes.setPlainText(normalized)
            self._notes.blockSignals(False)
            cursor = self._notes.textCursor()
            cursor.setPosition(position)
            self._notes.setTextCursor(cursor)
        self._notes_uses_default = normalized == self._default_notes_text
        self._update_notes_info()

    def _update_notes_info(self) -> None:
        self._notes_info.setText(f"{len(self.project_notes())}/{self._notes_max_chars} characters")

    def _set_default_notes_text(self, project_name: str) -> None:
        self._default_notes_text = build_project_readme_default_text(project_name or "project")
        self._notes.blockSignals(True)
        self._notes.setPlainText(self._default_notes_text)
        self._notes.blockSignals(False)
        self._notes_uses_default = True
        self._update_notes_info()
