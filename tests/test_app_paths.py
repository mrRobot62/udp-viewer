from __future__ import annotations

from pathlib import Path

from udp_log_viewer.app_paths import load_or_create_config


def test_load_or_create_config_supports_custom_config_path(tmp_path: Path) -> None:
    config_path = tmp_path / "custom" / "config.ini"

    cfg = load_or_create_config("LocalTools", "UdpLogViewer", "0.15.2", config_path=config_path)

    assert cfg.config_path == config_path
    assert cfg.app_support_dir == config_path.parent
    assert cfg.logs_dir == config_path.parent / "logs"
    assert cfg.config_path.exists()
