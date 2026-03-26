from __future__ import annotations

from pathlib import Path

from udp_log_viewer.connection_runtime import (
    LiveLogState,
    append_live_log_line,
    build_connection_status,
    close_live_log,
    live_status_snippet,
    open_live_log,
)


def test_open_append_and_close_live_log(tmp_path: Path) -> None:
    handle, path = open_live_log(tmp_path, "20260326_231500")
    state = LiveLogState(active_path=path, handle=handle)

    assert append_live_log_line(state, "hello") is True
    close_live_log(state)

    assert state.active_path is None
    assert state.last_session_path == path
    assert "hello" in path.read_text(encoding="utf-8")


def test_connection_status_text_contains_expected_values() -> None:
    text = build_connection_status(
        connected=True,
        bind_ip="0.0.0.0",
        port=10514,
        shown_lines=123,
        trimmed_lines_total=4,
        highlight_count=2,
        rx_packets=10,
        rx_lines=12,
        live_snippet="LIVE: test.txt (12 B)",
        paused_tail=5,
        paused_dropped=1,
        paused=True,
    )

    assert "Listener: ON" in text
    assert "pkts=10" in text
    assert "LIVE: test.txt" in text
    assert "PAUSED" in text


def test_live_status_snippet_for_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "live.txt"
    path.write_text("abc", encoding="utf-8")

    snippet = live_status_snippet(path)

    assert "live.txt" in snippet
    assert "B" in snippet
