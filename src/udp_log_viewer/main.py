from __future__ import annotations

import datetime as _dt
import os
import socket
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional, Tuple

from PyQt5.QtCore import QEvent, Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QIntValidator, QKeySequence, QTextCursor
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
    QShortcut,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .app_paths import AppPathsConfig, get_default_config_path, get_default_project_root_dir, load_or_create_config
from . import __display_version__
from .config_runtime import normalize_config_selection, resolve_config_path
from .connection_runtime import (
    LiveLogState,
    append_live_log_line,
    build_connection_status,
    close_live_log,
    ensure_active_live_log,
    ensure_logs_dir,
    format_bytes,
    live_status_snippet,
    reset_live_log_session,
)
from .file_runtime import copy_log_file, fsync_file_handle, write_text_log
from .highlighter import HighlightRule, LogHighlighter
from .listener_runtime import (
    parse_listener_request,
    reset_pause_state,
    stop_listener_thread,
)
from .replay_simulation import (
    TemperaturePlotSimulationState,
    TextSimulationState,
    build_temperature_replay_sample,
    build_text_replay_sample,
    create_temperature_plot_simulation_state,
    drain_replay_batch,
    next_client_logic_simulation_line,
    next_temperature_plot_simulation_lines,
    next_text_simulation_line,
)
from .rule_slots import (
    PatternSlot,
    build_highlight_rules,
    compile_slot_patterns,
    find_first_free_slot,
    match_exclude_slots,
    match_include_slots,
    strip_slot_colors,
    slots_from_json,
    slots_to_json,
)
from .settings_store import SettingsStore
from .ui_state import UiState
from .preferences import AppPreferences
from .preferences_dialog import PreferencesDialog
from .project_dialog import ProjectDialog
from .project_runtime import (
    RuntimeProject,
    build_project_filename,
    build_project_title_suffix,
    initialize_project,
    is_valid_project_name,
)
from .udp_listener import UdpListenerThread
from .udp_log_utils import drain_queue
from .data_visualizer.visualizer_manager import VisualizerManager

APP_ORG = "LocalTools"
APP_NAME = "UdpLogViewer"
APP_VERSION = __display_version__

SLOT_COUNT = 5

DEFAULT_MAX_LINES = 20000
DEFAULT_TRIM_CHUNK = 2000

REPLAY_TICK_MS = 25
REPLAY_LINES_PER_TICK = 40
MAIN_SAVE_SHORTCUT_TIPS = "Save shortcuts: Ctrl+S, Cmd+S, or F12."

class PatternEditDialog(QDialog):
    """
    Unified editor dialog used for Filter / Exclude / Highlight slots.

    - Slot: 1..5
    - Pattern: text
    - Mode: Substring / Regex
    - Color: Highlight only
    """

    def __init__(
        self,
        parent: QWidget,
        title: str,
        slot_index: int,
        slot: PatternSlot,
        suggested_index: int,
        *,
        show_color: bool,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._show_color = show_color

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
        self.sb_slot.setToolTip("Select which slot should store this rule.")
        grid.addWidget(self.sb_slot, 0, 1)

        grid.addWidget(QLabel("Pattern:"), 1, 0)
        self.ed_pattern = QLineEdit()
        self.ed_pattern.setText(slot.pattern)
        self.ed_pattern.setPlaceholderText('e.g. "[OVEN/INFO] [T11]" or "STATUS received"')
        self.ed_pattern.setToolTip("Enter the text or regular expression used to match log lines.")
        grid.addWidget(self.ed_pattern, 1, 1)

        grid.addWidget(QLabel("Mode:"), 2, 0)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Substring", "Regex"])
        self.cb_mode.setCurrentText(slot.mode or "Substring")
        self.cb_mode.setToolTip("Choose whether the pattern is matched as plain text or as a regular expression.")
        grid.addWidget(self.cb_mode, 2, 1)

        self.cb_color: QComboBox | None = None
        if self._show_color:
            grid.addWidget(QLabel("Color:"), 3, 0)
            self.cb_color = QComboBox()
            self.cb_color.addItems(["None", "Red", "Green", "Blue", "Orange", "Purple", "Gray"])
            self.cb_color.setCurrentText(slot.color or "None")
            self.cb_color.setToolTip("Choose the highlight color used for matching log lines.")
            grid.addWidget(self.cb_color, 3, 1)

        layout.addLayout(grid)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        btns.button(QDialogButtonBox.Ok).setText("SET")
        btns.button(QDialogButtonBox.Ok).setToolTip("Apply this rule to the selected slot.")
        btns.button(QDialogButtonBox.Cancel).setToolTip("Close the dialog without changing the selected slot.")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def result_data(self) -> Tuple[int, PatternSlot]:
        idx = int(self.sb_slot.value()) - 1
        slot = PatternSlot(
            pattern=self.ed_pattern.text().strip(),
            mode=self.cb_mode.currentText().strip() or "Substring",
            color=(self.cb_color.currentText().strip() if self.cb_color is not None else "None") or "None",
        )
        return idx, slot


def _get_local_ipv4() -> str:
    # Best-effort non-blocking local IP detection (no external traffic required).
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and ip != "0.0.0.0":
            return ip
    except Exception:
        pass
    return "0.0.0.0"


class MainWindow(QMainWindow):
    # INI keys (config.ini)
    _INI_SECTION_RULES = "rules"
    _INI_KEY_FILTER = "filter_slots_json"
    _INI_KEY_EXCLUDE = "exclude_slots_json"
    _INI_KEY_HL = "hl_slots_json"
    _QSETTINGS_CONFIG_PATH_KEY = "config/selected_path"

    def __init__(self) -> None:
        super().__init__()

        # QSettings (small UI toggles are ok here)
        self._settings = QSettings(APP_ORG, APP_NAME)
        config_path = self._resolve_config_path()

        # config.ini paths (AppSupport/custom) + logs dir
        self._paths_cfg: AppPathsConfig = load_or_create_config(
            APP_ORG,
            APP_NAME,
            APP_VERSION,
            config_path=config_path,
        )
        self._default_logs_dir = Path(self._paths_cfg.logs_dir)
        self._settings_store = SettingsStore(self._settings, self._paths_cfg.config_path)
        self._preferences = self._settings_store.load_preferences()
        self._ui_state = UiState(
            autoscroll=self._preferences.autoscroll_default,
            timestamp_enabled=self._preferences.timestamp_default,
            max_lines=self._preferences.max_lines_default,
        )

        # UDP listener
        self._listener: Optional[UdpListenerThread] = None
        self._connection_state = LiveLogState()

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
        self._text_simulation = TextSimulationState()

        self._sim_temperature_enabled = False
        self._sim_temperature_timer = QTimer(self)
        self._sim_temperature_timer.setInterval(250)  # ms
        self._sim_temperature_timer.timeout.connect(self._on_sim_temperature_tick)
        self._sim_temperature_state: TemperaturePlotSimulationState = create_temperature_plot_simulation_state()

        self._sim_logic_enabled = False
        self._sim_logic_timer = QTimer(self)
        self._sim_logic_timer.setInterval(1000)
        self._sim_logic_timer.timeout.connect(self._on_sim_logic_tick)

        self._sim_logic_state = [0] * 8


        # Replay (inject without UDP)
        self._replay_timer = QTimer(self)
        self._replay_timer.setInterval(REPLAY_TICK_MS)
        self._replay_timer.timeout.connect(self._replay_tick)
        self._replay_lines: Deque[str] = deque()
        self._replay_active = False
        self._replay_requires_connection = False

        # Replay CSV Temperature lines (inject without UDP)
        self._replay_timer_temperature = QTimer(self)
        self._replay_timer_temperature.setInterval(REPLAY_TICK_MS)
        self._replay_timer_temperature.timeout.connect(self._replay_tick_temperature)
        self._replay_lines_temperature: Deque[str] = deque()
        self._replay_active_temperature = False
        self._replay_temperature_requires_connection = False

        # Slot-based Filter / Exclude / Highlight
        self._filter_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._exclude_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]
        self._hl_slots: List[PatternSlot] = [PatternSlot() for _ in range(SLOT_COUNT)]

        # Compiled patterns per slot
        self._filter_slot_patterns: List[List[object]] = []
        self._exclude_slot_patterns: List[List[object]] = []

        # Highlight rules
        self._hl_rules: List[HighlightRule] = []

        self._local_ip = _get_local_ipv4()
        self._active_project: RuntimeProject | None = None
        self._update_window_title()

        self.resize(1100, 760)

        self._build_actions()
        self._build_ui()
        self._configure_main_shortcuts()
        self._configure_main_focus_navigation()

        self._load_settings()
        self._apply_state_to_widgets()

        # Load rules from config.ini first, then fall back to QSettings (legacy)
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

        # Data Visualizer (T3.4.3 controls + screenshots)
        self._visualizer_manager = VisualizerManager(
            config_path=self._paths_cfg.config_path,
            screenshot_dir=Path(self._paths_cfg.logs_dir) / "screenshots",
            preferences=self._preferences,
            diagnostic_callback=self._on_visualizer_diagnostic,
        )
        self._visualizer_manager.load_configs()
        self._sync_runtime_context()

    # ---------------- Helpers ----------------

    def _resolve_config_path(self) -> Path:
        return resolve_config_path(
            self._settings,
            settings_key=self._QSETTINGS_CONFIG_PATH_KEY,
            default_path=get_default_config_path(APP_ORG, APP_NAME),
            prompt_callback=self._prompt_for_config_path,
        )

    def _prompt_for_config_path(self, suggested_path: Path) -> Path:
        QMessageBox.information(
            self,
            "Config.ini Missing",
            "No config.ini was found.\n\nPlease choose a location for an existing config.ini or select a new location so the application can create one.",
        )

        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Config.ini Location",
            str(suggested_path),
            "INI Files (*.ini);;All Files (*)",
        )

        return normalize_config_selection(selected_path, suggested_path)

    @staticmethod
    def _now_stamp() -> str:
        return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    def _default_save_name(self) -> str:
        return self._build_log_filename("udp_log", self._now_stamp())

    def _build_log_filename(self, stem: str, stamp: str) -> str:
        return build_project_filename(self._project_name(), stem, stamp, ".txt")

    def _project_name(self) -> str | None:
        return self._active_project.name if self._active_project is not None else None

    def _project_output_dir(self) -> Path | None:
        if self._active_project is None:
            return None
        return self._active_project.output_dir

    def _preferred_log_dir(self) -> Path:
        if self._active_project is not None:
            return self._active_project.output_dir
        configured = (self._preferences.log_path or "").strip()
        if configured:
            return Path(configured).expanduser()
        return self._default_logs_dir

    def _preferred_project_root_dir(self) -> Path:
        configured = (self._preferences.project_root or "").strip()
        if configured:
            return Path(configured).expanduser()
        return Path(self._paths_cfg.project_root)

    def _default_save_path(self) -> Path:
        return self._preferred_log_dir() / self._default_save_name()

    def _update_window_title(self) -> None:
        self.setWindowTitle(
            f"UDP Log Viewer — {APP_VERSION} — {self._local_ip}{build_project_title_suffix(self._project_name())}"
        )

    def _sync_runtime_context(self) -> None:
        self._visualizer_manager.set_runtime_context(
            project_name=self._project_name(),
            output_dir=self._project_output_dir(),
        )
        self._update_window_title()

    def _reset_active_project(self) -> None:
        self._active_project = None
        self._preferences.project_root = ""
        default_root = get_default_project_root_dir()
        self._settings_store.save_preferences(self._preferences)
        self._settings_store.ini_set("paths", "project_root", str(default_root))
        self._paths_cfg.project_root = default_root
        self._sync_runtime_context()

    def _ensure_logs_dir(self) -> Path:
        return ensure_logs_dir(self._preferred_log_dir())

    def _open_new_live_log(self) -> None:
        try:
            stamp = self._now_stamp()
            path = reset_live_log_session(
                self._connection_state,
                self._ensure_logs_dir(),
                stamp,
                filename=self._build_log_filename("udp_live", stamp),
            )
            self.statusBar().showMessage(f"Live log: {path}", 4000)
        except Exception as e:
            self._connection_state.handle = None
            self._connection_state.active_path = None
            QMessageBox.critical(self, "Logfile Error", f"Could not create live logfile:\n{e}")
            self.log.appendPlainText(f"[UI/ERROR] Could not create live logfile: {e}")

    def _ensure_active_live_log(self) -> None:
        try:
            stamp = self._now_stamp()
            path = ensure_active_live_log(
                self._connection_state,
                self._ensure_logs_dir(),
                stamp,
                filename=self._build_log_filename("udp_live", stamp),
            )
            self.statusBar().showMessage(f"Live log: {path}", 4000)
        except Exception as e:
            self._connection_state.handle = None
            self._connection_state.active_path = None
            QMessageBox.critical(self, "Logfile Error", f"Could not prepare live logfile:\n{e}")
            self.log.appendPlainText(f"[UI/ERROR] Could not prepare live logfile: {e}")

    def _close_live_log(self) -> None:
        close_live_log(self._connection_state)

    def _is_connected(self) -> bool:
        return self._listener is not None

    def _set_action_checked_without_signal(self, action: QAction | None, checked: bool) -> None:
        if action is None:
            return
        action.blockSignals(True)
        action.setChecked(checked)
        action.blockSignals(False)

    def _require_connected_for_generated_data(self, action: QAction | None = None) -> bool:
        if self._is_connected():
            return True
        self._set_action_checked_without_signal(action, False)
        self.statusBar().showMessage("Simulation requires CONNECTED (start listener first).", 2500)
        return False

    def _set_generated_data_actions_enabled(self, enabled: bool) -> None:
        for action_name in ("act_simulate", "act_simulate_temperature", "act_simulate_logic"):
            action = getattr(self, action_name, None)
            if action is not None:
                action.setEnabled(enabled)

    def _append_to_live_log(self, line: str) -> None:
        if self._connection_state.handle is None:
            return
        try:
            append_live_log_line(self._connection_state, line)
        except Exception as e:
            self.log.appendPlainText(f"[UI/ERROR] Live logfile write failed: {e}")
            self._close_live_log()

    # ---------------- INI helpers (config.ini) ----------------

    def _ini_read(self) -> dict:
        return self._settings_store.ini_read()

    def _ini_get(self, section: str, key: str, default: str = "") -> str:
        return self._settings_store.ini_get(section, key, default)

    def _ini_set(self, section: str, key: str, value: str) -> None:
        try:
            self._settings_store.ini_set(section, key, value)
        except Exception as e:
            self.log.appendPlainText(f"[UI/WARN] config.ini write failed: {e}")

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

        self.act_preferences = QAction("Preferences...", self)
        self.act_preferences.setShortcut("Ctrl+,")
        self.act_preferences.triggered.connect(self.on_preferences_clicked)

        self.act_save = QAction("Save…", self)
        self.act_save.setShortcuts([QKeySequence.Save, QKeySequence("F12")])
        self.act_save.triggered.connect(self.on_save_clicked)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_quit.triggered.connect(self.close)

        file_menu.addAction(self.act_open_log)
        file_menu.addAction(self.act_replay_sample)
        file_menu.addAction(self.act_stop_replay)
        file_menu.addSeparator()
        file_menu.addAction(self.act_preferences)
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

        self.act_simulate_temperature = QAction("Simulate Plot Traffic", self)
        self.act_simulate_temperature.setCheckable(True)
        self.act_simulate_temperature.setToolTip("Generate sample numeric plot log lines locally (for visual graph testing)")
        self.act_simulate_temperature.toggled.connect(self.on_simulate_toggled_temperature)
        tools_menu.addAction(self.act_simulate_temperature)

        self.act_simulate_logic = QAction("Simulate Logic Traffic", self)
        self.act_simulate_logic.setCheckable(True)
        self.act_simulate_logic.toggled.connect(self.on_simulate_logic_toggled)
        tools_menu.addAction(self.act_simulate_logic)


        visualize_menu = self.menuBar().addMenu("Visualize")

        # Plot Visualizer
        self.menu_visualize_temperature = visualize_menu.addMenu("Plot")

        self.act_visualizer_csv_temp_config = QAction("Config", self)
        self.act_visualizer_csv_temp_config.triggered.connect(self.on_visualizer_csv_temp_config_clicked)
        self.menu_visualize_temperature.addAction(self.act_visualizer_csv_temp_config)

        self.act_visualizer_csv_temp_show = QAction("Show", self)
        self.act_visualizer_csv_temp_show.triggered.connect(self.on_visualizer_csv_temp_show_clicked)
        self.menu_visualize_temperature.addAction(self.act_visualizer_csv_temp_show)

        # LogicVisualizer
        self.logic_menu = visualize_menu.addMenu("Logic")

        self.act_logic_config = QAction("Config", self)
        self.act_logic_config.triggered.connect(self.on_visualizer_logic_config_clicked)

        self.act_logic_show = QAction("Show", self)
        self.act_logic_show.triggered.connect(self.on_visualizer_logic_show_clicked)

        self.logic_menu.addAction(self.act_logic_config)
        self.logic_menu.addAction(self.act_logic_show)




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

    def _configure_main_shortcuts(self) -> None:
        self._save_shortcuts = []
        for sequence in ("Ctrl+S", "Meta+S", "F12"):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(self.on_save_clicked)
            self._save_shortcuts.append(shortcut)

    def _configure_main_focus_navigation(self) -> None:
        self._main_tab_widgets = [
            self.btn_project,
            self.btn_save,
            self.btn_reset,
            self.btn_clear,
            self.btn_copy,
            self.btn_connect,
            self.btn_pause,
            self.chk_autoscroll,
            self.chk_timestamp,
            self.ed_bind_ip,
            self.ed_port,
            self.ed_max_lines,
            self.btn_filter_add,
            self.btn_filter_reset,
            self.btn_exclude_add,
            self.btn_exclude_reset,
            self.btn_hl_add,
            self.btn_hl_reset,
            self.log,
        ]
        for first, second in zip(self._main_tab_widgets, self._main_tab_widgets[1:]):
            self.setTabOrder(first, second)
        for widget in self._main_tab_widgets:
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if (
            hasattr(self, "_main_tab_widgets")
            and QEvent is not None
            and event.type() == QEvent.KeyPress
            and event.key() in (Qt.Key_Tab, Qt.Key_Backtab)
            and watched in self._main_tab_widgets
        ):
            self._move_main_focus(forward=event.key() == Qt.Key_Tab)
            return True
        return super().eventFilter(watched, event)

    def _move_main_focus(self, *, forward: bool) -> None:
        widgets = [widget for widget in getattr(self, "_main_tab_widgets", []) if widget.isVisible() and widget.isEnabled()]
        if not widgets:
            return
        current = self.focusWidget()
        try:
            index = widgets.index(current)
        except ValueError:
            index = -1 if forward else 0
        next_index = (index + 1) % len(widgets) if forward else (index - 1) % len(widgets)
        widgets[next_index].setFocus(Qt.TabFocusReason)

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # --- Top row ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.btn_project = QPushButton("PROJECT")
        self.btn_project.setFocusPolicy(Qt.StrongFocus)
        self.btn_project.setToolTip("Open the project dialog to create or edit the active project.")
        self.btn_project.clicked.connect(self.on_project_clicked)

        self.btn_save = QPushButton("SAVE")
        self.btn_save.setFocusPolicy(Qt.StrongFocus)
        self.btn_save.setToolTip(MAIN_SAVE_SHORTCUT_TIPS)
        self.btn_save.clicked.connect(self.on_save_clicked)

        self.btn_reset = QPushButton("RESET")
        self.btn_reset.setFocusPolicy(Qt.StrongFocus)
        self.btn_reset.setToolTip("Start a new session: stop the listener, clear buffers, and reset the active project.")
        self.btn_reset.clicked.connect(self.on_reset_clicked)

        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.setFocusPolicy(Qt.StrongFocus)
        self.btn_clear.setToolTip("Clear the visible log output without touching the live session file.")
        self.btn_clear.clicked.connect(self.on_clear_clicked)

        self.btn_copy = QPushButton("COPY")
        self.btn_copy.setFocusPolicy(Qt.StrongFocus)
        self.btn_copy.setToolTip("Copy the selected log text, or the full log if nothing is selected.")
        self.btn_copy.clicked.connect(self.on_copy_clicked)

        self.btn_connect = QToolButton()
        self.btn_connect.setText("CONNECT")
        self.btn_connect.setFocusPolicy(Qt.StrongFocus)
        self.btn_connect.setCheckable(True)
        self.btn_connect.setToolTip("Start or stop the UDP listener for the configured bind IP and port.")
        self.btn_connect.clicked.connect(self.on_connect_toggled)

        self.btn_pause = QToolButton()
        self.btn_pause.setText("PAUSE")
        self.btn_pause.setFocusPolicy(Qt.StrongFocus)
        self.btn_pause.setCheckable(True)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setToolTip("Pause or resume updates in the log view while logging continues in the background.")
        self.btn_pause.clicked.connect(self.on_pause_toggled)

        self.chk_autoscroll = QCheckBox("Auto-Scroll")
        self.chk_autoscroll.setFocusPolicy(Qt.StrongFocus)
        self.chk_autoscroll.setToolTip("Automatically keep the newest received log lines visible.")
        self.chk_autoscroll.stateChanged.connect(self.on_autoscroll_changed)

        self.chk_timestamp = QCheckBox("Timestamp")
        self.chk_timestamp.setFocusPolicy(Qt.StrongFocus)
        self.chk_timestamp.setToolTip("Prefix displayed log lines with a local timestamp. Applies on the next connect.")
        self.chk_timestamp.stateChanged.connect(self.on_timestamp_changed)

        top_row.addWidget(self.btn_project)
        top_row.addSpacing(18)
        top_row.addWidget(self.btn_save)
        top_row.addWidget(self.btn_reset)
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
        self.ed_bind_ip.setFocusPolicy(Qt.StrongFocus)
        self.ed_bind_ip.setPlaceholderText("0.0.0.0")
        self.ed_bind_ip.setToolTip("UDP bind address. Use 0.0.0.0 to listen on all local network interfaces.")
        self.ed_bind_ip.editingFinished.connect(self.on_settings_edited)

        lbl_port = QLabel("Port:")
        self.ed_port = QLineEdit()
        self.ed_port.setFocusPolicy(Qt.StrongFocus)
        self.ed_port.setValidator(QIntValidator(1, 65535, self))
        self.ed_port.setPlaceholderText("10514")
        self.ed_port.setToolTip("UDP port used by the listener.")
        self.ed_port.editingFinished.connect(self.on_settings_edited)

        lbl_max = QLabel("Max lines:")
        self.ed_max_lines = QLineEdit()
        self.ed_max_lines.setFocusPolicy(Qt.StrongFocus)
        self.ed_max_lines.setValidator(QIntValidator(1000, 500000, self))
        self.ed_max_lines.setPlaceholderText(str(DEFAULT_MAX_LINES))
        self.ed_max_lines.setToolTip("Maximum number of log lines kept in the visible UI before older lines are trimmed.")
        self.ed_max_lines.editingFinished.connect(self.on_settings_edited)

        settings_layout.addWidget(lbl_bind, 0, 0)
        settings_layout.addWidget(self.ed_bind_ip, 0, 1)
        settings_layout.addWidget(lbl_port, 0, 2)
        settings_layout.addWidget(self.ed_port, 0, 3)
        settings_layout.addWidget(lbl_max, 0, 4)
        settings_layout.addWidget(self.ed_max_lines, 0, 5)

        settings_layout.setColumnStretch(1, 1)
        root_layout.addWidget(settings_frame)

        # --- Filter/Exclude row ---
        fx_frame = QFrame()
        fx_frame.setFrameShape(QFrame.StyledPanel)
        fx_row = QHBoxLayout(fx_frame)
        fx_row.setContentsMargins(10, 10, 10, 10)
        fx_row.setSpacing(10)

        fx_row.addWidget(QLabel("Filter:"))

        self.btn_filter_add = QToolButton()
        self.btn_filter_add.setText("FILTER")
        self.btn_filter_add.setFocusPolicy(Qt.StrongFocus)
        self.btn_filter_add.setToolTip("Add or edit a filter rule. Only matching log lines stay visible.")
        self.btn_filter_add.clicked.connect(self.on_filter_add_clicked)
        fx_row.addWidget(self.btn_filter_add)

        self._filter_chips_container = QWidget()
        self._filter_chips_layout = QHBoxLayout(self._filter_chips_container)
        self._filter_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._filter_chips_layout.setSpacing(6)
        fx_row.addWidget(self._filter_chips_container, 1)

        self.btn_filter_reset = QPushButton("RESET")
        self.btn_filter_reset.setFocusPolicy(Qt.StrongFocus)
        self.btn_filter_reset.setToolTip("Remove all filter rules.")
        self.btn_filter_reset.clicked.connect(self.on_filter_reset_clicked)
        fx_row.addWidget(self.btn_filter_reset)

        fx_row.addSpacing(18)

        fx_row.addWidget(QLabel("Exclude:"))

        self.btn_exclude_add = QToolButton()
        self.btn_exclude_add.setText("EXCLUDE")
        self.btn_exclude_add.setFocusPolicy(Qt.StrongFocus)
        self.btn_exclude_add.setToolTip("Add or edit an exclude rule. Matching log lines are hidden.")
        self.btn_exclude_add.clicked.connect(self.on_exclude_add_clicked)
        fx_row.addWidget(self.btn_exclude_add)

        self._exclude_chips_container = QWidget()
        self._exclude_chips_layout = QHBoxLayout(self._exclude_chips_container)
        self._exclude_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._exclude_chips_layout.setSpacing(6)
        fx_row.addWidget(self._exclude_chips_container, 1)

        self.btn_exclude_reset = QPushButton("RESET")
        self.btn_exclude_reset.setFocusPolicy(Qt.StrongFocus)
        self.btn_exclude_reset.setToolTip("Remove all exclude rules.")
        self.btn_exclude_reset.clicked.connect(self.on_exclude_reset_clicked)
        fx_row.addWidget(self.btn_exclude_reset)

        root_layout.addWidget(fx_frame)

        # --- Highlight row ---
        hl_frame = QFrame()
        hl_frame.setFrameShape(QFrame.StyledPanel)
        hl_row = QHBoxLayout(hl_frame)
        hl_row.setContentsMargins(10, 10, 10, 10)
        hl_row.setSpacing(8)

        hl_row.addWidget(QLabel("Highlight:"))

        self.btn_hl_add = QToolButton()
        self.btn_hl_add.setText("HIGHLIGHT")
        self.btn_hl_add.setFocusPolicy(Qt.StrongFocus)
        self.btn_hl_add.setToolTip("Add or edit a highlight rule for matching log lines.")
        self.btn_hl_add.clicked.connect(self.on_hl_add_clicked)
        hl_row.addWidget(self.btn_hl_add)

        self._hl_chips_container = QWidget()
        self._hl_chips_layout = QHBoxLayout(self._hl_chips_container)
        self._hl_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._hl_chips_layout.setSpacing(6)
        hl_row.addWidget(self._hl_chips_container, 1)

        self.btn_hl_reset = QPushButton("RESET")
        self.btn_hl_reset.setFocusPolicy(Qt.StrongFocus)
        self.btn_hl_reset.setToolTip("Remove all highlight rules.")
        self.btn_hl_reset.clicked.connect(self.on_hl_reset_clicked)
        hl_row.addWidget(self.btn_hl_reset)

        root_layout.addWidget(hl_frame)

        # --- Content ---
        self.log = QPlainTextEdit()
        self.log.setFocusPolicy(Qt.StrongFocus)
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log.setToolTip("Shows the received log lines for the current session.")

        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(11)
        self.log.setFont(mono)

        self._highlighter = LogHighlighter(self.log.document())
        root_layout.addWidget(self.log, 1)

        self.statusBar().showMessage("Ready")
        self.log.appendPlainText("[MAIN/INFO] Ready.")

    # ---------------- Settings ----------------

    def _load_settings(self) -> None:
        self._ui_state = self._settings_store.load_ui_state(self._ui_state)

    def _save_settings(self) -> None:
        self._settings_store.save_ui_state(self._ui_state)

    def _apply_state_to_widgets(self) -> None:
        widgets = [
            self.ed_bind_ip,
            self.ed_port,
            self.chk_autoscroll,
            self.chk_timestamp,
            self.ed_max_lines,
        ]
        for widget in widgets:
            widget.blockSignals(True)
        try:
            self.ed_bind_ip.setText(self._ui_state.bind_ip)
            self.ed_port.setText(str(self._ui_state.port))
            self.chk_autoscroll.setChecked(self._ui_state.autoscroll)
            self.chk_timestamp.setChecked(self._ui_state.timestamp_enabled)
            self.ed_max_lines.setText(str(self._ui_state.max_lines))
        finally:
            for widget in widgets:
                widget.blockSignals(False)

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

    def on_preferences_clicked(self) -> None:
        dialog = PreferencesDialog(self._preferences, self)
        dialog.restore_button().clicked.connect(lambda: dialog.set_preferences(AppPreferences()))
        dialog.apply_button().clicked.connect(
            lambda: self._apply_preferences(dialog.result_preferences())
        )
        if dialog.exec_() != QDialog.Accepted:
            return
        self._apply_preferences(dialog.result_preferences())

    def _apply_preferences(self, preferences: AppPreferences) -> None:
        self._preferences = preferences
        self._settings_store.save_preferences(self._preferences)
        self._settings_store.ini_set("paths", "logs_dir", str(self._preferred_log_dir()))
        self._settings_store.ini_set("paths", "project_root", str(self._preferred_project_root_dir()))
        self._paths_cfg.logs_dir = self._preferred_log_dir()
        self._paths_cfg.project_root = self._preferred_project_root_dir()
        self._ui_state.autoscroll = self._preferences.autoscroll_default
        self._ui_state.timestamp_enabled = self._preferences.timestamp_default
        self._ui_state.max_lines = self._preferences.max_lines_default
        self._save_settings()
        self._apply_state_to_widgets()
        self._visualizer_manager.set_preferences(self._preferences)
        self.statusBar().showMessage(f"Preferences saved: Log path {self._preferred_log_dir()}", 3000)

    # ---------------- Slot persistence ----------------

    def _load_slot_list_from_json(self, raw: str) -> List[PatternSlot]:
        return slots_from_json(raw, SLOT_COUNT)

    def _save_slot_list_to_json(self, slots: List[PatternSlot]) -> str:
        return slots_to_json(slots)

    def _load_filter_slots(self) -> None:
        self._filter_slots = strip_slot_colors(self._settings_store.load_rule_slots(
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_FILTER,
            qsettings_key="filter/slots_json",
            slot_count=SLOT_COUNT,
        ))

    def _save_filter_slots(self) -> None:
        self._filter_slots = strip_slot_colors(self._filter_slots)
        self._settings_store.save_rule_slots(
            self._filter_slots,
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_FILTER,
            qsettings_key="filter/slots_json",
        )

    def _load_exclude_slots(self) -> None:
        self._exclude_slots = strip_slot_colors(self._settings_store.load_rule_slots(
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_EXCLUDE,
            qsettings_key="exclude/slots_json",
            slot_count=SLOT_COUNT,
        ))

    def _save_exclude_slots(self) -> None:
        self._exclude_slots = strip_slot_colors(self._exclude_slots)
        self._settings_store.save_rule_slots(
            self._exclude_slots,
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_EXCLUDE,
            qsettings_key="exclude/slots_json",
        )

    def _load_highlight_slots(self) -> None:
        self._hl_slots = self._settings_store.load_rule_slots(
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_HL,
            qsettings_key="hl/slots_json",
            slot_count=SLOT_COUNT,
        )

    def _save_highlight_slots(self) -> None:
        self._settings_store.save_rule_slots(
            self._hl_slots,
            ini_section=self._INI_SECTION_RULES,
            ini_key=self._INI_KEY_HL,
            qsettings_key="hl/slots_json",
        )

    # ---------------- Filter matching ----------------

    def _compile_slot_patterns(self, slots: List[PatternSlot]) -> List[List[object]]:
        return compile_slot_patterns(slots)

    def _match_include_slots(self, line: str) -> bool:
        return match_include_slots(line, self._filter_slot_patterns)

    def _match_exclude_slots(self, line: str) -> bool:
        return match_exclude_slots(line, self._exclude_slot_patterns)

    def _rebuild_filter_patterns(self) -> None:
        self._filter_slot_patterns = self._compile_slot_patterns(self._filter_slots)
        self._exclude_slot_patterns = self._compile_slot_patterns(self._exclude_slots)

    # ---------------- Highlight ----------------

    def _rebuild_highlight_rules(self) -> None:
        self._hl_rules = build_highlight_rules(self._hl_slots)

    def _apply_highlighter(self) -> None:
        self._highlighter.set_rules(self._hl_rules)
        self.statusBar().showMessage(f"Highlight rules active: {len(self._hl_rules)}", 2000)

    # ---------------- Chip UI helpers ----------------

    def _find_first_free_slot(self, slots: List[PatternSlot]) -> Optional[int]:
        return find_first_free_slot(slots)

    def _refresh_chips(self, layout: QHBoxLayout, slots: List[PatternSlot], on_edit, on_remove, *, show_color: bool) -> None:
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
            if show_color and s.color.strip().lower() != "none":
                txt = f"{txt} ({s.color})"
            btn = QToolButton()
            btn.setText(txt)
            btn.setStyleSheet(self._chip_style(s.color if show_color else "None"))
            btn.setToolTip(f"Slot {idx+1} — click to edit; right-click to remove")
            btn.clicked.connect(lambda _checked=False, i=idx: on_edit(i))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _pt, i=idx: on_remove(i))
            layout.addWidget(btn)

        layout.addStretch(1)

    def _refresh_filter_chips(self) -> None:
        self._refresh_chips(
            self._filter_chips_layout,
            self._filter_slots,
            self.on_filter_edit_clicked,
            self.on_filter_remove_clicked,
            show_color=False,
        )

    def _refresh_exclude_chips(self) -> None:
        self._refresh_chips(
            self._exclude_chips_layout,
            self._exclude_slots,
            self.on_exclude_edit_clicked,
            self.on_exclude_remove_clicked,
            show_color=False,
        )

    def _refresh_highlight_chips(self) -> None:
        self._refresh_chips(
            self._hl_chips_layout,
            self._hl_slots,
            self.on_hl_edit_clicked,
            self.on_hl_remove_clicked,
            show_color=True,
        )

    # ---------------- Dialog actions ----------------

    def _open_slot_dialog(self, title: str, slots: List[PatternSlot], slot_index: int) -> Optional[Tuple[int, PatternSlot]]:
        show_color = title == "Highlight"
        if slot_index < 0:
            free = self._find_first_free_slot(slots)
            if free is None:
                QMessageBox.information(self, title, f"All {SLOT_COUNT} slots are used.\nEdit an existing chip or RESET.")
                return None
            dlg = PatternEditDialog(
                self,
                f"Edit {title} Rule",
                slot_index=-1,
                slot=PatternSlot(),
                suggested_index=free,
                show_color=show_color,
            )
        else:
            if not (0 <= slot_index < SLOT_COUNT):
                return None
            dlg = PatternEditDialog(
                self,
                f"Edit {title} Rule",
                slot_index=slot_index,
                slot=slots[slot_index],
                suggested_index=slot_index,
                show_color=show_color,
            )

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

    def _dispatch_log_line(self, line: str, *, is_live_source: bool) -> None:
        raw_line = line

        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
            raw_line_ts = f"{timestamp}{raw_line}"
            #self._visualizer_manager.process_log_line(raw_line)
            self._visualizer_manager.process_log_line(raw_line_ts)
        except Exception:
            # T3.1.1: keep visualizer integration non-blocking for the main viewer path.
            pass

        if not self._match_include_slots(raw_line):
            return
        if self._match_exclude_slots(raw_line):
            return

        out_line = raw_line
        if self._ui_state.timestamp_enabled:
            out_line = f"{self._format_timestamp_prefix(datetime.now())} {raw_line}"

        if is_live_source:
            self._append_to_live_log(out_line)

        if self._ui_paused:
            if len(self._pause_buffer) >= self._pause_buffer.maxlen:
                self._pause_dropped += 1
            self._pause_buffer.append(out_line)
            return

        self._queue.append(out_line)

    def _ingest_line(self, line: str) -> None:
        self._dispatch_log_line(line, is_live_source=False)

    def _replay_tick(self) -> None:
        if self._replay_requires_connection and not self._is_connected():
            self.on_stop_replay_clicked()
            return
        if not self._replay_lines:
            self._replay_timer.stop()
            self._replay_active = False
            self.statusBar().showMessage("Replay finished", 2000)
            return

        for line in drain_replay_batch(self._replay_lines, REPLAY_LINES_PER_TICK):
            self._ingest_line(line)

    def _replay_tick_temperature(self) -> None:
        if self._replay_temperature_requires_connection and not self._is_connected():
            self.on_stop_replay_temperature_clicked()
            return
        if not self._replay_lines_temperature:
            self._replay_timer_temperature.stop()
            self._replay_active_temperature = False
            self.statusBar().showMessage("Replay plot finished", 2000)
            return

        for line in drain_replay_batch(self._replay_lines_temperature, REPLAY_LINES_PER_TICK):
            self._ingest_line(line)


    def on_open_log_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Log",
            str(self._preferred_log_dir()),
            "Text Files (*.txt);;All Files (*)",
        )
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
        self._replay_requires_connection = False
        self._replay_timer.start()
        self.statusBar().showMessage(f"Replay: {os.path.basename(path)} ({len(self._replay_lines)} lines)", 3000)

    # -------------------------------------------------------
    # simulation CSV Temperature lines
    # -------------------------------------------------------
    def on_replay_sample_temperature_clicked(self) -> None:
        if not self._require_connected_for_generated_data():
            return
        self.on_stop_replay_temperature_clicked()
        self._replay_lines_temperature = deque(build_temperature_replay_sample())
        self._replay_active_temperature = True
        self._replay_temperature_requires_connection = True
        self._replay_timer_temperature.start()
        self.statusBar().showMessage("Replay: plot sample", 2000)

    def on_stop_replay_temperature_clicked(self) -> None:
        if self._replay_timer_temperature.isActive():
            self._replay_timer_temperature.stop()
        self._replay_lines_temperature.clear()
        self._replay_active_temperature = False
        self._replay_temperature_requires_connection = False
        self.statusBar().showMessage("Replay plot stopped", 1500)

    # -------------------------------------------------------
    # simulation user friendly log entries
    # -------------------------------------------------------
    def on_replay_sample_clicked(self) -> None:
        if not self._require_connected_for_generated_data():
            return
        self.on_stop_replay_clicked()
        self._replay_lines = deque(build_text_replay_sample())
        self._replay_active = True
        self._replay_requires_connection = True
        self._replay_timer.start()
        self.statusBar().showMessage("Replay: sample", 2000)

    def on_stop_replay_clicked(self) -> None:
        if self._replay_timer.isActive():
            self._replay_timer.stop()
        self._replay_lines.clear()
        self._replay_active = False
        self._replay_requires_connection = False
        self.statusBar().showMessage("Replay stopped", 1500)

    # ---------------- Simulation (Tools menu) ----------------

    def on_visualizer_csv_temp_config_clicked(self) -> None:
        changed = self._visualizer_manager.configure_csv_temp(parent=self)
        if changed:
            self.statusBar().showMessage("Plot visualizer config saved", 3000)

    def on_visualizer_csv_temp_show_clicked(self) -> None:
        self._visualizer_manager.show_windows("plot")

    def on_visualizer_logic_config_clicked(self) -> None:
        changed = self._visualizer_manager.configure_logic(parent=self)
        if changed:
            self.statusBar().showMessage("Logic visualizer config saved", 3000)


    def on_visualizer_logic_show_clicked(self) -> None:
        self._visualizer_manager.show_windows("logic")

    def _on_visualizer_diagnostic(self, message: str) -> None:
        self.log.appendPlainText(message)

    def on_simulate_toggled(self, checked: bool) -> None:
        if checked:
            if not self._require_connected_for_generated_data(self.act_simulate):
                return
            self._start_simulation()
        else:
            self._stop_simulation()

    def on_simulate_toggled_temperature(self, checked: bool) -> None:
        if checked:
            if not self._require_connected_for_generated_data(self.act_simulate_temperature):
                return
            self._start_simulation_temperature()
        else:
            self._stop_simulation_temperature()

    def on_simulate_logic_toggled(self, checked: bool) -> None:
        if checked:
            if not self._require_connected_for_generated_data(self.act_simulate_logic):
                self._sim_logic_enabled = False
                self._sim_logic_timer.stop()
                return
            self._sim_logic_enabled = True
            self._sim_logic_timer.start()
        else:
            self._sim_logic_enabled = False
            self._sim_logic_timer.stop()

    def _start_simulation(self) -> None:
        if self._sim_timer.isActive():
            return
        self._sim_enabled = True
        self._text_simulation = TextSimulationState()
        self._sim_timer.start()
        self.statusBar().showMessage("Simulation: ON (default profile)", 2500)

    def _start_simulation_temperature(self) -> None:
        if self._sim_temperature_timer.isActive():
            return
        self._sim_temperature_enabled = True
        self._sim_temperature_state = create_temperature_plot_simulation_state()
        self._sim_temperature_timer.start()
        self.statusBar().showMessage("Simulation (PLOT): ON (default profile)", 2500)


    def _stop_simulation(self) -> None:
        self._sim_enabled = False
        if self._sim_timer.isActive():
            self._sim_timer.stop()
        self.statusBar().showMessage("Simulation: OFF", 1500)

    def _stop_simulation_temperature(self) -> None:
        self._sim_temperature_enabled = False
        if self._sim_temperature_timer.isActive():
            self._sim_temperature_timer.stop()
        self.statusBar().showMessage("Simulation (PLOT): OFF", 1500)


    def _on_sim_tick(self) -> None:
        if not self._sim_enabled or not self._is_connected():
            return
        line = self._sim_next_line()
        self._on_line_received(line)


    def _sim_next_line(self) -> str:
        return next_text_simulation_line(self._text_simulation)


    def _on_sim_temperature_tick(self) -> None:
        if not self._sim_temperature_enabled or not self._is_connected():
            return
        for line in next_temperature_plot_simulation_lines(self._sim_temperature_state):
            self._on_line_received(line)


    def _on_sim_logic_tick(self) -> None:
        if not self._sim_logic_enabled or not self._is_connected():
            return
        self._ingest_line(next_client_logic_simulation_line(self._sim_logic_state))


    

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

        self._connection_state.trimmed_lines_total += remove_n

    # ---------------- UDP listener ----------------

    def _start_listener(self) -> bool:
        if self._listener is not None:
            return True

        request, error = parse_listener_request(self.ed_bind_ip.text(), self.ed_port.text())
        if request is None:
            title = "Missing Port" if "empty" in (error or "").lower() else "Invalid Port"
            QMessageBox.warning(self, title, error or "Invalid listener settings.")
            return False

        self._ui_state.bind_ip = request.bind_ip
        self._ui_state.port = request.port

        self._connection_state.rx_packets = 0
        self._connection_state.rx_lines = 0

        t = UdpListenerThread(request.bind_ip, request.port, parent=self)
        t.line_received.connect(self._on_line_received)
        t.status_changed.connect(self._on_listener_status)
        t.error.connect(self._on_listener_error)
        t.rx_stats.connect(self._on_rx_stats)

        self._listener = t
        t.start()

        self._ensure_active_live_log()
        return True

    def _stop_listener(self) -> None:
        if self._listener is None:
            return
        t = self._listener
        self._listener = None

        stop_listener_thread(t, wait_ms=800)
        self._close_live_log()

    def _clear_session_buffers(self) -> None:
        self.log.clear()
        self._queue.clear()
        self._connection_state.trimmed_lines_total = 0
        self._connection_state.rx_packets = 0
        self._connection_state.rx_lines = 0
        self._pause_buffer, self._pause_dropped, self._ui_paused = reset_pause_state(
            self._pause_buffer,
            maxlen=self._pause_buffer.maxlen or 2000,
        )
        self.btn_pause.blockSignals(True)
        self.btn_pause.setChecked(False)
        self.btn_pause.blockSignals(False)
        self._visualizer_manager.clear_all_buffers()

    def _reset_runtime_sources(self) -> None:
        self.on_stop_replay_clicked()
        self.on_stop_replay_temperature_clicked()
        self._stop_simulation()
        self._stop_simulation_temperature()
        self._sim_logic_enabled = False
        if self._sim_logic_timer.isActive():
            self._sim_logic_timer.stop()

        for action_name in ("act_simulate", "act_simulate_temperature", "act_simulate_logic"):
            action = getattr(self, action_name, None)
            if action is None or not action.isChecked():
                continue
            action.blockSignals(True)
            action.setChecked(False)
            action.blockSignals(False)

    def _reset_session(self) -> Path | None:
        self._reset_runtime_sources()
        self._stop_listener()
        self._clear_session_buffers()
        self._ensure_active_live_log()
        self.btn_connect.blockSignals(True)
        self.btn_connect.setChecked(False)
        self.btn_connect.blockSignals(False)
        self._update_connection_ui()
        return self._connection_state.active_path

    def _on_line_received(self, line: str) -> None:
        self._dispatch_log_line(line, is_live_source=True)

    def _on_listener_status(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 1500)
        if self._listener is not None:
            QTimer.singleShot(1600, self._update_connection_ui)

    def _on_listener_error(self, msg: str) -> None:
        self._append_log_line(f"[UI/ERROR] {msg}", write_live=True)
        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        self.statusBar().showMessage(msg, 5000)

    # def _on_rx_stats(self, packets: int, lines: int) -> None:
    #     self._rx_packets = packets
    #     self._rx_lines = lines
    #     if self._listener is None:
    #         return

    #     paused_txt = ""
    #     if self._ui_paused:
    #         paused_txt = f" — PAUSED (tail={len(self._pause_buffer)} drop={self._pause_dropped})"

    #     self.statusBar().showMessage(
    #         f"Listener: ON — {self._ui_state.bind_ip}:{self._ui_state.port} — "
    #         f"pkts={packets} lines={lines} — shown={self.log.document().blockCount()} "
    #         f"dropped={self._trimmed_lines_total} — HL={len(self._hl_rules)}"
    #         + (f" — {self._live_status_snippet()}" if getattr(self, "_live_log_path", None) else "")
    #         + paused_txt
    #     )

    def _on_rx_stats(self, packets: int, lines: int) -> None:
        self._connection_state.rx_packets = packets
        self._connection_state.rx_lines = lines
        if self._listener is None:
            return
        self.statusBar().showMessage(
            build_connection_status(
                connected=True,
                bind_ip=self._ui_state.bind_ip,
                port=self._ui_state.port,
                shown_lines=self.log.document().blockCount(),
                trimmed_lines_total=self._connection_state.trimmed_lines_total,
                highlight_count=len(self._hl_rules),
                rx_packets=packets,
                rx_lines=lines,
                live_snippet=self._live_status_snippet(),
                paused_tail=len(self._pause_buffer),
                paused_dropped=self._pause_dropped,
                paused=bool(self._ui_paused),
            )
        )

    def _flush_log_queue(self) -> None:
        try:
            if not self._queue:
                return
            batch = drain_queue(self._queue, max_items=300)
            if not batch:
                return

            for line in batch:
                self.log.appendPlainText(line)

            try:
                if self._connection_state.handle is not None:
                    self._connection_state.handle.flush()
            except Exception:
                self._close_live_log()

            self._enforce_log_limit()

            if self._ui_state.autoscroll:
                self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        except Exception as e:
            # Never crash the UI loop due to logging.
            try:
                self.log.appendPlainText(f"[UI/WARN] flush failed: {e}")
            except Exception:
                pass

    # ---------------- UI actions ----------------

    def on_save_clicked(self) -> Path | None:
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log",
            str(self._default_save_path()),
            "Text Files (*.txt);;All Files (*)",
        )
        if not selected_path:
            return None
        path = Path(selected_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        src: Optional[Path] = None
        if self._connection_state.active_path is not None:
            src = self._connection_state.active_path
            try:
                if self._connection_state.handle is not None:
                    try:
                        fsync_file_handle(self._connection_state.handle)
                    except Exception:
                        pass
            except Exception:
                pass
        elif self._connection_state.last_session_path is not None and self._connection_state.last_session_path.exists():
            src = self._connection_state.last_session_path

        if src is not None and src.exists():
            try:
                copy_log_file(src, path)
                self.statusBar().showMessage(f"Saved: {path}", 5000)
                return path
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not copy logfile:\n{e}")
                return None

        try:
            write_text_log(path, self.log.toPlainText())
            self.statusBar().showMessage(f"Saved: {path}", 5000)
            return path
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Could not save file:\n{e}")
            return None

    def on_project_clicked(self) -> None:
        dialog = ProjectDialog(
            self._active_project,
            default_root_dir=self._preferred_project_root_dir(),
            parent=self,
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        project_name = dialog.project_name()
        if not is_valid_project_name(project_name):
            QMessageBox.warning(
                self,
                "Invalid Project Name",
                "Project name must contain 1 to 50 characters using letters, digits, underscores, or hyphens.",
            )
            return

        root_dir = dialog.root_dir()
        if not str(root_dir):
            QMessageBox.warning(self, "Missing Root Folder", "Please select a root folder.")
            return

        project = RuntimeProject(name=project_name, root_dir=root_dir)
        try:
            initialize_project(project, dialog.project_notes())
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Project Creation Failed",
                f"Could not create the project folder or README:\n{exc}",
            )
            return
        self._preferences.project_root = str(root_dir)
        self._settings_store.save_preferences(self._preferences)
        self._settings_store.ini_set("paths", "project_root", str(root_dir))
        self._paths_cfg.project_root = root_dir
        self._active_project = project
        self._sync_runtime_context()
        self.statusBar().showMessage(f"Project active: {project.output_dir}", 4000)

    def on_clear_clicked(self) -> None:
        self.log.clear()
        self._connection_state.trimmed_lines_total = 0
        self.statusBar().showMessage("Cleared (UI only)", 2000)

    def on_reset_clicked(self) -> None:
        new_live_log = self._reset_session()
        self._reset_active_project()
        if new_live_log is not None:
            self.statusBar().showMessage(f"Session reset. Listener OFF. New live log: {new_live_log}", 5000)
        else:
            self.statusBar().showMessage("Session reset. Listener OFF.", 4000)

    def on_copy_clicked(self) -> None:
        cursor = self.log.textCursor()
        selected = cursor.selectedText()
        if selected:
            QApplication.clipboard().setText(selected)
            self.statusBar().showMessage("Copied selection", 2000)
        else:
            QApplication.clipboard().setText(self.log.toPlainText())
            self.statusBar().showMessage("Copied all", 2000)

    def _current_session_log_path(self) -> Path | None:
        if self._connection_state.active_path is not None:
            return self._connection_state.active_path
        if self._connection_state.last_session_path is not None and self._connection_state.last_session_path.exists():
            return self._connection_state.last_session_path
        return None

    def _has_session_logs_to_save(self) -> bool:
        if self._connection_state.rx_lines > 0:
            return True

        session_log_path = MainWindow._current_session_log_path(self)
        if session_log_path is None:
            return False

        try:
            with session_log_path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.strip() and not line.startswith("#"):
                        return True
        except Exception:
            return True
        return False

    def _confirm_save_logs_before_exit(self) -> bool:
        if not MainWindow._has_session_logs_to_save(self):
            return True

        mb = QMessageBox(self)
        mb.setWindowTitle("Exit")
        mb.setIcon(QMessageBox.Question)
        mb.setText("Save logs before exit?")
        mb.setInformativeText("The current session contains received log data.")
        yes = mb.addButton("Save…", QMessageBox.YesRole)
        no = mb.addButton("No", QMessageBox.NoRole)
        cancel = mb.addButton("Cancel", QMessageBox.RejectRole)
        mb.setDefaultButton(yes)
        mb.exec_()

        clicked = mb.clickedButton()
        if clicked == cancel:
            return False
        if clicked == yes:
            return self.on_save_clicked() is not None
        return True

    def on_connect_toggled(self) -> None:
        requested = self.btn_connect.isChecked()
        saved_path: Path | None = None

        if requested:
            ok = self._start_listener()
            if not ok:
                self.btn_connect.setChecked(False)
                self._update_connection_ui()
                return

            self._pause_buffer, self._pause_dropped, self._ui_paused = reset_pause_state(
                self._pause_buffer,
                maxlen=self._pause_buffer.maxlen or 2000,
            )
            self.btn_pause.blockSignals(True)
            self.btn_pause.setChecked(False)
            self.btn_pause.blockSignals(False)

            self._append_log_line(f"[UI/INFO] Listening on {self._ui_state.bind_ip}:{self._ui_state.port}", write_live=False)
            if self._connection_state.active_path is not None:
                self.log.appendPlainText(f"[UI/INFO] Live logfile: {self._connection_state.active_path}")
        else:
            if self._listener is not None:
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
                    self.btn_connect.blockSignals(True)
                    self.btn_connect.setChecked(True)
                    self.btn_connect.blockSignals(False)
                    self._update_connection_ui()
                    return
                if clicked == yes:
                    saved_path = self.on_save_clicked()

            self._stop_listener()

            try:
                for action_name in ("act_simulate", "act_simulate_temperature", "act_simulate_logic"):
                    action = getattr(self, action_name, None)
                    if action is not None and action.isChecked():
                        action.setChecked(False)
            except Exception:
                pass

            self._pause_buffer, self._pause_dropped, self._ui_paused = reset_pause_state(
                self._pause_buffer,
                maxlen=self._pause_buffer.maxlen or 2000,
            )
            self.btn_pause.blockSignals(True)
            self.btn_pause.setChecked(False)
            self.btn_pause.blockSignals(False)

            self._visualizer_manager.clear_all_buffers()
            self._append_log_line("[UI/INFO] Listener stopped", write_live=False)

        self._update_connection_ui()
        if not requested and saved_path is not None:
            self.statusBar().showMessage(f"Saved: {saved_path}", 5000)

    def on_pause_toggled(self) -> None:
        if self._listener is None:
            self.btn_pause.setChecked(False)
            self._pause_buffer, self._pause_dropped, self._ui_paused = reset_pause_state(
                self._pause_buffer,
                maxlen=self._pause_buffer.maxlen or 2000,
            )
            self._update_connection_ui()
            return

        self._ui_paused = bool(self.btn_pause.isChecked())

        if self._ui_paused:
            self.statusBar().showMessage("UI paused (logging continues)", 2000)
        else:
            dropped = self._pause_dropped
            buffered = list(self._pause_buffer)
            self._pause_buffer.clear()
            self._pause_dropped = 0

            if dropped > 0:
                self._queue.append(f"[UI/INFO] Resume: {dropped} lines skipped while paused (showing latest tail).")
            for ln in buffered:
                self._queue.append(ln)

            self._flush_log_queue()
            self.statusBar().showMessage("UI resumed", 1500)

        self._update_connection_ui()

    def on_timestamp_changed(self) -> None:
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
        self._set_generated_data_actions_enabled(connected)

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

            self.statusBar().showMessage(
                build_connection_status(
                    connected=True,
                    bind_ip=self._ui_state.bind_ip,
                    port=self._ui_state.port,
                    shown_lines=self.log.document().blockCount(),
                    trimmed_lines_total=self._connection_state.trimmed_lines_total,
                    highlight_count=len(self._hl_rules),
                    rx_packets=self._connection_state.rx_packets,
                    rx_lines=self._connection_state.rx_lines,
                    live_snippet=self._live_status_snippet(),
                    paused_tail=len(self._pause_buffer),
                    paused_dropped=self._pause_dropped,
                    paused=bool(self._ui_paused),
                )
            )
        else:
            self.chk_timestamp.setEnabled(True)
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")

            self.btn_pause.setEnabled(False)
            self.btn_pause.setText("PAUSE")
            self.btn_pause.setStyleSheet("QToolButton { background-color: #b0b0b0; font-weight: bold; }")

            self.statusBar().showMessage(
                build_connection_status(
                    connected=False,
                    bind_ip=self._ui_state.bind_ip,
                    port=self._ui_state.port,
                    shown_lines=self.log.document().blockCount(),
                    trimmed_lines_total=self._connection_state.trimmed_lines_total,
                    highlight_count=len(self._hl_rules),
                )
            )

    # --- Live logfile status ---
    @staticmethod
    def _format_bytes(n: int) -> str:
        return format_bytes(n)

    @staticmethod
    def _format_timestamp_prefix(dt: datetime) -> str:
        return dt.strftime("%Y%m%d-%H:%M:%S.") + f"{dt.microsecond//1000:03d}"

    def _append_log_line(self, line: str, *, write_live: bool = False) -> None:
        out_line = line
        if self._ui_state.timestamp_enabled:
            out_line = f"{self._format_timestamp_prefix(datetime.now())} {line}"

        self.log.appendPlainText(out_line)

        if write_live and self._connection_state.handle is not None:
            try:
                self._append_to_live_log(out_line)
            except Exception:
                pass

        if self._ui_state.autoscroll:
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def _live_status_snippet(self) -> str:
        return live_status_snippet(self._connection_state.active_path)

    # ---------------- Qt overrides ----------------

    def closeEvent(self, event) -> None:
        if not self._confirm_save_logs_before_exit():
            event.ignore()
            return
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
        try:
            self._visualizer_manager.close_all_windows()
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
