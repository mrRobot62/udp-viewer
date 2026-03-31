from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9]{1,15}$")


@dataclass(slots=True)
class RuntimeProject:
    name: str
    root_dir: Path

    @property
    def output_dir(self) -> Path:
        return self.root_dir / self.name


def normalize_project_name(value: str) -> str:
    return (value or "").strip()


def is_valid_project_name(value: str) -> bool:
    return bool(_PROJECT_NAME_RE.fullmatch(normalize_project_name(value)))


def build_project_filename(project_name: str | None, stem: str, stamp: str, suffix: str) -> str:
    normalized_stem = (stem or "").strip().strip("_") or "artifact"
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    if project_name:
        return f"{project_name}_{normalized_stem}_{stamp}{normalized_suffix}"
    return f"{normalized_stem}_{stamp}{normalized_suffix}"


def build_project_title_suffix(project_name: str | None) -> str:
    if not project_name:
        return ""
    return f" ({project_name})"
