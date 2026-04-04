from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque


@dataclass(frozen=True)
class ListenerRequest:
    bind_ip: str
    port: int


def parse_listener_request(bind_ip_text: str, port_text: str) -> tuple[ListenerRequest | None, str | None]:
    bind_ip = bind_ip_text.strip() or "0.0.0.0"
    port_raw = port_text.strip()

    if not port_raw:
        return None, "Port is empty. Please enter a port number."

    try:
        port = int(port_raw)
        if not (1 <= port <= 65535):
            raise ValueError("Port out of range")
    except Exception:
        return None, "Port must be a number between 1 and 65535."

    return ListenerRequest(bind_ip=bind_ip, port=port), None


def reset_pause_state(pause_buffer: Deque[str], *, maxlen: int = 2000) -> tuple[Deque[str], int, bool]:
    return deque(maxlen=maxlen), 0, False


def stop_listener_thread(listener, *, wait_ms: int = 800) -> None:
    try:
        listener.stop()
        if listener.wait(wait_ms):
            return
        listener.wait(max(wait_ms, 2000))
    except Exception:
        pass
