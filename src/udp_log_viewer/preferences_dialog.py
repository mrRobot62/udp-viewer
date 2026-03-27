from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .preferences import AppPreferences


class PreferencesDialog(QDialog):
    def __init__(self, preferences: AppPreferences, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(620, 420)

        root = QVBoxLayout(self)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_visualizer_tab(), "Visualizer")
        root.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply,
            parent=self,
        )
        self._restore_button = QPushButton("Restore Defaults")
        buttons.addButton(self._restore_button, QDialogButtonBox.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._apply_button = buttons.button(QDialogButtonBox.Apply)
        root.addWidget(buttons)

        self.set_preferences(preferences)

    def apply_button(self) -> QPushButton:
        return self._apply_button

    def restore_button(self) -> QPushButton:
        return self._restore_button

    def result_preferences(self) -> AppPreferences:
        return AppPreferences(
            language=self._language.currentData() or "de",
            autoscroll_default=self._autoscroll_default.isChecked(),
            timestamp_default=self._timestamp_default.isChecked(),
            max_lines_default=int(self._max_lines_default.value()),
            visualizer_presets=(
                int(self._preset_1.value()),
                int(self._preset_2.value()),
                int(self._preset_3.value()),
                int(self._preset_4.value()),
            ),
            plot_sliding_window_default=self._plot_sliding_default.isChecked(),
            plot_window_size_default=int(self._plot_window_size_default.value()),
            logic_sliding_window_default=self._logic_sliding_default.isChecked(),
            logic_window_size_default=int(self._logic_window_size_default.value()),
        )

    def set_preferences(self, preferences: AppPreferences) -> None:
        self._language.setCurrentIndex(max(0, self._language.findData(preferences.language)))
        self._autoscroll_default.setChecked(preferences.autoscroll_default)
        self._timestamp_default.setChecked(preferences.timestamp_default)
        self._max_lines_default.setValue(preferences.max_lines_default)
        self._preset_1.setValue(preferences.visualizer_presets[0])
        self._preset_2.setValue(preferences.visualizer_presets[1])
        self._preset_3.setValue(preferences.visualizer_presets[2])
        self._preset_4.setValue(preferences.visualizer_presets[3])
        self._plot_sliding_default.setChecked(preferences.plot_sliding_window_default)
        self._plot_window_size_default.setValue(preferences.plot_window_size_default)
        self._logic_sliding_default.setChecked(preferences.logic_sliding_window_default)
        self._logic_window_size_default.setValue(preferences.logic_window_size_default)

    def _build_general_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QFormLayout(tab)

        self._language = QComboBox(tab)
        self._language.addItem("Deutsch", "de")
        self._language.addItem("English", "en")

        self._autoscroll_default = QCheckBox("Enabled", tab)
        self._timestamp_default = QCheckBox("Enabled", tab)
        self._max_lines_default = QSpinBox(tab)
        self._max_lines_default.setRange(1000, 500000)

        layout.addRow("Language", self._language)
        layout.addRow("Auto-Scroll Default", self._autoscroll_default)
        layout.addRow("Timestamp Default", self._timestamp_default)
        layout.addRow("Max Lines Default", self._max_lines_default)
        return tab

    def _build_visualizer_tab(self) -> QWidget:
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("Window Presets"))
        self._preset_1 = self._build_preset_spin(tab)
        self._preset_2 = self._build_preset_spin(tab)
        self._preset_3 = self._build_preset_spin(tab)
        self._preset_4 = self._build_preset_spin(tab)
        for widget in (self._preset_1, self._preset_2, self._preset_3, self._preset_4):
            presets_row.addWidget(widget)
        presets_row.addStretch(1)
        layout.addLayout(presets_row)

        form = QFormLayout()
        self._plot_sliding_default = QCheckBox("Enabled", tab)
        self._plot_window_size_default = QSpinBox(tab)
        self._plot_window_size_default.setRange(10, 100000)
        self._logic_sliding_default = QCheckBox("Enabled", tab)
        self._logic_window_size_default = QSpinBox(tab)
        self._logic_window_size_default.setRange(10, 100000)

        form.addRow("Plot Sliding Window Default", self._plot_sliding_default)
        form.addRow("Plot Default Window Size", self._plot_window_size_default)
        form.addRow("Logic Sliding Window Default", self._logic_sliding_default)
        form.addRow("Logic Default Window Size", self._logic_window_size_default)
        layout.addLayout(form)
        layout.addStretch(1)
        return tab

    @staticmethod
    def _build_preset_spin(parent: QWidget) -> QSpinBox:
        spin = QSpinBox(parent)
        spin.setRange(10, 100000)
        spin.setSingleStep(10)
        return spin
