from __future__ import annotations

from collections import deque

from udp_log_viewer.listener_runtime import (
    ListenerRequest,
    parse_listener_request,
    reset_pause_state,
    stop_listener_thread,
)


def test_parse_listener_request_accepts_valid_input() -> None:
    request, error = parse_listener_request("0.0.0.0", "10514")

    assert error is None
    assert request == ListenerRequest(bind_ip="0.0.0.0", port=10514)


def test_parse_listener_request_rejects_invalid_port() -> None:
    request, error = parse_listener_request("0.0.0.0", "99999")

    assert request is None
    assert error == "Port must be a number between 1 and 65535."


def test_reset_pause_state_clears_buffer() -> None:
    buffer = deque(["a", "b"], maxlen=2000)

    new_buffer, dropped, paused = reset_pause_state(buffer, maxlen=2000)

    assert list(new_buffer) == []
    assert dropped == 0
    assert paused is False


def test_stop_listener_thread_invokes_stop_and_wait() -> None:
    class FakeListener:
        def __init__(self) -> None:
            self.stopped = False
            self.waited = None

        def stop(self) -> None:
            self.stopped = True

        def wait(self, timeout: int) -> None:
            self.waited = timeout

    fake = FakeListener()
    stop_listener_thread(fake, wait_ms=123)

    assert fake.stopped is True
    assert fake.waited == 123
