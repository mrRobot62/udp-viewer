from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import random
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, List, Optional, Tuple

from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QIntValidator, QTextCursor
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .highlighter import HighlightRule, LogHighlighter
from .udp_listener import UdpListenerThread
from .udp_log_utils import drain_queue, compile_patterns, match_include, match_exclude

APP_ORG = "LocalTools"
APP_NAME = "UdpLogViewer"
APP_VERSION = "0.14-step9.1-pause-savelogic"

SLOT_COUNT = 5

DEFAULT_MAX_LINES = 20000
DEFAULT_TRIM_CHUNK = 2000

REPLAY_TICK_MS = 25
REPLAY_LINES_PER_TICK = 40


@dataclass
class UiState:
    bind_ip: str = "0.0.0.0"
    port: int = 10514
    autoscroll: bool = True

    timestamp_enabled: bool = False
    max_lines: int = DEFAULT_MAX_LINES


@dataclass
class PatternSlot:
    pattern: str = ""
    mode: str = "Substring"     # "Substring" | "Regex"
    color: str = "None"         # chip tint; for Highlight also drives log coloring


class PatternEditDialog(QDialog):
    """
    Unified editor dialog used for Filter / Exclude / Highlight slots.

    - Slot: 1..5
    - Pattern: text
    - Mode: Substring / Regex
    - Color: None / ... (Filter & Exclude: chip-only; Highlight: chip + log coloring)
    """

    def __init__(self, parent: QWidget, title: str, slot_index: int, slot: PatternSlot, suggested_index: int) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Slot:"), 0, 0)
        self.sb_slot = QSpinBox()
        self.sb_slot.setRange(1, SLOT_COUNT)
        self.sb_slot.setValue((slot_index + 1) if slot_index >= 0 else (suggested_index + 1))
        grid.addWidget(self.sb_slot, 0, 1)

        grid.addWidget(QLabel("Pattern:"), 1, 0)
        self.ed_pattern = QLineEdit()
        self.ed_pattern.setText(slot.pattern)
        self.ed_pattern.setPlaceholderText('e.g. "[OVEN/INFO] [T11]" or "STATUS received"')
        grid.addWidget(self.ed_pattern, 1, 1)

        grid.addWidget(QLabel("Mode:"), 2, 0)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Substring", "Regex"])
        self.cb_mode.setCurrentText(slot.mode or "Substring")
        grid.addWidget(self.cb_mode, 2, 1)

        grid.addWidget(QLabel("Color:"), 3, 0)
        self.cb_color = QComboBox()
        self.cb_color.addItems(["None", "Red", "Green", "Blue", "Orange", "Purple", "Gray"])
        self.cb_color.setCurrentText(slot.color or "None")
        grid.addWidget(self.cb_color, 3, 1)

        layout.addLayout(grid)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        btns.button(QDialogButtonBox.Ok).setText("SET")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def result_data(self) -> Tuple[int, PatternSlot]:
        idx = int(self.sb_slot.value()) - 1
        slot = PatternSlot(
            pattern=self.ed_pattern.text().strip(),
            mode=self.cb_mode.currentText().strip() or "Substring",
            color=self.cb_color.currentText().strip() or "None",
        )
        return idx, slot


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._settings = QSettings(APP_ORG, APP_NAME)
        self._ui_state = UiState()

        # UDP listener
        self._listener: Optional[UdpListenerThread] = None
        self._rx_packets = 0
        self._rx_lines = 0

        # Queue + batching for UI
        self._queue: Deque[str] = deque()
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(50)
        self._flush_timer.timeout.connect(self._flush_log_queue)
        self._flush_timer.start()

        # UI pause (freeze view while still logging to file)
        self._ui_paused: bool = False
        self._pause_buffer: Deque[str] = deque(maxlen=2000)
        self._pause_dropped: int = 0


        # Simulation (Tools -> Simulate Traffic)
        self._sim_enabled = False
        self._sim_timer = QTimer(self)
        self._sim_timer.setInterval(120)  # ms
        self._sim_timer.timeout.connect(self._on_sim_tick)
        self._sim_seq = 0
        self._sim_ntc = 22.0
        self._sim_core = 23.0
        self._sim_tgt = 40.0
        self._sim_heater = 0
        self._sim_mask = 0x0000

        # Replay (inject without UDP)
        self._replay_timer = QTimer(self)
        self._replay_timer.setInterval(REPLAY_TICK_MS)
        self._replay_timer.timeout.connect(self._replay_tick)
        self._replay_lines: Deque[str] = deque()
        self._replay_active = False

        # Slot-based Filter / Exclude / Highlight
        self._filter_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._exclude_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._hl_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]

        # Compiled patterns per slot
        self._filter_slot_patterns: List[List[object]] = []
        self._exclude_slot_patterns: List[List[object]] = []

        # Highlight rules
        self._hl_rules: List[HighlightRule] = []

        # Log limit counters
        self._trimmed_lines_total = 0

        # Continuous file logging per connection
        self._live_log_path: Optional[Path] = None
        self._live_log_handle = None  # type: ignore[assignment]
        self._last_session_log_path: Optional[Path] = None

        self.setWindowTitle(f"UDP Log Viewer — {APP_VERSION}")
        self.resize(1100, 760)

        self._build_actions()
        self._build_ui()

        self._load_settings()
        self._apply_state_to_widgets()

        self._load_filter_slots()
        self._load_exclude_slots()
        self._load_highlight_slots()

        self._rebuild_filter_patterns()
        self._rebuild_highlight_rules()
        self._apply_highlighter()

        self._refresh_filter_chips()
        self._refresh_exclude_chips()
        self._refresh_highlight_chips()

        self._update_connection_ui()

    # ---------------- Helpers ----------------

    @staticmethod
    def _now_stamp() -> str:
        return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    def _default_save_name(self) -> str:
        return f"udp_log_{self._now_stamp()}.txt"

    def _ensure_data_logs_dir(self) -> Path:
        # relative to current working directory (workspace root when launched from VS Code)
        p = Path("data") / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _open_new_live_log(self) -> None:
        self._close_live_log()

        logs_dir = self._ensure_data_logs_dir()
        name = f"udp_live_{self._now_stamp()}.txt"
        path = logs_dir / name

        try:
            f = open(path, "w", encoding="utf-8", newline="\n")
            self._live_log_handle = f
            self._live_log_path = path
            f.write(f"# UDP Log Viewer live session — {self._now_stamp()}\n")
            f.flush()
            self.statusBar().showMessage(f"Live log: {path}", 3000)
        except Exception as e:
            self._live_log_handle = None
            self._live_log_path = None
            self.log.appendPlainText(f"[UI/ERROR] Could not create live logfile: {e}")
            if self._ui_state.autoscroll:
                self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _close_live_log(self) -> None:
        try:
            if self._live_log_handle is not None:
                try:
                    self._live_log_handle.flush()
                except Exception:
                    pass
                self._live_log_handle.close()
        except Exception:
            pass
        self._last_session_log_path = self._live_log_path
        self._live_log_handle = None
        self._live_log_path = None

    def _append_to_live_log(self, line: str) -> None:
        if self._live_log_handle is None:
            return
        try:
            self._live_log_handle.write(line + "\n")
        except Exception as e:
            self.log.appendPlainText(f"[UI/ERROR] Live logfile write failed: {e}")
            self._close_live_log()

    # ---------------- UI ----------------

    def _build_actions(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        self.act_open_log = QAction("Open Log…", self)
        self.act_open_log.setShortcut("Ctrl+O")
        self.act_open_log.triggered.connect(self.on_open_log_clicked)

        self.act_replay_sample = QAction("Replay Sample", self)
        self.act_replay_sample.triggered.connect(self.on_replay_sample_clicked)

        self.act_stop_replay = QAction("Stop Replay", self)
        self.act_stop_replay.triggered.connect(self.on_stop_replay_clicked)

        self.act_save = QAction("Save…", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.on_save_clicked)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        file_menu.addAction(self.act_open_log)
        file_menu.addAction(self.act_replay_sample)
        file_menu.addAction(self.act_stop_replay)
        file_menu.addSeparator()
        file_menu.addAction(self.act_save)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        tools_menu = self.menuBar().addMenu("Tools")

        self.act_simulate = QAction("Simulate Traffic", self)
        self.act_simulate.setCheckable(True)
        self.act_simulate.setToolTip("Generate sample log lines locally (for filter/highlight testing)")
        self.act_simulate.toggled.connect(self.on_simulate_toggled)

        tools_menu.addAction(self.act_simulate)

    def _chip_style(self, color: str) -> str:
        bg = "#f5f5f5"
        if color.lower() == "red":
            bg = "#ffecec"
        elif color.lower() == "green":
            bg = "#eaffea"
        elif color.lower() == "blue":
            bg = "#eef3ff"
        elif color.lower() == "orange":
            bg = "#fff1e6"
        elif color.lower() == "purple":
            bg = "#f4eaff"
        elif color.lower() == "gray":
            bg = "#eeeeee"

        return (
            "QToolButton {"
            "  border: 1px solid #c9c9c9;"
            "  border-radius: 10px;"
            "  padding: 4px 10px;"
            f"  background: {bg};"
            "}"
            "QToolButton:hover { background: #eeeeee; }"
        )

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # --- Top row ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.btn_save = QPushButton("SAVE")
        self.btn_save.clicked.connect(self.on_save_clicked)

        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.clicked.connect(self.on_clear_clicked)

        self.btn_copy = QPushButton("COPY")
        self.btn_copy.clicked.connect(self.on_copy_clicked)

        self.btn_connect = QToolButton()
        self.btn_connect.setText("CONNECT")
        self.btn_connect.setCheckable(True)
        self.btn_connect.clicked.connect(self.on_connect_toggled)

        self.btn_pause = QToolButton()
        self.btn_pause.setText("PAUSE")
        self.btn_pause.setCheckable(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.on_pause_toggled)

        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.stateChanged.connect(self.on_autoscroll_changed)
        
        self.chk_timestamp = QCheckBox("Timestamp")
        self.chk_timestamp.stateChanged.connect(self.on_timestamp_changed)

        top_row.addWidget(self.btn_save)
        top_row.addWidget(self.btn_clear)
        top_row.addWidget(self.btn_copy)
        top_row.addSpacing(12)
        top_row.addWidget(self.btn_connect)
        top_row.addWidget(self.btn_pause)
        top_row.addSpacing(12)
        top_row.addWidget(self.chk_autoscroll)
        top_row.addWidget(self.chk_timestamp)
        top_row.addStretch(1)

        root_layout.addLayout(top_row)

        # --- Settings row ---
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        settings_layout = QGridLayout(settings_frame)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setHorizontalSpacing(10)
        settings_layout.setVerticalSpacing(6)

        lbl_bind = QLabel("Bind-IP:")
        self.ed_bind_ip = QLineEdit()
        self.ed_bind_ip.setPlaceholderText("0.0.0.0")
        self.ed_bind_ip.editingFinished.connect(self.on_settings_edited)

        lbl_port = QLabel("Port:")
        self.ed_port = QLineEdit()
        self.ed_port.setValidator(QIntValidator(1, 65535, self))
        self.ed_port.setPlaceholderText("10514")
        self.ed_port.editingFinished.connect(self.on_settings_edited)

        lbl_max = QLabel("Max lines:")
        self.ed_max_lines = QLineEdit()
        self.ed_max_lines.setValidator(QIntValidator(1000, 500000, self))
        self.ed_max_lines.setPlaceholderText(str(DEFAULT_MAX_LINES))
        self.ed_max_lines.editingFinished.connect(self.on_settings_edited)

        settings_layout.addWidget(lbl_bind, 0, 0)
        settings_layout.addWidget(self.ed_bind_ip, 0, 1)
        settings_layout.addWidget(lbl_port, 0, 2)
        settings_layout.addWidget(self.ed_port, 0, 3)
        settings_layout.addWidget(lbl_max, 0, 4)
        settings_layout.addWidget(self.ed_max_lines, 0, 5)

        settings_layout.setColumnStretch(1, 1)

        root_layout.addWidget(settings_frame)

        # --- Filter/Exclude row (chips + dialog + reset) ---
        fx_frame = QFrame()
        fx_frame.setFrameShape(QFrame.StyledPanel)
        fx_row = QHBoxLayout(fx_frame)
        fx_row.setContentsMargins(10, 10, 10, 10)
        fx_row.setSpacing(10)

        fx_row.addWidget(QLabel("Filter:"))

        self.btn_filter_add = QToolButton()
        self.btn_filter_add.setText("FILTER")
        self.btn_filter_add.clicked.connect(self.on_filter_add_clicked)
        fx_row.addWidget(self.btn_filter_add)

        self._filter_chips_container = QWidget()
        self._filter_chips_layout = QHBoxLayout(self._filter_chips_container)
        self._filter_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._filter_chips_layout.setSpacing(6)
        fx_row.addWidget(self._filter_chips_container, 1)

        self.btn_filter_reset = QPushButton("RESET")
        self.btn_filter_reset.clicked.connect(self.on_filter_reset_clicked)
        fx_row.addWidget(self.btn_filter_reset)

        fx_row.addSpacing(18)

        fx_row.addWidget(QLabel("Exclude:"))

        self.btn_exclude_add = QToolButton()
        self.btn_exclude_add.setText("EXCLUDE")
        self.btn_exclude_add.clicked.connect(self.on_exclude_add_clicked)
        fx_row.addWidget(self.btn_exclude_add)

        self._exclude_chips_container = QWidget()
        self._exclude_chips_layout = QHBoxLayout(self._exclude_chips_container)
        self._exclude_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._exclude_chips_layout.setSpacing(6)
        fx_row.addWidget(self._exclude_chips_container, 1)

        self.btn_exclude_reset = QPushButton("RESET")
        self.btn_exclude_reset.clicked.connect(self.on_exclude_reset_clicked)
        fx_row.addWidget(self.btn_exclude_reset)

        root_layout.addWidget(fx_frame)

        # --- Highlight row (chips + dialog + reset) ---
        hl_frame = QFrame()
        hl_frame.setFrameShape(QFrame.StyledPanel)

        hl_row = QHBoxLayout(hl_frame)
        hl_row.setContentsMargins(10, 10, 10, 10)
        hl_row.setSpacing(8)

        hl_row.addWidget(QLabel("Highlight:"))

        self.btn_hl_add = QToolButton()
        self.btn_hl_add.setText("HIGHLIGHT")
        self.btn_hl_add.clicked.connect(self.on_hl_add_clicked)
        hl_row.addWidget(self.btn_hl_add)

        self._hl_chips_container = QWidget()
        self._hl_chips_layout = QHBoxLayout(self._hl_chips_container)
        self._hl_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._hl_chips_layout.setSpacing(6)
        hl_row.addWidget(self._hl_chips_container, 1)

        self.btn_hl_reset = QPushButton("RESET")
        self.btn_hl_reset.clicked.connect(self.on_hl_reset_clicked)
        hl_row.addWidget(self.btn_hl_reset)

        root_layout.addWidget(hl_frame)

        # --- Content ---
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)

        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(11)
        self.log.setFont(mono)

        self._highlighter = LogHighlighter(self.log.document())

        root_layout.addWidget(self.log, 1)

        self.statusBar().showMessage("Ready")
        self.log.appendPlainText("[MAIN/INFO] Step 6.0 ready (Replay + per-connection live file).")

    # ---------------- Settings ----------------

    def _load_settings(self) -> None:
        s = self._settings
        self._ui_state.bind_ip = s.value("net/bind_ip", self._ui_state.bind_ip, type=str)
        self._ui_state.port = s.value("net/port", self._ui_state.port, type=int)
        self._ui_state.autoscroll = s.value("ui/autoscroll", self._ui_state.autoscroll, type=bool)
        self._ui_state.timestamp_enabled = s.value("ui/timestamp", self._ui_state.timestamp_enabled, type=bool)
        self._ui_state.max_lines = s.value("log/max_lines", self._ui_state.max_lines, type=int)

    def _save_settings(self) -> None:
        s = self._settings
        s.setValue("net/bind_ip", self._ui_state.bind_ip)
        s.setValue("net/port", int(self._ui_state.port))
        s.setValue("ui/autoscroll", bool(self._ui_state.autoscroll))
        s.setValue("ui/timestamp", bool(self._ui_state.timestamp_enabled))
        s.setValue("log/max_lines", int(self._ui_state.max_lines))

        self._save_filter_slots()
        self._save_exclude_slots()
        self._save_highlight_slots()

    def _apply_state_to_widgets(self) -> None:
        self.ed_bind_ip.setText(self._ui_state.bind_ip)
        self.ed_port.setText(str(self._ui_state.port))
        self.chk_autoscroll.setChecked(self._ui_state.autoscroll)
        self.chk_timestamp.setChecked(self._ui_state.timestamp_enabled)
        self.ed_max_lines.setText(str(self._ui_state.max_lines))

    def on_settings_edited(self) -> None:
        self._ui_state.bind_ip = self.ed_bind_ip.text().strip() or "0.0.0.0"
        try:
            self._ui_state.port = int(self.ed_port.text().strip())
        except Exception:
            pass

        try:
            ml = int(self.ed_max_lines.text().strip())
            ml = max(1000, min(500000, ml))
            self._ui_state.max_lines = ml
        except Exception:
            pass

        self._save_settings()
        self._update_connection_ui()

    # ---------------- Slot persistence ----------------

    def _load_slot_list(self, key: str) -> List[PatternSlot]:
        raw = self._settings.value(key, "", type=str)
        if not raw:
            return [PatternSlot() for _ in range(SLOT_COUNT)]
        try:
            items = json.loads(raw)
            if not isinstance(items, list):
                return [PatternSlot() for _ in range(SLOT_COUNT)]
            out: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]
            for i in range(min(SLOT_COUNT, len(items))):
                if not isinstance(items[i], dict):
                    continue
                out[i] = PatternSlot(
                    pattern=str(items[i].get("pattern", "")).strip(),
                    mode=str(items[i].get("mode", "Substring")).strip() or "Substring",
                    color=str(items[i].get("color", "None")).strip() or "None",
                )
            return out
        except Exception:
            return [PatternSlot() for _ in range(SLOT_COUNT)]

    def _save_slot_list(self, key: str, slots: List[PatternSlot]) -> None:
        items = [{"pattern": s.pattern, "mode": s.mode, "color": s.color} for s in slots]
        self._settings.setValue(key, json.dumps(items))

    def _load_filter_slots(self) -> None:
        slots = self._load_slot_list("filter/slots_json")
        if all(not s.pattern.strip() for s in slots):
            legacy = self._settings.value("filter/include_text", "", type=str)
            legacy_mode = self._settings.value("filter/include_mode", "Substring", type=str) or "Substring"
            if legacy.strip():
                slots[0] = PatternSlot(pattern=legacy.strip(), mode=legacy_mode, color="None")
        self._filter_slots = slots

    def _save_filter_slots(self) -> None:
        self._save_slot_list("filter/slots_json", self._filter_slots)

    def _load_exclude_slots(self) -> None:
        slots = self._load_slot_list("exclude/slots_json")
        if all(not s.pattern.strip() for s in slots):
            legacy = self._settings.value("filter/exclude_text", "", type=str)
            legacy_mode = self._settings.value("filter/exclude_mode", "Substring", type=str) or "Substring"
            if legacy.strip():
                slots[0] = PatternSlot(pattern=legacy.strip(), mode=legacy_mode, color="None")
        self._exclude_slots = slots

    def _save_exclude_slots(self) -> None:
        self._save_slot_list("exclude/slots_json", self._exclude_slots)

    def _load_highlight_slots(self) -> None:
        slots = self._load_slot_list("hl/slots_json")
        if all(not s.pattern.strip() for s in slots):
            raw_old = self._settings.value("hl/rules_json", "", type=str)
            if raw_old:
                try:
                    items = json.loads(raw_old)
                    if isinstance(items, list) and items and isinstance(items[0], dict):
                        it0 = items[0]
                        slots[0] = PatternSlot(
                            pattern=str(it0.get("pattern", "")).strip(),
                            mode=str(it0.get("mode", "Substring")).strip() or "Substring",
                            color=str(it0.get("color", "None")).strip() or "None",
                        )
                except Exception:
                    pass
        self._hl_slots = slots

    def _save_highlight_slots(self) -> None:
        self._save_slot_list("hl/slots_json", self._hl_slots)

    # ---------------- Filter matching ----------------

    def _compile_slot_patterns(self, slots: List[PatternSlot]) -> List[List[object]]:
        compiled: List[List[object]] = []
        for s in slots:
            if not s.pattern.strip():
                continue
            pats = compile_patterns(s.pattern, s.mode)
            if pats:
                compiled.append(pats)
        return compiled

    def _match_include_slots(self, line: str) -> bool:
        if not self._filter_slot_patterns:
            return True
        for pats in self._filter_slot_patterns:
            if not self._match_all(line, pats):
                return False
        return True

    def _match_exclude_slots(self, line: str) -> bool:
        for pats in self._exclude_slot_patterns:
            if self._match_all(line, pats):
                return True
        return False

    @staticmethod
    def _match_all(line: str, patterns: List[object]) -> bool:
        for p in patterns:
            try:
                if hasattr(p, "search"):
                    if p.search(line) is None:
                        return False
                elif callable(p):
                    if not bool(p(line)):
                        return False
                else:
                    if str(p) not in line:
                        return False
            except Exception:
                return False
        return True

    def _rebuild_filter_patterns(self) -> None:
        self._filter_slot_patterns = self._compile_slot_patterns(self._filter_slots)
        self._exclude_slot_patterns = self._compile_slot_patterns(self._exclude_slots)

    # ---------------- Highlight ----------------

    def _rebuild_highlight_rules(self) -> None:
        rules: List[HighlightRule] = []
        for s in self._hl_slots:
            if not s.pattern.strip():
                continue
            if s.color.strip().lower() == "none":
                continue
            r = HighlightRule.create(s.pattern, s.mode, s.color)
            if r is not None:
                rules.append(r)
        self._hl_rules = rules

    def _apply_highlighter(self) -> None:
        self._highlighter.set_rules(self._hl_rules)
        self.statusBar().showMessage(f"Highlight rules active: {len(self._hl_rules)}", 2000)

    # ---------------- Chip UI helpers ----------------

    def _find_first_free_slot(self, slots: List[PatternSlot]) -> Optional[int]:
        for i, s in enumerate(slots):
            if not s.pattern.strip():
                return i
        return None

    def _refresh_chips(self, layout: QHBoxLayout, slots: List[PatternSlot], on_edit, on_remove) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        active = [i for i, s in enumerate(slots) if s.pattern.strip()]
        if not active:
            lbl = QLabel("no rules")
            lbl.setStyleSheet("color: #777777;")
            layout.addWidget(lbl)
            layout.addStretch(1)
            return

        for idx in active:
            s = slots[idx]
            txt = f"{s.pattern}"
            if s.color.strip().lower() != "none":
                txt = f"{txt} ({s.color})"
            btn = QToolButton()
            btn.setText(txt)
            btn.setStyleSheet(self._chip_style(s.color))
            btn.setToolTip(f"Slot {idx+1} — click to edit; right-click to remove")
            btn.clicked.connect(lambda _checked=False, i=idx: on_edit(i))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _pt, i=idx: on_remove(i))
            layout.addWidget(btn)

        layout.addStretch(1)

    def _refresh_filter_chips(self) -> None:
        self._refresh_chips(self._filter_chips_layout, self._filter_slots, self.on_filter_edit_clicked, self.on_filter_remove_clicked)

    def _refresh_exclude_chips(self) -> None:
        self._refresh_chips(self._exclude_chips_layout, self._exclude_slots, self.on_exclude_edit_clicked, self.on_exclude_remove_clicked)

    def _refresh_highlight_chips(self) -> None:
        self._refresh_chips(self._hl_chips_layout, self._hl_slots, self.on_hl_edit_clicked, self.on_hl_remove_clicked)

    # ---------------- Dialog actions ----------------

    def _open_slot_dialog(self, title: str, slots: List[PatternSlot], slot_index: int) -> Optional[Tuple[int, PatternSlot]]:
        if slot_index < 0:
            free = self._find_first_free_slot(slots)
            if free is None:
                QMessageBox.information(self, title, f"All {SLOT_COUNT} slots are used.\nEdit an existing chip or RESET.")
                return None
            dlg = PatternEditDialog(self, f"Edit {title} Rule", slot_index=-1, slot=PatternSlot(), suggested_index=free)
        else:
            if not (0 <= slot_index < SLOT_COUNT):
                return None
            dlg = PatternEditDialog(self, f"Edit {title} Rule", slot_index=slot_index, slot=slots[slot_index], suggested_index=slot_index)

        if dlg.exec_() != QDialog.Accepted:
            return None
        return dlg.result_data()

    # Filter

    def on_filter_add_clicked(self) -> None:
        res = self._open_slot_dialog("Filter", self._filter_slots, -1)
        if res is None:
            return
        idx, slot = res
        self._filter_slots[idx] = slot
        self._rebuild_filter_patterns()
        self._save_filter_slots()
        self._refresh_filter_chips()

    def on_filter_edit_clicked(self, idx: int) -> None:
        res = self._open_slot_dialog("Filter", self._filter_slots, idx)
        if res is None:
            return
        new_idx, slot = res
        if new_idx == idx:
            self._filter_slots[idx] = slot
        else:
            self._filter_slots[new_idx] = slot
            self._filter_slots[idx] = PatternSlot()
        self._rebuild_filter_patterns()
        self._save_filter_slots()
        self._refresh_filter_chips()

    def on_filter_remove_clicked(self, idx: int) -> None:
        if not (0 <= idx < SLOT_COUNT):
            return
        self._filter_slots[idx] = PatternSlot()
        self._rebuild_filter_patterns()
        self._save_filter_slots()
        self._refresh_filter_chips()

    def on_filter_reset_clicked(self) -> None:
        self._filter_slots = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._rebuild_filter_patterns()
        self._save_filter_slots()
        self._refresh_filter_chips()
        self.log.appendPlainText("[UI/INFO] Filter RESET")

    # Exclude

    def on_exclude_add_clicked(self) -> None:
        res = self._open_slot_dialog("Exclude", self._exclude_slots, -1)
        if res is None:
            return
        idx, slot = res
        self._exclude_slots[idx] = slot
        self._rebuild_filter_patterns()
        self._save_exclude_slots()
        self._refresh_exclude_chips()

    def on_exclude_edit_clicked(self, idx: int) -> None:
        res = self._open_slot_dialog("Exclude", self._exclude_slots, idx)
        if res is None:
            return
        new_idx, slot = res
        if new_idx == idx:
            self._exclude_slots[idx] = slot
        else:
            self._exclude_slots[new_idx] = slot
            self._exclude_slots[idx] = PatternSlot()
        self._rebuild_filter_patterns()
        self._save_exclude_slots()
        self._refresh_exclude_chips()

    def on_exclude_remove_clicked(self, idx: int) -> None:
        if not (0 <= idx < SLOT_COUNT):
            return
        self._exclude_slots[idx] = PatternSlot()
        self._rebuild_filter_patterns()
        self._save_exclude_slots()
        self._refresh_exclude_chips()

    def on_exclude_reset_clicked(self) -> None:
        self._exclude_slots = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._rebuild_filter_patterns()
        self._save_exclude_slots()
        self._refresh_exclude_chips()
        self.log.appendPlainText("[UI/INFO] Exclude RESET")

    # Highlight

    def on_hl_add_clicked(self) -> None:
        res = self._open_slot_dialog("Highlight", self._hl_slots, -1)
        if res is None:
            return
        idx, slot = res
        self._hl_slots[idx] = slot
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._save_highlight_slots()
        self._refresh_highlight_chips()

    def on_hl_edit_clicked(self, idx: int) -> None:
        res = self._open_slot_dialog("Highlight", self._hl_slots, idx)
        if res is None:
            return
        new_idx, slot = res
        if new_idx == idx:
            self._hl_slots[idx] = slot
        else:
            self._hl_slots[new_idx] = slot
            self._hl_slots[idx] = PatternSlot()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._save_highlight_slots()
        self._refresh_highlight_chips()

    def on_hl_remove_clicked(self, idx: int) -> None:
        if not (0 <= idx < SLOT_COUNT):
            return
        self._hl_slots[idx] = PatternSlot()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._save_highlight_slots()
        self._refresh_highlight_chips()

    def on_hl_reset_clicked(self) -> None:
        self._hl_slots = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._save_highlight_slots()
        self._refresh_highlight_chips()
        self.log.appendPlainText("[UI/INFO] Highlight RESET")

    # ---------------- Replay / Inject ----------------

    def _ingest_line(self, line: str) -> None:
        if not self._match_include_slots(line):
            return
        if self._match_exclude_slots(line):
            return
        self._queue.append(line)

    def _replay_tick(self) -> None:
        if not self._replay_lines:
            self._replay_timer.stop()
            self._replay_active = False
            self.statusBar().showMessage("Replay finished", 2000)
            return

        for _ in range(REPLAY_LINES_PER_TICK):
            if not self._replay_lines:
                break
            self._ingest_line(self._replay_lines.popleft())

    def on_open_log_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Log", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = [ln.rstrip("\r\n") for ln in f.readlines()]
        except Exception as e:
            QMessageBox.critical(self, "Open Log Failed", f"Could not open file:\n{e}")
            return

        self.on_stop_replay_clicked()
        self._replay_lines = deque([ln for ln in lines if ln.strip() and not ln.startswith("#")])
        self._replay_active = True
        self._replay_timer.start()
        self.statusBar().showMessage(f"Replay: {os.path.basename(path)} ({len(self._replay_lines)} lines)", 3000)

    def on_replay_sample_clicked(self) -> None:
        sample = [
            "[MAIN/INFO] ======================================================",
            "[MAIN/INFO] === ESP32-S3 + ST7701 480x480 + LVGL 9.4.x + Touch ===",
            "[MAIN/INFO] ======================================================",
            "[WIFI] Connected. IP: 192.168.0.103",
            "[UDP] selftest: sending 3 packets...",
            "[HOST/INFO] STATUS received, mask=0x0000 (    0x0000), adc=[203,0,0,0] tempRaw=203",
            "[OVEN/INFO] [T11] mode=0 door=0 lock=0 ntc=20.30 core=23.15 ui=23.15 ctrl=23.15 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=0 heatRemMs=0 restRemMs=0",
            "[OVEN/INFO] [T11] mode=0 door=0 lock=0 ntc=20.80 core=23.20 ui=23.20 ctrl=23.20 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=1 heatRemMs=2000 restRemMs=0",
            "[HEATER/DBG] pwm=4000Hz duty=50%",
            "[HOST/INFO] STATUS received, mask=0x1010 (    0x1010), adc=[205,0,0,0] tempRaw=205",
            "[UI/INFO] Listener: ON — 0.0.0.0:10514",
            "[UI/ERROR] UDP listener error: [Errno 9] Bad file descriptor",
            "[OVEN/WARN] Door opened — entering WAIT",
            "[OVEN/INFO] [T11] mode=1 door=1 lock=1 ntc=21.00 core=23.25 ui=23.25 ctrl=23.25 tgt=40.00 lo=37.00 hi=43.00 heaterIntent=0 heatRemMs=0 restRemMs=3000",
            "[MAIN/INFO] Sample done.",
        ]

        self.on_stop_replay_clicked()
        self._replay_lines = deque(sample)
        self._replay_active = True
        self._replay_timer.start()
        self.statusBar().showMessage("Replay: sample", 2000)

    def on_stop_replay_clicked(self) -> None:
        if self._replay_timer.isActive():
            self._replay_timer.stop()
        self._replay_lines.clear()
        self._replay_active = False
        self.statusBar().showMessage("Replay stopped", 1500)

    # ---------------- Simulation (Tools menu) ----------------

    def on_simulate_toggled(self, checked: bool) -> None:
        # Simulation uses the same processing path as UDP lines (filters/highlights/livefile/timestamp).
        if checked:
            if self._listener is None:
                # only meaningful while connected (per-connection live logfile semantics)
                self.act_simulate.blockSignals(True)
                self.act_simulate.setChecked(False)
                self.act_simulate.blockSignals(False)
                self.statusBar().showMessage("Simulation requires CONNECTED (start listener first).", 2500)
                return
            self._start_simulation()
        else:
            self._stop_simulation()

    def _start_simulation(self) -> None:
        if self._sim_timer.isActive():
            return
        self._sim_enabled = True
        self._sim_seq = 0
        self._sim_ntc = 22.0
        self._sim_core = 23.0
        self._sim_tgt = 40.0
        self._sim_heater = 0
        self._sim_mask = 0x0000
        self._sim_timer.start()
        self.statusBar().showMessage("Simulation: ON (default profile)", 2500)

    def _stop_simulation(self) -> None:
        self._sim_enabled = False
        if self._sim_timer.isActive():
            self._sim_timer.stop()
        self.statusBar().showMessage("Simulation: OFF", 1500)

    def _on_sim_tick(self) -> None:
        if not self._sim_enabled or self._listener is None:
            return
        line = self._sim_next_line()
        # Feed the same pipeline as real UDP input.
        self._on_line_received(line)

    def _sim_next_line(self) -> str:
        # Lightweight stream of realistic lines for filter/exclude/highlight testing.
        self._sim_seq += 1
        if self._sim_seq % 13 == 0:
            self._sim_heater = 1 - self._sim_heater
        if self._sim_heater:
            self._sim_ntc += 0.15 + random.random() * 0.05
            self._sim_core += 0.05 + random.random() * 0.03
        else:
            self._sim_ntc -= 0.03 + random.random() * 0.02
            self._sim_core -= 0.01 + random.random() * 0.01
        self._sim_ntc = max(18.0, min(80.0, self._sim_ntc))
        self._sim_core = max(18.0, min(70.0, self._sim_core))
        if self._sim_seq % 40 == 0:
            self._sim_mask ^= 0x0010
        if self._sim_seq % 97 == 0:
            self._sim_mask ^= 0x0040
        r = random.random()
        if r < 0.45:
            adc0 = int(self._sim_ntc * 10)
            return f"[HOST/INFO] STATUS received, mask=0x{self._sim_mask:04x} (    0x{self._sim_mask:04x}), adc=[{adc0},0,0,0] tempRaw={adc0}"
        if r < 0.70:
            heater_intent = 1 if self._sim_heater and self._sim_core < (self._sim_tgt - 0.3) else 0
            heat_rem = 800 if self._sim_heater else 0
            rest_rem = 0 if self._sim_heater else 1200
            lo = self._sim_tgt - 3.0
            hi = self._sim_tgt + 3.0
            return (
                f"[OVEN/INFO] [T11] mode=0 door=0 lock=0 "
                f"ntc={self._sim_ntc:0.2f} core={self._sim_core:0.2f} ui={self._sim_core:0.2f} ctrl={self._sim_core:0.2f} "
                f"tgt={self._sim_tgt:0.2f} lo={lo:0.2f} hi={hi:0.2f} "
                f"heaterIntent={heater_intent} heatRemMs={heat_rem} restRemMs={rest_rem}"
            )
        if r < 0.80:
            return f"[HEATER/INFO] {'ON' if self._sim_heater else 'OFF'} pwm=4000Hz duty=50%"
        if r < 0.90:
            return "[UI/DEBUG] screen_main tick"
        if r < 0.97:
            return "[HOST/DEBUG] RX burst: 128 bytes"
        return "[HOST/ERROR] UART timeout while polling STATUS"

    # ---------------- Log limits ----------------

    def _enforce_log_limit(self) -> None:
        max_lines = int(self._ui_state.max_lines) if self._ui_state.max_lines else DEFAULT_MAX_LINES
        if max_lines < 1000:
            max_lines = 1000

        doc = self.log.document()
        blocks = doc.blockCount()
        if blocks <= max_lines:
            return

        remove_n = min(DEFAULT_TRIM_CHUNK, blocks - max_lines)
        if remove_n <= 0:
            return

        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.Start)
        for _ in range(remove_n):
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        self._trimmed_lines_total += remove_n

    # ---------------- UDP listener ----------------

    def _start_listener(self) -> bool:
        if self._listener is not None:
            return True

        bind_ip = self.ed_bind_ip.text().strip() or "0.0.0.0"
        port_text = self.ed_port.text().strip()

        if not port_text:
            QMessageBox.warning(self, "Missing Port", "Port is empty. Please enter a port number.")
            return False

        try:
            port = int(port_text)
            if not (1 <= port <= 65535):
                raise ValueError("Port out of range")
        except Exception:
            QMessageBox.warning(self, "Invalid Port", "Port must be a number between 1 and 65535.")
            return False

        self._ui_state.bind_ip = bind_ip
        self._ui_state.port = port

        self._rx_packets = 0
        self._rx_lines = 0

        t = UdpListenerThread(bind_ip, port, parent=self)
        t.line_received.connect(self._on_line_received)
        t.status_changed.connect(self._on_listener_status)
        t.error.connect(self._on_listener_error)
        t.rx_stats.connect(self._on_rx_stats)

        self._listener = t
        t.start()

        # Per connection: create a fresh live log file (NEW)
        self._open_new_live_log()
        return True

    def _stop_listener(self) -> None:
        if self._listener is None:
            return
        t = self._listener
        self._listener = None

        try:
            t.stop()
            t.wait(800)
        except Exception:
            pass

        self._close_live_log()


    
    def _on_line_received(self, line: str) -> None:
            # Common ingress for UDP + Simulation. Always persist to live file while connected.
            if not self._match_include_slots(line):
                return
            if self._match_exclude_slots(line):
                return
    
            out_line = line
            if self._ui_state.timestamp_enabled:
                out_line = f"{self._format_timestamp_prefix(datetime.now())} {line}"
    
            # Always write to the per-connection live file (even if UI is paused).
            if self._listener is not None:
                self._append_to_live_log(out_line)
    
            if self._ui_paused:
                # Keep only a tail buffer so Resume shows the newest context without unbounded memory growth.
                if len(self._pause_buffer) >= self._pause_buffer.maxlen:
                    self._pause_dropped += 1
                self._pause_buffer.append(out_line)
                return
    
            self._queue.append(out_line)

    def _on_listener_status(self, msg: str) -> None:
        # The listener may emit transient status messages. Show briefly, then restore our rich status line.
        self.statusBar().showMessage(msg, 1500)
        if self._listener is not None:
            QTimer.singleShot(1600, self._update_connection_ui)


    def _on_listener_error(self, msg: str) -> None:
        self._append_log_line(f"[UI/ERROR] {msg}", write_live=True)
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        self.statusBar().showMessage(msg, 5000)

    
    def _on_rx_stats(self, packets: int, lines: int) -> None:
            self._rx_packets = packets
            self._rx_lines = lines
            if self._listener is None:
                return
    
            paused_txt = ""
            if self._ui_paused:
                paused_txt = f" — PAUSED (tail={len(self._pause_buffer)} drop={self._pause_dropped})"
    
            self.statusBar().showMessage(
                f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — "
                f"pkts={packets} lines={lines} — shown={self.log.document().blockCount()} "
                f"dropped={self._trimmed_lines_total} — HL={len(self._hl_rules)}"
                + (f" — {self._live_status_snippet()}" if getattr(self, "_live_log_path", None) else "")
                + paused_txt
            )

    def _flush_log_queue(self) -> None:
        if not self._queue:
            return
        batch = drain_queue(self._queue, max_items=300)
        if not batch:
            return

        for line in batch:
            self.log.appendPlainText(line)

        try:
            if self._live_log_handle is not None:
                self._live_log_handle.flush()
        except Exception:
            self._close_live_log()

        self._enforce_log_limit()

        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    # ---------------- UI actions ----------------

    
    def on_save_clicked(self) -> None:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Log",
                self._default_save_name(),
                "Text Files (*.txt);;All Files (*)",
            )
            if not path:
                return
    
            # Prefer copying the per-connection live logfile (even if already disconnected).
            src: Optional[Path] = None
            if self._live_log_path is not None:
                src = self._live_log_path
                try:
                    if self._live_log_handle is not None:
                        try:
                            self._live_log_handle.flush()
                            os.fsync(self._live_log_handle.fileno())
                        except Exception:
                            pass
                except Exception:
                    pass
            elif self._last_session_log_path is not None and self._last_session_log_path.exists():
                src = self._last_session_log_path
    
            if src is not None and src.exists():
                try:
                    import shutil
                    shutil.copy2(str(src), path)
                    self.statusBar().showMessage(f"Saved (copied): {path}", 4000)
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Save Failed", f"Could not copy logfile:\n{e}")
                    return
    
            # Fallback: save current UI content (e.g., when no session file exists).
            try:
                content = self.log.toPlainText()
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")
                self.statusBar().showMessage(f"Saved: {path}", 4000)
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")

    def on_clear_clicked(self) -> None:
        self.log.clear()
        self._trimmed_lines_total = 0
        self.statusBar().showMessage("Cleared (UI only)", 2000)

    def on_copy_clicked(self) -> None:
        cursor = self.log.textCursor()
        selected = cursor.selectedText()
        if selected:
            QApplication.clipboard().setText(selected)
            self.statusBar().showMessage("Copied selection", 2000)
        else:
            QApplication.clipboard().setText(self.log.toPlainText())
            self.statusBar().showMessage("Copied all", 2000)

    
    def on_connect_toggled(self) -> None:
            requested = self.btn_connect.isChecked()
    
            if requested:
                ok = self._start_listener()
                if not ok:
                    self.btn_connect.setChecked(False)
                    self._update_connection_ui()
                    return
    
                self._ui_paused = False
                self.btn_pause.blockSignals(True)
                self.btn_pause.setChecked(False)
                self.btn_pause.blockSignals(False)
    
                self._append_log_line(
                    f"[UI/INFO] Listening on {self._ui_state.bind_ip}:{self._ui_state.port}",
                    write_live=False,
                )
                if self._live_log_path is not None:
                    self.log.appendPlainText(f"[UI/INFO] Live logfile: {self._live_log_path}")
            else:
                # Disconnect requested
                if self._listener is not None:
                    # Offer to save/copy the session logfile so nothing gets lost.
                    mb = QMessageBox(self)
                    mb.setWindowTitle("Disconnect")
                    mb.setIcon(QMessageBox.Question)
                    mb.setText("Disconnect now?")
                    mb.setInformativeText("Do you want to save/copy the current session log before disconnecting?")
                    yes = mb.addButton("Save…", QMessageBox.YesRole)
                    no = mb.addButton("No", QMessageBox.NoRole)
                    cancel = mb.addButton("Cancel", QMessageBox.RejectRole)
                    mb.setDefaultButton(yes)
                    mb.exec_()
    
                    clicked = mb.clickedButton()
                    if clicked == cancel:
                        # Abort disconnect
                        self.btn_connect.blockSignals(True)
                        self.btn_connect.setChecked(True)
                        self.btn_connect.blockSignals(False)
                        self._update_connection_ui()
                        return
                    if clicked == yes:
                        self.on_save_clicked()
    
                self._stop_listener()
    
                # stop simulation when disconnecting
                try:
                    if hasattr(self, "act_simulate") and self.act_simulate.isChecked():
                        self.act_simulate.setChecked(False)
                except Exception:
                    pass
    
                # reset pause state
                self._ui_paused = False
                self._pause_buffer.clear()
                self._pause_dropped = 0
                self.btn_pause.blockSignals(True)
                self.btn_pause.setChecked(False)
                self.btn_pause.blockSignals(False)
    
                self._append_log_line("[UI/INFO] Listener stopped", write_live=False)
    
            self._update_connection_ui()

    def on_pause_toggled(self) -> None:
        if self._listener is None:
            # Should not happen, keep it safe.
            self.btn_pause.setChecked(False)
            self._ui_paused = False
            self._pause_buffer.clear()
            self._pause_dropped = 0
            self._update_connection_ui()
            return

        self._ui_paused = bool(self.btn_pause.isChecked())

        if self._ui_paused:
            self.statusBar().showMessage("UI paused (logging continues)", 2000)
        else:
            # Resume: flush buffered tail into the UI queue and jump to newest lines.
            dropped = self._pause_dropped
            buffered = list(self._pause_buffer)
            self._pause_buffer.clear()
            self._pause_dropped = 0

            if dropped > 0:
                self._queue.append(f"[UI/INFO] Resume: {dropped} lines skipped while paused (showing latest tail).")
            for ln in buffered:
                self._queue.append(ln)

            # trigger immediate UI update
            self._flush_log_queue()
            self.statusBar().showMessage("UI resumed", 1500)

        self._update_connection_ui()

    def on_timestamp_changed(self) -> None:
        # Must be toggled before CONNECT (UI disables it while connected).
        self._ui_state.timestamp_enabled = self.chk_timestamp.isChecked()
        self._save_settings()
        self.statusBar().showMessage(
            f"Timestamp: {'ON' if self._ui_state.timestamp_enabled else 'OFF'} (applies on next CONNECT)",
            2500,
        )

    def on_autoscroll_changed(self) -> None:
        self._ui_state.autoscroll = self.chk_autoscroll.isChecked()
        self._save_settings()
        self.statusBar().showMessage(f"Auto-Scroll: {'ON' if self._ui_state.autoscroll else 'OFF'}", 2000)

    
    def _update_connection_ui(self) -> None:
            connected = self._listener is not None
    
            if connected:
                self.chk_timestamp.setEnabled(False)
    
                self.btn_connect.setText("CONNECTED")
                self.btn_connect.setStyleSheet("QToolButton { background-color: #2ecc71; font-weight: bold; }")
    
                self.btn_pause.setEnabled(True)
                if self._ui_paused:
                    self.btn_pause.setText("RESUME")
                    self.btn_pause.setStyleSheet("QToolButton { background-color: #e74c3c; font-weight: bold; }")
                else:
                    self.btn_pause.setText("PAUSE")
                    self.btn_pause.setStyleSheet("QToolButton { background-color: #2ecc71; font-weight: bold; }")
    
                paused_txt = ""
                if self._ui_paused:
                    paused_txt = f" — PAUSED (tail={len(self._pause_buffer)} drop={self._pause_dropped})"
    
                self.statusBar().showMessage(
                    f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — "
                    f"pkts={self._rx_packets} lines={self._rx_lines} — shown={self.log.document().blockCount()} "
                    f"dropped={self._trimmed_lines_total} — HL={len(self._hl_rules)}"
                    + (f" — {self._live_status_snippet()}" if getattr(self, "_live_log_path", None) else "")
                    + paused_txt
                )
            else:
                self.chk_timestamp.setEnabled(True)
    
                self.btn_connect.setText("CONNECT")
                self.btn_connect.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")
    
                self.btn_pause.setEnabled(False)
                self.btn_pause.setText("PAUSE")
                self.btn_pause.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")
    
                self.statusBar().showMessage(
                    f"Listener: OFF — {self._ui_state.bind_ip}:{self._ui_state.port} — "
                    f"shown={self.log.document().blockCount()} dropped={self._trimmed_lines_total} — HL={len(self._hl_rules)}"
                )

    # --- Step 6.3 live logfile status ---
    @staticmethod
    def _format_bytes(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n/1024.0:.1f} KB"
        if n < 1024 * 1024 * 1024:
            return f"{n/(1024.0*1024.0):.1f} MB"
        return f"{n/(1024.0*1024.0*1024.0):.2f} GB"

    @staticmethod
    def _format_timestamp_prefix(dt: datetime) -> str:
        # Format: yyyymmdd-hh:mm:ss.mmm
        return dt.strftime("%Y%m%d-%H:%M:%S.") + f"{dt.microsecond//1000:03d}"

    def _append_log_line(self, line: str, *, write_live: bool = False) -> None:
        out_line = line
        if self._ui_state.timestamp_enabled:
            out_line = f"{self._format_timestamp_prefix(datetime.now())} {line}"

        self.log.appendPlainText(out_line)

        if write_live and getattr(self, "_live_log_handle", None) is not None:
            try:
                self._append_to_live_log(out_line)
            except Exception:
                pass

        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _live_status_snippet(self) -> str:
        if getattr(self, "_live_log_path", None) is None:
            return ""
        try:
            size = self._live_log_path.stat().st_size
        except Exception:
            size = 0
        return f"LIVE: {self._live_log_path.name} ({self._format_bytes(size)})"


    # ---------------- Qt overrides ----------------

    def closeEvent(self, event) -> None:
        try:
            self.on_stop_replay_clicked()
        except Exception:
            pass
        try:
            self._stop_simulation()
        except Exception:
            pass
        try:
            self._stop_listener()
        except Exception:
            pass
        self._save_settings()
        super().closeEvent(event)


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    w = MainWindow()
    w.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
