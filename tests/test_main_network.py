"""Cover transport selection and session lifecycle through the real main window."""

import socket
import time
from types import SimpleNamespace

import pytest
from PyQt5.QtCore import QSettings, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from udp_log_viewer.main import MainWindow
from udp_log_viewer.rule_slots import PatternSlot
from udp_log_viewer.data_visualizer.logic_visualizer_window import LogicMeasurement
from udp_log_viewer.data_visualizer.visualizer_config import VisualizerConfig
from udp_log_viewer.data_visualizer.visualizer_field_config import VisualizerFieldConfig
from udp_log_viewer.data_visualizer.visualizer_slot import VisualizerSlotId


def pump_until(app, predicate, timeout=3.0) -> None:
    """Deliver Qt events while waiting for a bounded asynchronous transition."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    assert predicate(), "Timed out waiting for window state"


@pytest.fixture
def window(tmp_path, monkeypatch):
    """Isolate application settings, log output and project paths per test."""
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "ui.ini"), QSettings.IniFormat)
    config = tmp_path / "config.ini"
    config.write_text("", encoding="utf-8")
    monkeypatch.setattr("udp_log_viewer.main.QSettings", lambda *args: settings)
    monkeypatch.setattr(MainWindow, "_resolve_config_path", lambda self: config)
    monkeypatch.setattr("udp_log_viewer.main.load_or_create_config", lambda *args, **kwargs: SimpleNamespace(
        config_path=config, logs_dir=tmp_path / "logs", project_root=tmp_path / "projects"
    ))
    monkeypatch.setattr("udp_log_viewer.main.get_default_project_root_dir", lambda: tmp_path / "projects")
    monkeypatch.setattr("udp_log_viewer.main._get_local_ipv4", lambda: "127.0.0.1")
    monkeypatch.setattr(MainWindow, "_confirm_save_logs_before_exit", lambda self: True)

    def unexpected_dialog(parent, title, message, *args, **kwargs):
        """Fail with the diagnostic instead of hanging on an offscreen dialog."""
        pytest.fail(f"Unexpected dialog {title}: {message}")

    for method in ("critical", "warning", "information"):
        monkeypatch.setattr(QMessageBox, method, unexpected_dialog)
    view = MainWindow()
    view.chk_timestamp.setChecked(False)
    view.ed_bind_ip.setText("127.0.0.1")
    try:
        yield app, view
    finally:
        view.close()
        pump_until(app, lambda: not view._stopping_listeners)
        app.processEvents()
        view._flush_timer.stop()
        view.deleteLater()
        app.processEvents()


def start(view, app, protocol):
    """Select a free local port and start the chosen transport via the UI."""
    kind = socket.SOCK_STREAM if protocol == "tcp" else socket.SOCK_DGRAM
    with socket.socket(socket.AF_INET, kind) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    view.cb_protocol.setCurrentText(protocol.upper())
    view.ed_port.setText(str(port))
    view.btn_connect.setChecked(True)
    view.on_connect_toggled()
    pump_until(app, view._is_connected)
    return ("127.0.0.1", port)


def send(endpoint, protocol, payload):
    """Send a payload through the actual selected network transport."""
    if protocol == "tcp":
        with socket.create_connection(endpoint, timeout=1) as sender:
            sender.sendall(payload)
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            sender.sendto(payload, endpoint)


def test_discovery_controls_and_listener_lifecycle(window):
    """Persist discovery controls and tie the responder to the selected TCP session."""
    app, view = window
    view.cb_protocol.setCurrentText("UDP")
    view._update_connection_ui()
    assert not view.chk_discovery.isEnabled()
    view.cb_protocol.setCurrentText("TCP")
    assert view.chk_discovery.isEnabled()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("0.0.0.0", 0))
        discovery_port = probe.getsockname()[1]
    view.sp_discovery_port.setValue(discovery_port)
    view.chk_discovery.setChecked(True)
    endpoint = start(view, app, "tcp")
    assert not view.chk_discovery.isEnabled()
    assert not view.sp_discovery_port.isEnabled()
    assert view._settings.value("net/discovery_enabled", type=bool)
    assert view.ed_server_id.text() == view._settings.value("net/server_id")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        sender.settimeout(1)
        sender.sendto(b"ULV_DISCOVER 1 0123456789abcdef\n", ("127.0.0.1", discovery_port))
        answer, _ = sender.recvfrom(256)
        assert answer.split()[-2].decode() == view.ed_server_id.text()
        assert int(answer.split()[-1]) == endpoint[1]
    view._stop_listener()
    pump_until(app, lambda: not view._stopping_listeners)
    assert view.chk_discovery.isEnabled()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("0.0.0.0", discovery_port))


@pytest.mark.parametrize("protocol", ["udp", "tcp"])
def test_network_uses_shared_filter_file_visualizer_and_counter_paths(window, monkeypatch, protocol):
    """Both transports count before filtering and feed the shared visualizer path."""
    app, view = window
    visualized = []
    monkeypatch.setattr(view._visualizer_manager, "process_log_line", visualized.append)
    view._filter_slots = [PatternSlot(pattern="keep", mode="Substring", color="None")]
    view._rebuild_filter_patterns()
    endpoint = start(view, app, protocol)
    assert not view.cb_protocol.isEnabled()
    assert view._settings.value("net/protocol") == protocol
    send(endpoint, protocol, b"keep this\ndiscard this\n")
    pump_until(app, lambda: view._connection_state.rx_lines == 2)
    view._flush_log_queue()
    assert len(visualized) == 2
    assert visualized[0].endswith("keep this")
    assert "keep this" in view.log.toPlainText()
    assert "discard this" not in view.log.toPlainText()
    view._connection_state.handle.flush()
    saved = view._connection_state.active_path.read_text(encoding="utf-8")
    assert "keep this" in saved
    assert "discard this" not in saved
    if protocol == "tcp":
        assert view._connection_state.rx_bytes == len(b"keep this\ndiscard this\n")
        assert "bytes=" in view.statusBar().currentMessage()
        assert "pkts=" not in view.statusBar().currentMessage()
    else:
        assert view._connection_state.rx_packets == 1


@pytest.mark.parametrize("protocol", ["udp", "tcp"])
def test_disconnect_reset_project_reconnect_rejects_old_signals(window, monkeypatch, protocol, tmp_path):
    """Reset keeps the visualizer reset hook and excludes old worker events."""
    app, view = window
    resets = []
    original_clear = view._visualizer_manager.clear_all_buffers

    def clear():
        """Record calls while preserving the real manager reset behavior."""
        resets.append(True)
        original_clear()

    monkeypatch.setattr(view._visualizer_manager, "clear_all_buffers", clear)
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: 0)
    monkeypatch.setattr(
        QMessageBox, "clickedButton",
        lambda self: next(button for button in self.buttons() if self.buttonRole(button) == QMessageBox.NoRole),
    )
    for graph_type, field, marker in (
        ("logic", "ch0", "[CSV_TEST_LOGIC]"), ("plot", "value", "[CSV_TEST_PLOT]")
    ):
        view._visualizer_manager.configs_by_type[graph_type][0] = VisualizerConfig(
            enabled=True, title=marker, filter_string=marker, graph_type=graph_type,
            fields=[VisualizerFieldConfig(field, active=True, numeric=True, scale=1, plot=True, axis="Y1")],
        )
    endpoint = start(view, app, protocol)
    send(endpoint, protocol, b"before reset\n[CSV_TEST_LOGIC];0\n[CSV_TEST_PLOT];10\n")
    pump_until(app, lambda: view._connection_state.rx_lines == 3)
    logic = view._visualizer_manager.windows_by_slot[VisualizerSlotId("logic", 0)]
    plot = view._visualizer_manager.windows_by_slot[VisualizerSlotId("plot", 0)]
    assert len(logic.samples) == len(plot.samples) == 1
    logic.set_auto_refresh(False)
    plot.set_auto_refresh(False)
    assert logic._widget is not None
    logic._widget._measurement = LogicMeasurement("ch0", 0, "rising", None, None, "edge")
    logic._widget._cursor_line.set_visible(True)
    old = view._listener
    view.btn_connect.setChecked(False)
    view.on_connect_toggled()
    assert view._listener is None
    assert view._stopping_listeners
    assert view._start_listener() is False
    # Queued signals still retain their sender, but that sender is no longer active.
    old.line_received.emit("stale line")
    old.rx_stats.emit(999, 999)
    old.error.emit("stale error")
    view.on_reset_clicked()
    pump_until(app, lambda: not view._stopping_listeners)
    assert len(resets) >= 2
    assert view._connection_state.rx_lines == 0
    assert "stale" not in view.log.toPlainText()
    assert view._listener_error_text == ""
    assert logic.auto_refresh_enabled and plot.auto_refresh_enabled
    assert logic.freeze_sample_index is None and plot.freeze_sample_index is None
    assert not logic.samples and not plot.samples
    assert logic._widget._measurement is None
    assert not logic._widget._cursor_line.get_visible()
    assert logic._widget._auto_refresh_checkbox.isChecked()
    from udp_log_viewer.project_runtime import RuntimeProject

    view._active_project = RuntimeProject(name="Next", root_dir=tmp_path / "projects")
    view._sync_runtime_context()
    endpoint = start(view, app, protocol)
    send(endpoint, protocol, b"after reset\n[CSV_TEST_LOGIC];1\n[CSV_TEST_PLOT];20\n")
    pump_until(app, lambda: view._connection_state.rx_lines == 3)
    view._flush_log_queue()
    assert "after reset" in view.log.toPlainText()
    assert "before reset" not in view.log.toPlainText()
    assert logic.samples[-1].values_by_name["ch0"] == 1
    assert plot.samples[-1].values_by_name["value"] == 20
    assert len(logic.samples) == len(plot.samples) == 1
    assert logic._widget._get_visible_samples()


def test_bind_error_returns_ui_to_disconnected(window):
    """Failed binding must not leave CONNECTED or disabled endpoint controls."""
    app, view = window
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        view.cb_protocol.setCurrentText("TCP")
        view.ed_port.setText(str(occupied.getsockname()[1]))
        view.btn_connect.setChecked(True)
        view.on_connect_toggled()
        pump_until(app, lambda: view._listener is None and not view._stopping_listeners)
    assert not view.btn_connect.isChecked()
    assert view.cb_protocol.isEnabled()
    assert "TCP listener error" in view.lbl_network_status.text()


def test_cancelled_save_keeps_tcp_listener_running(window, monkeypatch):
    """Cancelling the save dialog also cancels the requested disconnect."""
    app, view = window
    start(view, app, "tcp")
    worker = view._listener
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: 0)
    monkeypatch.setattr(
        QMessageBox, "clickedButton",
        lambda self: next(button for button in self.buttons() if self.buttonRole(button) == QMessageBox.YesRole),
    )
    monkeypatch.setattr(view, "on_save_clicked", lambda: None)
    view.btn_connect.setChecked(False)
    view.on_connect_toggled()
    assert view._listener is worker
    assert view._is_connected()
    assert view.btn_connect.isChecked()


@pytest.mark.parametrize("protocol", ["udp", "tcp"])
def test_window_close_is_asynchronous_and_releases_worker(window, protocol):
    """Closing keeps Qt responsive while pending network shutdown completes."""
    app, view = window
    endpoint = start(view, app, protocol)
    send(endpoint, protocol, b"last line\n")
    pump_until(app, lambda: view._connection_state.rx_lines == 1)
    ticks = []
    QTimer.singleShot(0, lambda: ticks.append(True))
    view.close()
    assert view._close_pending
    pump_until(app, lambda: bool(ticks) and not view._stopping_listeners)
    assert view._listener is None
    assert view._connection_state.handle is None
