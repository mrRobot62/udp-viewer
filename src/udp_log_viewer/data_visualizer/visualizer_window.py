from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import re

from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QCheckBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover - fallback for non-Qt test environments
    Qt = None
    QWidget = object  # type: ignore[assignment]
    _PYQT_AVAILABLE = False

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    _MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover - fallback for non-GUI test environments
    FigureCanvas = None
    Figure = None
    _MATPLOTLIB_AVAILABLE = False

if TYPE_CHECKING:
    from matplotlib.axes import Axes


class VisualizerWindow:
    def __init__(self, config: VisualizerConfig, screenshot_dir: str | Path | None = None) -> None:
        self.config = config
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir is not None else None
        self.samples: list[VisualizerSample] = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index: int | None = None
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
        def __init__(self, controller: VisualizerWindow) -> None:
            super().__init__()
            self._controller = controller

            self.setWindowTitle(controller.config.title or "Data Visualizer")
            self.resize(980, 560)

            self._figure = Figure(figsize=(8, 4))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._axes_y1: Axes = self._figure.add_subplot(111)
            self._axes_y2: Axes = self._axes_y1.twinx()

            self._auto_refresh_checkbox = QCheckBox("Auto Refresh")
            self._auto_refresh_checkbox.setChecked(True)
            self._auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)

            self._refresh_button = QPushButton("Refresh")
            self._refresh_button.clicked.connect(self._on_refresh_clicked)

            self._screenshot_button = QPushButton("Screenshot")
            self._screenshot_button.clicked.connect(self._on_screenshot_clicked)

            self._status_label = QLabel("Samples: 0 visible / 0 total")

            top_bar = QHBoxLayout()
            top_bar.addWidget(self._auto_refresh_checkbox)
            top_bar.addWidget(self._refresh_button)
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
            self._render_plot()

        def save_screenshot(self) -> Path | None:
            target_dir = self._controller.screenshot_dir
            if target_dir is None:
                target_dir = Path.cwd() / "screenshots"
            target_dir.mkdir(parents=True, exist_ok=True)

            safe_title = self._sanitize_filename(self._controller.config.title or "visualizer")
            filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            target_path = target_dir / filename

            self._figure.savefig(target_path, dpi=150, bbox_inches="tight")
            self._status_label.setText(f"Screenshot saved: {target_path.name}")
            return target_path

        def _on_auto_refresh_changed(self, state: int) -> None:
            enabled = state == Qt.Checked
            self._controller.set_auto_refresh(enabled)

        def _on_refresh_clicked(self) -> None:
            self._controller.clear_samples()

        def _on_screenshot_clicked(self) -> None:
            self.save_screenshot()

        def _render_plot(self) -> None:
            self.setWindowTitle(self._controller.config.title or "Data Visualizer")
            self._axes_y1.clear()
            self._axes_y2.clear()

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

                if field.render_style == "Step":
                    target_axis.step(x_values, y_values, where="post", **plot_kwargs)
                else:
                    target_axis.plot(x_values, y_values, **plot_kwargs)

                if field.axis == "Y2":
                    plotted_y2 = True
                else:
                    plotted_y1 = True

            self._apply_axis_settings()
            visible_count = len(samples)
            total_count = len(self._controller.samples)
            self._status_label.setText(f"Samples: {visible_count} visible / {total_count} total")

            if plotted_y1:
                self._axes_y1.legend(loc="upper left")
            if plotted_y2:
                self._axes_y2.legend(loc="upper right")

            self._figure.tight_layout()
            self._canvas.draw_idle()

        def _get_visible_samples(self) -> list[VisualizerSample]:
            if self._controller.freeze_sample_index is not None:
                visible = self._controller.samples[: self._controller.freeze_sample_index]
            else:
                visible = self._controller.samples

            if not visible:
                return []

            if not self._controller.config.x_axis.continuous:
                return visible

            x_max = self._controller.config.x_axis.max_value
            if x_max is None:
                return visible

            try:
                window_size = int(x_max)
            except (TypeError, ValueError):
                return visible

            if window_size <= 0:
                return visible

            return visible[-window_size:]

        def _apply_axis_settings(self) -> None:
            x_axis = self._controller.config.x_axis
            y1_axis = self._controller.config.y1_axis
            y2_axis = self._controller.config.y2_axis

            self._axes_y1.set_xlabel(x_axis.label or "Samples")
            self._axes_y1.set_ylabel(y1_axis.label or "Y1")
            self._axes_y2.set_ylabel(y2_axis.label or "Y2")

            if y1_axis.logarithmic:
                self._axes_y1.set_yscale("log")
            if y2_axis.logarithmic:
                self._axes_y2.set_yscale("log")

            if y1_axis.min_value is not None or y1_axis.max_value is not None:
                self._axes_y1.set_ylim(bottom=y1_axis.min_value, top=y1_axis.max_value)
            if y2_axis.min_value is not None or y2_axis.max_value is not None:
                self._axes_y2.set_ylim(bottom=y2_axis.min_value, top=y2_axis.max_value)

            visible_samples = self._get_visible_samples()
            if x_axis.continuous and x_axis.max_value is not None and visible_samples:
                right = len(visible_samples) - 1
                left = 0
                self._axes_y1.set_xlim(left=left, right=max(right, 1))
            elif not x_axis.continuous and visible_samples:
                self._axes_y1.set_xlim(left=0, right=max(len(visible_samples) - 1, 1))

            self._axes_y1.grid(True)

        @staticmethod
        def _sanitize_filename(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "visualizer"

else:

    class _VisualizerWindowWidget:  # pragma: no cover - placeholder only
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
