"""Cover platform keepalive options and reset recovery without restarting the server."""

import errno
import socket
import time

from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication

from udp_log_viewer.tcp_listener import TcpListenerThread, configure_tcp_keepalive


def test_keepalive_options_on_local_socket():
    """Verify the host accepts bounded probe timers without application payloads."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        configure_tcp_keepalive(client)
        assert client.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) != 0
        idle = getattr(socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None))
        if idle is not None:
            assert client.getsockopt(socket.IPPROTO_TCP, idle) == 5
        if hasattr(socket, "TCP_KEEPINTVL"):
            assert client.getsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL) == 2
        if hasattr(socket, "TCP_KEEPCNT"):
            assert client.getsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT) == 3


def test_windows_legacy_keepalive(monkeypatch):
    """Use millisecond ioctl controls when Windows lacks named TCP timer options."""
    for name in ("TCP_KEEPIDLE", "TCP_KEEPALIVE", "TCP_KEEPINTVL", "TCP_KEEPCNT"):
        monkeypatch.delattr(socket, name, raising=False)
    monkeypatch.setattr(socket, "SIO_KEEPALIVE_VALS", 12345, raising=False)
    calls = []

    class Client:
        """Record option calls without depending on a Windows test host."""

        def setsockopt(self, *args):
            """Record ordinary socket options."""
            calls.append(args)

        def ioctl(self, *args):
            """Record Windows-specific timer configuration."""
            calls.append(args)

    configure_tcp_keepalive(Client())
    assert calls == [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1), (12345, (1, 5000, 2000))]


def test_keepalive_timeout_releases_discovery_and_preserves_logs(monkeypatch):
    """Inject kernel timeout on an unclosed peer; reconnect on the same TCP listener."""
    app = QApplication.instance() or QApplication([])
    import udp_log_viewer.tcp_listener as module

    original_select = module.select.select
    accepted = []
    expire = [False]
    original_configure = module.configure_tcp_keepalive

    def configure(client):
        """Record accepted sockets while applying the real host keepalive options."""
        original_configure(client)
        accepted.append(client)

    def selected(read, write, error, timeout):
        """Make the first peer readable when its simulated kernel timer expires."""
        if expire[0] and accepted and accepted[0] in read:
            return [accepted[0]], [], []
        return original_select(read, write, error, timeout)

    original_socket = socket.socket

    class ServerSocket(original_socket):
        """Provide an accepted socket that can report a keepalive timeout."""

        def accept(self):
            """Wrap only server-side accepted sockets, preserving their descriptors."""
            client, address = super().accept()
            return TimedSocket(fileno=client.detach()), address

    class TimedSocket(original_socket):
        """Simulate a lost sender without closing its client-side TCP socket."""

        def recv(self, *args):
            """Report the same error a kernel emits after unanswered keepalive probes."""
            if expire[0] and accepted and self is accepted[0]:
                raise OSError(errno.ETIMEDOUT, "simulated keepalive timeout")
            return super().recv(*args)

    monkeypatch.setattr(module.socket, "socket", ServerSocket)
    monkeypatch.setattr(module.select, "select", selected)
    monkeypatch.setattr(module, "configure_tcp_keepalive", configure)
    worker = TcpListenerThread("127.0.0.1", 0, discovery_port=0, server_id="reset-test")
    ready = QSignalSpy(worker.ready)
    lines = QSignalSpy(worker.line_received)
    errors = QSignalSpy(worker.error)

    def wait_for(condition):
        """Pump events to a bounded condition instead of depending on fixed sleeps."""
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            app.processEvents()
            if condition():
                return
            time.sleep(.005)
        assert condition()

    worker.start()
    first = None
    try:
        wait_for(lambda: len(ready) == 1)
        first = socket.create_connection(("127.0.0.1", worker._port), timeout=1)
        first.sendall(b"before reset\nold-tail")
        wait_for(lambda: len(lines) == 1)
        with original_socket(socket.AF_INET, socket.SOCK_DGRAM) as discovery:
            discovery.settimeout(.15)
            discovery.sendto(b"ULV_DISCOVER 1 0123456789abcdef\n", ("127.0.0.1", worker._discovery_port))
            try:
                discovery.recvfrom(256)
                assert False, "Healthy idle sender must retain its slot"
            except socket.timeout:
                pass
            expire[0] = True
            wait_for(lambda: any("incomplete" in row[0] for row in errors))
            discovery.settimeout(1)
            discovery.sendto(b"ULV_DISCOVER 1 0123456789abcdef\n", ("127.0.0.1", worker._discovery_port))
            answer, _ = discovery.recvfrom(256)
            assert int(answer.split()[-1]) == worker._port
        with socket.create_connection(("127.0.0.1", worker._port), timeout=1) as second:
            second.sendall(b"after reset\n")
            wait_for(lambda: len(lines) == 2)
        assert [row[0] for row in lines] == ["before reset", "after reset"]
        assert len(ready) == 1 and worker.isRunning()
    finally:
        if first is not None:
            first.close()
        worker.stop()
        assert worker.wait(3000)
