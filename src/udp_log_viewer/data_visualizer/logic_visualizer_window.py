from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class LogicVisualizerWindow(QWidget):
    def __init__(self, config, screenshot_dir: Path | None = None) -> None:
        super().__init__()
        self.config = config
        self.samples: List[dict] = []

        self.setWindowTitle(config.title or "Logic Visualizer")
        self.resize(800, 400)

        layout = QVBoxLayout()
        self.label = QLabel("LogicGraph (T3.7.0 placeholder)")
        layout.addWidget(self.label)

        self.setLayout(layout)

    def append_sample(self, sample):
        self.samples.append(sample)

    def clear_samples(self):
        self.samples.clear()

    def set_auto_refresh(self, enabled: bool):
        pass

    def refresh_plot(self):
        pass

    def rebuild_plot(self):
        pass

    def save_screenshot(self):
        return None
