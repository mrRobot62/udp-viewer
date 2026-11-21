"""Exercise real loopback sockets and Qt worker delivery for both transports."""

import socket
import time
from contextlib import contextmanager

import pytest
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication

from udp_log_viewer.tcp_listener import TcpListenerThread
from udp_log_viewer.udp_listener import UdpListenerThread


@pytest.fixture
def app():
    """Keep a Qt event loop available for queued worker signals."""
    return QApplication.instance() or QApplication([])


def wait_until(app, predicate, timeout=3.0) -> None:
    """Pump queued Qt events until a condition holds or a deadline expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    assert predicate(), "Timed out waiting for network/Qt state"


@contextmanager
def running_listener(app, cls, port=0):
    """Start a worker on loopback and always join it before releasing Qt."""
    worker = cls("127.0.0.1", port)
    ready = QSignalSpy(worker.ready)
    lines = QSignalSpy(worker.line_received)
    errors = QSignalSpy(worker.error)
    stats = QSignalSpy(worker.rx_stats)
    statuses = QSignalSpy(worker.status_changed)
    worker.start()
    try:
        wait_until(app, lambda: len(ready) == 1 or bool(errors))
        assert len(ready) == 1, f"Listener failed to start: {list(errors)}"
        yield worker, lines, errors, stats, statuses
    finally:
        worker.stop()
        assert worker.wait(3000)
        app.processEvents()


def test_tcp_fragmentation_reconnect_and_counters(app) -> None:
    """Reassemble lines, discard an EOF tail and keep cumulative counters."""
    with running_listener(app, TcpListenerThread) as (worker, lines, errors, stats, statuses):
        endpoint = ("127.0.0.1", worker._port)
        with socket.create_connection(endpoint, timeout=1) as sender:
            sender.sendall(b"Gr\xc3")
            wait_until(app, lambda: len(stats) > 0)
            assert list(lines) == []
            sender.sendall(b"\xbc\xc3\x9fe\r\nsecond\npartial")
            wait_until(app, lambda: len(lines) == 2)
        wait_until(app, lambda: any("incomplete" in row[0] for row in errors))
        with socket.create_connection(endpoint, timeout=1) as sender:
            sender.sendall(b"new\n")
            wait_until(app, lambda: len(lines) == 3)
        assert [row[0] for row in lines] == ["Grüße", "second", "new"]
        assert stats[-1] == [len("Grüße\r\nsecond\npartialnew\n".encode()), 3]
        assert worker.isRunning()


def test_tcp_rejects_second_client_without_disrupting_first(app) -> None:
    """Reject a competing sender and preserve the active stream."""
    with running_listener(app, TcpListenerThread) as (worker, lines, errors, stats, statuses):
        endpoint = ("127.0.0.1", worker._port)
        with socket.create_connection(endpoint, timeout=1) as first:
            first.sendall(b"first\n")
            wait_until(app, lambda: len(lines) == 1)
            with socket.create_connection(endpoint, timeout=1) as second:
                wait_until(app, lambda: len(errors) == 1)
                assert second.recv(1) == b""
            first.sendall(b"still here\n")
            wait_until(app, lambda: len(lines) == 2)
        assert "another sender" in errors[0][0]
        assert lines[-1] == ["still here"]


def test_tcp_oversize_disconnect_preserves_server(app, monkeypatch) -> None:
    """Limit failures affect only the sender, not subsequent connections."""
    from udp_log_viewer.tcp_listener import TcpLineBuffer

    monkeypatch.setattr("udp_log_viewer.tcp_listener.TcpLineBuffer", lambda: TcpLineBuffer(8))
    with running_listener(app, TcpListenerThread) as (worker, lines, errors, stats, statuses):
        endpoint = ("127.0.0.1", worker._port)
        with socket.create_connection(endpoint, timeout=1) as sender:
            sender.sendall(b"ok\n123456789")
            wait_until(app, lambda: len(errors) > 0)
            assert sender.recv(1) == b""
        with socket.create_connection(endpoint, timeout=1) as sender:
            sender.sendall(b"new\n")
            wait_until(app, lambda: len(lines) == 2)
        assert [row[0] for row in lines] == ["ok", "new"]
        assert "exceeds" in errors[0][0]


def test_udp_preserves_datagrams_line_splitting_and_counters(app) -> None:
    """Keep existing UDP CR/LF splitting and count even blank datagrams."""
    with running_listener(app, UdpListenerThread) as (worker, lines, errors, stats, statuses):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            endpoint = ("127.0.0.1", worker._port)
            sender.sendto(b"one\rtwo\r\nthree\n \n", endpoint)
            sender.sendto(b"", endpoint)
        wait_until(app, lambda: len(stats) == 2)
        assert [row[0] for row in lines] == ["one", "two", "three"]
        assert stats[-1] == [2, 3]
        assert not errors


@pytest.mark.parametrize("connected", [False, True])
def test_tcp_stop_and_rebind(app, connected) -> None:
    """Release listening and accepted sockets on stop, permitting reuse."""
    with running_listener(app, TcpListenerThread) as (worker, lines, errors, stats, statuses):
        port = worker._port
        sender = socket.create_connection(("127.0.0.1", port), timeout=1) if connected else None
        try:
            if sender is not None:
                sender.sendall(b"pending")
                wait_until(app, lambda: len(stats) > 0)
            worker.stop()
            wait_until(app, lambda: worker.isFinished())
            assert not errors
        finally:
            if sender is not None:
                sender.close()
    with running_listener(app, TcpListenerThread, port) as (worker, lines, errors, stats, statuses):
        with socket.create_connection(("127.0.0.1", port), timeout=1) as sender:
            sender.sendall(b"after restart\n")
            wait_until(app, lambda: len(lines) == 1)
        assert lines[0] == ["after restart"]


def test_tcp_bind_failure_finishes_without_ready(app) -> None:
    """A busy port emits an error and never reports listener readiness."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        worker = TcpListenerThread("127.0.0.1", occupied.getsockname()[1])
        errors = QSignalSpy(worker.error)
        ready = QSignalSpy(worker.ready)
        worker.start()
        try:
            wait_until(app, lambda: worker.isFinished() and len(errors) > 0)
            assert not ready
        finally:
            worker.stop()
            assert worker.wait(3000)
