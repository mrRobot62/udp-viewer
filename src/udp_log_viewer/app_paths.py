from __future__ import annotations

"""
App paths + config.ini handling.

Goals:
- Provide a stable, writable base directory for config + logs in bundled apps.
- Default logs dir:
  - macOS:   ~/Library/Application Support/<ORG>/<APP>/logs
  - Windows: %APPDATA%\\<ORG>\\<APP>\\logs
  - Linux:   ~/.local/share/<ORG>/<APP>/logs

The config file is stored next to logs dir as:
  <app_support_dir>/config.ini

Users can edit config.ini to override defaults (e.g., logs_dir).
"""

from dataclasses import dataclass
from pathlib import Path
import configparser
import os
import sys


@dataclass
class AppPathsConfig:
    """Configuration container for AppPaths."""
    app_support_dir: Path
    config_path: Path
    logs_dir: Path
    project_root: Path
    version: str


def _get_app_support_dir(org: str, app: str) -> Path:
    """Return app support dir."""
    if sys.platform.startswith("darwin"):
        return Path.home() / "Library" / "Application Support" / org / app
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / org / app
    # linux/other
    return Path.home() / ".local" / "share" / org / app


def _get_default_documents_dir() -> Path:
    """Return default documents dir."""
    if sys.platform.startswith("win"):
        base = os.environ.get("USERPROFILE") or str(Path.home())
        return Path(base) / "Documents"
    return Path.home() / "Documents"


def get_default_app_support_dir(org: str, app: str) -> Path:
    """Return default app support dir."""
    return _get_app_support_dir(org, app)


def get_default_config_path(org: str, app: str) -> Path:
    """Return default config path."""
    return get_default_app_support_dir(org, app) / "config.ini"


def get_default_project_root_dir() -> Path:
    """Return default project root dir."""
    return _get_default_documents_dir()


def load_or_create_config(
    org: str,
    app: str,
    version: str,
    *,
    config_path: str | Path | None = None,
) -> AppPathsConfig:
    """Load or create config."""
    if config_path is None:
        cfg_path = get_default_config_path(org, app)
    else:
        cfg_path = Path(config_path).expanduser()

    root = cfg_path.parent
    root.mkdir(parents=True, exist_ok=True)

    logs_dir_default = root / "logs"
    project_root_default = get_default_project_root_dir()

    cp = configparser.ConfigParser()
    if cfg_path.exists():
        try:
            cp.read(cfg_path, encoding="utf-8")
        except Exception:
            # If config is unreadable, start fresh but don't crash.
            cp = configparser.ConfigParser()

    if not cp.has_section("app"):
        cp.add_section("app")
    if not cp.has_option("app", "version"):
        cp.set("app", "version", version)

    if not cp.has_section("general"):
        cp.add_section("general")
    if not cp.has_option("general", "version"):
        cp.set("general", "version", version)

    if not cp.has_section("paths"):
        cp.add_section("paths")
    if not cp.has_option("paths", "logs_dir"):
        cp.set("paths", "logs_dir", str(logs_dir_default))
    if not cp.has_option("paths", "project_root"):
        cp.set("paths", "project_root", str(project_root_default))

    # Persist any missing defaults
    try:
        with open(cfg_path, "w", encoding="utf-8", newline="\n") as f:
            cp.write(f)
    except Exception:
        # Still proceed with defaults; caller will handle log creation failures.
        pass

    logs_dir = Path(cp.get("paths", "logs_dir", fallback=str(logs_dir_default))).expanduser()
    project_root = Path(cp.get("paths", "project_root", fallback=str(project_root_default))).expanduser()
    return AppPathsConfig(
        app_support_dir=root,
        config_path=cfg_path,
        logs_dir=logs_dir,
        project_root=project_root,
        version=version,
    )
