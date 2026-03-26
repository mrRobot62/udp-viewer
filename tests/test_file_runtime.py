from __future__ import annotations

from pathlib import Path

from udp_log_viewer.file_runtime import copy_log_file, default_save_name, write_text_log


def test_default_save_name_uses_stamp() -> None:
    assert default_save_name("20260326_231500") == "udp_log_20260326_231500.txt"


def test_write_text_log_appends_trailing_newline(tmp_path: Path) -> None:
    target = tmp_path / "out.txt"
    write_text_log(target, "hello")

    assert target.read_text(encoding="utf-8") == "hello\n"


def test_copy_log_file_copies_contents(tmp_path: Path) -> None:
    source = tmp_path / "src.txt"
    target = tmp_path / "dst.txt"
    source.write_text("abc", encoding="utf-8")

    copy_log_file(source, target)

    assert target.read_text(encoding="utf-8") == "abc"
