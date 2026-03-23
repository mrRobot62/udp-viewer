from __future__ import annotations

from typing import TYPE_CHECKING

from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QCheckBox,
        QHBoxLayout,
        QLabel,
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
    """
    Controller-style wrapper around an optional PyQt/Matplotlib window.

    - In the real app (QApplication available), a QWidget-based graph window is created.
    - In tests without QApplication, the object still buffers samples and stays usable.
    """

    def __init__(self, config: VisualizerConfig) -> None:
        self.config = config
        self.samples: list[VisualizerSample] = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index: int | None = None
        self.refresh_request_count = 0
        self.rebuild_request_count = 0

        self._widget: _VisualizerWindowWidget | None = None
        if self._can_create_widget():
            self._widget = _VisualizerWindowWidget(self)

    def append_sample(self, sample: VisualizerSample) -> None:
        self.samples.append(sample)
        self._trim_samples_if_needed()

        if self.auto_refresh_enabled:
            self.refresh_plot()

    def set_auto_refresh(self, enabled: bool) -> None:
        self.auto_refresh_enabled = enabled

        if enabled:
            self.freeze_sample_index = None
            self.rebuild_plot()
            return

        self.freeze_sample_index = len(self.samples)

    def refresh_plot(self) -> None:
        self.refresh_request_count += 1
        if self._widget is not None:
            self._widget.refresh_plot()

    def rebuild_plot(self) -> None:
        self.rebuild_request_count += 1
        if self._widget is not None:
            self._widget.rebuild_plot()

    def show(self) -> None:
        if self._widget is not None:
            self._widget.show()

    def close(self) -> None:
        if self._widget is not None:
            self._widget.close()

    def is_gui_available(self) -> bool:
        return self._widget is not None

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
            self.resize(900, 500)

            self._figure = Figure(figsize=(8, 4))
            self._canvas = FigureCanvas(self._figure)
            self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._axes: Axes = self._figure.add_subplot(111)

            self._auto_refresh_checkbox = QCheckBox("Auto Refresh")
            self._auto_refresh_checkbox.setChecked(True)
            self._auto_refresh_checkbox.stateChanged.connect(self._on_auto_refresh_changed)

            self._status_label = QLabel("Samples: 0")

            top_bar = QHBoxLayout()
            top_bar.addWidget(self._auto_refresh_checkbox)
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

        def _on_auto_refresh_changed(self, state: int) -> None:
            enabled = state == Qt.Checked
            self._controller.set_auto_refresh(enabled)

        def _render_plot(self) -> None:
            self._axes.clear()

            samples = self._get_visible_samples()
            plotted_any = False
            x_values = list(range(len(samples)))

            for field in self._controller.config.fields:
                if not field.plot or not field.field_name:
                    continue

                y_values = [sample.values_by_name.get(field.field_name) for sample in samples]
                if not any(value is not None for value in y_values):
                    continue

                label = field.field_name
                if field.unit:
                    label = f"{label} [{field.unit}]"

                self._axes.plot(
                    x_values,
                    y_values,
                    label=label,
                    color=field.color or None,
                    linestyle=_to_matplotlib_linestyle(field.line_style),
                )
                plotted_any = True

            self._apply_axis_settings()
            self._status_label.setText(f"Samples: {len(self._controller.samples)}")

            if plotted_any:
                self._axes.legend(loc="best")

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
            y_axis = self._controller.config.y_axis

            self._axes.set_xlabel(x_axis.label or "Samples")
            self._axes.set_ylabel(y_axis.label or "Value")

            if y_axis.logarithmic:
                self._axes.set_yscale("log")

            if y_axis.min_value is not None or y_axis.max_value is not None:
                self._axes.set_ylim(bottom=y_axis.min_value, top=y_axis.max_value)

            if x_axis.continuous and x_axis.max_value is not None:
                visible_samples = self._get_visible_samples()
                if visible_samples:
                    right = len(visible_samples) - 1
                    left = 0
                    self._axes.set_xlim(left=left, right=max(right, 1))

            self._axes.grid(True)

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

        def close(self) -> None:
            pass


def _to_matplotlib_linestyle(value: str | None) -> str:
    normalized = (value or "solid").strip().lower()

    mapping = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":",
        "dashdot": "-.",
    }

    return mapping.get(normalized, "-")
