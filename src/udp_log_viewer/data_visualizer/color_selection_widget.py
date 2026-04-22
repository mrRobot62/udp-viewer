from __future__ import annotations

import re

from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QWidget

HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")

PRESET_COLORS: tuple[tuple[str, str], ...] = (
    ("Blue", "#1f77b4"),
    ("Orange", "#ff7f0e"),
    ("Green", "#2ca02c"),
    ("Red", "#d62728"),
    ("Purple", "#9467bd"),
    ("Brown", "#8c564b"),
    ("Pink", "#e377c2"),
    ("Gray", "#7f7f7f"),
    ("Olive", "#bcbd22"),
    ("Cyan", "#17becf"),
    ("Teal", "#1b9e77"),
    ("Magenta", "#e7298a"),
    ("Gold", "#e6ab02"),
    ("Navy", "#264653"),
    ("Coral", "#f4a261"),
    ("Black", "#000000"),
)
CUSTOM_COLOR_LABEL = "Custom"
DEFAULT_COLOR_CODE = PRESET_COLORS[0][1]

LEGACY_COLOR_ALIASES = {
    "black": "#000000",
    "gray": "#7f7f7f",
    "grey": "#7f7f7f",
    "red": "#d62728",
    "blue": "#1f77b4",
    "green": "#2ca02c",
    "orange": "#ff7f0e",
    "purple": "#9467bd",
}

PRESET_COLOR_BY_LABEL = {label: code for label, code in PRESET_COLORS}
PRESET_LABEL_BY_CODE = {code: label for label, code in PRESET_COLORS}


def normalize_color_code(color: str | None, fallback: str = DEFAULT_COLOR_CODE) -> str:
    """Normalize color code."""
    candidate = (color or "").strip()
    if not candidate:
        return fallback
    mapped = LEGACY_COLOR_ALIASES.get(candidate.lower())
    if mapped is not None:
        return mapped
    if HEX_COLOR_PATTERN.fullmatch(candidate):
        return candidate.lower()
    return fallback


class ColorSelectionWidget(QWidget):
    """Combined preset and hex-code editor for visualizer field colors."""
    def __init__(self, color: str = DEFAULT_COLOR_CODE, parent: QWidget | None = None) -> None:
        """Initialize ColorSelectionWidget and prepare its initial state."""
        super().__init__(parent)
        self._syncing = False

        self.combo_box = QComboBox(self)
        for label, code in PRESET_COLORS:
            self.combo_box.addItem(label, code)
        self.combo_box.addItem(CUSTOM_COLOR_LABEL, CUSTOM_COLOR_LABEL)
        self.combo_box.setToolTip("Choose one of the preset colors or keep Custom for a manual HTML color code.")

        self.line_edit = QLineEdit(self)
        self.line_edit.setPlaceholderText("#RRGGBB")
        self.line_edit.setToolTip("Enter the HTML color code used for this field.")
        self.line_edit.setValidator(QRegularExpressionValidator(QRegularExpression("^#?[0-9A-Fa-f]{0,6}$"), self.line_edit))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.combo_box, 1)
        layout.addWidget(self.line_edit, 1)

        self.combo_box.currentIndexChanged.connect(self._on_combo_changed)
        self.line_edit.textChanged.connect(self._on_text_changed)

        self.set_color(color)

    def color_code(self) -> str:
        """Handle color code."""
        return normalize_color_code(self.line_edit.text(), fallback=self._selected_or_default_color())

    def set_color(self, color: str) -> None:
        """Set color."""
        normalized = normalize_color_code(color)
        self._syncing = True
        self.line_edit.setText(normalized)
        preset_label = PRESET_LABEL_BY_CODE.get(normalized, CUSTOM_COLOR_LABEL)
        self.combo_box.setCurrentText(preset_label)
        self._syncing = False

    def _selected_or_default_color(self) -> str:
        """Internal helper for selected or default color."""
        selected = self.combo_box.currentData()
        if isinstance(selected, str) and selected.startswith("#"):
            return selected.lower()
        return DEFAULT_COLOR_CODE

    def _on_combo_changed(self) -> None:
        """Handle combo changed events."""
        if self._syncing:
            return
        selected = self.combo_box.currentData()
        if not isinstance(selected, str) or not selected.startswith("#"):
            return
        self._syncing = True
        self.line_edit.setText(selected.lower())
        self._syncing = False

    def _on_text_changed(self, text: str) -> None:
        """Handle text changed events."""
        if self._syncing:
            return
        normalized = normalize_color_code(text, fallback="")
        if not normalized:
            return
        self._syncing = True
        self.combo_box.setCurrentText(PRESET_LABEL_BY_CODE.get(normalized, CUSTOM_COLOR_LABEL))
        self._syncing = False
