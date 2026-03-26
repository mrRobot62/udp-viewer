from __future__ import annotations

import os
import shutil
from pathlib import Path


def default_save_name(stamp: str) -> str:
    return f"udp_log_{stamp}.txt"


def flush_file_handle(handle: object | None) -> None:
    if handle is None:
        return
    handle.flush()


def fsync_file_handle(handle: object | None) -> None:
    if handle is None:
        return
    handle.flush()
    os.fsync(handle.fileno())


def copy_log_file(source: Path, target: str | Path) -> None:
    shutil.copy2(str(source), str(target))


def write_text_log(target: str | Path, content: str) -> None:
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        if not content.endswith("\n"):
            handle.write("\n")
