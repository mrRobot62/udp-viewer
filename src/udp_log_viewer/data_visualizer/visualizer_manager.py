from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt5.QtWidgets import QWidget

from .config_store import ConfigStore
from .csv_log_parser import CsvLogParser
from .logic_visualizer_config_dialog import LogicVisualizerConfigDialog
from .logic_visualizer_window import LogicVisualizerWindow
from .visualizer_config import VisualizerConfig
from .visualizer_config_dialog import VisualizerConfigDialog
from .visualizer_slot import SLOT_COUNT, VisualizerGraphType, VisualizerSlotId, iter_slot_ids
from .visualizer_window import VisualizerWindow
from ..preferences import AppPreferences


class VisualizerManager:
    def __init__(
        self,
        config_path: str | Path | None = None,
        screenshot_dir: str | Path | None = None,
        preferences: AppPreferences | None = None,
        diagnostic_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.parser = CsvLogParser()
        self.preferences = preferences or AppPreferences()
        self.config_store = ConfigStore(config_path=config_path, preferences=self.preferences)
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir is not None else None
        self.diagnostic_callback = diagnostic_callback
        self.configs_by_type: dict[VisualizerGraphType, list[VisualizerConfig]] = {
            "plot": [VisualizerConfig(graph_type="plot") for _ in range(SLOT_COUNT)],
            "logic": [VisualizerConfig(graph_type="logic") for _ in range(SLOT_COUNT)],
        }
        self.selected_slot_by_type: dict[VisualizerGraphType, int] = {"plot": 0, "logic": 0}
        self.windows_by_slot: dict[VisualizerSlotId, VisualizerWindow | LogicVisualizerWindow] = {}
        self.sample_counters_by_slot: dict[VisualizerSlotId, int] = {}

    def load_configs(self) -> None:
        self.config_store = ConfigStore(config_path=self.config_store._config_path, preferences=self.preferences)
        self.configs_by_type = self.config_store.load_slot_configs()
        self.windows_by_slot.clear()
        self.sample_counters_by_slot.clear()

    def set_preferences(self, preferences: AppPreferences) -> None:
        self.preferences = preferences
        self.config_store = ConfigStore(config_path=self.config_store._config_path, preferences=self.preferences)

    def save_configs(self) -> None:
        self.config_store.save_slot_configs(self.configs_by_type)

    def process_log_line(self, line: str) -> int:
        accepted_samples = 0
        for graph_type in ("plot", "logic"):
            for slot_id in iter_slot_ids(graph_type):
                config = self.get_config(slot_id)
                if not config.is_routable:
                    continue
                sample_index = self.sample_counters_by_slot.get(slot_id, 0)
                sample = self.parser.parse_line(line, config, sample_index)
                if sample is None:
                    continue
                window = self._get_or_create_window(slot_id, config)
                if not self._window_is_available(window, slot_id):
                    continue
                window.append_sample(sample)
                self.sample_counters_by_slot[slot_id] = sample_index + 1
                accepted_samples += 1
                # self._diag(
                #     f"[VIS/{slot_id.graph_type.upper()}] SLOT {slot_id.slot_number} matched {config.filter_string} sample={sample_index + 1}"
                # )
        return accepted_samples

    def set_visualizers(self, configs: list[VisualizerConfig]) -> None:
        self.configs_by_type["plot"] = list(configs[:SLOT_COUNT]) + [
            VisualizerConfig(graph_type="plot") for _ in range(max(0, SLOT_COUNT - len(configs)))
        ]
        self.windows_by_slot = {
            slot_id: window for slot_id, window in self.windows_by_slot.items() if slot_id.graph_type != "plot"
        }
        self.sample_counters_by_slot = {
            slot_id: count for slot_id, count in self.sample_counters_by_slot.items() if slot_id.graph_type != "plot"
        }

    @property
    def visualizers(self) -> list[VisualizerConfig]:
        return self.configs_by_type["plot"]

    def get_window(self, index: int) -> VisualizerWindow | LogicVisualizerWindow | None:
        return self.windows_by_slot.get(VisualizerSlotId(graph_type="plot", slot_index=index))

    def get_slot_window(
        self,
        graph_type: VisualizerGraphType,
        slot_index: int,
    ) -> VisualizerWindow | LogicVisualizerWindow | None:
        return self.windows_by_slot.get(VisualizerSlotId(graph_type=graph_type, slot_index=slot_index))

    def show_window(self, index: int) -> None:
        self.show_windows("plot", slots=[index])

    def show_windows(self, graph_type: VisualizerGraphType, slots: list[int] | None = None) -> None:
        if not self.configs_by_type:
            self.load_configs()

        active_slots: set[int] = set()
        slot_indices = slots if slots is not None else list(range(SLOT_COUNT))
        for slot_index in slot_indices:
            if not (0 <= slot_index < SLOT_COUNT):
                continue
            config = self.configs_by_type[graph_type][slot_index]
            slot_id = VisualizerSlotId(graph_type=graph_type, slot_index=slot_index)
            if not config.enabled:
                self._diag(f"[VIS/{graph_type.upper()}] SLOT {slot_id.slot_number} skipped: disabled")
                self.close_window(slot_id)
                continue
            if not config.filter_string:
                self._diag(f"[VIS/{graph_type.upper()}] SLOT {slot_id.slot_number} skipped: empty filter")
                self.close_window(slot_id)
                continue
            if not config.fields:
                self._diag(f"[VIS/{graph_type.upper()}] SLOT {slot_id.slot_number} skipped: no fields configured")
                self.close_window(slot_id)
                continue
            active_slots.add(slot_index)
            window = self._get_or_create_window(slot_id, config)
            if not self._window_is_available(window, slot_id):
                continue
            window.show()
            self._diag(
                f"[VIS/{graph_type.upper()}] SLOT {slot_id.slot_number} window shown title='{config.title or '-'}' filter='{config.filter_string}'"
            )

        if slots is None:
            for slot_id in list(self.windows_by_slot):
                if slot_id.graph_type != graph_type:
                    continue
                if slot_id.slot_index not in active_slots:
                    self.close_window(slot_id)

    def close_window(self, slot: int | VisualizerSlotId) -> None:
        slot_id = slot if isinstance(slot, VisualizerSlotId) else VisualizerSlotId(graph_type="plot", slot_index=slot)
        window = self.windows_by_slot.pop(slot_id, None)
        if window is not None:
            window.close()

    def close_all_windows(self) -> None:
        for window in list(self.windows_by_slot.values()):
            try:
                window.close()
            except Exception:
                pass
        self.windows_by_slot.clear()

    def clear_all_buffers(self) -> None:
        self.sample_counters_by_slot.clear()
        for window in self.windows_by_slot.values():
            window.clear_samples()

    def clear_window_buffer(self, index: int) -> None:
        slot_id = VisualizerSlotId(graph_type="plot", slot_index=index)
        self.sample_counters_by_slot[slot_id] = 0
        window = self.windows_by_slot.get(slot_id)
        if window is not None:
            window.clear_samples()

    def configure_csv_temp(self, parent: QWidget | None = None) -> bool:
        return self._configure_slots("plot", parent=parent)

    def configure_logic(self, parent: QWidget | None = None) -> bool:
        return self._configure_slots("logic", parent=parent)

    def show_logic_window(self) -> None:
        self.show_windows("logic")

    def get_config(self, slot_id: VisualizerSlotId) -> VisualizerConfig:
        return self.configs_by_type[slot_id.graph_type][slot_id.slot_index]

    def _configure_slots(self, graph_type: VisualizerGraphType, parent: QWidget | None = None) -> bool:
        if not self.configs_by_type:
            self.load_configs()

        configs = self.configs_by_type[graph_type]
        selected_slot = self.selected_slot_by_type.get(graph_type, 0)
        if graph_type == "logic":
            dialog = LogicVisualizerConfigDialog(configs=configs, current_slot=selected_slot, parent=parent)
        else:
            dialog = VisualizerConfigDialog(configs=configs, current_slot=selected_slot, parent=parent)
        if dialog.exec_() != dialog.Accepted:
            return False

        self.configs_by_type[graph_type] = dialog.result_configs()
        self.selected_slot_by_type[graph_type] = dialog.current_slot()
        self.save_configs()

        for slot_index in range(SLOT_COUNT):
            slot_id = VisualizerSlotId(graph_type=graph_type, slot_index=slot_index)
            existing_window = self.windows_by_slot.pop(slot_id, None)
            if existing_window is not None:
                existing_window.close()
            self.sample_counters_by_slot[slot_id] = 0

        return True

    def _get_or_create_window(
        self,
        slot_id: VisualizerSlotId,
        config: VisualizerConfig,
    ) -> VisualizerWindow | LogicVisualizerWindow:
        existing_window = self.windows_by_slot.get(slot_id)
        if existing_window is not None:
            return existing_window
        if slot_id.graph_type == "logic":
            window = LogicVisualizerWindow(
                config,
                screenshot_dir=self.screenshot_dir,
                window_size_presets=self.preferences.visualizer_presets,
            )
        else:
            window = VisualizerWindow(
                config,
                screenshot_dir=self.screenshot_dir,
                window_size_presets=self.preferences.visualizer_presets,
            )

        if hasattr(window, "set_initial_position"):
            window.set_initial_position(
                slot_index=slot_id.slot_index,
                group_offset=1 if slot_id.graph_type == "logic" else 0,
            )
        self.windows_by_slot[slot_id] = window
        return window

    def _window_is_available(
        self,
        window: VisualizerWindow | LogicVisualizerWindow,
        slot_id: VisualizerSlotId,
    ) -> bool:
        is_available = getattr(window, "is_gui_available", lambda: True)()
        if is_available:
            return True
        self._diag(
            f"[VIS/{slot_id.graph_type.upper()}] SLOT {slot_id.slot_number} window unavailable: PyQt/matplotlib backend missing"
        )
        return False

    def _diag(self, message: str) -> None:
        if self.diagnostic_callback is not None:
            self.diagnostic_callback(message)
