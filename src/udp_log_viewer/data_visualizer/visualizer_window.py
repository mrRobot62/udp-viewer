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
from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample
from ..preferences import DEFAULT_VISUALIZER_PRESETS
from ..project_runtime import build_project_filename, build_project_title_suffix

try:
    from PyQt5.QtCore import QEvent, Qt, QSettings
    from PyQt5.QtGui import QKeySequence
    from PyQt5.QtWidgets import (
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
except Exception:  # pragma: no cover - fallback for non-Qt test environments
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
    from matplotlib.ticker import MultipleLocator
    from matplotlib import transforms
    _MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover - fallback for non-GUI test environments
    FigureCanvas = None
    Figure = None
    MultipleLocator = None
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
class PlotMeasurement:
    """Selected measurement span for the plot visualizer."""
    start_index: int
    end_index: int | None


def parse_plot_timestamp(timestamp_raw: str) -> datetime | None:
    """Parse a visualizer sample timestamp for plot measurements."""
    return parse_footer_timestamp(timestamp_raw)


def format_plot_measurement_duration(start_time: datetime | None, end_time: datetime | None) -> str:
    """Format a plot measurement span as ``MM:SS.hh``."""
    if start_time is None or end_time is None:
        return "--:--.--"
    delta_ms = max(0, int(round((end_time - start_time).total_seconds() * 1000.0)))
    minutes, remainder_ms = divmod(delta_ms, 60_000)
    seconds, milliseconds = divmod(remainder_ms, 1000)
    hundredths = milliseconds // 10
    return f"{minutes:02d}:{seconds:02d}.{hundredths:02d}"


def _build_plot_stats_text(series_metadata: list[dict[str, object]]) -> str:
    """Build and return plot stats text."""
    parts: list[str] = []
    for meta in series_metadata:
        field_name = str(meta.get("field_name", "")).strip()
        if not field_name:
            continue
        render_style = str(meta.get("render_style", "") or "").strip().lower()
        if render_style != "line":
            continue
        if not bool(meta.get("statistic", True)):
            continue
        unit = str(meta.get("unit", "") or "")
        parts.append(
            f"{field_name} MAX/Mean/Current:{_format_plot_value(meta.get('max'), unit)}/{_format_plot_value(meta.get('mean'), unit)}/{_format_plot_value(meta.get('latest'), unit)}"
        )
    return " - ".join(parts)


def _build_plot_field_lookup(series_metadata: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Build and return plot field lookup."""
    return {
        str(meta.get("field_name", "")).strip().lower(): meta
        for meta in series_metadata
        if str(meta.get("field_name", "")).strip()
    }


def _resolve_plot_footer_placeholder(key: str, context: dict[str, object], series_metadata: list[dict[str, object]]) -> str | None:
    """Resolve plot footer placeholder."""
    normalized = key.strip()
    if not normalized:
        return None
    direct = resolve_footer_context_placeholder(normalized, context)
    if direct is not None:
        return direct

    parts = normalized.split(":")
    field_lookup = _build_plot_field_lookup(series_metadata)
    if len(parts) >= 2 and parts[0].strip().lower() in {"current", "latest", "mean", "avg", "max"}:
        metric = parts[0].strip().lower()
        field_name = parts[1].strip().lower()
        format_spec = ":".join(parts[2:]).strip() if len(parts) > 2 else ""
        meta = field_lookup.get(field_name)
        if meta is None:
            return None
        unit = str(meta.get("unit", "") or "")
        metric_aliases = {
            "current": "latest",
            "latest": "latest",
            "mean": "mean",
            "avg": "mean",
            "max": "max",
        }
        metric_key = metric_aliases.get(metric)
        if metric_key is None:
            return None
        return _format_plot_value(meta.get(metric_key), unit, format_spec=format_spec)

    field_name, format_spec = split_footer_placeholder(normalized)
    meta = field_lookup.get(field_name.lower())
    if meta is None:
        return None
    return _format_plot_value(meta.get("latest"), str(meta.get("unit", "") or ""), format_spec=format_spec)


def build_plot_footer_status(
    samples: list[VisualizerSample],
    series_metadata: list[dict[str, object]],
    footer_status_format: str = "",
) -> str:
    """Build and return plot footer status."""
    context = build_footer_context(samples)
    stats_text = _build_plot_stats_text(series_metadata)
    formatted = format_footer_template(
        footer_status_format,
        lambda key: _resolve_plot_footer_placeholder(key, context, series_metadata),
    )
    if formatted:
        return formatted
    parts = [
        f"Start: {context['start']}",
        f"Duration: {context['duration']}",
    ]
    if stats_text:
        parts.append(stats_text)
    return " - ".join(parts)


def advance_plot_measurement(measurement: PlotMeasurement | None, clicked_index: int) -> PlotMeasurement:
    """Advance plot measurement."""
    if measurement is None or measurement.end_index is not None:
        return PlotMeasurement(start_index=clicked_index, end_index=None)
    return PlotMeasurement(start_index=measurement.start_index, end_index=clicked_index)


def choose_plot_measurement_label_anchor(start_x: int, end_x: int, label_text: str) -> tuple[float, str]:
    """Choose plot measurement label anchor."""
    span = abs(end_x - start_x)
    min_span_for_center = max(4, len(label_text) // 2)
    if span >= min_span_for_center:
        return (start_x + end_x) / 2.0, "center"
    return max(start_x, end_x) + 0.35, "left"


class VisualizerWindow:
    """Window controller for Visualizer."""
    def __init__(
        self,
        config: VisualizerConfig,
        screenshot_dir: str | Path | None = None,
        window_size_presets: tuple[int, ...] | None = None,
        project_name: str | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        """Initialize VisualizerWindow and prepare its initial state."""
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
        self.runtime_show_legend = bool(config.show_legend)
        self.refresh_request_count = 0
        self.rebuild_request_count = 0
        self._widget: _VisualizerWindowWidget | None = None
        self._ensure_widget()

    def append_sample(self, sample: VisualizerSample) -> None:
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
            return
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
        self.runtime_show_legend = bool(self.config.show_legend)
        self.rebuild_plot()

    def refresh_plot(self) -> None:
        """Refresh plot."""
        self.refresh_request_count += 1
        widget = self._ensure_widget()
        if widget is not None:
            widget.refresh_plot()

    def rebuild_plot(self) -> None:
        """Rebuild plot."""
        self.rebuild_request_count += 1
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

    def save_screenshot(self) -> Path | None:
        """Save screenshot."""
        widget = self._ensure_widget()
        if widget is None:
            return None
        return widget.save_screenshot()

    def is_gui_available(self) -> bool:
        """Return whether gui available."""
        return self._ensure_widget() is not None

    def get_visible_samples_for_test(self) -> list[VisualizerSample]:
        """Return visible samples for test."""
        visible = self.samples[: self.freeze_sample_index] if self.freeze_sample_index is not None else self.samples
        if not visible:
            return []
        if not self.runtime_sliding_window_enabled:
            return list(visible)
        return list(visible[-self.runtime_window_size :])

    def _ensure_widget(self) -> "_VisualizerWindowWidget | None":
        """Ensure widget."""
        if self._widget is not None:
            return self._widget
        if not self._can_create_widget():
            return None
        self._widget = _VisualizerWindowWidget(self)
        return self._widget

    def _trim_samples_if_needed(self) -> None:
        """Internal helper for trim samples if needed."""
        max_samples = self.config.max_samples
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

    class _VisualizerWindowWidget(QWidget):
        _SETTINGS_ORG = "LocalTools"
        _SETTINGS_APP = "UdpLogViewer"
        _SETTINGS_KEY = "visualizer/screenshot_dir"
        _BASE_X = 120
        _BASE_Y = 120
        _OFFSET_X = 36
        _OFFSET_Y = 28

        def __init__(self, controller: VisualizerWindow) -> None:
            super().__init__()
            self._controller = controller
            self._initial_position_applied = False

            self.setWindowTitle(self._build_window_title())
            self.resize(980, 560)
            self.setFocusPolicy(Qt.StrongFocus)

            self._figure = Figure(figsize=(8, 4))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._canvas.setFocusPolicy(Qt.ClickFocus)
            self._axes_y1: Axes = self._figure.add_subplot(111)
            self._axes_y2: Axes = self._axes_y1.twinx()
            self._annotation = None
            self._hover_line_y1 = self._axes_y1.axhline(y=0, color="#666666", linestyle=":", linewidth=0.9, visible=False)
            self._hover_line_y2 = self._axes_y2.axhline(y=0, color="#666666", linestyle=":", linewidth=0.9, visible=False)
            self._series_metadata: list[dict[str, object]] = []
            self._measurement: PlotMeasurement | None = None
            self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
            self._canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)
            self._canvas.mpl_connect("button_press_event", self._on_mouse_click)

            self._auto_refresh_checkbox = QCheckBox("Auto Refresh")
            self._auto_refresh_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._auto_refresh_checkbox.setChecked(True)
            self._auto_refresh_checkbox.setToolTip("Refresh the plot automatically whenever a new sample arrives.")
            self._auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)

            self._refresh_button = QPushButton("Refresh")
            self._refresh_button.setFocusPolicy(Qt.StrongFocus)
            self._refresh_button.setToolTip("Clear all currently buffered samples and start the plot from an empty buffer.")
            self._refresh_button.clicked.connect(self._on_refresh_clicked)

            self._sliding_window_checkbox = QCheckBox("Sliding Window")
            self._sliding_window_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._sliding_window_checkbox.setChecked(self._controller.runtime_sliding_window_enabled)
            self._sliding_window_checkbox.setToolTip("Limit the plot to the most recent samples instead of showing the full buffer.")
            self._sliding_window_checkbox.stateChanged.connect(self._on_sliding_window_changed)

            self._legend_checkbox = QCheckBox("Legend")
            self._legend_checkbox.setFocusPolicy(Qt.StrongFocus)
            self._legend_checkbox.setChecked(self._controller.runtime_show_legend)
            self._legend_checkbox.setToolTip("Show or hide the plot legend.")
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
            self._footer_label = QLabel(build_plot_footer_status([], []))
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

        def save_screenshot(self) -> Path | None:
            if QFileDialog is None:
                return None

            default_dir = self._get_default_screenshot_dir()
            suggested_name = self._build_screenshot_filename()

            selected_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Screenshot",
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

        def _settings(self) -> QSettings | None:
            if QSettings is None:
                return None
            return QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)

        def _build_screenshot_filename(self) -> str:
            safe_title = self._sanitize_filename(self._controller.config.title or "visualizer")
            return build_project_filename(
                self._controller.project_name,
                safe_title,
                datetime.now().strftime('%Y%m%d_%H%M%S'),
                ".png",
            )

        def _build_window_title(self) -> str:
            return f"{self._controller.config.title or 'Data Visualizer'}{build_project_title_suffix(self._controller.project_name)}"

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

        def _render_plot(self) -> None:
            self.setWindowTitle(self._build_window_title())
            self._annotation = None
            self._axes_y1.clear()
            self._axes_y2.clear()
            self._hover_line_y1 = self._axes_y1.axhline(y=0, color="#666666", linestyle=":", linewidth=0.9, visible=False)
            self._hover_line_y2 = self._axes_y2.axhline(y=0, color="#666666", linestyle=":", linewidth=0.9, visible=False)
            self._series_metadata = []

            samples = self._get_visible_samples()
            plotted_y1 = False
            plotted_y2 = False
            x_values = list(range(len(samples)))

            for field in self._controller.config.fields:
                if not field.active:
                    continue
                if not field.plot or not field.field_name:
                    continue

                y_values = [sample.values_by_name.get(field.field_name) for sample in samples]
                if not any(value is not None for value in y_values):
                    continue

                label = field.field_name
                if field.unit:
                    label = f"{label} [{field.unit}]"

                target_axis = self._axes_y2 if field.axis == "Y2" else self._axes_y1
                plot_kwargs = {
                    "label": label,
                    "color": field.color or None,
                    "linestyle": _to_matplotlib_linestyle(field.line_style),
                }

                if getattr(field, "render_style", "Line") == "Step":
                    line = target_axis.step(x_values, y_values, where="post", **plot_kwargs)[0]
                else:
                    line = target_axis.plot(x_values, y_values, **plot_kwargs)[0]

                numeric_values = [float(value) for value in y_values if value is not None]
                if numeric_values:
                    self._series_metadata.append(
                        {
                            "axis": target_axis,
                            "field_name": field.field_name,
                            "unit": field.unit,
                            "statistic": getattr(field, "statistic", True),
                            "render_style": field.render_style,
                            "color": line.get_color(),
                            "x_values": list(x_values),
                            "y_values": list(y_values),
                            "latest": numeric_values[-1],
                            "mean": sum(numeric_values) / len(numeric_values),
                            "max": max(numeric_values),
                            "latest_index": max(i for i, value in enumerate(y_values) if value is not None),
                        }
                    )

                if field.axis == "Y2":
                    plotted_y2 = True
                else:
                    plotted_y1 = True

            self._apply_axis_settings(samples)

            self._footer_label.setText(
                build_plot_footer_status(
                    self._controller.samples,
                    self._series_metadata,
                    self._controller.config.footer_status_format,
                )
            )

            self._draw_end_labels()
            if plotted_y1 and self._controller.runtime_show_legend:
                self._axes_y1.legend(loc="upper left")
            if plotted_y2 and self._controller.runtime_show_legend:
                self._axes_y2.legend(loc="upper right")

            self._draw_measurement_overlay(samples)
            self._figure.subplots_adjust(bottom=0.24)
            self._canvas.draw_idle()

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

        def _apply_axis_settings(self, visible_samples: list[VisualizerSample]) -> None:
            x_axis = self._controller.config.x_axis
            y1_axis = self._controller.config.y1_axis
            y2_axis = self._controller.config.y2_axis
            y2_binary_step = _uses_binary_step_axis(self._controller.config.fields, axis="Y2")

            self._axes_y1.set_xlabel("Time")
            self._axes_y1.set_ylabel(y1_axis.label or "Y1")
            self._axes_y2.set_ylabel(y2_axis.label or "Y2")
            self._apply_axis_visual_identity(self._axes_y1, label_color="#202020", spine_side="left")
            self._apply_axis_visual_identity(self._axes_y2, label_color="#8a2b2b", spine_side="right")

            # Only primary axis shows x labels
            self._axes_y2.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)

            if y1_axis.logarithmic:
                self._axes_y1.set_yscale("log")
            if y2_axis.logarithmic:
                self._axes_y2.set_yscale("log")

            if y1_axis.min_value is not None or y1_axis.max_value is not None:
                self._axes_y1.set_ylim(bottom=y1_axis.min_value, top=y1_axis.max_value)
            self._apply_tick_config(self._axes_y1, y1_axis)
            if y2_binary_step:
                self._axes_y2.set_ylim(bottom=-0.1, top=1.15)
                self._axes_y2.set_yticks([0.0, 1.0])
                self._axes_y2.set_yticklabels(["0", "1"])
            elif y2_axis.min_value is not None or y2_axis.max_value is not None:
                self._axes_y2.set_ylim(bottom=y2_axis.min_value, top=y2_axis.max_value)
                self._apply_tick_config(self._axes_y2, y2_axis)

            if visible_samples:
                self._axes_y1.set_xlim(left=0, right=max(len(visible_samples) - 1, 1))

                tick_positions = self._build_tick_positions(len(visible_samples))
                tick_labels = [self._format_time_label(visible_samples[i].timestamp_raw) for i in tick_positions]

                self._axes_y1.set_xticks(tick_positions)
                self._axes_y1.set_xticklabels(tick_labels)
                self._axes_y1.tick_params(axis="x", labelbottom=True)

                for label in self._axes_y1.get_xticklabels():
                    label.set_rotation(45)
                    label.set_horizontalalignment("right")
                    label.set_visible(True)
            else:
                self._axes_y1.set_xlim(left=0, right=1)
                self._axes_y1.set_xticks([])
                self._axes_y1.tick_params(axis="x", labelbottom=True)

            self._axes_y1.grid(True)
            self._axes_y1.grid(True, which="minor", alpha=0.25)
            self._axes_y2.grid(False)

        def _apply_tick_config(self, axis: Axes, axis_config: VisualizerAxisConfig) -> None:
            if MultipleLocator is None or axis_config.logarithmic:
                return
            major_step = self._normalized_major_tick_step(axis_config)
            if major_step is not None:
                axis.yaxis.set_major_locator(MultipleLocator(major_step))
            if self._is_temperature_axis(axis_config):
                axis.yaxis.set_minor_locator(MultipleLocator(5.0))

        @staticmethod
        def _is_temperature_axis(axis_config: VisualizerAxisConfig) -> bool:
            label = (axis_config.label or "").strip().lower()
            return "temp" in label or "temperature" in label

        @staticmethod
        def _normalized_major_tick_step(axis_config: VisualizerAxisConfig) -> float | None:
            step = axis_config.major_tick_step
            if step is None or step <= 0:
                return None
            max_value = axis_config.max_value
            upper_bound = max(1.0, (max_value / 5.0) if max_value is not None and max_value > 0 else step)
            return min(max(1.0, step), upper_bound)

        def _draw_end_labels(self) -> None:
            if not self._series_metadata:
                return
            offsets_by_axis = {
                self._axes_y1: _build_staggered_label_offsets(self._series_metadata, self._axes_y1),
                self._axes_y2: _build_staggered_label_offsets(self._series_metadata, self._axes_y2),
            }
            for meta in self._series_metadata:
                axis = meta["axis"]
                latest_value = meta["latest"]
                latest_index = meta["latest_index"]
                color = meta["color"]
                vertical_offset = offsets_by_axis.get(axis, {}).get(id(meta), 0)
                axis.annotate(
                    _format_plot_value(latest_value),
                    xy=(latest_index, latest_value),
                    xytext=(8, vertical_offset),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    color=color,
                    fontsize=9,
                    bbox={
                        "boxstyle": "round,pad=0.2",
                        "facecolor": "white",
                        "edgecolor": color,
                        "alpha": 0.88,
                    },
                    annotation_clip=False,
                )

        def _apply_axis_visual_identity(self, axis: Axes, *, label_color: str, spine_side: str) -> None:
            axis.yaxis.set_label_position(spine_side)
            if spine_side == "left":
                axis.yaxis.tick_left()
            else:
                axis.yaxis.tick_right()
            axis.tick_params(axis="y", colors=label_color)
            axis.yaxis.label.set_color(label_color)
            axis.spines[spine_side].set_color(label_color)

        def _on_mouse_move(self, event) -> None:
            if event.inaxes not in (self._axes_y1, self._axes_y2):
                self._hide_annotation()
                return
            if event.xdata is None or event.ydata is None:
                self._hide_annotation()
                return

            match = self._find_hover_match(event)
            if match is None:
                self._hide_annotation()
                return

            axis = match["axis"]
            x_value = match["x"]
            y_value = match["y"]
            color = match["color"]
            self._show_hover_line(axis, y_value, color)
            self._canvas.setCursor(Qt.CrossCursor)
            tooltip = (
                f"{match['field_name']}: {_format_plot_value(y_value, match['unit'])}\n"
                f"Latest: {_format_plot_value(match['latest'], match['unit'])}\n"
                f"Max: {_format_plot_value(match['max'], match['unit'])}"
            )
            if self._annotation is None:
                self._annotation = axis.annotate(
                    tooltip,
                    xy=(x_value, y_value),
                    xytext=(14, 14),
                    textcoords="offset points",
                    bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fffff0", "edgecolor": color, "alpha": 0.95},
                    color="#202020",
                    fontsize=9,
                    annotation_clip=False,
                )
            else:
                if self._annotation.axes is not axis:
                    self._annotation.set_visible(False)
                    self._annotation = axis.annotate(
                        tooltip,
                        xy=(x_value, y_value),
                        xytext=(14, 14),
                        textcoords="offset points",
                        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fffff0", "edgecolor": color, "alpha": 0.95},
                        color="#202020",
                        fontsize=9,
                        annotation_clip=False,
                    )
                else:
                    self._annotation.xy = (x_value, y_value)
                    self._annotation.set_text(tooltip)
                    self._annotation.set_visible(True)
                    if self._annotation.get_bbox_patch() is not None:
                        self._annotation.get_bbox_patch().set_edgecolor(color)
            self._canvas.draw_idle()

        def _on_mouse_leave(self, event) -> None:
            self._hide_annotation()

        def _on_mouse_click(self, event) -> None:
            if event.inaxes not in (self._axes_y1, self._axes_y2) or event.button != 1:
                return
            if event.xdata is None:
                return

            visible_samples = self._get_visible_samples()
            if not visible_samples:
                return

            self.setFocus(Qt.MouseFocusReason)
            clicked_index = max(0, min(int(round(event.xdata)), len(visible_samples) - 1))
            next_measurement = advance_plot_measurement(self._measurement, clicked_index)
            if self._measurement is None or self._measurement.end_index is not None:
                self._pause_for_measurement()
            self._measurement = next_measurement
            self._status_label.setText(self._build_measurement_label(visible_samples, next_measurement))
            self._render_plot()

        def _hide_annotation(self) -> None:
            if self._annotation is not None:
                self._annotation.set_visible(False)
            self._hide_hover_lines()
            self._canvas.setCursor(Qt.ArrowCursor)
            self._canvas.draw_idle()

        def _show_hover_line(self, axis: Axes, y_value: float, color: str) -> None:
            target_line = self._hover_line_y2 if axis is self._axes_y2 else self._hover_line_y1
            other_line = self._hover_line_y1 if axis is self._axes_y2 else self._hover_line_y2
            target_line.set_ydata([y_value, y_value])
            target_line.set_color(color)
            target_line.set_visible(True)
            other_line.set_visible(False)

        def _hide_hover_lines(self) -> None:
            self._hover_line_y1.set_visible(False)
            self._hover_line_y2.set_visible(False)

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

        def _find_hover_match(self, event) -> dict[str, object] | None:
            best_match = None
            best_distance = None
            hover_threshold_px = 18.0
            for meta in self._series_metadata:
                x_values = meta["x_values"]
                y_values = meta["y_values"]
                if not x_values:
                    continue
                axis = meta["axis"]
                nearest_index = None
                nearest_distance = None
                for idx, (x_value, y_value) in enumerate(zip(x_values, y_values)):
                    if y_value is None:
                        continue
                    screen_x, screen_y = axis.transData.transform((float(x_value), float(y_value)))
                    distance = ((float(screen_x) - float(event.x)) ** 2 + (float(screen_y) - float(event.y)) ** 2) ** 0.5
                    if nearest_distance is None or distance < nearest_distance:
                        nearest_distance = distance
                        nearest_index = idx
                if nearest_index is None or nearest_distance is None:
                    continue
                if nearest_distance > hover_threshold_px:
                    continue
                y_value = y_values[nearest_index]
                if y_value is None:
                    continue
                if best_distance is None or nearest_distance < best_distance:
                    best_distance = nearest_distance
                    best_match = {
                        **meta,
                        "x": x_values[nearest_index],
                        "y": float(y_value),
                    }
            return best_match

        def _draw_measurement_overlay(self, visible_samples: list[VisualizerSample]) -> None:
            measurement = self._measurement
            if measurement is None or measurement.start_index >= len(visible_samples):
                if measurement is not None:
                    self._measurement = None
                return

            start_x = measurement.start_index
            self._axes_y1.axvline(start_x, color="#d62728", linestyle="--", linewidth=1.6, zorder=6)
            self._axes_y1.text(
                start_x,
                1.03,
                "A",
                transform=self._axes_y1.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=10,
                color="#d62728",
                fontweight="bold",
                zorder=8,
            )

            if measurement.end_index is None or measurement.end_index >= len(visible_samples):
                return

            end_x = measurement.end_index
            left_x = min(start_x, end_x)
            right_x = max(start_x, end_x)
            self._axes_y1.axvline(end_x, color="#1f77b4", linestyle="--", linewidth=1.6, zorder=6)
            self._axes_y1.text(
                end_x,
                1.03,
                "B",
                transform=self._axes_y1.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=10,
                color="#1f77b4",
                fontweight="bold",
                zorder=8,
            )
            self._axes_y1.annotate(
                "",
                xy=(right_x, 1.01),
                xytext=(left_x, 1.01),
                xycoords=self._axes_y1.get_xaxis_transform(),
                textcoords=self._axes_y1.get_xaxis_transform(),
                arrowprops={"arrowstyle": "<->", "linestyle": ":", "color": "#444444", "linewidth": 1.2},
                zorder=7,
            )
            label_text = self._build_measurement_label(visible_samples, measurement)
            label_x, label_align = choose_plot_measurement_label_anchor(start_x, end_x, label_text)
            text_transform = transforms.blended_transform_factory(self._axes_y1.transData, self._axes_y1.transAxes)
            self._axes_y1.text(
                label_x,
                1.07,
                label_text,
                transform=text_transform,
                ha=label_align,
                va="bottom",
                fontsize=9,
                color="#222222",
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "#ffffff", "edgecolor": "#cccccc", "alpha": 0.92},
                zorder=8,
            )

        def _build_measurement_label(self, visible_samples: list[VisualizerSample], measurement: PlotMeasurement) -> str:
            if measurement.end_index is None:
                return f"A {self._format_measurement_timestamp(visible_samples[measurement.start_index].timestamp_raw)}"

            start_time = parse_plot_timestamp(visible_samples[measurement.start_index].timestamp_raw)
            end_time = parse_plot_timestamp(visible_samples[measurement.end_index].timestamp_raw)
            return f"A-B {format_plot_measurement_duration(start_time, end_time)}"

        @staticmethod
        def _format_measurement_timestamp(timestamp_raw: str) -> str:
            if not timestamp_raw:
                return "--:--:--.--"
            value = timestamp_raw.split(" ")[0]
            if "-" in value:
                value = value.split("-", 1)[1]
            return value[:-1] if "." in value and len(value.split(".", 1)[1]) >= 3 else value

        def set_initial_position(self, *, slot_index: int, group_offset: int = 0) -> None:
            if self._initial_position_applied:
                return
            offset_index = slot_index + max(0, group_offset) * 2
            self.move(
                self._BASE_X + offset_index * self._OFFSET_X,
                self._BASE_Y + offset_index * self._OFFSET_Y,
            )
            self._initial_position_applied = True

        @staticmethod
        def _build_tick_positions(count: int) -> list[int]:
            if count <= 0:
                return []
            if count == 1:
                return [0]

            max_ticks = 8
            if count <= max_ticks:
                return list(range(count))

            step = max(1, count // (max_ticks - 1))
            positions = list(range(0, count, step))
            if positions[-1] != count - 1:
                positions.append(count - 1)
            return positions

        @staticmethod
        def _format_time_label(timestamp_raw: str) -> str:
            if not timestamp_raw:
                return ""

            value = timestamp_raw.strip()

            if "-" in value:
                parts = value.split("-", 1)
                if len(parts) == 2:
                    value = parts[1]

            if "." in value:
                value = value.split(".", 1)[0]

            return value

        @staticmethod
        def _sanitize_filename(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "visualizer"

else:

    class _VisualizerWindowWidget:  # pragma: no cover
        def __init__(self, controller: VisualizerWindow) -> None:
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

        def save_screenshot(self) -> Path | None:
            return None


def _to_matplotlib_linestyle(value: str | None) -> str:
    """Internal helper for to matplotlib linestyle."""
    normalized = (value or "solid").strip().lower()
    mapping = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":",
        "dashdot": "-.",
    }
    return mapping.get(normalized, "-")


def _format_plot_value(value: float | int | None, unit: str = "", *, format_spec: str = "") -> str:
    """Internal helper for format plot value."""
    if value is None:
        return "-"
    if format_spec:
        return format_footer_value(float(value), format_spec, unit)
    formatted = f"{float(value):.1f}".rstrip("0").rstrip(".")
    if unit:
        return f"{formatted} {unit}"
    return formatted


def _build_staggered_label_offsets(
    series_metadata: list[dict[str, object]],
    axis: "Axes",
    *,
    min_gap_points: int = 14,
    max_offset_points: int = 42,
) -> dict[int, int]:
    """Build and return staggered label offsets."""
    axis_series = [meta for meta in series_metadata if meta.get("axis") is axis]
    if len(axis_series) <= 1:
        return {id(meta): 0 for meta in axis_series}

    ordered_series = sorted(axis_series, key=lambda meta: float(meta.get("latest", 0.0)))
    offsets: dict[int, int] = {}
    previous_y_px: float | None = None
    previous_offset = 0

    for meta in ordered_series:
        latest_value = float(meta.get("latest", 0.0))
        latest_index = float(meta.get("latest_index", 0.0))
        _, y_px = axis.transData.transform((latest_index, latest_value))

        offset = 0
        if previous_y_px is not None and abs(y_px - previous_y_px) < min_gap_points:
            direction = 1 if previous_offset <= 0 else -1
            magnitude = min(max_offset_points, abs(previous_offset) + min_gap_points)
            offset = direction * magnitude

        offsets[id(meta)] = offset
        previous_y_px = y_px + offset
        previous_offset = offset

    return offsets


def _uses_binary_step_axis(fields, *, axis: str) -> bool:
    """Internal helper for uses binary step axis."""
    for field in fields:
        if not getattr(field, "active", False):
            continue
        if not getattr(field, "plot", False):
            continue
        if getattr(field, "axis", "Y1") != axis:
            continue
        if getattr(field, "render_style", "Line") == "Step":
            return True
    return False
