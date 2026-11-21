"""Bounded UDP discovery for the TCP log server (wire protocol version 1)."""

import re
import socket
import time

MAX_DATAGRAM = 192
REQUEST = re.compile(rb"ULV_DISCOVER 1 ([0-9a-f]{16})\n")


def discovery_reply(data: bytes, server_id: str, tcp_port: int) -> bytes | None:
    """Echo a valid request nonce with the stable identity and listening TCP port."""
    match = REQUEST.fullmatch(data)
    if match is None or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", server_id):
        return None
    if not 1 <= tcp_port <= 65535:
        return None
    return b"ULV_SERVER 1 " + match[1] + f" {server_id} {tcp_port}\n".encode("ascii")


class DiscoveryResponder:
    """Serve discovery in the TCP worker, with bounded work and a global reply limit."""

    def __init__(self, bind_ip: str, port: int, server_id: str, tcp_port: int) -> None:
        """Bind broadcast reception separately from an explicitly bound reply source."""
        if discovery_reply(b"ULV_DISCOVER 1 0123456789abcdef\n", server_id, tcp_port) is None:
            raise ValueError("Invalid discovery identity or TCP port")
        self.server_id = server_id
        self.tcp_port = tcp_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._reply_socket = self.socket
        self._tokens = 20.0
        self._updated = time.monotonic()
        try:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.socket.bind(("0.0.0.0", port))
            self.port = self.socket.getsockname()[1]
            self.socket.setblocking(False)
            if bind_ip != "0.0.0.0":
                self._reply_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._reply_socket.bind((bind_ip, 0))
                self._reply_socket.setblocking(False)
        except Exception:
            self.close()
            raise

    def respond(self, *, available: bool) -> None:
        """Consume at most one datagram, responding only while the TCP slot is free."""
        try:
            data, peer = self.socket.recvfrom(MAX_DATAGRAM + 1)
        except BlockingIOError:
            return
        if not available or len(data) > MAX_DATAGRAM or peer[1] == 0:
            return
        answer = discovery_reply(data, self.server_id, self.tcp_port)
        if answer is None:
            return
        now = time.monotonic()
        self._tokens = min(20.0, self._tokens + (now - self._updated) * 10)
        self._updated = now
        if self._tokens >= 1:
            self._tokens -= 1
            try:
                self._reply_socket.sendto(answer, peer)
            except BlockingIOError:
                pass

    def close(self) -> None:
        """Release receive and reply sockets on TCP stop, reset or initialization error."""
        if self._reply_socket is not self.socket:
            self._reply_socket.close()
        self.socket.close()
