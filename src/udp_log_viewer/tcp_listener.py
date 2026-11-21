"""Single-client TCP log server with bounded UTF-8 line framing."""

from __future__ import annotations

import select
import socket
import threading
from collections.abc import Iterator

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtNetwork import QAbstractSocket, QNetworkInterface

from .server_discovery import DiscoveryResponder


MAX_MESSAGE_BYTES = 1024 * 1024


def configure_tcp_keepalive(client: socket.socket) -> None:
    """Detect reset/powered-off senders without expiring healthy idle connections."""
    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    idle = getattr(socket, "TCP_KEEPIDLE", getattr(socket, "TCP_KEEPALIVE", None))
    interval = getattr(socket, "TCP_KEEPINTVL", None)
    if idle is not None and interval is not None:
        client.setsockopt(socket.IPPROTO_TCP, idle, 5)
        client.setsockopt(socket.IPPROTO_TCP, interval, 2)
    elif hasattr(socket, "SIO_KEEPALIVE_VALS"):
        # Older Windows exposes the idle/interval controls in milliseconds via ioctl.
        client.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 5000, 2000))
    else:
        raise OSError("Short TCP keepalive intervals are unavailable on this platform")
    count = getattr(socket, "TCP_KEEPCNT", None)
    if count is not None:
        client.setsockopt(socket.IPPROTO_TCP, count, 3)


def tcp_listening_status(bind_ip: str, port: int) -> str:
    """Show concrete sender destinations without advertising the wildcard address."""
    addresses = {bind_ip} if bind_ip != "0.0.0.0" else set()
    if bind_ip == "0.0.0.0":
        for interface in QNetworkInterface.allInterfaces():
            flags = interface.flags()
            if not (flags & QNetworkInterface.IsUp and flags & QNetworkInterface.IsRunning):
                continue
            if flags & QNetworkInterface.IsLoopBack:
                continue
            for entry in interface.addressEntries():
                address = entry.ip()
                if address.protocol() == QAbstractSocket.IPv4Protocol and not address.isLoopback():
                    value = address.toString()
                    if value != "0.0.0.0":
                        addresses.add(value)
    if not addresses:
        return f"TCP ready — local sender: 127.0.0.1:{port} (no active LAN IPv4 address) — waiting for sender"
    destinations = ", ".join(f"{address}:{port}" for address in sorted(addresses))
    local_only = " (this computer only)" if all(address.startswith("127.") for address in addresses) else ""
    return f"TCP ready — connect sender to: {destinations}{local_only} — waiting for sender"


class TcpLineBuffer:
    """Frame LF/CRLF messages before decoding fragmented UTF-8 bytes."""

    def __init__(self, max_message_bytes: int = MAX_MESSAGE_BYTES) -> None:
        """Create an empty buffer with a positive payload limit."""
        if max_message_bytes < 1:
            raise ValueError("Message size limit must be positive")
        self.max_message_bytes = max_message_bytes
        self._pending = bytearray()

    def clear(self) -> int:
        """Discard an incomplete message and return its byte count."""
        size = len(self._pending)
        self._pending.clear()
        return size

    def feed(self, data: bytes) -> Iterator[str]:
        """Yield complete nonblank lines, raising on oversized payloads."""
        start = 0
        while start < len(data):
            end = data.find(b"\n", start)
            stop = len(data) if end < 0 else end
            fragment = data[start:stop]
            size = len(self._pending) + len(fragment)
            # One trailing CR may belong to the CRLF delimiter.
            trailing_cr = fragment.endswith(b"\r") if fragment else self._pending.endswith(b"\r")
            if size > self.max_message_bytes + int(trailing_cr):
                self.clear()
                raise ValueError(f"TCP message exceeds {self.max_message_bytes} bytes")
            self._pending.extend(fragment)
            if end < 0:
                return
            payload = bytes(self._pending)
            self._pending.clear()
            if payload.endswith(b"\r"):
                payload = payload[:-1]
            line = payload.decode("utf-8", errors="replace")
            if line.strip():
                yield line
            start = end + 1


class TcpListenerThread(QThread):
    """Receive one TCP sender at a time without blocking the GUI thread."""

    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error = pyqtSignal(str)
    rx_stats = pyqtSignal(object, object)  # cumulative bytes, complete nonblank lines
    ready = pyqtSignal()

    def __init__(self, bind_ip: str, port: int, *, parent=None, discovery_port: int | None = None, server_id: str = "") -> None:
        """Store the local endpoint and initialize a fresh receive session."""
        super().__init__(parent)
        self._bind_ip = bind_ip
        self._port = port
        self._stop_evt = threading.Event()
        self._discovery_port = discovery_port
        self._server_id = server_id

    def stop(self) -> None:
        """Request shutdown; the worker owns and closes all sockets."""
        self._stop_evt.set()

    def run(self) -> None:
        """Accept senders, frame messages and keep listening after peer loss."""
        server = None
        client = None
        discovery = None
        buffer = TcpLineBuffer()
        received_bytes = 0
        received_lines = 0
        try:
            self.status_changed.emit(f"Binding TCP {self._bind_ip}:{self._port} ...")
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Windows SO_REUSEADDR permits competing listeners; avoid it there.
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._bind_ip, self._port))
            self._port = server.getsockname()[1]
            server.listen(8)
            server.setblocking(False)
            if self._discovery_port is not None:
                try:
                    discovery = DiscoveryResponder(self._bind_ip, self._discovery_port, self._server_id, self._port)
                    self._discovery_port = discovery.port
                except (OSError, ValueError) as exc:
                    self.error.emit(f"TCP discovery unavailable (manual connections still work): {exc}")
            self.ready.emit()
            self.status_changed.emit(tcp_listening_status(server.getsockname()[0], self._port))
            while not self._stop_evt.is_set():
                sockets = [server] if client is None else [server, client]
                if discovery is not None:
                    sockets.append(discovery.socket)
                readable, _, _ = select.select(sockets, [], [], 0.10)
                if self._stop_evt.is_set():
                    break
                # Consume EOF before accepting a replacement sender.
                if client is not None and client in readable:
                    disconnected = False
                    try:
                        data = client.recv(65536)
                        if data:
                            received_bytes += len(data)
                            try:
                                for line in buffer.feed(data):
                                    if self._stop_evt.is_set():
                                        break
                                    received_lines += 1
                                    self.line_received.emit(line)
                            finally:
                                self.rx_stats.emit(received_bytes, received_lines)
                        else:
                            disconnected = True
                    except BlockingIOError:
                        pass
                    except (OSError, ValueError) as exc:
                        self.error.emit(f"TCP sender disconnected: {exc}")
                        disconnected = True
                    if disconnected:
                        client.close()
                        client = None
                        pending = buffer.clear()
                        if pending:
                            self.error.emit(f"TCP discarded incomplete message ({pending} bytes)")
                        self.status_changed.emit(tcp_listening_status(server.getsockname()[0], self._port))
                if server in readable:
                    try:
                        incoming, address = server.accept()
                    except BlockingIOError:
                        continue
                    if client is not None:
                        incoming.close()
                        self.error.emit(f"TCP sender {address[0]}:{address[1]} rejected: another sender is connected")
                    else:
                        client = incoming
                        client.setblocking(False)
                        try:
                            configure_tcp_keepalive(client)
                        except OSError as exc:
                            self.error.emit(f"TCP reset detection may be delayed: {exc}")
                        local_ip, local_port = client.getsockname()
                        self.status_changed.emit(
                            f"TCP server {local_ip}:{local_port} — sender connected: {address[0]}:{address[1]}"
                        )
                if discovery is not None and discovery.socket in readable:
                    try:
                        discovery.respond(available=client is None)
                    except OSError as exc:
                        self.error.emit(f"TCP discovery stopped (manual connections still work): {exc}")
                        discovery.close()
                        discovery = None
        except Exception as exc:
            if not self._stop_evt.is_set():
                self.error.emit(f"TCP listener error: {exc}")
        finally:
            buffer.clear()
            if discovery is not None:
                discovery.close()
            for sock in (client, server):
                if sock is not None:
                    sock.close()
            self.status_changed.emit("Listener stopped")
