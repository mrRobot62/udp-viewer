from __future__ import annotations

import json
import sys
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple

from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QAction,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QSizePolicy,
    QFrame,
    QDialog,
    QDialogButtonBox,
    QSpinBox,
)

from .udp_listener import UdpListenerThread
from .udp_log_utils import drain_queue, compile_patterns, match_include, match_exclude
from .highlighter import HighlightRule, LogHighlighter

APP_ORG = "LocalTools"
APP_NAME = "UdpLogViewer"
APP_VERSION = "0.5-step4.4-optionB1-chips"

HIGHLIGHT_SLOTS = 5


@dataclass
class UiState:
    bind_ip: str = "0.0.0.0"
    port: int = 10514
    autoscroll: bool = True

    include_text: str = ""
    include_mode: str = "Substring"
    exclude_text: str = ""
    exclude_mode: str = "Substring"


@dataclass
class HighlightSlot:
    pattern: str = ""
    mode: str = "Substring"     # "Substring" | "Regex"
    color: str = "None"         # "None" | "Red" | ...


class HighlightEditDialog(QDialog):
    def __init__(self, parent: QWidget, slot_index: int, slot: HighlightSlot, suggested_index: int) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Highlight Rule")
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Slot:"), 0, 0)
        self.sb_slot = QSpinBox()
        self.sb_slot.setRange(1, HIGHLIGHT_SLOTS)
        self.sb_slot.setValue((slot_index + 1) if slot_index >= 0 else (suggested_index + 1))
        grid.addWidget(self.sb_slot, 0, 1)

        grid.addWidget(QLabel("Pattern:"), 1, 0)
        self.ed_pattern = QLineEdit()
        self.ed_pattern.setText(slot.pattern)
        self.ed_pattern.setPlaceholderText('e.g. "[OVEN/INFO] [T11]" or "ERROR"')
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
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def result_data(self) -> Tuple[int, HighlightSlot]:
        idx = int(self.sb_slot.value()) - 1
        slot = HighlightSlot(
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

        # Queue + batching
        self._queue: Deque[str] = deque()
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(50)
        self._flush_timer.timeout.connect(self._flush_log_queue)
        self._flush_timer.start()

        # Filter
        self._include_patterns = []
        self._exclude_patterns = []

        # Highlighting (B1: fixed 5 slots, chips show active)
        self._hl_slots: List[HighlightSlot] = [HighlightSlot() for _ in range(HIGHLIGHT_SLOTS)]
        self._hl_rules: List[HighlightRule] = []

        self.setWindowTitle(f"UDP Log Viewer — {APP_VERSION}")
        self.resize(1100, 750)

        self._build_actions()
        self._build_ui()

        self._load_settings()
        self._apply_state_to_widgets()
        self._rebuild_filter_patterns()

        self._load_highlight_slots()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._refresh_highlight_chips()

        self._update_connection_ui()

    # ---------------- UI ----------------

    def _build_actions(self) -> None:
        file_menu = self.menuBar().addMenu("File")

        self.act_save = QAction("Save…", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.on_save_clicked)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        file_menu.addAction(self.act_save)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

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

        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.stateChanged.connect(self.on_autoscroll_changed)

        top_row.addWidget(self.btn_save)
        top_row.addWidget(self.btn_clear)
        top_row.addWidget(self.btn_copy)
        top_row.addSpacing(12)
        top_row.addWidget(self.btn_connect)
        top_row.addSpacing(12)
        top_row.addWidget(self.chk_autoscroll)
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

        settings_layout.addWidget(lbl_bind, 0, 0)
        settings_layout.addWidget(self.ed_bind_ip, 0, 1)
        settings_layout.addWidget(lbl_port, 0, 2)
        settings_layout.addWidget(self.ed_port, 0, 3)
        settings_layout.setColumnStretch(1, 1)

        root_layout.addWidget(settings_frame)

        # --- Filter panel ---
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)

        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(6)

        lbl_inc = QLabel("Include:")
        self.ed_include = QLineEdit()
        self.ed_include.setPlaceholderText('e.g. "[OVEN/INFO] [T11]"  or  "[HOST/INFO];mask=0x1000"')
        self.ed_include.textChanged.connect(self.on_filter_ui_changed)

        self.cb_include_mode = QComboBox()
        self.cb_include_mode.addItems(["Substring", "Regex"])
        self.cb_include_mode.currentTextChanged.connect(self.on_filter_ui_changed)

        lbl_exc = QLabel("Exclude:")
        self.ed_exclude = QLineEdit()
        self.ed_exclude.setPlaceholderText('e.g. "STATUS received"')
        self.ed_exclude.textChanged.connect(self.on_filter_ui_changed)

        self.cb_exclude_mode = QComboBox()
        self.cb_exclude_mode.addItems(["Substring", "Regex"])
        self.cb_exclude_mode.currentTextChanged.connect(self.on_filter_ui_changed)

        filter_layout.addWidget(lbl_inc, 0, 0)
        filter_layout.addWidget(self.ed_include, 0, 1)
        filter_layout.addWidget(self.cb_include_mode, 0, 2)
        filter_layout.addWidget(lbl_exc, 1, 0)
        filter_layout.addWidget(self.ed_exclude, 1, 1)
        filter_layout.addWidget(self.cb_exclude_mode, 1, 2)
        filter_layout.setColumnStretch(1, 1)

        root_layout.addWidget(filter_frame)

        # --- Highlight row (Option B1: chips + add) ---
        hl_frame = QFrame()
        hl_frame.setFrameShape(QFrame.StyledPanel)

        hl_row = QHBoxLayout(hl_frame)
        hl_row.setContentsMargins(10, 10, 10, 10)
        hl_row.setSpacing(8)

        hl_row.addWidget(QLabel("Highlight:"))

        self.btn_hl_add = QToolButton()
        self.btn_hl_add.setText("+")
        self.btn_hl_add.setToolTip("Add highlight rule (max 5 slots)")
        self.btn_hl_add.clicked.connect(self.on_hl_add_clicked)
        hl_row.addWidget(self.btn_hl_add)

        self._chips_container = QWidget()
        self._chips_layout = QHBoxLayout(self._chips_container)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(6)
        hl_row.addWidget(self._chips_container, 1)

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
        self.log.appendPlainText("[MAIN/INFO] Step 4.4 (Option B1 chips) ready.")

    # ---------------- Settings ----------------

    def _load_settings(self) -> None:
        s = self._settings
        self._ui_state.bind_ip = s.value("net/bind_ip", self._ui_state.bind_ip, type=str)
        self._ui_state.port = s.value("net/port", self._ui_state.port, type=int)
        self._ui_state.autoscroll = s.value("ui/autoscroll", self._ui_state.autoscroll, type=bool)

        self._ui_state.include_text = s.value("filter/include_text", "", type=str)
        self._ui_state.include_mode = s.value("filter/include_mode", "Substring", type=str)
        self._ui_state.exclude_text = s.value("filter/exclude_text", "", type=str)
        self._ui_state.exclude_mode = s.value("filter/exclude_mode", "Substring", type=str)

    def _save_settings(self) -> None:
        s = self._settings
        s.setValue("net/bind_ip", self._ui_state.bind_ip)
        s.setValue("net/port", int(self._ui_state.port))
        s.setValue("ui/autoscroll", bool(self._ui_state.autoscroll))

        s.setValue("filter/include_text", self._ui_state.include_text)
        s.setValue("filter/include_mode", self._ui_state.include_mode)
        s.setValue("filter/exclude_text", self._ui_state.exclude_text)
        s.setValue("filter/exclude_mode", self._ui_state.exclude_mode)

        self._save_highlight_slots()

    def _apply_state_to_widgets(self) -> None:
        self.ed_bind_ip.setText(self._ui_state.bind_ip)
        self.ed_port.setText(str(self._ui_state.port))
        self.chk_autoscroll.setChecked(self._ui_state.autoscroll)

        self.ed_include.setText(self._ui_state.include_text)
        self.cb_include_mode.setCurrentText(self._ui_state.include_mode)
        self.ed_exclude.setText(self._ui_state.exclude_text)
        self.cb_exclude_mode.setCurrentText(self._ui_state.exclude_mode)

    # ---------------- Filter ----------------

    def _rebuild_filter_patterns(self) -> None:
        self._include_patterns = compile_patterns(self._ui_state.include_text, self._ui_state.include_mode)
        self._exclude_patterns = compile_patterns(self._ui_state.exclude_text, self._ui_state.exclude_mode)

    def on_filter_ui_changed(self) -> None:
        self._ui_state.include_text = self.ed_include.text()
        self._ui_state.include_mode = self.cb_include_mode.currentText()
        self._ui_state.exclude_text = self.ed_exclude.text()
        self._ui_state.exclude_mode = self.cb_exclude_mode.currentText()
        self._rebuild_filter_patterns()

    # ---------------- Highlight (B1 chips) ----------------

    def _active_slot_indices(self) -> List[int]:
        out = []
        for i, s in enumerate(self._hl_slots):
            if s.pattern.strip() and s.color.strip().lower() != "none":
                out.append(i)
        return out

    def _find_first_free_slot(self) -> Optional[int]:
        for i, s in enumerate(self._hl_slots):
            if not s.pattern.strip() and s.color.strip().lower() == "none":
                return i
        return None

    def _chip_style(self) -> str:
        return (
            "QToolButton {"
            "  border: 1px solid #c9c9c9;"
            "  border-radius: 10px;"
            "  padding: 4px 10px;"
            "  background: #f5f5f5;"
            "}"
            "QToolButton:hover { background: #eeeeee; }"
        )

    def _refresh_highlight_chips(self) -> None:
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

        active = self._active_slot_indices()
        if not active:
            lbl = QLabel("no rules")
            lbl.setStyleSheet("color: #777777;")
            self._chips_layout.addWidget(lbl)
            self._chips_layout.addStretch(1)
            return

        for idx in active:
            slot = self._hl_slots[idx]
            txt = f"{slot.pattern} ({slot.color})"
            btn = QToolButton()
            btn.setText(txt)
            btn.setStyleSheet(self._chip_style())
            btn.setToolTip(f"Slot {idx+1} — click to edit; right-click to remove")
            btn.clicked.connect(lambda _checked=False, i=idx: self.on_hl_edit_clicked(i))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _pt, i=idx: self.on_hl_remove_clicked(i))
            self._chips_layout.addWidget(btn)

        self._chips_layout.addStretch(1)

    def _slots_to_rules(self) -> List[HighlightRule]:
        rules: List[HighlightRule] = []
        for slot in self._hl_slots:
            if not slot.pattern.strip():
                continue
            if slot.color.strip().lower() == "none":
                continue
            r = HighlightRule.create(slot.pattern, slot.mode, slot.color)
            if r is not None:
                rules.append(r)
        return rules

    def _rebuild_highlight_rules(self) -> None:
        self._hl_rules = self._slots_to_rules()

    def _apply_highlighter(self) -> None:
        self._highlighter.set_rules(self._hl_rules)
        self.statusBar().showMessage(f"Highlight rules active: {len(self._hl_rules)}", 2000)

    def _load_highlight_slots(self) -> None:
        s = self._settings
        raw_slots = s.value("hl/slots_json", "", type=str)
        if not raw_slots:
            raw_old = s.value("hl/rules_json", "", type=str)
            if raw_old:
                try:
                    items = json.loads(raw_old)
                    if isinstance(items, list) and items:
                        it0 = items[0] if isinstance(items[0], dict) else None
                        if it0:
                            self._hl_slots[0] = HighlightSlot(
                                pattern=str(it0.get("pattern", "")).strip(),
                                mode=str(it0.get("mode", "Substring")).strip() or "Substring",
                                color=str(it0.get("color", "None")).strip() or "None",
                            )
                except Exception:
                    pass
            return

        try:
            items = json.loads(raw_slots)
            if not isinstance(items, list):
                return
            for i in range(HIGHLIGHT_SLOTS):
                if i >= len(items) or not isinstance(items[i], dict):
                    continue
                self._hl_slots[i] = HighlightSlot(
                    pattern=str(items[i].get("pattern", "")).strip(),
                    mode=str(items[i].get("mode", "Substring")).strip() or "Substring",
                    color=str(items[i].get("color", "None")).strip() or "None",
                )
        except Exception:
            pass

    def _save_highlight_slots(self) -> None:
        items = [{"pattern": s.pattern, "mode": s.mode, "color": s.color} for s in self._hl_slots]
        self._settings.setValue("hl/slots_json", json.dumps(items))

    def on_hl_add_clicked(self) -> None:
        free = self._find_first_free_slot()
        if free is None:
            QMessageBox.information(self, "Highlight", "All 5 highlight slots are used.\nEdit an existing chip or RESET.")
            return

        dlg = HighlightEditDialog(self, slot_index=-1, slot=HighlightSlot(), suggested_index=free)
        if dlg.exec_() != QDialog.Accepted:
            return

        idx, slot = dlg.result_data()
        self._hl_slots[idx] = slot
        self._save_highlight_slots()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._refresh_highlight_chips()

    def on_hl_edit_clicked(self, idx: int) -> None:
        if not (0 <= idx < HIGHLIGHT_SLOTS):
            return
        dlg = HighlightEditDialog(self, slot_index=idx, slot=self._hl_slots[idx], suggested_index=idx)
        if dlg.exec_() != QDialog.Accepted:
            return

        new_idx, slot = dlg.result_data()
        if new_idx == idx:
            self._hl_slots[idx] = slot
        else:
            self._hl_slots[new_idx] = slot
            self._hl_slots[idx] = HighlightSlot()

        self._save_highlight_slots()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._refresh_highlight_chips()

    def on_hl_remove_clicked(self, idx: int) -> None:
        if not (0 <= idx < HIGHLIGHT_SLOTS):
            return
        self._hl_slots[idx] = HighlightSlot()
        self._save_highlight_slots()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._refresh_highlight_chips()

    def on_hl_reset_clicked(self) -> None:
        self._hl_slots = [HighlightSlot() for _ in range(HIGHLIGHT_SLOTS)]
        self._save_highlight_slots()
        self._rebuild_highlight_rules()
        self._apply_highlighter()
        self._refresh_highlight_chips()

        self.log.appendPlainText("[UI/INFO] Highlight RESET: cleared all slots")
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

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

    def _on_line_received(self, line: str) -> None:
        if not match_include(line, self._include_patterns):
            return
        if match_exclude(line, self._exclude_patterns):
            return
        self._queue.append(line)

    def _on_listener_status(self, msg: str) -> None:
        self.statusBar().showMessage(msg)

    def _on_listener_error(self, msg: str) -> None:
        self.log.appendPlainText(f"[UI/ERROR] {msg}")
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        self.statusBar().showMessage(msg, 5000)

    def _on_rx_stats(self, packets: int, lines: int) -> None:
        self._rx_packets = packets
        self._rx_lines = lines
        if self._listener is not None:
            self.statusBar().showMessage(
                f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — pkts={packets} lines={lines} — HL={len(self._hl_rules)}"
            )

    def _flush_log_queue(self) -> None:
        if not self._queue:
            return
        batch = drain_queue(self._queue, max_items=300)
        if not batch:
            return
        for line in batch:
            self.log.appendPlainText(line)
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    # ---------------- UI actions ----------------

    def on_save_clicked(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            "udp_log.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return

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
        self.statusBar().showMessage("Cleared", 2000)

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
            self.log.appendPlainText(f"[UI/INFO] Listening on {self._ui_state.bind_ip}:{self._ui_state.port}")
        else:
            self._stop_listener()
            self.log.appendPlainText("[UI/INFO] Listener stopped")

        self._update_connection_ui()

    def on_autoscroll_changed(self) -> None:
        self._ui_state.autoscroll = self.chk_autoscroll.isChecked()
        self.statusBar().showMessage(f"Auto-Scroll: {'ON' if self._ui_state.autoscroll else 'OFF'}", 2000)

    def on_settings_edited(self) -> None:
        self._ui_state.bind_ip = self.ed_bind_ip.text().strip() or "0.0.0.0"
        try:
            self._ui_state.port = int(self.ed_port.text().strip())
        except Exception:
            pass

    def _update_connection_ui(self) -> None:
        connected = self._listener is not None

        if connected:
            self.btn_connect.setText("CONNECTED")
            self.btn_connect.setStyleSheet("QToolButton { background-color: #2ecc71; font-weight: bold; }")
            self.statusBar().showMessage(
                f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — pkts={self._rx_packets} lines={self._rx_lines} — HL={len(self._hl_rules)}"
            )
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")
            self.statusBar().showMessage(
                f"Listener: OFF — {self._ui_state.bind_ip}:{self._ui_state.port} — HL={len(self._hl_rules)}"
            )

    # ---------------- Qt overrides ----------------

    def closeEvent(self, event) -> None:
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
