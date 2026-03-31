from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import re

from .visualizer_sample import VisualizerSample
from ..preferences import DEFAULT_VISUALIZER_PRESETS
from ..project_runtime import build_project_filename, build_project_title_suffix

try:
    from PyQt5.QtCore import Qt, QSettings
    from PyQt5.QtWidgets import (
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSpinBox,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover
    Qt = None
    QSettings = None
    QFileDialog = None
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


class LogicVisualizerWindow:
    def __init__(
        self,
        config,
        screenshot_dir: str | Path | None = None,
        window_size_presets: tuple[int, ...] | None = None,
        project_name: str | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
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
        self._widget: _LogicVisualizerWindowWidget | None = None

        self._ensure_widget()

    def append_sample(self, sample) -> None:
        self.samples.append(sample)
        self._trim_samples_if_needed()
        if self.auto_refresh_enabled:
            self.refresh_plot()

    def clear_samples(self) -> None:
        self.samples.clear()
        self.freeze_sample_index = None
        self.rebuild_plot()

    def set_auto_refresh(self, enabled: bool) -> None:
        self.auto_refresh_enabled = enabled
        if enabled:
            self.freeze_sample_index = None
            self.rebuild_plot()
        else:
            self.freeze_sample_index = len(self.samples)

    def set_runtime_sliding_window_enabled(self, enabled: bool) -> None:
        self.runtime_sliding_window_enabled = bool(enabled)
        self.rebuild_plot()

    def set_runtime_window_size(self, value: int) -> None:
        self.runtime_window_size = self._normalize_runtime_window_size(value)
        self.rebuild_plot()

    def reset_runtime_window(self) -> None:
        self.runtime_sliding_window_enabled = bool(self.config.sliding_window_enabled)
        self.runtime_window_size = self._normalize_runtime_window_size(self.config.default_window_size)
        self.rebuild_plot()

    def refresh_plot(self) -> None:
        widget = self._ensure_widget()
        if widget is not None:
            widget.refresh_plot()

    def rebuild_plot(self) -> None:
        widget = self._ensure_widget()
        if widget is not None:
            widget.rebuild_plot()

    def show(self) -> None:
        widget = self._ensure_widget()
        if widget is not None:
            widget.show()
            widget.raise_()
            widget.activateWindow()

    def set_initial_position(self, *, slot_index: int, group_offset: int = 0) -> None:
        widget = self._ensure_widget()
        if widget is not None and hasattr(widget, "set_initial_position"):
            widget.set_initial_position(slot_index=slot_index, group_offset=group_offset)

    def close(self) -> None:
        if self._widget is not None:
            self._widget.close()

    def save_screenshot(self):
        widget = self._ensure_widget()
        if widget is None:
            return None
        return widget.save_screenshot()

    def get_visible_samples_for_test(self) -> list[VisualizerSample]:
        visible = self.samples[: self.freeze_sample_index] if self.freeze_sample_index is not None else self.samples
        if not visible:
            return []
        if not self.runtime_sliding_window_enabled:
            return list(visible)
        return list(visible[-self.runtime_window_size :])

    def _ensure_widget(self):
        if self._widget is not None:
            return self._widget
        if not self._can_create_widget():
            return None
        self._widget = _LogicVisualizerWindowWidget(self)
        return self._widget

    def _trim_samples_if_needed(self) -> None:
        max_samples = getattr(self.config, "max_samples", 2000)
        if len(self.samples) <= max_samples:
            return
        overflow = len(self.samples) - max_samples
        del self.samples[:overflow]
        if self.freeze_sample_index is not None:
            self.freeze_sample_index = max(0, self.freeze_sample_index - overflow)

    def _normalize_runtime_window_size(self, value: int | str | None) -> int:
        try:
            parsed = int(value) if value is not None else self.config.default_window_size
        except (TypeError, ValueError):
            parsed = self.config.default_window_size
        if parsed <= 0:
            parsed = self.config.default_window_size
        return min(parsed, self.config.max_samples)

    @staticmethod
    def _can_create_widget() -> bool:
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

            self._figure = Figure(figsize=(10, 5))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._axes: Axes = self._figure.add_subplot(111)

            # Vertical cursor line
            self._cursor_line = self._axes.axvline(x=0, color="gray", linestyle="--", visible=False)

            # Mouse tracking on matplotlib canvas
            self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
            self._canvas.mpl_connect("axes_leave_event", self._on_mouse_leave)

            self._auto_refresh_checkbox = QCheckBox("Auto Refresh")
            self._auto_refresh_checkbox.setChecked(True)
            self._auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)

            self._refresh_button = QPushButton("Refresh")
            self._refresh_button.clicked.connect(self._on_refresh_clicked)

            self._sliding_window_checkbox = QCheckBox("Sliding Window")
            self._sliding_window_checkbox.setChecked(self._controller.runtime_sliding_window_enabled)
            self._sliding_window_checkbox.stateChanged.connect(self._on_sliding_window_changed)

            self._window_size_spin = QSpinBox()
            self._window_size_spin.setRange(10, max(10, self._controller.config.max_samples))
            self._window_size_spin.setSingleStep(50)
            self._window_size_spin.setKeyboardTracking(False)
            self._window_size_spin.setMinimumWidth(88)
            self._window_size_spin.setValue(self._controller.runtime_window_size)
            self._window_size_spin.valueChanged.connect(self._on_window_size_changed)

            self._preset_buttons: list[QPushButton] = []
            for preset in self._controller.window_size_presets:
                button = QPushButton(str(preset))
                button.clicked.connect(lambda _checked=False, value=preset: self._set_window_preset(value))
                self._preset_buttons.append(button)

            self._reset_button = QPushButton("Reset")
            self._reset_button.clicked.connect(self._on_reset_window_clicked)

            self._screenshot_button = QPushButton("Screenshot")
            self._screenshot_button.clicked.connect(self._on_screenshot_clicked)

            self._status_label = QLabel("Samples: 0 visible / 0 total")

            top_bar = QHBoxLayout()
            top_bar.addWidget(self._auto_refresh_checkbox)
            top_bar.addWidget(self._refresh_button)
            top_bar.addWidget(self._sliding_window_checkbox)
            for button in self._preset_buttons:
                top_bar.addWidget(button)
            top_bar.addWidget(QLabel("Window Size"))
            top_bar.addWidget(self._window_size_spin)
            top_bar.addWidget(self._reset_button)
            top_bar.addWidget(self._screenshot_button)
            top_bar.addWidget(self._status_label)
            top_bar.addStretch(1)

            layout = QVBoxLayout()
            layout.addLayout(top_bar)
            layout.addWidget(self._canvas)
            self.setLayout(layout)

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
            self._controller.set_auto_refresh(state == Qt.Checked)

        def _on_refresh_clicked(self) -> None:
            self._controller.clear_samples()

        def _on_sliding_window_changed(self, state: int) -> None:
            self._controller.set_runtime_sliding_window_enabled(state == Qt.Checked)

        def _on_window_size_changed(self, value: int) -> None:
            self._controller.set_runtime_window_size(value)

        def _set_window_preset(self, value: int) -> None:
            self._window_size_spin.setValue(min(value, self._controller.config.max_samples))

        def _on_reset_window_clicked(self) -> None:
            self._controller.reset_runtime_window()

        def _on_screenshot_clicked(self) -> None:
            self.save_screenshot()

        def _sync_runtime_controls(self) -> None:
            self._sliding_window_checkbox.blockSignals(True)
            self._window_size_spin.blockSignals(True)
            self._sliding_window_checkbox.setChecked(self._controller.runtime_sliding_window_enabled)
            self._window_size_spin.setMaximum(max(10, self._controller.config.max_samples))
            self._window_size_spin.setValue(self._controller.runtime_window_size)
            self._window_size_spin.setEnabled(self._controller.runtime_sliding_window_enabled)
            self._sliding_window_checkbox.blockSignals(False)
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

        def _render_plot(self) -> None:
            self.setWindowTitle(self._build_window_title())
            self._axes.clear()

            visible_samples = self._get_visible_samples()
            active_fields = [
                f for f in self._controller.config.fields[:8]
                if getattr(f, "active", False) and getattr(f, "plot", True)
            ]

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
            self._status_label.setText(
                f"Samples: {len(visible_samples)} visible / {len(self._controller.samples)} total"
            )

            if plotted_count > 0 and getattr(self._controller.config, "show_legend", True):
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
