from __future__ import annotations

import sys
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

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
)

from .udp_log_utils import drain_queue, compile_patterns, match_include, match_exclude
from .udp_listener import UdpListenerThread
from .udp_log_utils import drain_queue

APP_ORG = "LocalTools"
APP_NAME = "UdpLogViewer"
APP_VERSION = "0.2-step2"


@dataclass
class UiState:
    bind_ip: str = "0.0.0.0"
    port: int = 10514
    autoscroll: bool = True

    include_text: str = ""
    include_mode: str = "Substring"  # Step 3
    exclude_text: str = ""
    exclude_mode: str = "Substring"  # Step 3

    hl_text: str = ""                # Step 4
    hl_mode: str = "Substring"
    hl_color: str = "None"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._settings = QSettings(APP_ORG, APP_NAME)
        self._ui_state = UiState()

        # Step 2: real listener thread + queue + batching
        self._listener: Optional[UdpListenerThread] = None
        self._rx_packets = 0
        self._rx_lines = 0

        self._queue: Deque[str] = deque()
        self._include_patterns = []
        self._exclude_patterns = []


        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(50)  # ms
        self._flush_timer.timeout.connect(self._flush_log_queue)
        self._flush_timer.start()

        self.setWindowTitle(f"UDP Log Viewer — {APP_VERSION}")
        self.resize(1100, 750)

        self._build_actions()
        self._build_ui()

        self._load_settings()
        self._apply_state_to_widgets()
        self._update_connection_ui()

    # ---------------- UI construction ----------------

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

        # --- Top toolbar row ---
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

        # --- Settings row (Bind-IP / Port) ---
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

        # --- Filter panel (Step 3 logic) ---
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)

        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(6)

        lbl_inc = QLabel("Include:")
        self.ed_include = QLineEdit()
        self.ed_include.setPlaceholderText(
            'e.g. "[OVEN/INFO] [T11]"  or  "[HOST/INFO];mask=0x1000"'
        )
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

        # --- Highlight panel (Step 4 logic) ---
        hl_frame = QFrame()
        hl_frame.setFrameShape(QFrame.StyledPanel)

        hl_layout = QGridLayout(hl_frame)
        hl_layout.setContentsMargins(10, 10, 10, 10)
        hl_layout.setHorizontalSpacing(10)
        hl_layout.setVerticalSpacing(6)

        lbl_hl = QLabel("Highlight:")
        self.ed_hl = QLineEdit()
        self.ed_hl.setPlaceholderText('e.g. "received;0x0000" (semicolon = AND)')
        self.ed_hl.textChanged.connect(self.on_highlight_ui_changed)

        self.cb_hl_mode = QComboBox()
        self.cb_hl_mode.addItems(["Substring", "Regex"])
        self.cb_hl_mode.currentTextChanged.connect(self.on_highlight_ui_changed)

        self.cb_hl_color = QComboBox()
        self.cb_hl_color.addItems(["None", "Red", "Green", "Blue", "Orange", "Purple", "Gray"])
        self.cb_hl_color.currentTextChanged.connect(self.on_highlight_ui_changed)

        self.btn_hl_set = QPushButton("SET")
        self.btn_hl_set.clicked.connect(self.on_highlight_set_clicked)

        self.btn_hl_unset = QPushButton("UNSET")
        self.btn_hl_unset.clicked.connect(self.on_highlight_unset_clicked)

        self.btn_hl_reset = QPushButton("RESET")
        self.btn_hl_reset.clicked.connect(self.on_highlight_reset_clicked)

        hl_layout.addWidget(lbl_hl, 0, 0)
        hl_layout.addWidget(self.ed_hl, 0, 1)
        hl_layout.addWidget(self.cb_hl_mode, 0, 2)
        hl_layout.addWidget(self.cb_hl_color, 0, 3)
        hl_layout.addWidget(self.btn_hl_set, 0, 4)
        hl_layout.addWidget(self.btn_hl_unset, 0, 5)
        hl_layout.addWidget(self.btn_hl_reset, 0, 6)
        hl_layout.setColumnStretch(1, 1)

        root_layout.addWidget(hl_frame)

        # --- Content log ---
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)

        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(11)
        self.log.setFont(mono)

        root_layout.addWidget(self.log, 1)

        # Status bar
        self.statusBar().showMessage("Ready")

        self.log.appendPlainText("[MAIN/INFO] Step 2 ready. Press CONNECT to start UDP listener.")

    # ---------------- Settings persistence ----------------

    def _load_settings(self) -> None:
        s = self._settings
        self._ui_state.bind_ip = s.value("net/bind_ip", self._ui_state.bind_ip, type=str)
        self._ui_state.port = s.value("net/port", self._ui_state.port, type=int)
        self._ui_state.autoscroll = s.value("ui/autoscroll", self._ui_state.autoscroll, type=bool)

        self._ui_state.include_text = s.value("filter/include_text", "", type=str)
        self._ui_state.include_mode = s.value("filter/include_mode", "Substring", type=str)
        self._ui_state.exclude_text = s.value("filter/exclude_text", "", type=str)
        self._ui_state.exclude_mode = s.value("filter/exclude_mode", "Substring", type=str)

        self._ui_state.hl_text = s.value("hl/text", "", type=str)
        self._ui_state.hl_mode = s.value("hl/mode", "Substring", type=str)
        self._ui_state.hl_color = s.value("hl/color", "None", type=str)

    def _save_settings(self) -> None:
        s = self._settings
        s.setValue("net/bind_ip", self._ui_state.bind_ip)
        s.setValue("net/port", int(self._ui_state.port))
        s.setValue("ui/autoscroll", bool(self._ui_state.autoscroll))

        s.setValue("filter/include_text", self._ui_state.include_text)
        s.setValue("filter/include_mode", self._ui_state.include_mode)
        s.setValue("filter/exclude_text", self._ui_state.exclude_text)
        s.setValue("filter/exclude_mode", self._ui_state.exclude_mode)

        s.setValue("hl/text", self._ui_state.hl_text)
        s.setValue("hl/mode", self._ui_state.hl_mode)
        s.setValue("hl/color", self._ui_state.hl_color)

    def _apply_state_to_widgets(self) -> None:
        self.ed_bind_ip.setText(self._ui_state.bind_ip)
        self.ed_port.setText(str(self._ui_state.port))
        self.chk_autoscroll.setChecked(self._ui_state.autoscroll)

        self.ed_include.setText(self._ui_state.include_text)
        self.cb_include_mode.setCurrentText(self._ui_state.include_mode)
        self.ed_exclude.setText(self._ui_state.exclude_text)
        self.cb_exclude_mode.setCurrentText(self._ui_state.exclude_mode)

        self.ed_hl.setText(self._ui_state.hl_text)
        self.cb_hl_mode.setCurrentText(self._ui_state.hl_mode)
        self.cb_hl_color.setCurrentText(self._ui_state.hl_color)

    # ---------------- Step 2: Listener handling ----------------

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

        t.line_received.disconnect()
        t.status_changed.disconnect()
        t.error.disconnect()
        t.rx_stats.disconnect()

        t.stop()
        t.wait(800)

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
                f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — pkts={packets} lines={lines}"
            )

    def _flush_log_queue(self) -> None:
        if not self._queue:
            return

        batch = drain_queue(self._queue, max_items=300)
        if not batch:
            return

        # Append in one go (still line-by-line but within UI loop tick)
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

    def on_filter_ui_changed(self) -> None:
        self._ui_state.include_text = self.ed_include.text()
        self._ui_state.include_mode = self.cb_include_mode.currentText()
        self._ui_state.exclude_text = self.ed_exclude.text()
        self._ui_state.exclude_mode = self.cb_exclude_mode.currentText()

        self._include_patterns = compile_patterns(
            self._ui_state.include_text,
            self._ui_state.include_mode
        )

        self._exclude_patterns = compile_patterns(
            self._ui_state.exclude_text,
            self._ui_state.exclude_mode
        )

    def on_highlight_ui_changed(self) -> None:
        self._ui_state.hl_text = self.ed_hl.text()
        self._ui_state.hl_mode = self.cb_hl_mode.currentText()
        self._ui_state.hl_color = self.cb_hl_color.currentText()
        # Step 4: highlighter will use these settings

    def on_highlight_set_clicked(self) -> None:
        self.log.appendPlainText("[UI/INFO] Highlight SET (not implemented yet; Step 4)")
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def on_highlight_unset_clicked(self) -> None:
        self.log.appendPlainText("[UI/INFO] Highlight UNSET (not implemented yet; Step 4)")
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def on_highlight_reset_clicked(self) -> None:
        self.log.appendPlainText("[UI/INFO] Highlight RESET (not implemented yet; Step 4)")
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _update_connection_ui(self) -> None:
        connected = self._listener is not None

        if connected:
            self.btn_connect.setText("CONNECTED")
            self.btn_connect.setStyleSheet("QToolButton { background-color: #2ecc71; font-weight: bold; }")
            self.statusBar().showMessage(
                f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — pkts={self._rx_packets} lines={self._rx_lines}"
            )
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")
            self.statusBar().showMessage(f"Listener: OFF — {self._ui_state.bind_ip}:{self._ui_state.port}")

    # ---------------- Qt overrides ----------------

    def closeEvent(self, event) -> None:
        # Stop listener cleanly on exit
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