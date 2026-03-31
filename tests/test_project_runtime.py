from __future__ import annotations

from udp_log_viewer.project_runtime import (
    build_project_filename,
    build_project_title_suffix,
    is_valid_project_name,
)


def test_project_name_validation_accepts_short_alnum_names() -> None:
    assert is_valid_project_name("Project42") is True
    assert is_valid_project_name("ABC123xyz") is True
    assert is_valid_project_name("Demo_123") is True
    assert is_valid_project_name("Project_Name_123456") is True


def test_project_name_validation_rejects_invalid_names() -> None:
    assert is_valid_project_name("") is False
    assert is_valid_project_name("project-1") is False
    assert is_valid_project_name("abcdefghijklmnopqrstu") is False


def test_build_project_filename_prefixes_project_name() -> None:
    assert build_project_filename("Demo1", "udp_live", "20260331_120000", ".txt") == "Demo1_udp_live_20260331_120000.txt"
    assert build_project_filename(None, "udp_live", "20260331_120000", ".txt") == "udp_live_20260331_120000.txt"


def test_build_project_title_suffix_formats_project_name() -> None:
    assert build_project_title_suffix("Demo1") == " (Demo1)"
    assert build_project_title_suffix(None) == ""
