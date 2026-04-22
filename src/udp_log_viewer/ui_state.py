from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UiState:
    """Runtime state container for Ui."""
    bind_ip: str = "0.0.0.0"
    port: int = 10514
    autoscroll: bool = True
    timestamp_enabled: bool = False
    max_lines: int = 20000
