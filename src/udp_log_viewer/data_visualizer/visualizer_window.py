from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import re

from .visualizer_axis_config import VisualizerAxisConfig
from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample
from ..preferences import DEFAULT_VISUALIZER_PRESETS

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
except Exception:  # pragma: no cover - fallback for non-Qt test environments
    Qt = None
    QSettings = None
    QFileDialog = None
    QWidget = object  # type: ignore[assignment]
    _PYQT_AVAILABLE = False

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.ticker import MultipleLocator
    _MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover - fallback for non-GUI test environments
    FigureCanvas = None
    Figure = None
    MultipleLocator = None
    _MATPLOTLIB_AVAILABLE = False

if TYPE_CHECKING:
    from matplotlib.axes import Axes


class VisualizerWindow:
    def __init__(
        self,
        config: VisualizerConfig,
        screenshot_dir: str | Path | None = None,
        window_size_presets: tuple[int, ...] | None = None,
    ) -> None:
        self.config = config
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir is not None else None
        self.window_size_presets = tuple(window_size_presets or DEFAULT_VISUALIZER_PRESETS)
        self.samples: list[VisualizerSample] = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index: int | None = None
        self.runtime_sliding_window_enabled = bool(config.sliding_window_enabled)
        self.runtime_window_size = self._normalize_runtime_window_size(config.default_window_size)
        self.refresh_request_count = 0
        self.rebuild_request_count = 0
        self._widget: _VisualizerWindowWidget | None = None
        self._ensure_widget()

    def append_sample(self, sample: VisualizerSample) -> None:
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
            return
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
        self.refresh_request_count += 1
        widget = self._ensure_widget()
        if widget is not None:
            widget.refresh_plot()

    def rebuild_plot(self) -> None:
        self.rebuild_request_count += 1
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

    def save_screenshot(self) -> Path | None:
        widget = self._ensure_widget()
        if widget is None:
            return None
        return widget.save_screenshot()

    def is_gui_available(self) -> bool:
        return self._ensure_widget() is not None

    def get_visible_samples_for_test(self) -> list[VisualizerSample]:
        visible = self.samples[: self.freeze_sample_index] if self.freeze_sample_index is not None else self.samples
        if not visible:
            return []
        if not self.runtime_sliding_window_enabled:
            return list(visible)
        return list(visible[-self.runtime_window_size :])

    def _ensure_widget(self) -> "_VisualizerWindowWidget | None":
        if self._widget is not None:
            return self._widget
        if not self._can_create_widget():
            return None
        self._widget = _VisualizerWindowWidget(self)
        return self._widget

    def _trim_samples_if_needed(self) -> None:
        max_samples = self.config.max_samples
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

            self.setWindowTitle(controller.config.title or "Data Visualizer")
            self.resize(980, 560)

            self._figure = Figure(figsize=(8, 4))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._axes_y1: Axes = self._figure.add_subplot(111)
            self._axes_y2: Axes = self._axes_y1.twinx()
            self._annotation = None
            self._series_metadata: list[dict[str, object]] = []
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

        def _settings(self) -> QSettings | None:
            if QSettings is None:
                return None
            return QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)

        def _build_screenshot_filename(self) -> str:
            safe_title = self._sanitize_filename(self._controller.config.title or "visualizer")
            return f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        def _on_auto_refresh_changed(self, state: int) -> None:
            enabled = state == Qt.Checked
            self._controller.set_auto_refresh(enabled)

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

        def _render_plot(self) -> None:
            self.setWindowTitle(self._controller.config.title or "Data Visualizer")
            self._annotation = None
            self._axes_y1.clear()
            self._axes_y2.clear()
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
                            "color": line.get_color(),
                            "x_values": list(x_values),
                            "y_values": list(y_values),
                            "latest": numeric_values[-1],
                            "max": max(numeric_values),
                            "latest_index": max(i for i, value in enumerate(y_values) if value is not None),
                        }
                    )

                if field.axis == "Y2":
                    plotted_y2 = True
                else:
                    plotted_y1 = True

            self._apply_axis_settings(samples)

            visible_count = len(samples)
            total_count = len(self._controller.samples)
            self._status_label.setText(f"Samples: {visible_count} visible / {total_count} total")

            self._draw_end_labels()
            if plotted_y1 and getattr(self._controller.config, "show_legend", True):
                self._axes_y1.legend(loc="upper left")
            if plotted_y2 and getattr(self._controller.config, "show_legend", True):
                self._axes_y2.legend(loc="upper right")

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
            for meta in self._series_metadata:
                axis = meta["axis"]
                latest_value = meta["latest"]
                latest_index = meta["latest_index"]
                color = meta["color"]
                axis.annotate(
                    _format_plot_value(latest_value),
                    xy=(latest_index, latest_value),
                    xytext=(8, 0),
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
            tooltip = (
                f"{match['field_name']}: {_format_plot_value(y_value, match['unit'])} | "
                f"Latest: {_format_plot_value(match['latest'], match['unit'])} | "
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

        def _hide_annotation(self) -> None:
            if self._annotation is None:
                return
            self._annotation.set_visible(False)
            self._canvas.draw_idle()

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
    normalized = (value or "solid").strip().lower()
    mapping = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":",
        "dashdot": "-.",
    }
    return mapping.get(normalized, "-")


def _format_plot_value(value: float | int | None, unit: str = "") -> str:
    if value is None:
        return "-"
    formatted = f"{float(value):.3f}".rstrip("0").rstrip(".")
    if unit:
        return f"{formatted} {unit}"
    return formatted


def _uses_binary_step_axis(fields, *, axis: str) -> bool:
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
