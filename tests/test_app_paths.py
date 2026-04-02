from __future__ import annotations

import os
from pathlib import Path

from udp_log_viewer.app_paths import get_default_project_root_dir, load_or_create_config


def test_load_or_create_config_supports_custom_config_path(tmp_path: Path) -> None:
    config_path = tmp_path / "custom" / "config.ini"

    cfg = load_or_create_config("LocalTools", "UdpLogViewer", "0.15.2", config_path=config_path)

    assert cfg.config_path == config_path
    assert cfg.app_support_dir == config_path.parent
    assert cfg.logs_dir == config_path.parent / "logs"
    assert cfg.project_root == Path.home() / "Documents"
    assert cfg.config_path.exists()


def test_default_project_root_uses_windows_documents(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("USERPROFILE", r"C:\Users\TestUser")

    project_root = get_default_project_root_dir()

    assert str(project_root) == os.path.join(r"C:\Users\TestUser", "Documents")
