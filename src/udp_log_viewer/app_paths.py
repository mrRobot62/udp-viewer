from __future__ import annotations

import configparser
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AppPathsConfig:
    """
    Runtime-configurable paths for UDP Log Viewer.

    The config file lives in the per-user config location:
      macOS:   ~/Library/Application Support/<org>/<app>/config.ini
      Windows: %APPDATA%\<org>\<app>\config.ini
      Linux:   ~/.config/<org>/<app>/config.ini

    Users may edit the config.ini to override default locations (e.g., log directory).
    """
    config_path: Path
    logs_dir: Path
    app_version: str


def _user_app_dir(app_org: str, app_name: str) -> Path:
    """
    Return a writable per-user directory for app data/config.

    We intentionally avoid relative paths so packaged apps (DMG/EXE) work reliably.
    """
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / app_org / app_name


def _default_logs_dir(app_org: str, app_name: str) -> Path:
    return _user_app_dir(app_org, app_name) / "logs"


def load_or_create_config(app_org: str, app_name: str, app_version: str) -> AppPathsConfig:
    """
    Load config.ini if present; otherwise create it with defaults.

    Always ensures the current application version is written into the INI:
      [app]
      version = <app_version>
    """
    app_dir = _user_app_dir(app_org, app_name)
    cfg_path = app_dir / "config.ini"

    cp = configparser.ConfigParser()
    if cfg_path.exists():
        try:
            cp.read(cfg_path, encoding="utf-8")
        except Exception:
            # If parsing fails, fall back to defaults and overwrite below.
            cp = configparser.ConfigParser()

    # defaults
    if "paths" not in cp:
        cp["paths"] = {}
    if "app" not in cp:
        cp["app"] = {}

    # logs_dir (user-overridable)
    raw_logs = cp["paths"].get("logs_dir", "").strip()
    logs_dir = Path(raw_logs).expanduser() if raw_logs else _default_logs_dir(app_org, app_name)

    # version (always written)
    cp["app"]["version"] = str(app_version)

    # write back if missing or changed or file absent
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8", newline="\n") as f:
            cp.write(f)
    except Exception:
        # If we cannot write, still return a usable default path under home.
        logs_dir = logs_dir if logs_dir else _default_logs_dir(app_org, app_name)

    return AppPathsConfig(config_path=cfg_path, logs_dir=logs_dir, app_version=str(app_version))
