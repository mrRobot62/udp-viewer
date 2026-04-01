# Release 0.16.0

Release date: 2026-04-01

## Summary

Version `0.16.0` finalizes the new session-oriented `RESET` workflow,
interactive logic-graph measurement, project notes, keyboard-driven
navigation, and refreshed packaging and release documentation.

## Highlights

- new main-window `RESET` action for starting a fresh log phase inside
  the same application session
- active `PROJECT` context stays unchanged during reset
- current live log is closed cleanly and a fresh live log file is
  prepared immediately
- project descriptions can be authored in the `PROJECT` dialog and are
  written as `README_<projectname>.md` into the project folder
- logic-graph edge measurement with red/blue markers and duration label
- `Shift`-click period measurement in the logic graph
- active measurement pauses the logic graph until `Space` or `Esc`
  clears it
- compact measurement labels move to the right of the blue end marker
  when the span is too short
- `Window Size` runtime and config limits aligned to `1..5000`
- runtime `Legend` toggles in plot and logic graph windows
- explicit `TAB` navigation plus save/screenshot shortcuts in the main
  and graph windows

## Validation

The release branch was validated with the relevant automated test sets
for runtime helpers, sliding-window behavior, logic measurement
handling, and project persistence, including:

- `tests/test_core_behavior.py`
- `tests/test_connection_runtime.py`
- `tests/test_listener_runtime.py`
- `tests/test_project_runtime.py`
- `tests/test_sliding_window_behavior.py`

## Packaging Status

- published release tag: `0.16.0`
- published release assets:
  - `UDPLogViewer-0.16.0.dmg`
  - `UDPLogViewer-0.16.0-Setup.exe`
- local and CI packaging paths are documented in the current build and
  packaging references

## Related Files

- [CHANGELOG.md](/Users/bernhardklein/workspace/python/udp-viewer/CHANGELOG.md)
- [README.md](/Users/bernhardklein/workspace/python/udp-viewer/README.md)
- [README_de.md](/Users/bernhardklein/workspace/python/udp-viewer/README_de.md)
- [USER_GUIDE_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_en.md)
- [USER_GUIDE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_de.md)
- [BUILD_AND_PACKAGING_REFERENCE_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/BUILD_AND_PACKAGING_REFERENCE_en.md)
- [BUILD_AND_PACKAGING_REFERENCE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/BUILD_AND_PACKAGING_REFERENCE_de.md)
