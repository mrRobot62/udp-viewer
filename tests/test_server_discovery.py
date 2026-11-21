"""Check discovery framing, real UDP/TCP lifecycle and persistent settings."""

import socket
import time

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from udp_log_viewer.server_discovery import discovery_reply
from udp_log_viewer.settings_store import SettingsStore
from udp_log_viewer.tcp_listener import TcpListenerThread
from udp_log_viewer.ui_state import UiState

REQUEST = b"ULV_DISCOVER 1 0123456789abcdef\n"


@pytest.mark.parametrize("packet", [b"", b"ULV_DISCOVER 2 0123456789abcdef\n", REQUEST + b"x",
                                     REQUEST[:-1], REQUEST.replace(b"abcdef", b"ABCDEF"), b"x" * 1024])
def test_invalid_requests(packet):
    """Ignore unsupported versions, invalid nonce, truncation and trailing data."""
    assert discovery_reply(packet, "viewer-1", 10514) is None


def test_reply_and_identity(tmp_path):
    """Use the actual TCP port and preserve one generated ID across restarts."""
    assert discovery_reply(REQUEST, "viewer-1", 45678) == b"ULV_SERVER 1 0123456789abcdef viewer-1 45678\n"
    assert discovery_reply(REQUEST, "bad id", 10514) is None
    q = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    store = SettingsStore(q, tmp_path / "config.ini")
    state = store.load_ui_state(UiState())
    assert not state.discovery_enabled and state.discovery_port == 10515
    assert len(state.server_id) == 32
    state.discovery_enabled = True
    state.discovery_port = 12000
    store.save_ui_state(state)
    assert store.load_ui_state(UiState()) == state


def test_discovery_tcp_stop_and_rebind():
    """Discover over a real UDP socket, send TCP logs, then release both listeners."""
    app = QApplication.instance() or QApplication([])
    worker = TcpListenerThread("127.0.0.1", 0, discovery_port=0, server_id="viewer-test")
    worker.start()
    try:
        deadline = time.monotonic() + 3
        while worker._discovery_port == 0 and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.005)
        assert worker._discovery_port
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(1)
            client.sendto(REQUEST, ("127.0.0.1", worker._discovery_port))
            answer, peer = client.recvfrom(256)
            assert peer[0] == "127.0.0.1"
            assert answer == discovery_reply(REQUEST, "viewer-test", worker._port)
            with socket.create_connection((peer[0], int(answer.split()[-1])), timeout=1) as tcp:
                tcp.sendall(b"discovered\n")
                time.sleep(.05)
                client.sendto(REQUEST, ("127.0.0.1", worker._discovery_port))
                client.settimeout(.2)
                with pytest.raises(socket.timeout):
                    client.recvfrom(256)
        worker.stop()
        assert worker.wait(3000)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(("0.0.0.0", worker._discovery_port))
    finally:
        worker.stop()
        assert worker.wait(3000)


def test_discovery_bind_error_keeps_tcp_available():
    """Discovery port conflicts must not disable manual TCP connections."""
    app = QApplication.instance() or QApplication([])
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as occupied:
        occupied.bind(("0.0.0.0", 0))
        worker = TcpListenerThread("127.0.0.1", 0, discovery_port=occupied.getsockname()[1], server_id="test")
        worker.start()
        try:
            deadline = time.monotonic() + 3
            while worker._port == 0 and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(.005)
            with socket.create_connection(("127.0.0.1", worker._port), timeout=1):
                pass
        finally:
            worker.stop()
            assert worker.wait(3000)
