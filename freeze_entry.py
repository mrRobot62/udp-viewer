"""Frozen entrypoint for cx_Freeze.

This file exists to avoid relative-import issues when the app is frozen.
It imports and runs the regular package main().
"""

from __future__ import annotations


def main() -> int:
    # Import the package entrypoint in a way that works both in dev and frozen builds.
    from udp_log_viewer.main import main as app_main  # type: ignore
    return int(app_main())


if __name__ == "__main__":
    raise SystemExit(main())
