from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .preferences import AppPreferences, FOOTER_PRESET_NAME_MAX_LENGTH, FooterPresetScope, FooterStatusPreset


class PreferencesDialog(QDialog):
    """Dialog for editing global application and visualizer defaults."""
    FOOTER_PRESET_VISIBLE_ROWS = 8
    FOOTER_SCOPE_OPTIONS: tuple[tuple[str, FooterPresetScope], ...] = (
        ("All", "all"),
        ("Plot", "plot"),
        ("Logic", "logic"),
    )

    def __init__(self, preferences: AppPreferences, parent: QWidget | None = None) -> None:
        """Initialize PreferencesDialog and prepare its initial state."""
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self._syncing_footer_editor = False
        self.resize(1240, 760)

        root = QVBoxLayout(self)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_visualizer_tab(), "Visualizer")
        root.addWidget(tabs)

        buttons = QHBoxLayout()
        self._restore_button = QPushButton("Restore Defaults")
        self._restore_button.setToolTip("Reset all preference values in this dialog to the application defaults.")
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setToolTip("Close the dialog without saving the current changes.")
        self._cancel_button.clicked.connect(self.reject)
        self._apply_button = QPushButton("Apply")
        self._apply_button.setToolTip("Save the displayed preferences without closing the dialog.")
        self._save_button = QPushButton("Save")
        self._save_button.setDefault(True)
        self._save_button.setToolTip("Save the displayed preferences and close the dialog.")
        self._save_button.clicked.connect(self.accept)
        buttons.addWidget(self._restore_button)
        buttons.addStretch(1)
        buttons.addWidget(self._cancel_button)
        buttons.addWidget(self._apply_button)
        buttons.addWidget(self._save_button)
        root.addLayout(buttons)

        self.set_preferences(preferences)

    def apply_button(self) -> QPushButton:
        """Return the Apply button for external signal wiring."""
        return self._apply_button

    def restore_button(self) -> QPushButton:
        """Return the Restore Defaults button for external signal wiring."""
        return self._restore_button

    def result_preferences(self) -> AppPreferences:
        """Build and return the preferences object represented by the dialog state."""
        return AppPreferences(
            language=self._language.currentData() or "de",
            autoscroll_default=self._autoscroll_default.isChecked(),
            timestamp_default=self._timestamp_default.isChecked(),
            max_lines_default=int(self._max_lines_default.value()),
            log_path=self._log_path.text().strip(),
            visualizer_presets=(
                int(self._preset_1.value()),
                int(self._preset_2.value()),
                int(self._preset_3.value()),
                int(self._preset_4.value()),
            ),
            footer_status_presets=self._footer_presets_from_table(),
            plot_sliding_window_default=self._plot_sliding_default.isChecked(),
            plot_window_size_default=int(self._plot_window_size_default.value()),
            logic_sliding_window_default=self._logic_sliding_default.isChecked(),
            logic_window_size_default=int(self._logic_window_size_default.value()),
        )

    def set_preferences(self, preferences: AppPreferences) -> None:
        """Populate the dialog widgets from an existing preferences object."""
        self._language.setCurrentIndex(max(0, self._language.findData(preferences.language)))
        self._autoscroll_default.setChecked(preferences.autoscroll_default)
        self._timestamp_default.setChecked(preferences.timestamp_default)
        self._max_lines_default.setValue(preferences.max_lines_default)
        self._log_path.setText(preferences.log_path)
        self._preset_1.setValue(preferences.visualizer_presets[0])
        self._preset_2.setValue(preferences.visualizer_presets[1])
        self._preset_3.setValue(preferences.visualizer_presets[2])
        self._preset_4.setValue(preferences.visualizer_presets[3])
        self._set_footer_presets_table(preferences.footer_status_presets)
        self._plot_sliding_default.setChecked(preferences.plot_sliding_window_default)
        self._plot_window_size_default.setValue(preferences.plot_window_size_default)
        self._logic_sliding_default.setChecked(preferences.logic_sliding_window_default)
        self._logic_window_size_default.setValue(preferences.logic_window_size_default)

    def _build_general_tab(self) -> QWidget:
        """Build the tab that edits language, logging, and UI defaults."""
        tab = QWidget(self)
        layout = QFormLayout(tab)

        self._language = QComboBox(tab)
        self._language.addItem("Deutsch", "de")
        self._language.addItem("English", "en")
        self._language.setToolTip("Choose the display language used by the application.")

        self._autoscroll_default = QCheckBox("Enabled", tab)
        self._autoscroll_default.setToolTip("Default state for Auto-Scroll when the application starts.")
        self._timestamp_default = QCheckBox("Enabled", tab)
        self._timestamp_default.setToolTip("Default state for Timestamp when the application starts.")
        self._max_lines_default = QSpinBox(tab)
        self._max_lines_default.setRange(1000, 500000)
        self._max_lines_default.setToolTip("Default maximum number of visible log lines kept in the UI.")
        self._log_path = QLineEdit(tab)
        self._log_path.setMinimumWidth(420)
        self._log_path.setToolTip("Default folder used for saved logs and live session log files.")
        self._log_path_browse = QPushButton("Browse…", tab)
        self._log_path_browse.setToolTip("Choose the default folder used for log files.")
        self._log_path_browse.clicked.connect(self._browse_log_path)
        log_path_row = QHBoxLayout()
        log_path_row.setContentsMargins(0, 0, 0, 0)
        log_path_row.addWidget(self._log_path)
        log_path_row.addWidget(self._log_path_browse)
        log_path_row.setStretch(0, 1)
        log_path_widget = QWidget(tab)
        log_path_widget.setLayout(log_path_row)

        layout.addRow("Language", self._language)
        layout.addRow("Auto-Scroll Default", self._autoscroll_default)
        layout.addRow("Timestamp Default", self._timestamp_default)
        layout.addRow("Max Lines Default", self._max_lines_default)
        layout.addRow("Log Path", log_path_widget)
        return tab

    def _build_visualizer_tab(self) -> QWidget:
        """Build the tab that edits visualizer presets and footer templates."""
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("Window Presets"))
        self._preset_1 = self._build_preset_spin(tab)
        self._preset_2 = self._build_preset_spin(tab)
        self._preset_3 = self._build_preset_spin(tab)
        self._preset_4 = self._build_preset_spin(tab)
        for widget in (self._preset_1, self._preset_2, self._preset_3, self._preset_4):
            widget.setToolTip("Preset value offered in the visualizer windows for quick window-size changes.")
            presets_row.addWidget(widget)
        presets_row.addStretch(1)
        layout.addLayout(presets_row)

        layout.addWidget(QLabel("Footer Presets"))
        self._footer_presets_table = QTableWidget(0, 3, tab)
        self._footer_presets_table.setHorizontalHeaderLabels(["Preset Name", "Type", "Format"])
        self._footer_presets_table.verticalHeader().setVisible(False)
        self._footer_presets_table.setSelectionBehavior(self._footer_presets_table.SelectRows)
        self._footer_presets_table.setSelectionMode(self._footer_presets_table.SingleSelection)
        self._footer_presets_table.horizontalHeader().setStretchLastSection(True)
        self._footer_presets_table.setToolTip(
            "Reusable footer format presets for plot and logic visualizer slot dialogs."
        )
        self._footer_presets_table.itemChanged.connect(self._on_footer_preset_item_changed)
        self._footer_presets_table.itemSelectionChanged.connect(self._load_selected_footer_format_editor)
        self._configure_footer_presets_table_size()
        layout.addWidget(self._footer_presets_table, 1)

        footer_buttons = QHBoxLayout()
        for text, handler, tip in (
            ("ADD", self._on_footer_preset_add, "Append a new preset row at the end of the table."),
            ("DELETE", self._on_footer_preset_delete, "Delete the selected preset row."),
            ("UP", self._on_footer_preset_up, "Move the selected preset row up."),
            ("DOWN", self._on_footer_preset_down, "Move the selected preset row down."),
        ):
            button = QPushButton(text, tab)
            button.setToolTip(tip)
            button.clicked.connect(handler)
            footer_buttons.addWidget(button)
        footer_buttons.addStretch(1)
        layout.addLayout(footer_buttons)

        layout.addWidget(QLabel("Selected Footer Format"))
        self._footer_format_editor = QPlainTextEdit(tab)
        self._footer_format_editor.setMinimumHeight(90)
        self._footer_format_editor.setPlaceholderText("Samples:{samples}\nDauer:{duration}")
        self._footer_format_editor.setToolTip(
            "Edit the selected preset format. Use real line breaks here; saved presets keep them."
        )
        self._footer_format_editor.textChanged.connect(self._on_footer_format_editor_changed)
        layout.addWidget(self._footer_format_editor)

        form = QFormLayout()
        self._plot_sliding_default = QCheckBox("Enabled", tab)
        self._plot_sliding_default.setToolTip("Default sliding-window state for new plot visualizer windows.")
        self._plot_window_size_default = QSpinBox(tab)
        self._plot_window_size_default.setRange(10, 100000)
        self._plot_window_size_default.setToolTip("Default plot window size used when a new plot visualizer is opened.")
        self._logic_sliding_default = QCheckBox("Enabled", tab)
        self._logic_sliding_default.setToolTip("Default sliding-window state for new logic visualizer windows.")
        self._logic_window_size_default = QSpinBox(tab)
        self._logic_window_size_default.setRange(10, 100000)
        self._logic_window_size_default.setToolTip("Default logic window size used when a new logic visualizer is opened.")

        form.addRow("Plot Sliding Window Default", self._plot_sliding_default)
        form.addRow("Plot Default Window Size", self._plot_window_size_default)
        form.addRow("Logic Sliding Window Default", self._logic_sliding_default)
        form.addRow("Logic Default Window Size", self._logic_window_size_default)
        layout.addLayout(form)
        return tab

    @staticmethod
    def _build_preset_spin(parent: QWidget) -> QSpinBox:
        """Build and return preset spin."""
        spin = QSpinBox(parent)
        spin.setRange(10, 100000)
        spin.setSingleStep(10)
        return spin

    def _browse_log_path(self) -> None:
        """Internal helper for browse log path."""
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Default Log Folder",
            self._log_path.text().strip(),
        )
        if selected:
            self._log_path.setText(selected)

    def _footer_presets_from_table(self) -> tuple[FooterStatusPreset, ...]:
        """Internal helper for footer presets from table."""
        presets: list[FooterStatusPreset] = []
        for row in range(self._footer_presets_table.rowCount()):
            name = self._footer_presets_table.item(row, 0).text().strip() if self._footer_presets_table.item(row, 0) else ""
            scope = self._footer_scope_text(row)
            fmt = self._footer_presets_table.item(row, 2).text().strip() if self._footer_presets_table.item(row, 2) else ""
            if name and fmt:
                presets.append(FooterStatusPreset(name=name, scope=scope, format=fmt))
        return tuple(presets)

    def _set_footer_presets_table(self, presets: tuple[FooterStatusPreset, ...]) -> None:
        """Set footer presets table."""
        self._footer_presets_table.setRowCount(0)
        for preset in presets:
            self._insert_footer_preset_row(self._footer_presets_table.rowCount(), preset.name, preset.scope, preset.format)
        if self._footer_presets_table.rowCount() > 0:
            self._footer_presets_table.selectRow(0)
        self._load_selected_footer_format_editor()

    def _insert_footer_preset_row(self, row: int, name: str, scope: FooterPresetScope, fmt: str) -> None:
        """Internal helper for insert footer preset row."""
        self._footer_presets_table.insertRow(row)
        self._footer_presets_table.setItem(row, 0, QTableWidgetItem(name))
        self._footer_presets_table.setCellWidget(row, 1, self._build_footer_scope_combo(scope))
        self._footer_presets_table.setItem(row, 2, QTableWidgetItem(fmt))
        if self._footer_presets_table.item(row, 0) is not None:
            self._footer_presets_table.item(row, 0).setToolTip(
                f"Maximum {FOOTER_PRESET_NAME_MAX_LENGTH} characters."
            )

    def _selected_footer_preset_row(self) -> int:
        """Internal helper for selected footer preset row."""
        row = self._footer_presets_table.currentRow()
        return row if row >= 0 else self._footer_presets_table.rowCount() - 1

    def _on_footer_preset_add(self) -> None:
        """Handle footer preset add events."""
        insert_at = self._footer_presets_table.rowCount()
        self._insert_footer_preset_row(insert_at, "New Preset", "all", "Samples:{samples}\\nDauer:{duration}")
        self._footer_presets_table.selectRow(insert_at)

    def _on_footer_preset_delete(self) -> None:
        """Handle footer preset delete events."""
        row = self._footer_presets_table.currentRow()
        if row < 0:
            return
        self._footer_presets_table.removeRow(row)
        if self._footer_presets_table.rowCount() > 0:
            self._footer_presets_table.selectRow(min(row, self._footer_presets_table.rowCount() - 1))

    def _on_footer_preset_up(self) -> None:
        """Handle footer preset up events."""
        self._move_footer_preset_row(-1)

    def _on_footer_preset_down(self) -> None:
        """Handle footer preset down events."""
        self._move_footer_preset_row(1)

    def _move_footer_preset_row(self, offset: int) -> None:
        """Internal helper for move footer preset row."""
        row = self._footer_presets_table.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= self._footer_presets_table.rowCount():
            return
        current_name = self._footer_presets_table.item(row, 0).text() if self._footer_presets_table.item(row, 0) else ""
        current_scope = self._footer_scope_text(row)
        current_format = self._footer_presets_table.item(row, 2).text() if self._footer_presets_table.item(row, 2) else ""
        target_name = self._footer_presets_table.item(target, 0).text() if self._footer_presets_table.item(target, 0) else ""
        target_scope = self._footer_scope_text(target)
        target_format = self._footer_presets_table.item(target, 2).text() if self._footer_presets_table.item(target, 2) else ""
        self._footer_presets_table.item(row, 0).setText(target_name)
        self._footer_scope_combo(row).setCurrentText(self._footer_scope_label(target_scope))
        self._footer_presets_table.item(row, 2).setText(target_format)
        self._footer_presets_table.item(target, 0).setText(current_name)
        self._footer_scope_combo(target).setCurrentText(self._footer_scope_label(current_scope))
        self._footer_presets_table.item(target, 2).setText(current_format)
        self._footer_presets_table.selectRow(target)

    def _on_footer_preset_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle footer preset item changed events."""
        if item.column() != 0:
            if item.column() == 2 and item.row() == self._footer_presets_table.currentRow():
                self._load_selected_footer_format_editor()
            return
        normalized = AppPreferences._normalize_footer_preset_name(item.text())
        if item.text() == normalized:
            return
        self._footer_presets_table.blockSignals(True)
        item.setText(normalized)
        self._footer_presets_table.blockSignals(False)

    def _load_selected_footer_format_editor(self) -> None:
        """Load selected footer format editor."""
        row = self._footer_presets_table.currentRow()
        text = ""
        if row >= 0 and self._footer_presets_table.item(row, 2) is not None:
            text = self._footer_presets_table.item(row, 2).text()
        self._syncing_footer_editor = True
        self._footer_format_editor.setPlainText(text)
        self._syncing_footer_editor = False

    def _on_footer_format_editor_changed(self) -> None:
        """Handle footer format editor changed events."""
        if self._syncing_footer_editor:
            return
        row = self._footer_presets_table.currentRow()
        if row < 0:
            return
        item = self._footer_presets_table.item(row, 2)
        if item is None:
            item = QTableWidgetItem("")
            self._footer_presets_table.setItem(row, 2, item)
        self._footer_presets_table.blockSignals(True)
        item.setText(self._footer_format_editor.toPlainText())
        self._footer_presets_table.blockSignals(False)

    def _footer_scope_combo(self, row: int) -> QComboBox:
        """Internal helper for footer scope combo."""
        combo = self._footer_presets_table.cellWidget(row, 1)
        assert isinstance(combo, QComboBox)
        return combo

    def _footer_scope_text(self, row: int) -> FooterPresetScope:
        """Internal helper for footer scope text."""
        return self._footer_scope_combo(row).currentData() or "all"

    def _build_footer_scope_combo(self, scope: FooterPresetScope) -> QComboBox:
        """Build and return footer scope combo."""
        combo = QComboBox(self._footer_presets_table)
        for label, value in self.FOOTER_SCOPE_OPTIONS:
            combo.addItem(label, value)
        combo.setCurrentText(self._footer_scope_label(scope))
        combo.setToolTip("Choose whether this preset is available for all visualizers, only plot, or only logic.")
        return combo

    def _configure_footer_presets_table_size(self) -> None:
        """Internal helper for configure footer presets table size."""
        header_height = self._footer_presets_table.horizontalHeader().height()
        row_height = self._footer_presets_table.verticalHeader().defaultSectionSize()
        frame_height = self._footer_presets_table.frameWidth() * 2
        visible_height = header_height + (row_height * self.FOOTER_PRESET_VISIBLE_ROWS) + frame_height + 6
        self._footer_presets_table.setMinimumHeight(visible_height)

    @classmethod
    def _footer_scope_label(cls, scope: FooterPresetScope) -> str:
        """Internal helper for footer scope label."""
        for label, value in cls.FOOTER_SCOPE_OPTIONS:
            if value == scope:
                return label
        return "All"
