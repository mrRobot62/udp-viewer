# Release 0.16.0 RC1

Release date: 2026-03-31

## Summary

Version `0.16.0` is prepared as a release candidate on the feature
branch and combines the new session-oriented `RESET` workflow with
interactive measurement support in the logic graph.

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

The release-candidate branch was validated with the relevant automated
test sets for runtime helpers, sliding-window behavior, and logic
measurement handling, including:

- `tests/test_core_behavior.py`
- `tests/test_connection_runtime.py`
- `tests/test_listener_runtime.py`
- `tests/test_project_runtime.py`
- `tests/test_sliding_window_behavior.py`

## Packaging Status

- macOS packaging path prepared via `./build_dmg.sh`
- Windows packaging path prepared via `build_exe.bat`,
  `freeze_setup.py`, and the Inno Setup installer flow
- release branch keeps packaging metadata and docs aligned to
  `0.16.0`

## Branching Note

This release candidate is intended to live on the feature branch and is
not merged into `main`. The `main` branch remains on the older stable
line.

## Related Files

- [CHANGELOG.md](/Users/bernhardklein/workspace/python/udp-viewer/CHANGELOG.md)
- [README.md](/Users/bernhardklein/workspace/python/udp-viewer/README.md)
- [README_de.md](/Users/bernhardklein/workspace/python/udp-viewer/README_de.md)
- [USER_GUIDE_en.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_en.md)
- [USER_GUIDE_de.md](/Users/bernhardklein/workspace/python/udp-viewer/docs/USER_GUIDE_de.md)
