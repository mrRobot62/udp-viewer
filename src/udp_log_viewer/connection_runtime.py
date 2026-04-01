from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LiveLogState:
    active_path: Path | None = None
    last_session_path: Path | None = None
    handle: object | None = None
    trimmed_lines_total: int = 0
    rx_packets: int = 0
    rx_lines: int = 0


def ensure_logs_dir(logs_dir: str | Path) -> Path:
    path = Path(logs_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def open_live_log(logs_dir: str | Path, stamp: str, filename: str | None = None) -> tuple[object, Path]:
    base_dir = ensure_logs_dir(logs_dir)
    path = base_dir / (filename or f"udp_live_{stamp}.txt")
    handle = open(path, "w", encoding="utf-8", newline="\n")
    handle.write(f"# UDP Log Viewer live session — {stamp}\n")
    handle.flush()
    return handle, path


def ensure_active_live_log(
    state: LiveLogState,
    logs_dir: str | Path,
    stamp: str,
    filename: str | None = None,
) -> Path:
    if state.handle is not None and state.active_path is not None:
        return state.active_path
    handle, path = open_live_log(logs_dir, stamp, filename=filename)
    state.handle = handle
    state.active_path = path
    return path


def reset_live_log_session(
    state: LiveLogState,
    logs_dir: str | Path,
    stamp: str,
    filename: str | None = None,
) -> Path:
    close_live_log(state)
    return ensure_active_live_log(state, logs_dir, stamp, filename=filename)


def close_live_log(state: LiveLogState) -> None:
    try:
        if state.handle is not None:
            try:
                state.handle.flush()
            except Exception:
                pass
            state.handle.close()
    except Exception:
        pass
    state.last_session_path = state.active_path
    state.handle = None
    state.active_path = None


def append_live_log_line(state: LiveLogState, line: str) -> bool:
    if state.handle is None:
        return False
    state.handle.write(line + "\n")
    return True


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024.0:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024.0 * 1024.0):.1f} MB"
    return f"{size / (1024.0 * 1024.0 * 1024.0):.2f} GB"


def live_status_snippet(active_path: Path | None) -> str:
    if active_path is None:
        return ""
    try:
        size = active_path.stat().st_size
    except Exception:
        size = 0
    return f"LIVE: {active_path.name} ({format_bytes(size)})"


def build_connection_status(
    *,
    connected: bool,
    bind_ip: str,
    port: int,
    shown_lines: int,
    trimmed_lines_total: int,
    highlight_count: int,
    rx_packets: int = 0,
    rx_lines: int = 0,
    live_snippet: str = "",
    paused_tail: int = 0,
    paused_dropped: int = 0,
    paused: bool = False,
) -> str:
    if connected:
        paused_text = ""
        if paused:
            paused_text = f" — PAUSED (tail={paused_tail} drop={paused_dropped})"
        live_text = f" — {live_snippet}" if live_snippet else ""
        return (
            f"Listener: ON — {bind_ip}:{port} — "
            f"pkts={rx_packets} lines={rx_lines} — shown={shown_lines} "
            f"dropped={trimmed_lines_total} — HL={highlight_count}"
            f"{live_text}{paused_text}"
        )
    return (
        f"Listener: OFF — {bind_ip}:{port} — "
        f"shown={shown_lines} dropped={trimmed_lines_total} — HL={highlight_count}"
    )
