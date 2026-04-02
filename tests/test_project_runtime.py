from __future__ import annotations

from datetime import datetime
from pathlib import Path

from udp_log_viewer.project_runtime import (
    PROJECT_README_MAX_CHARS,
    RuntimeProject,
    build_project_readme_default_text,
    build_project_readme_filename,
    build_project_filename,
    build_project_title_suffix,
    initialize_project,
    is_valid_project_name,
    load_project_readme,
    normalize_project_notes,
    write_project_readme,
)


def test_project_name_validation_accepts_short_alnum_names() -> None:
    assert is_valid_project_name("Project42") is True
    assert is_valid_project_name("ABC123xyz") is True
    assert is_valid_project_name("Demo_123") is True
    assert is_valid_project_name("Demo-123") is True
    assert is_valid_project_name("Project_Name_123456") is True
    assert is_valid_project_name("P" * 50) is True


def test_project_name_validation_rejects_invalid_names() -> None:
    assert is_valid_project_name("") is False
    assert is_valid_project_name("project 1") is False
    assert is_valid_project_name("P" * 51) is False


def test_build_project_filename_prefixes_project_name() -> None:
    assert build_project_filename("Demo1", "udp_live", "20260331_120000", ".txt") == "Demo1_udp_live_20260331_120000.txt"
    assert build_project_filename(None, "udp_live", "20260331_120000", ".txt") == "udp_live_20260331_120000.txt"


def test_build_project_title_suffix_formats_project_name() -> None:
    assert build_project_title_suffix("Demo1") == " (Demo1)"
    assert build_project_title_suffix(None) == ""


def test_build_project_readme_filename_uses_project_name() -> None:
    assert build_project_readme_filename("Demo-1") == "README_Demo-1.md"


def test_build_project_readme_default_text_contains_project_and_timestamp() -> None:
    assert build_project_readme_default_text("Demo_1", datetime(2026, 4, 1, 8, 9, 10)) == "# Demo_1 - 2026-04-01 08:09:10\n"


def test_normalize_project_notes_limits_text_length() -> None:
    assert len(normalize_project_notes("x" * (PROJECT_README_MAX_CHARS + 50))) == PROJECT_README_MAX_CHARS


def test_write_and_load_project_readme_roundtrip(tmp_path: Path) -> None:
    project = RuntimeProject(name="Demo-1", root_dir=tmp_path)

    path = write_project_readme(project, "# Demo-1 - 2026-04-01 08:09:10\ntext")

    assert path == project.output_dir / "README_Demo-1.md"
    assert load_project_readme(project) == "# Demo-1 - 2026-04-01 08:09:10\ntext"


def test_initialize_project_creates_directory_and_readme(tmp_path: Path) -> None:
    project = RuntimeProject(name="Demo-1", root_dir=tmp_path)

    path = initialize_project(project, "# Demo-1 - 2026-04-01 08:09:10\ntext")

    assert project.output_dir.is_dir()
    assert path == project.output_dir / "README_Demo-1.md"
    assert load_project_readme(project) == "# Demo-1 - 2026-04-01 08:09:10\ntext"


def test_initialize_project_propagates_directory_creation_errors(tmp_path: Path, monkeypatch) -> None:
    project = RuntimeProject(name="Demo-1", root_dir=tmp_path)

    def fail_mkdir(*args, **kwargs):
        raise PermissionError("access denied")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    try:
        initialize_project(project, "# Demo-1 - 2026-04-01 08:09:10\ntext")
    except PermissionError as exc:
        assert "access denied" in str(exc)
    else:
        raise AssertionError("Expected PermissionError")
