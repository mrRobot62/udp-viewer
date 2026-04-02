from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re


_PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
PROJECT_README_MAX_CHARS = 1024


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


def build_project_readme_filename(project_name: str) -> str:
    return f"README_{normalize_project_name(project_name)}.md"


def build_project_readme_default_text(project_name: str, created_at: datetime | None = None) -> str:
    current = created_at or datetime.now()
    return f"# {normalize_project_name(project_name)} - {current.strftime('%Y-%m-%d %H:%M:%S')}\n"


def normalize_project_notes(value: str | None, *, max_chars: int = PROJECT_README_MAX_CHARS) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    return text[:max_chars]


def project_readme_path(project: RuntimeProject) -> Path:
    return project.output_dir / build_project_readme_filename(project.name)


def write_project_readme(project: RuntimeProject, content: str) -> Path:
    path = project_readme_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_project_notes(content)
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return path


def initialize_project(project: RuntimeProject, readme_content: str) -> Path:
    project.output_dir.mkdir(parents=True, exist_ok=True)
    return write_project_readme(project, readme_content)


def load_project_readme(project: RuntimeProject) -> str | None:
    path = project_readme_path(project)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
