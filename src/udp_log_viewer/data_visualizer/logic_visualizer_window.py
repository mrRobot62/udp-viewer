from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import re

from .footer_status import (
    build_footer_context,
    format_footer_template,
    format_footer_value,
    parse_footer_timestamp,
    resolve_footer_context_placeholder,
    split_footer_placeholder,
)
from .visualizer_sample import VisualizerSample
from ..preferences import DEFAULT_VISUALIZER_PRESETS
from ..project_runtime import build_project_filename, build_project_title_suffix

try:
    from PyQt5.QtCore import QEvent, Qt, QSettings
    from PyQt5.QtGui import QKeySequence
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QShortcut,
        QSpinBox,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover
    QApplication = None
    QEvent = None
    QKeySequence = None
    Qt = None
    QSettings = None
    QFileDialog = None
    QShortcut = None
    QWidget = object  # type: ignore[assignment]
    _PYQT_AVAILABLE = False

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib import transforms
    _MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover
    FigureCanvas = None
    Figure = None
    transforms = None
    _MATPLOTLIB_AVAILABLE = False

if TYPE_CHECKING:
    from matplotlib.axes import Axes


WINDOW_SIZE_MIN = 1
WINDOW_SIZE_MAX = 5000
def _build_window_size_tooltip(max_samples: int) -> str:
    """Build and return window size tooltip."""
    return f"Number of most recent samples shown when the sliding window is enabled. Allowed range: {WINDOW_SIZE_MIN} to {max(WINDOW_SIZE_MIN, min(max_samples, WINDOW_SIZE_MAX))}."


WINDOW_SIZE_TOOLTIP = _build_window_size_tooltip(WINDOW_SIZE_MAX)
SCREENSHOT_SHORTCUT_TIPS = "Screenshot shortcuts: Ctrl+Shift+S, Cmd+Shift+S, or F12."


@dataclass(slots=True, frozen=True)
class LogicMeasurement:
    """Selected edge or period measurement inside the logic visualizer."""
    field_name: str
    start_index: int
    start_edge: str
    end_index: int | None
    end_edge: str | None
    mode: str


def parse_visualizer_timestamp(timestamp_raw: str) -> datetime | None:
    """Parse a visualizer sample timestamp for logic measurements."""
    return parse_footer_timestamp(timestamp_raw)


def format_measurement_duration(start_time: datetime | None, end_time: datetime | None) -> str:
    """Format a logic measurement span as ``MM:SS.mmm``."""
    if start_time is None or end_time is None:
        return "--:--.---"
    delta_ms = max(0, int(round((end_time - start_time).total_seconds() * 1000.0)))
    minutes, remainder_ms = divmod(delta_ms, 60_000)
    seconds, milliseconds = divmod(remainder_ms, 1000)
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _build_logic_field_lookup(samples: list[VisualizerSample]) -> dict[str, float]:
    """Build and return logic field lookup."""
    if not samples:
        return {}
    latest_values = samples[-1].values_by_name
    return {
        str(field_name).strip().lower(): float(value)
        for field_name, value in latest_values.items()
        if str(field_name).strip() and value is not None
    }


def _resolve_logic_footer_placeholder(key: str, context: dict[str, object], field_lookup: dict[str, float]) -> str | None:
    """Resolve logic footer placeholder."""
    context_value = resolve_footer_context_placeholder(key, context)
    if context_value is not None:
        return context_value
    field_name, format_spec = split_footer_placeholder(key)
    value = field_lookup.get(field_name.lower())
    if value is None:
        return None
    if format_spec:
        return format_footer_value(value, format_spec)
    return str(int(value))


def build_logic_footer_status(samples: list[VisualizerSample], footer_status_format: str = "") -> str:
    """Build and return logic footer status."""
    context = build_footer_context(samples)
    field_lookup = _build_logic_field_lookup(samples)
    formatted = format_footer_template(
        footer_status_format,
        lambda key: _resolve_logic_footer_placeholder(key, context, field_lookup),
    )
    if formatted:
        return formatted
    return " - ".join(
        [
            f"Start: {context['start']}",
            f"Duration: {context['duration']}",
        ]
    )


def choose_measurement_label_anchor(start_x: int, end_x: int, label_text: str) -> tuple[float, str]:
    """Choose measurement label anchor."""
    span = max(0, end_x - start_x)
    min_span_for_center = max(4, len(label_text) // 2)
    if span >= min_span_for_center:
        return (start_x + end_x) / 2.0, "center"
    return end_x + 0.35, "left"


def _logic_level_from_sample(sample: VisualizerSample, field_name: str) -> bool | None:
    """Internal helper for logic level from sample."""
    raw = sample.values_by_name.get(field_name)
    if raw is None:
        return None
    return float(raw) >= 0.5


def find_next_logic_edge(
    samples: list[VisualizerSample],
    field_name: str,
    start_index: int,
    *,
    edge_type: str | None = None,
) -> tuple[int, str] | None:
    """Find next logic edge."""
    if len(samples) < 2:
        return None

    begin = max(1, int(start_index))
    for index in range(begin, len(samples)):
        prev_level = _logic_level_from_sample(samples[index - 1], field_name)
        curr_level = _logic_level_from_sample(samples[index], field_name)
        if prev_level is None or curr_level is None or prev_level == curr_level:
            continue
        current_edge = "rising" if curr_level else "falling"
        if edge_type is None or current_edge == edge_type:
            return index, current_edge
    return None


def build_logic_measurement(
    samples: list[VisualizerSample],
    field_name: str,
    clicked_index: int,
    *,
    same_edge_only: bool,
) -> LogicMeasurement | None:
    """Build and return logic measurement."""
    start_edge = find_next_logic_edge(samples, field_name, clicked_index)
    if start_edge is None:
        return None

    start_index, start_kind = start_edge
    end_edge = find_next_logic_edge(
        samples,
        field_name,
        start_index + 1,
        edge_type=start_kind if same_edge_only else None,
    )
    end_index = end_edge[0] if end_edge is not None else None
    end_kind = end_edge[1] if end_edge is not None else None
    return LogicMeasurement(
        field_name=field_name,
        start_index=start_index,
        start_edge=start_kind,
        end_index=end_index,
        end_edge=end_kind,
        mode="period" if same_edge_only else "edge",
    )


class LogicVisualizerWindow:
    """Window controller for LogicVisualizer."""
    def __init__(
        self,
        config,
        screenshot_dir: str | Path | None = None,
        window_size_presets: tuple[int, ...] | None = None,
        project_name: str | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        """Initialize LogicVisualizerWindow and prepare its initial state."""
        self.config = config
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir is not None else None
        self.window_size_presets = tuple(window_size_presets or DEFAULT_VISUALIZER_PRESETS)
        self.project_name = (project_name or "").strip() or None
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.samples: list[VisualizerSample] = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index: int | None = None
        self.runtime_sliding_window_enabled = bool(config.sliding_window_enabled)
        self.runtime_window_size = self._normalize_runtime_window_size(config.default_window_size)
        self.runtime_show_legend = bool(getattr(config, "show_legend", True))
        self._widget: _LogicVisualizerWindowWidget | None = None

        self._ensure_widget()

    def append_sample(self, sample) -> None:
        """Append sample."""
        self.samples.append(sample)
        self._trim_samples_if_needed()
        if self.auto_refresh_enabled:
            self.refresh_plot()

    def clear_samples(self) -> None:
        """Clear samples."""
        self.samples.clear()
        self.freeze_sample_index = None
        self.rebuild_plot()

    def set_auto_refresh(self, enabled: bool) -> None:
        """Set auto refresh."""
        self.auto_refresh_enabled = enabled
        if enabled:
            self.freeze_sample_index = None
            self.rebuild_plot()
        else:
            self.freeze_sample_index = len(self.samples)

    def set_runtime_sliding_window_enabled(self, enabled: bool) -> None:
        """Set runtime sliding window enabled."""
        self.runtime_sliding_window_enabled = bool(enabled)
        self.rebuild_plot()

    def set_runtime_window_size(self, value: int) -> None:
        """Set runtime window size."""
        self.runtime_window_size = self._normalize_runtime_window_size(value)
        self.rebuild_plot()

    def set_runtime_show_legend(self, enabled: bool) -> None:
        """Set runtime show legend."""
        self.runtime_show_legend = bool(enabled)
        self.rebuild_plot()

    def reset_runtime_window(self) -> None:
        """Reset runtime window."""
        self.runtime_sliding_window_enabled = bool(self.config.sliding_window_enabled)
        self.runtime_window_size = self._normalize_runtime_window_size(self.config.default_window_size)
        self.runtime_show_legend = bool(getattr(self.config, "show_legend", True))
        self.rebuild_plot()

    def refresh_plot(self) -> None:
        """Refresh plot."""
        widget = self._ensure_widget()
        if widget is not None:
            widget.refresh_plot()

    def rebuild_plot(self) -> None:
        """Rebuild plot."""
        widget = self._ensure_widget()
        if widget is not None:
            widget.rebuild_plot()

    def show(self) -> None:
        """Show the underlying Qt window."""
        widget = self._ensure_widget()
        if widget is not None:
            widget.show()
            widget.raise_()
            widget.activateWindow()

    def update_runtime_context(self, *, project_name: str | None, output_dir: str | Path | None) -> None:
        """Update runtime context."""
        self.project_name = (project_name or "").strip() or None
        self.output_dir = Path(output_dir) if output_dir is not None else None
        if self._widget is not None:
            self._widget.setWindowTitle(self._widget._build_window_title())

    def set_initial_position(self, *, slot_index: int, group_offset: int = 0) -> None:
        """Set initial position."""
        widget = self._ensure_widget()
        if widget is not None and hasattr(widget, "set_initial_position"):
            widget.set_initial_position(slot_index=slot_index, group_offset=group_offset)

    def close(self) -> None:
        """Close the underlying Qt window or runtime resource."""
        if self._widget is not None:
            self._widget.close()

    def save_screenshot(self):
        """Save screenshot."""
        widget = self._ensure_widget()
        if widget is None:
            return None
        return widget.save_screenshot()

    def get_visible_samples_for_test(self) -> list[VisualizerSample]:
        """Return visible samples for test."""
        visible = self.samples[: self.freeze_sample_index] if self.freeze_sample_index is not None else self.samples
        if not visible:
            return []
        if not self.runtime_sliding_window_enabled:
            return list(visible)
        return list(visible[-self.runtime_window_size :])

    def _ensure_widget(self):
        """Ensure widget."""
        if self._widget is not None:
            return self._widget
        if not self._can_create_widget():
            return None
        self._widget = _LogicVisualizerWindowWidget(self)
        return self._widget

    def _trim_samples_if_needed(self) -> None:
        """Internal helper for trim samples if needed."""
        max_samples = getattr(self.config, "max_samples", 2000)
        if len(self.samples) <= max_samples:
            return
        overflow = len(self.samples) - max_samples
        del self.samples[:overflow]
        if self.freeze_sample_index is not None:
            self.freeze_sample_index = max(0, self.freeze_sample_index - overflow)

    def _normalize_runtime_window_size(self, value: int | str | None) -> int:
        """Normalize runtime window size."""
        try:
            parsed = int(value) if value is not None else self.config.default_window_size
        except (TypeError, ValueError):
            parsed = self.config.default_window_size
        if parsed <= 0:
            parsed = self.config.default_window_size
        return max(WINDOW_SIZE_MIN, min(parsed, self.config.max_samples, WINDOW_SIZE_MAX))

    @staticmethod
    def _can_create_widget() -> bool:
        """Return whether create widget."""
        if not (_PYQT_AVAILABLE and _MATPLOTLIB_AVAILABLE):
            return False
        try:
            from PyQt5.QtWidgets import QApplication
            return QApplication.instance() is not None
        except Exception:
            return False


if _PYQT_AVAILABLE and _MATPLOTLIB_AVAILABLE:

    class _LogicVisualizerWindowWidget(QWidget):
        _ROW_SPACING = 1.8
        _ROW_LOW_LEVEL = 0.18
        _ROW_HIGH_LEVEL = 0.82
        _ROW_CENTER = 0.50
        _ROW_BG_BOTTOM = 0.02
        _ROW_BG_TOP = 0.98
        _SETTINGS_ORG = "LocalTools"
        _SETTINGS_APP = "UdpLogViewer"
        _SETTINGS_KEY = "logic_visualizer/screenshot_dir"
        _BASE_X = 180
        _BASE_Y = 160
        _OFFSET_X = 36
        _OFFSET_Y = 28

        def __init__(self, controller: LogicVisualizerWindow) -> None:
            super().__init__()
            self._controller = controller
            self._initial_position_applied = False

            self.setWindowTitle(self._build_window_title())
            self.resize(1100, 620)
            self.setFocusPolicy(Qt.StrongFocus)

            self._figure = Figure(figsize=(10, 5))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._canvas.setFocusPolicy(Qt.ClickFocus)
            self._axes: Axes = self._figure.add_subplot(111)

            # Vertical cursor line
            self._cursor_line = self._axes.axvline(x=0, color="gray", linestyle="--", visible=False)
            self._measurement: LogicMeasurement | None = None

            # Mouse tracking on matplotlib canvas
            self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
            self._canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)
            self._canvas.mpl_connect("button_press_event", self._on_mouse_click)

            self._auto_refresh_checkbox = QCheckBox("Auto Refresh")
            self._auto_refresh_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._auto_refresh_checkbox.setChecked(True)
            self._auto_refresh_checkbox.setToolTip("Refresh the logic diagram automatically whenever a new sample arrives.")
            self._auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)

            self._refresh_button = QPushButton("Refresh")
            self._refresh_button.setFocusPolicy(Qt.StrongFocus)
            self._refresh_button.setToolTip("Clear all currently buffered samples and start the logic diagram from an empty buffer.")
            self._refresh_button.clicked.connect(self._on_refresh_clicked)

            self._sliding_window_checkbox = QCheckBox("Sliding Window")
            self._sliding_window_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._sliding_window_checkbox.setChecked(self._controller.runtime_sliding_window_enabled)
            self._sliding_window_checkbox.setToolTip("Limit the logic diagram to the most recent samples instead of showing the full buffer.")
            self._sliding_window_checkbox.stateChanged.connect(self._on_sliding_window_changed)

            self._legend_checkbox = QCheckBox("Legend")
            self._legend_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._legend_checkbox.setChecked(self._controller.runtime_show_legend)
            self._legend_checkbox.setToolTip("Show or hide the legend.")
            self._legend_checkbox.stateChanged.connect(self._on_legend_changed)

            self._window_size_spin = QSpinBox()
            self._window_size_spin.setRange(WINDOW_SIZE_MIN, max(WINDOW_SIZE_MIN, min(self._controller.config.max_samples, WINDOW_SIZE_MAX)))
            self._window_size_spin.setSingleStep(50)
            self._window_size_spin.setKeyboardTracking(False)
            self._window_size_spin.setMinimumWidth(88)
            self._window_size_spin.setToolTip(_build_window_size_tooltip(self._controller.config.max_samples))
            self._window_size_spin.setValue(self._controller.runtime_window_size)
            self._window_size_spin.valueChanged.connect(self._on_window_size_changed)

            self._preset_buttons: list[QPushButton] = []
            for preset in self._controller.window_size_presets:
                button = QPushButton(str(preset))
                button.setFocusPolicy(Qt.StrongFocus)
                button.setToolTip(f"Set the sliding window size to {preset} samples.")
                button.clicked.connect(lambda _checked=False, value=preset: self._set_window_preset(value))
                self._preset_buttons.append(button)

            self._reset_button = QPushButton("Reset")
            self._reset_button.setFocusPolicy(Qt.StrongFocus)
            self._reset_button.setToolTip("Restore the runtime window settings from the slot defaults.")
            self._reset_button.clicked.connect(self._on_reset_window_clicked)

            self._screenshot_button = QPushButton("Screenshot")
            self._screenshot_button.setFocusPolicy(Qt.StrongFocus)
            self._screenshot_button.clicked.connect(self._on_screenshot_clicked)
            self._screenshot_button.setToolTip(SCREENSHOT_SHORTCUT_TIPS)

            self._status_label = QLabel("")
            self._footer_label = QLabel(build_logic_footer_status([]))
            self._footer_label.setWordWrap(True)
            self._footer_label.setMinimumWidth(0)
            self._footer_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self._footer_label.setMaximumHeight(self.fontMetrics().lineSpacing() * 2 + 8)

            top_bar = QHBoxLayout()
            top_bar.addWidget(self._auto_refresh_checkbox)
            top_bar.addWidget(self._refresh_button)
            top_bar.addWidget(self._sliding_window_checkbox)
            top_bar.addWidget(self._legend_checkbox)
            for button in self._preset_buttons:
                top_bar.addWidget(button)
            window_size_label = QLabel("Window Size")
            window_size_label.setToolTip(_build_window_size_tooltip(self._controller.config.max_samples))
            top_bar.addWidget(window_size_label)
            top_bar.addWidget(self._window_size_spin)
            top_bar.addWidget(self._reset_button)
            top_bar.addWidget(self._screenshot_button)
            top_bar.addWidget(self._status_label)
            top_bar.addStretch(1)

            layout = QVBoxLayout()
            layout.addLayout(top_bar)
            layout.addWidget(self._canvas)
            layout.addWidget(self._footer_label)
            self.setLayout(layout)
            self._screenshot_shortcuts = self._build_screenshot_shortcuts()
            self._measurement_shortcuts = self._build_measurement_shortcuts()
            self._configure_tab_order()

            self.rebuild_plot()

        def refresh_plot(self) -> None:
            if not self._controller.auto_refresh_enabled:
                return
            self._render_plot()

        def rebuild_plot(self) -> None:
            self._sync_runtime_controls()
            self._render_plot()

        def save_screenshot(self):
            if QFileDialog is None:
                return None

            default_dir = self._get_default_screenshot_dir()
            suggested_name = self._build_screenshot_filename()

            selected_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Logic Screenshot",
                str(default_dir / suggested_name),
                "PNG Files (*.png)",
            )
            if not selected_path:
                self._status_label.setText("Screenshot canceled")
                return None

            target_path = Path(selected_path)
            if target_path.suffix.lower() != ".png":
                target_path = target_path.with_suffix(".png")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            self._figure.savefig(target_path, dpi=150, bbox_inches="tight")
            self._save_last_screenshot_dir(target_path.parent)
            self._status_label.setText(f"Screenshot saved: {target_path.name}")
            return target_path

        def _get_default_screenshot_dir(self) -> Path:
            if self._controller.output_dir is not None:
                return self._controller.output_dir
            persisted = self._load_last_screenshot_dir()
            if persisted is not None:
                return persisted
            return Path.cwd()

        def _load_last_screenshot_dir(self) -> Path | None:
            settings = self._settings()
            if settings is None:
                return None
            raw = settings.value(self._SETTINGS_KEY, "", type=str)
            if not raw:
                return None
            candidate = Path(raw)
            if candidate.exists() and candidate.is_dir():
                return candidate
            return None

        def _save_last_screenshot_dir(self, path: Path) -> None:
            settings = self._settings()
            if settings is None:
                return
            settings.setValue(self._SETTINGS_KEY, str(path))

        def _build_screenshot_shortcuts(self) -> list[QShortcut]:
            shortcuts: list[QShortcut] = []
            if QShortcut is None or QKeySequence is None:
                return shortcuts
            for sequence in ("Ctrl+Shift+S", "Meta+Shift+S", "F12"):
                shortcut = QShortcut(QKeySequence(sequence), self)
                shortcut.activated.connect(self._on_screenshot_clicked)
                shortcuts.append(shortcut)
            return shortcuts

        def _build_measurement_shortcuts(self) -> list[QShortcut]:
            shortcuts: list[QShortcut] = []
            if QShortcut is None or QKeySequence is None:
                return shortcuts
            space_shortcut = QShortcut(QKeySequence("Space"), self)
            space_shortcut.activated.connect(self._on_space_shortcut)
            shortcuts.append(space_shortcut)

            escape_shortcut = QShortcut(QKeySequence("Esc"), self)
            escape_shortcut.activated.connect(self._on_escape_shortcut)
            shortcuts.append(escape_shortcut)
            return shortcuts

        def _configure_tab_order(self) -> None:
            tab_widgets = [
                self._auto_refresh_checkbox,
                self._refresh_button,
                self._sliding_window_checkbox,
                self._legend_checkbox,
                *self._preset_buttons,
                self._window_size_spin,
                self._reset_button,
                self._screenshot_button,
                self._canvas,
            ]
            for first, second in zip(tab_widgets, tab_widgets[1:]):
                self.setTabOrder(first, second)
            self._tab_widgets = tab_widgets
            for widget in self._tab_widgets:
                widget.installEventFilter(self)

        def eventFilter(self, watched, event):
            if QEvent is not None and event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                if watched in getattr(self, "_tab_widgets", []):
                    self._move_focus(forward=event.key() == Qt.Key_Tab)
                    return True
            return super().eventFilter(watched, event)

        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key_Space:
                self._on_space_shortcut()
                event.accept()
                return
            if event.key() == Qt.Key_Escape:
                self._on_escape_shortcut()
                event.accept()
                return
            super().keyPressEvent(event)

        def _move_focus(self, *, forward: bool) -> None:
            widgets = [widget for widget in getattr(self, "_tab_widgets", []) if widget.isVisible() and widget.isEnabled()]
            if not widgets:
                return
            current = self.focusWidget()
            try:
                index = widgets.index(current)
            except ValueError:
                index = -1 if forward else 0
            next_index = (index + 1) % len(widgets) if forward else (index - 1) % len(widgets)
            widgets[next_index].setFocus(Qt.TabFocusReason)

        def _settings(self):
            if QSettings is None:
                return None
            return QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)

        def _build_screenshot_filename(self) -> str:
            safe_title = self._sanitize_filename(self._controller.config.title or "logic_visualizer")
            return build_project_filename(
                self._controller.project_name,
                safe_title,
                datetime.now().strftime('%Y%m%d_%H%M%S'),
                ".png",
            )

        def _build_window_title(self) -> str:
            return f"{self._controller.config.title or 'Logic Visualizer'}{build_project_title_suffix(self._controller.project_name)}"

        def _on_auto_refresh_changed(self, state: int) -> None:
            enabled = state == Qt.Checked
            if enabled and self._measurement is not None:
                self._clear_measurement(resume=True)
                return
            self._controller.set_auto_refresh(enabled)

        def _on_refresh_clicked(self) -> None:
            self._controller.clear_samples()

        def _on_sliding_window_changed(self, state: int) -> None:
            self._controller.set_runtime_sliding_window_enabled(state == Qt.Checked)

        def _on_legend_changed(self, state: int) -> None:
            self._controller.set_runtime_show_legend(state == Qt.Checked)

        def _on_window_size_changed(self, value: int) -> None:
            self._controller.set_runtime_window_size(value)

        def _set_window_preset(self, value: int) -> None:
            self._window_size_spin.setValue(min(value, self._controller.config.max_samples, WINDOW_SIZE_MAX))

        def _on_reset_window_clicked(self) -> None:
            self._controller.reset_runtime_window()

        def _on_screenshot_clicked(self) -> None:
            self.save_screenshot()

        def _on_space_shortcut(self) -> None:
            self._auto_refresh_checkbox.setChecked(not self._auto_refresh_checkbox.isChecked())

        def _on_escape_shortcut(self) -> None:
            if self._measurement is None:
                return
            self._clear_measurement(resume=True)

        def _sync_runtime_controls(self) -> None:
            self._auto_refresh_checkbox.blockSignals(True)
            self._sliding_window_checkbox.blockSignals(True)
            self._legend_checkbox.blockSignals(True)
            self._window_size_spin.blockSignals(True)
            self._auto_refresh_checkbox.setChecked(self._controller.auto_refresh_enabled)
            self._sliding_window_checkbox.setChecked(self._controller.runtime_sliding_window_enabled)
            self._legend_checkbox.setChecked(self._controller.runtime_show_legend)
            self._window_size_spin.setRange(
                WINDOW_SIZE_MIN,
                max(WINDOW_SIZE_MIN, min(self._controller.config.max_samples, WINDOW_SIZE_MAX)),
            )
            self._window_size_spin.setValue(self._controller.runtime_window_size)
            self._window_size_spin.setEnabled(self._controller.runtime_sliding_window_enabled)
            self._auto_refresh_checkbox.blockSignals(False)
            self._sliding_window_checkbox.blockSignals(False)
            self._legend_checkbox.blockSignals(False)
            self._window_size_spin.blockSignals(False)

        def _on_mouse_move(self, event) -> None:
            if event.inaxes != self._axes:
                return
            if event.xdata is None:
                return

            self._cursor_line.set_xdata([event.xdata, event.xdata])
            self._cursor_line.set_visible(True)
            self._canvas.draw_idle()

        def _on_mouse_leave(self, event) -> None:
            self._cursor_line.set_visible(False)
            self._canvas.draw_idle()

        def _on_mouse_click(self, event) -> None:
            if event.inaxes != self._axes or event.button != 1:
                return
            if event.xdata is None or event.ydata is None:
                return

            visible_samples = self._get_visible_samples()
            active_fields = self._get_active_fields()
            if not visible_samples or not active_fields:
                return

            self.setFocus(Qt.MouseFocusReason)
            field = self._field_at_y(event.ydata, active_fields)
            if field is None:
                return

            clicked_index = max(0, min(int(round(event.xdata)), len(visible_samples) - 1))
            same_edge_only = self._shift_pressed()
            measurement = build_logic_measurement(
                visible_samples,
                field.field_name,
                clicked_index,
                same_edge_only=same_edge_only,
            )
            if measurement is None:
                self._status_label.setText(f"No next edge found for {field.field_name}")
                return

            self._pause_for_measurement()
            self._measurement = measurement
            if measurement.end_index is None:
                self._status_label.setText(f"{field.field_name}: no matching end edge found")
            else:
                self._status_label.setText(self._build_measurement_label(visible_samples, measurement))
            self._render_plot()

        def _render_plot(self) -> None:
            self.setWindowTitle(self._build_window_title())
            self._axes.clear()

            visible_samples = self._get_visible_samples()
            active_fields = self._get_active_fields()

            x_values = list(range(len(visible_samples)))
            plotted_count = 0

            for idx, field in enumerate(active_fields):
                base = idx * self._ROW_SPACING
                y_values = []
                logic_states = []
                has_any = False
                low_level = base + self._ROW_LOW_LEVEL
                high_level = base + self._ROW_HIGH_LEVEL

                for sample in visible_samples:
                    raw = sample.values_by_name.get(field.field_name)
                    if raw is None:
                        y_values.append(None)
                        logic_states.append(False)
                        continue

                    logic_high = float(raw) >= 0.5
                    logic_states.append(logic_high)
                    y_values.append(high_level if logic_high else low_level)
                    has_any = True

                if not has_any:
                    continue

                row_color = getattr(field, "color", None) or None

                self._axes.axhspan(
                    base + self._ROW_BG_BOTTOM,
                    base + self._ROW_BG_TOP,
                    color="#f5f5f5",
                    alpha=0.65,
                    zorder=0,
                )

                self._axes.fill_between(
                    x_values,
                    [low_level] * len(x_values),
                    y_values,
                    where=logic_states,
                    step="post",
                    color=row_color,
                    alpha=0.22,
                    linewidth=0.0,
                    interpolate=True,
                    zorder=2,
                )

                self._axes.step(
                    x_values,
                    y_values,
                    where="post",
                    color=row_color,
                    linestyle="-",
                    linewidth=2.2,
                    label=field.field_name,
                    zorder=3,
                )

                self._axes.axhline(low_level, color="#d0d0d0", linestyle=":", linewidth=0.8, zorder=1)
                self._axes.axhline(high_level, color="#d0d0d0", linestyle=":", linewidth=0.8, zorder=1)
                self._axes.axhline(base + self._ROW_SPACING, color="#8c8c8c", linestyle="-", linewidth=1.0, zorder=1)
                plotted_count += 1

            self._apply_axis_settings(active_fields, len(visible_samples))
            self._footer_label.setText(
                build_logic_footer_status(
                    self._controller.samples,
                    self._controller.config.footer_status_format,
                )
            )

            if plotted_count > 0 and self._controller.runtime_show_legend:
                self._axes.legend(loc="upper right")

            # --- X axis: timestamp labels ---
            visible_samples = self._get_visible_samples()
            if visible_samples:
                count = len(visible_samples)

                step = max(1, count // 8)
                indices = list(range(0, count, step))
                if indices[-1] != count - 1:
                    indices.append(count - 1)

                labels = [
                    self._format_time_label(visible_samples[i].timestamp_raw)
                    for i in indices
                ]

                self._axes.set_xticks(indices)
                self._axes.set_xticklabels(labels, rotation=45, ha="right")

            self._draw_measurement_overlay(visible_samples, active_fields)

            # Keep cursor hidden after full redraw until mouse enters again
            self._cursor_line = self._axes.axvline(x=0, color="gray", linestyle="--", visible=False)
            self._figure.tight_layout()
            self._canvas.draw_idle()

        def _apply_axis_settings(self, active_fields, visible_count: int) -> None:
            self._axes.set_xlabel(getattr(self._controller.config.x_axis, "label", "") or "Samples")
            self._axes.set_ylabel("Logic Channels")

            yticks = []
            yticklabels = []
            for idx, field in enumerate(active_fields):
                center = idx * self._ROW_SPACING + self._ROW_CENTER
                yticks.append(center)
                yticklabels.append(field.field_name)

            if yticks:
                self._axes.set_yticks(yticks)
                self._axes.set_yticklabels(yticklabels)

            if active_fields:
                top = (len(active_fields) - 1) * self._ROW_SPACING + (self._ROW_SPACING + 0.2)
                self._axes.set_ylim(-0.1, top)
            else:
                self._axes.set_ylim(-0.3, 1.3)

            if visible_count:
                self._axes.set_xlim(0, max(visible_count - 1, 1))

            self._axes.grid(True, axis="x")

        def set_initial_position(self, *, slot_index: int, group_offset: int = 0) -> None:
            if self._initial_position_applied:
                return
            offset_index = slot_index + max(0, group_offset) * 2
            self.move(
                self._BASE_X + offset_index * self._OFFSET_X,
                self._BASE_Y + offset_index * self._OFFSET_Y,
            )
            self._initial_position_applied = True

        def _get_visible_samples(self) -> list[VisualizerSample]:
            if self._controller.freeze_sample_index is not None:
                visible = self._controller.samples[: self._controller.freeze_sample_index]
            else:
                visible = self._controller.samples

            if not visible:
                return []

            if not self._controller.runtime_sliding_window_enabled:
                return visible
            return visible[-self._controller.runtime_window_size :]

        def _get_active_fields(self):
            return [
                field for field in self._controller.config.fields[:8]
                if getattr(field, "active", False) and getattr(field, "plot", True)
            ]

        def _field_at_y(self, y_value: float, active_fields):
            for idx, field in enumerate(active_fields):
                base = idx * self._ROW_SPACING
                if base <= y_value <= (base + self._ROW_SPACING):
                    return field
            return None

        def _shift_pressed(self) -> bool:
            if QApplication is None:
                return False
            return bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)

        def _pause_for_measurement(self) -> None:
            self._controller.set_auto_refresh(False)
            self._set_auto_refresh_checkbox_state(False)

        def _clear_measurement(self, *, resume: bool) -> None:
            self._measurement = None

            if not resume:
                self._set_auto_refresh_checkbox_state(self._controller.auto_refresh_enabled)
                self._render_plot()
                return

            self._controller.set_auto_refresh(True)
            self._set_auto_refresh_checkbox_state(True)

        def _set_auto_refresh_checkbox_state(self, enabled: bool) -> None:
            self._auto_refresh_checkbox.blockSignals(True)
            self._auto_refresh_checkbox.setChecked(enabled)
            self._auto_refresh_checkbox.blockSignals(False)

        def _draw_measurement_overlay(self, visible_samples: list[VisualizerSample], active_fields) -> None:
            measurement = self._measurement
            if measurement is None:
                return

            field_index = next(
                (idx for idx, field in enumerate(active_fields) if field.field_name == measurement.field_name),
                None,
            )
            if field_index is None or measurement.start_index >= len(visible_samples):
                self._measurement = None
                return

            row_y = field_index * self._ROW_SPACING + 1.08
            start_x = measurement.start_index
            self._axes.axvline(start_x, color="#d62728", linestyle="--", linewidth=1.6, zorder=6)

            if measurement.end_index is None or measurement.end_index >= len(visible_samples):
                return

            end_x = measurement.end_index
            self._axes.axvline(end_x, color="#1f77b4", linestyle="--", linewidth=1.6, zorder=6)
            self._axes.annotate(
                "",
                xy=(end_x, row_y),
                xytext=(start_x, row_y),
                arrowprops={"arrowstyle": "<->", "linestyle": "--", "color": "#444444", "linewidth": 1.2},
                zorder=7,
            )
            label_text = self._build_measurement_label(visible_samples, measurement)
            label_x, label_align = choose_measurement_label_anchor(start_x, end_x, label_text)
            self._axes.text(
                label_x,
                row_y + 0.08,
                label_text,
                ha=label_align,
                va="bottom",
                fontsize=9,
                color="#222222",
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "#ffffff", "edgecolor": "#cccccc", "alpha": 0.92},
                zorder=8,
            )

        def _build_measurement_label(self, visible_samples: list[VisualizerSample], measurement: LogicMeasurement) -> str:
            if measurement.end_index is None:
                prefix = "PERIOD" if measurement.mode == "period" else "EDGE"
                return f"{prefix} --:--.---"

            start_time = parse_visualizer_timestamp(visible_samples[measurement.start_index].timestamp_raw)
            end_time = parse_visualizer_timestamp(visible_samples[measurement.end_index].timestamp_raw)
            prefix = "PERIOD" if measurement.mode == "period" else "EDGE"
            return f"{prefix} {format_measurement_duration(start_time, end_time)}"

        def _format_time_label(self, timestamp_raw: str) -> str:
            if not timestamp_raw:
                return ""

            try:
                # erwartet Format: YYYYMMDD-HH:MM:SS.xxx
                time_part = timestamp_raw.split(" ")[0]
                if "-" in time_part:
                    time_part = time_part.split("-")[1]
                if "." in time_part:
                    time_part = time_part.split(".")[0]
                return time_part
            except Exception:
                return ""

        @staticmethod
        def _sanitize_filename(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "logic_visualizer"

else:

    class _LogicVisualizerWindowWidget:  # pragma: no cover
        def __init__(self, controller: LogicVisualizerWindow) -> None:
            self._controller = controller

        def refresh_plot(self) -> None:
            pass

        def rebuild_plot(self) -> None:
            pass

        def show(self) -> None:
            pass

        def raise_(self) -> None:
            pass

        def activateWindow(self) -> None:
            pass

        def close(self) -> None:
            pass

        def save_screenshot(self):
            return None
